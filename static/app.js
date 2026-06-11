// ═══════════════════════════════════════════════════════════════
// ShiftPulse — Frontend Application Logic
// ═══════════════════════════════════════════════════════════════

let META = {};
const today = new Date().toISOString().split('T')[0];
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

// ── Utilities ──
async function api(url) { const r = await fetch(url); return r.json(); }
function $(id) { return document.getElementById(id); }
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function loading() { return '<div class="loading-overlay"><div class="spinner"></div>Loading...</div>'; }

function metricCard(label, value, delta, deltaClass) {
    return `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value">${value}</div>${delta ? `<div class="metric-delta ${deltaClass||''}">${delta}</div>` : ''}</div>`;
}

function tableHTML(headers, rows) {
    let h = '<div class="table-wrapper"><table class="data-table"><thead><tr>';
    headers.forEach(x => h += `<th>${x}</th>`);
    h += '</tr></thead><tbody>';
    rows.forEach(r => { h += '<tr>'; r.forEach(c => h += `<td>${c}</td>`); h += '</tr>'; });
    return h + '</tbody></table></div>';
}

// ── Clock ──
function updateClock() {
    const now = new Date();
    $('sb-clock-time').textContent = now.toLocaleTimeString('en-US', {hour:'2-digit',minute:'2-digit',hour12:true});
    $('sb-clock-date').textContent = now.toLocaleDateString('en-US', {weekday:'long',year:'numeric',month:'long',day:'numeric'});
}
setInterval(updateClock, 1000); updateClock();

// ── Tabs ──
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        $(btn.dataset.tab).classList.add('active');
    });
});

// ── Init ──
async function init() {
    META = await api('/api/meta');
    $('sb-emp-count').textContent = META.employees.length;
    $('sb-shift-count').textContent = META.shifts.length;
    if (META.dateRange.min) $('sb-date-range').textContent = `📅 Data: ${META.dateRange.min} → ${META.dateRange.max}`;

    // Legend
    let lg = '';
    META.legend.forEach(l => {
        lg += `<div class="legend-item"><span class="legend-dot" style="background:${l.color}"></span><span class="legend-code" style="color:${l.color}">${l.code}</span><span class="legend-timing">${l.timing}</span></div>`;
    });
    $('sb-legend').innerHTML = lg;

    // Populate selects
    const empOpts = '<option value="">Select...</option>' + META.employees.map(e => `<option>${esc(e)}</option>`).join('');
    $('t1-emp').innerHTML = empOpts;
    $('t2-emp').innerHTML = empOpts;

    // Shifts/support selects
    $('t3-shift').innerHTML = '<option>All Shifts</option>' + META.shifts.map(s => `<option>${s}</option>`).join('');
    $('t3-support').innerHTML = '<option>All Types</option>' + META.supportTypes.map(s => `<option>${esc(s)}</option>`).join('');

    // Dates
    [$('t1-date'),$('t3-date'),$('t5-date'),$('t6-date')].forEach(el => el.value = today);

    // Pills for smart filter
    buildPills('t6-shifts', META.shifts);
    buildPills('t6-supports', META.supportTypes);
    buildPills('t6-locations', META.locations);

    // Month selector for calendar
    if (META.dateRange.min) {
        const cal = await api(`/api/calendar?name=&month=1&year=2026`);
        let mhtml = '';
        (cal.availableMonths || []).forEach(m => {
            const sel = (m.month === new Date().getMonth()+1 && m.year === new Date().getFullYear()) ? ' selected' : '';
            mhtml += `<option value="${m.month}-${m.year}"${sel}>${MONTHS[m.month-1]} ${m.year}</option>`;
        });
        $('t2-month').innerHTML = mhtml;
    }

    // Event listeners
    $('t1-emp').addEventListener('change', loadEmployeeLookup);
    $('t1-date').addEventListener('change', loadEmployeeLookup);
    $('t2-emp').addEventListener('change', loadCalendar);
    $('t2-month').addEventListener('change', loadCalendar);
    $('t3-date').addEventListener('change', loadAvailability);
    $('t3-shift').addEventListener('change', loadAvailability);
    $('t3-support').addEventListener('change', loadAvailability);
    $('t5-date').addEventListener('change', loadAnalytics);

    loadRealtime();
}

function buildPills(containerId, items) {
    const c = $(containerId);
    c.innerHTML = items.map(i => `<span class="pill" data-val="${esc(i)}" onclick="this.classList.toggle('selected');loadSmartFilter()">${esc(i)}</span>`).join('');
}

function getSelectedPills(containerId) {
    return Array.from($(containerId).querySelectorAll('.pill.selected')).map(p => p.dataset.val);
}

// ═══ TAB 1: Employee Lookup ═══
async function loadEmployeeLookup() {
    const name = $('t1-emp').value, dt = $('t1-date').value;
    if (!name) { $('t1-result').innerHTML = '<div class="info-box">👆 Select an employee from the dropdown to view their shift details.</div>'; return; }
    $('t1-result').innerHTML = loading();
    const d = await api(`/api/employee-lookup?name=${encodeURIComponent(name)}&date=${dt}`);
    if (!d.found) { $('t1-result').innerHTML = `<div class="warning-box">No shift data found for <b>${esc(name)}</b> on <b>${dt}</b>.</div>`; return; }

    let timeline = '';
    if (d.timing) {
        timeline = `<div class="sub-header">⏰ Shift Timing</div>
            <p><b>Timing:</b> ${d.timing.timing}</p><p><b>Start:</b> ${d.timing.start}</p><p><b>End:</b> ${d.timing.end}</p>
            <div class="timeline-bar"><div class="timeline-fill" style="left:${d.timing.leftPct}%;width:${d.timing.widthPct}%;background:${d.color}"></div>
            <div class="timeline-labels">0h ─────────── 12h ─────────── 24h</div></div>`;
    } else if (['Leave','Week Off','Holiday'].includes(d.status)) {
        timeline = `<div class="info-box">Employee is on <b>${d.status}</b> today.</div>`;
    }

    $('t1-result').innerHTML = `<div class="gradient-divider"></div>
        <div class="metrics-row">${metricCard('👤 Employee', esc(d.name))}${metricCard('📋 Shift', d.shiftCode||'—')}${metricCard('📌 Status', d.status)}${metricCard('⚡ Right Now', d.realTime)}</div>
        <div class="gradient-divider"></div>
        <div class="two-col">
            <div class="glass-card"><div class="sub-header">📝 Employee Details</div>
                <p><b>Support Types:</b> ${esc(d.supportTypes)}</p><p><b>Reporting To:</b> ${esc(d.reportingTo)}</p>
                <p><b>Location:</b> ${esc(d.location)}</p><p><b>Gender:</b> ${esc(d.gender)}</p></div>
            <div class="glass-card">${timeline}</div>
        </div>`;
}

// ═══ TAB 2: Calendar ═══
async function loadCalendar() {
    const name = $('t2-emp').value;
    if (!name) { $('t2-result').innerHTML = '<div class="info-box">👆 Select an employee to view their monthly shift calendar.</div>'; return; }
    const mv = $('t2-month').value.split('-'), month = parseInt(mv[0]), year = parseInt(mv[1]);
    $('t2-result').innerHTML = loading();
    const d = await api(`/api/calendar?name=${encodeURIComponent(name)}&month=${month}&year=${year}`);

    const todayObj = new Date();
    const firstDay = new Date(year, month-1, 1).getDay();
    const adj = (firstDay === 0) ? 6 : firstDay - 1; // Monday start
    const totalDays = new Date(year, month, 0).getDate();

    let cal = `<h3 style="margin-bottom:12px">${MONTHS[month-1]} ${year} — ${esc(name)}</h3><div class="cal-grid">`;
    ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].forEach(d2 => cal += `<div class="cal-header">${d2}</div>`);
    for (let i = 0; i < adj; i++) cal += '<div class="cal-empty"></div>';

    const counts = {};
    for (let day = 1; day <= totalDays; day++) {
        const info = d.dayShifts[String(day)] || {};
        const code = info.code || '';
        const color = info.color || '#64748b';
        const bg = info.bg || 'rgba(100,116,139,0.15)';
        const isToday = (day === todayObj.getDate() && month === todayObj.getMonth()+1 && year === todayObj.getFullYear());
        const tooltip = code ? `${code}: ${info.timing || info.status || ''}` : '';
        if (code) counts[code] = (counts[code]||0) + 1;
        cal += `<div class="cal-day${isToday?' cal-today':''}" style="background:${bg};color:${color};border-color:${color}33" title="${tooltip}"><span class="day-num">${day}</span><span class="shift-label">${code||'—'}</span></div>`;
    }
    cal += '</div>';

    // Summary
    cal += '<div class="gradient-divider"></div><div class="sub-header">📊 Monthly Summary</div><div class="cal-summary">';
    Object.entries(counts).sort((a,b)=>b[1]-a[1]).forEach(([code,count]) => {
        const color = (d.dayShifts[Object.keys(d.dayShifts).find(k=>d.dayShifts[k].code===code)]||{}).color||'#64748b';
        cal += `<div class="cal-summary-item"><div class="count" style="color:${color}">${count}</div><div class="label">${code} Days</div></div>`;
    });
    cal += '</div>';
    $('t2-result').innerHTML = cal;
}

// ═══ TAB 3: Availability ═══
async function loadAvailability() {
    const dt=$('t3-date').value, sf=$('t3-shift').value, sp=$('t3-support').value;
    $('t3-result').innerHTML = loading();
    const d = await api(`/api/shift-availability?date=${dt}&shift=${encodeURIComponent(sf)}&support=${encodeURIComponent(sp)}`);
    if (d.total === 0) { $('t3-result').innerHTML = `<div class="warning-box">No data found for <b>${dt}</b> with the selected filters.</div>`; return; }

    const pct = d.total > 0 ? Math.round(d.availableCount/d.total*100) : 0;
    let h = `<div class="metrics-row">${metricCard('👥 Total Employees', d.total)}${metricCard('✅ Available', d.availableCount, `${pct}%`, 'positive')}${metricCard('🚫 Unavailable', d.unavailableCount, d.unavailableCount>0?`-${d.unavailableCount}`:'0', 'negative')}</div>`;
    h += '<div class="gradient-divider"></div><div class="two-col">';

    // Available
    h += '<div><div class="sub-header">✅ Available Employees</div>';
    if (d.available.length) {
        h += tableHTML(['Employee','Shift','Support Types','Location','Timing'], d.available.map(e=>[esc(e.name),`<span style="color:${e.color};font-weight:600">${e.shiftCode}</span>`,esc(e.supportTypes),esc(e.location),e.timing||'']));
    } else h += '<div class="info-box">No available employees for this filter.</div>';
    h += '</div>';

    // Unavailable
    h += '<div><div class="sub-header">🚫 Unavailable Employees</div>';
    if (d.unavailable.length) {
        h += tableHTML(['Employee','Reason','Support Types','Location'], d.unavailable.map(e=>[esc(e.name),e.reason,esc(e.supportTypes),esc(e.location)]));
    } else h += '<div class="success-box">Everyone is available! 🎉</div>';
    h += '</div></div>';

    $('t3-result').innerHTML = h;
}

// ═══ TAB 4: Real-Time ═══
async function loadRealtime() {
    const now = new Date();
    $('t4-time').textContent = `🕐 ${now.toLocaleTimeString('en-US')} — ${now.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'})}`;
    $('t4-result').innerHTML = loading();
    const d = await api('/api/realtime');

    if (!d.hasData) { $('t4-result').innerHTML = `<div class="warning-box">No shift data available for today.${d.dateRange.min ? ` Available dates: <b>${d.dateRange.min}</b> to <b>${d.dateRange.max}</b>` : ''}</div>`; return; }

    let h = `<div class="metrics-row">${metricCard('🟢 Active Now', d.counts.active)}${metricCard('🟡 Upcoming', d.counts.upcoming)}${metricCard('⚪ Off Duty', d.counts.offDuty)}${metricCard('❓ Unknown', d.counts.unknown)}</div>`;
    h += '<div class="gradient-divider"></div><div class="sub-header">🟢 Currently Active Employees</div>';
    if (d.active.length) {
        h += '<div class="emp-grid">';
        d.active.forEach(e => {
            h += `<div class="emp-card" style="border-left-color:${e.color}"><div class="emp-name">${esc(e.name)}</div><div class="emp-shift" style="color:${e.color}">● Shift ${e.shiftCode} — ${e.timing}</div><div class="emp-support">${esc(e.supportTypes)}</div><div class="emp-location">📍 ${esc(e.location)}</div></div>`;
        });
        h += '</div>';
    } else h += '<div class="info-box">No employees are currently active.</div>';

    h += '<div class="gradient-divider"></div><div class="sub-header">🟡 Upcoming Shifts</div>';
    if (d.upcoming.length) {
        h += tableHTML(['Employee','Shift','Support Types','Location','Timing'], d.upcoming.map(e=>[esc(e.name),`<span style="color:${e.color};font-weight:600">${e.shiftCode}</span>`,esc(e.supportTypes),esc(e.location),e.timing]));
    } else h += '<div class="info-box">No upcoming shifts.</div>';

    // Off duty collapsible
    h += `<div style="margin-top:16px"><div class="collapsible-header" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open')">⚪ Off Duty / Leave / Week Off Employees <span class="arrow">▼</span></div><div class="collapsible-body">`;
    if (d.offDuty.length) {
        h += '<div style="padding:12px 0">' + tableHTML(['Employee','Shift','Support Types','Reason'], d.offDuty.map(e=>[esc(e.name),e.shiftCode,esc(e.supportTypes),e.reason])) + '</div>';
    } else h += '<div class="info-box" style="margin:12px 0">No off-duty employees.</div>';
    h += '</div></div>';

    $('t4-result').innerHTML = h;
}

// ═══ TAB 5: Analytics ═══
let chartInstances = {};
async function loadAnalytics() {
    const dt = $('t5-date').value;
    $('t5-result').innerHTML = loading();
    const d = await api(`/api/analytics?date=${dt}`);
    if (!d.hasData) { $('t5-result').innerHTML = `<div class="warning-box">No data available for <b>${dt}</b>.</div>`; return; }

    // Destroy old charts
    Object.values(chartInstances).forEach(c => c.destroy());
    chartInstances = {};

    let h = '<div class="gradient-divider"></div><div class="two-col"><div class="glass-card"><div class="sub-header">📊 Shift Distribution</div><div class="chart-container"><canvas id="chart-dist"></canvas></div></div>';
    h += '<div class="glass-card"><div class="sub-header">📋 Summary Table</div>';
    const total = d.shiftDistribution.reduce((s,x)=>s+x.count,0);
    h += tableHTML(['Shift','Employees','%','Timing'], d.shiftDistribution.map(x=>[`<span style="color:${x.color};font-weight:700">${x.code}</span>`,x.count,x.percentage+'%',x.timing]));
    h += '</div></div>';

    if (d.supportBreakdown.length) {
        h += '<div class="gradient-divider"></div><div class="glass-card"><div class="sub-header">🏢 Support Type × Shift Breakdown</div><div class="chart-container"><canvas id="chart-support"></canvas></div></div>';
    }
    if (d.locationBreakdown.length) {
        h += '<div class="gradient-divider"></div><div class="glass-card"><div class="sub-header">📍 Availability by Location</div><div class="chart-container"><canvas id="chart-location"></canvas></div></div>';
    }
    $('t5-result').innerHTML = h;

    // Render charts
    setTimeout(() => {
        const distCtx = document.getElementById('chart-dist');
        if (distCtx) {
            chartInstances.dist = new Chart(distCtx, {
                type: 'bar',
                data: { labels: d.shiftDistribution.map(x=>x.code), datasets: [{ data: d.shiftDistribution.map(x=>x.count), backgroundColor: d.shiftDistribution.map(x=>x.color), borderWidth: 0, borderRadius: 6 }] },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.03)' } }, y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.03)' } } } }
            });
        }
        const supCtx = document.getElementById('chart-support');
        if (supCtx && d.supportBreakdown.length) {
            const supTypes = [...new Set(d.supportBreakdown.map(x=>x.supportType))];
            const shifts = [...new Set(d.supportBreakdown.map(x=>x.shiftCode))];
            const datasets = shifts.map(s => ({
                label: s, backgroundColor: d.supportBreakdown.find(x=>x.shiftCode===s)?.color || '#64748b',
                data: supTypes.map(t => { const f = d.supportBreakdown.find(x=>x.supportType===t&&x.shiftCode===s); return f?f.count:0; }), borderRadius: 4
            }));
            chartInstances.support = new Chart(supCtx, {
                type: 'bar',
                data: { labels: supTypes, datasets },
                options: { responsive: true, plugins: { legend: { labels: { color: '#e2e8f0' } } }, scales: { x: { stacked: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.03)' } }, y: { stacked: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.03)' } } } }
            });
        }
        const locCtx = document.getElementById('chart-location');
        if (locCtx && d.locationBreakdown.length) {
            chartInstances.location = new Chart(locCtx, {
                type: 'bar',
                data: { labels: d.locationBreakdown.map(x=>x.location), datasets: [{ data: d.locationBreakdown.map(x=>x.count), backgroundColor: '#818cf8', borderRadius: 6, borderWidth: 0 }] },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.03)' } }, y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.03)' } } } }
            });
        }
    }, 50);
}

// ═══ TAB 6: Smart Filter ═══
async function loadSmartFilter() {
    const dt=$('t6-date').value, shifts=getSelectedPills('t6-shifts'), supports=getSelectedPills('t6-supports'), locations=getSelectedPills('t6-locations');
    const avail = $('t6-toggle').classList.contains('active');
    let url = `/api/smart-filter?date=${dt}&available=${avail}`;
    shifts.forEach(s => url += `&shift=${encodeURIComponent(s)}`);
    supports.forEach(s => url += `&support=${encodeURIComponent(s)}`);
    locations.forEach(s => url += `&location=${encodeURIComponent(s)}`);

    $('t6-result').innerHTML = loading();
    const d = await api(url);

    let parts = [`<b>${new Date(dt+'T00:00').toLocaleDateString('en-US',{weekday:'long',month:'short',day:'numeric'})}</b>`];
    if (shifts.length) parts.push(`Shifts: ${shifts.join(', ')}`);
    if (supports.length) parts.push(`Support: ${supports.join(', ')}`);
    if (locations.length) parts.push(`Location: ${locations.join(', ')}`);

    let h = `<p style="margin-bottom:8px">🔎 Showing results for: ${parts.join(' | ')}</p><p style="font-weight:700;margin-bottom:16px">${d.count} employee(s) found</p>`;

    if (d.results.length) {
        h += tableHTML(['Employee','Shift','Support Types','Location','Reports To','Timing','Status','Now'],
            d.results.map(e=>[esc(e.name),`<span style="color:${e.color};font-weight:600">${e.shiftCode}</span>`,esc(e.supportTypes),esc(e.location),esc(e.reportingTo),e.timing,e.status,e.realTime]));
        // CSV download
        let csv = 'Employee,Shift,Support Types,Location,Reports To,Timing,Status,Real-Time\n';
        d.results.forEach(e => csv += `"${e.name}","${e.shiftCode}","${e.supportTypes}","${e.location}","${e.reportingTo}","${e.timing}","${e.status}","${e.realTime}"\n`);
        const blob = new Blob([csv], {type:'text/csv'});
        const blobUrl = URL.createObjectURL(blob);
        h += `<a href="${blobUrl}" download="shift_filter_${dt}.csv" class="btn-download">📥 Download Results as CSV</a>`;
    } else {
        h += '<div class="info-box">No employees match the current filters. Try adjusting your criteria.</div>';
    }
    $('t6-result').innerHTML = h;
}

$('t6-date').addEventListener?.('change', loadSmartFilter);
setTimeout(() => $('t6-date')?.addEventListener('change', loadSmartFilter), 100);

async function refreshData() {
    await fetch('/api/reload', {method:'POST'});
    location.reload();
}

// ── Boot ──
init();
