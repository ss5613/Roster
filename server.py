"""
server.py — Flask backend for ShiftPulse
Run: python server.py → open http://localhost:5000
"""
import os, json
from datetime import datetime, date, time
from flask import Flask, jsonify, send_from_directory, request
import pandas as pd
from data_loader import (
    load_and_process_all, get_employee_status, get_all_support_types,
    is_available, classify_real_time, SHIFT_COLORS, SHIFT_COLOR_BG,
)

app = Flask(__name__, static_folder="static")
EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Shift draft (1).xlsx")

employee_master, shift_data, shift_timings, shift_lookup = load_and_process_all(EXCEL_PATH)
all_employees = sorted(shift_data["Associate Name"].unique().tolist()) if not shift_data.empty else []
all_shifts = sorted([c for c in shift_data["Shift Code"].unique() if c and c not in ("","NAN","NONE")]) if not shift_data.empty else []
all_support_types = get_all_support_types(employee_master) if not employee_master.empty else []
all_locations = sorted([l for l in shift_data["Location"].unique() if l != "N/A"]) if "Location" in shift_data.columns else []
all_dates = sorted(shift_data["Date"].dropna().unique().tolist()) if not shift_data.empty else []

def d2s(d):
    if isinstance(d, datetime): return d.date().isoformat()
    if isinstance(d, date): return d.isoformat()
    return str(d)

def timing_str(code):
    c = str(code).strip().upper()
    if c in shift_lookup:
        sl = shift_lookup[c]
        if sl.get("timing_str") and sl["timing_str"] not in ("","nan","None"): return sl["timing_str"]
        return f"{sl['start_str']} - {sl['end_str']}"
    return "—"

@app.route("/")
def index(): return send_from_directory("static", "index.html")

@app.route("/api/meta")
def api_meta():
    legend = []
    for code in all_shifts:
        legend.append({"code":code,"color":SHIFT_COLORS.get(code,"#64748b"),"bg":SHIFT_COLOR_BG.get(code,"rgba(100,116,139,0.15)"),"timing":timing_str(code)})
    for code,label in [("WO","Week Off"),("HO","Holiday"),("LEAVE","Leave")]:
        legend.append({"code":code,"color":SHIFT_COLORS.get(code,"#64748b"),"bg":SHIFT_COLOR_BG.get(code,"rgba(100,116,139,0.15)"),"timing":label})
    return jsonify({"employees":all_employees,"shifts":all_shifts,"supportTypes":all_support_types,"locations":all_locations,
        "dateRange":{"min":d2s(min(all_dates)) if all_dates else None,"max":d2s(max(all_dates)) if all_dates else None},"legend":legend})

@app.route("/api/employee-lookup")
def api_employee_lookup():
    name=request.args.get("name",""); d=request.args.get("date",date.today().isoformat()); ld=date.fromisoformat(d); ct=datetime.now().time()
    es=shift_data[(shift_data["Associate Name"].str.upper()==name.upper())&(shift_data["Date"]==ld)]
    if es.empty: return jsonify({"found":False})
    row=es.iloc[0]; sc=str(row["Shift Code"]).strip().upper()
    ti=None
    if sc in shift_lookup:
        t=shift_lookup[sc]; sh=t["start"].hour+t["start"].minute/60; eh=t["end"].hour+t["end"].minute/60
        lp=(sh/24)*100; wp=((eh-sh)/24)*100 if sh<eh else ((24-sh+eh)/24)*100
        ti={"timing":timing_str(sc),"start":t["start_str"],"end":t["end_str"],"leftPct":lp,"widthPct":min(wp,100-lp)}
    return jsonify({"found":True,"name":str(row["Associate Name"]),"shiftCode":sc,"status":get_employee_status(sc),
        "realTime":classify_real_time(sc,shift_lookup,ct),"color":SHIFT_COLORS.get(sc,"#64748b"),
        "supportTypes":str(row.get("All Support Str","N/A")),"reportingTo":str(row.get("Reporting Manager","N/A")),
        "location":str(row.get("Location","N/A")),"gender":str(row.get("Gender","N/A")),"timing":ti})

@app.route("/api/calendar")
def api_calendar():
    name=request.args.get("name",""); month=int(request.args.get("month",datetime.now().month)); year=int(request.args.get("year",datetime.now().year))
    ed=shift_data[(shift_data["Associate Name"].str.upper()==name.upper())&(shift_data["Date"].apply(lambda d:d.month==month and d.year==year if isinstance(d,date) else False))]
    ds={}
    for _,row in ed.iterrows():
        if isinstance(row["Date"],date):
            c=str(row["Shift Code"]).strip().upper()
            ds[str(row["Date"].day)]={"code":c,"color":SHIFT_COLORS.get(c,"#64748b"),"bg":SHIFT_COLOR_BG.get(c,"rgba(100,116,139,0.15)"),"timing":timing_str(c),"status":get_employee_status(c)}
    am=sorted(set((d.month,d.year) for d in all_dates if isinstance(d,date)))
    return jsonify({"dayShifts":ds,"availableMonths":[{"month":m,"year":y} for m,y in am]})

@app.route("/api/shift-availability")
def api_shift_availability():
    d=request.args.get("date",date.today().isoformat()); sf=request.args.get("shift","All Shifts"); spf=request.args.get("support","All Types")
    ld=date.fromisoformat(d); dd=shift_data[shift_data["Date"]==ld].copy()
    if sf!="All Shifts": dd=dd[dd["Shift Code"].str.upper()==sf.upper()]
    if spf!="All Types": dd=dd[dd["All Support Types"].apply(lambda t:spf.upper() in [x.upper() for x in t] if isinstance(t,list) else False)]
    if dd.empty: return jsonify({"total":0,"available":[],"unavailable":[],"availableCount":0,"unavailableCount":0})
    am=dd["Shift Code"].apply(is_available); av=dd[am]; un=dd[~am]
    def r2d(row,t=True):
        sc=str(row["Shift Code"]).strip().upper()
        r={"name":str(row["Associate Name"]),"shiftCode":sc,"supportTypes":str(row.get("All Support Str","N/A")),"location":str(row.get("Location","N/A")),"color":SHIFT_COLORS.get(sc,"#64748b"),"reason":get_employee_status(sc)}
        if t: r["timing"]=timing_str(sc)
        return r
    return jsonify({"total":len(dd),"availableCount":len(av),"unavailableCount":len(un),"available":[r2d(r) for _,r in av.iterrows()],"unavailable":[r2d(r,False) for _,r in un.iterrows()]})

@app.route("/api/realtime")
def api_realtime():
    tv=date.today(); ct=datetime.now().time(); td=shift_data[shift_data["Date"]==tv].copy()
    if td.empty: return jsonify({"hasData":False,"dateRange":{"min":d2s(min(all_dates)) if all_dates else None,"max":d2s(max(all_dates)) if all_dates else None}})
    td["RTS"]=td["Shift Code"].apply(lambda c:classify_real_time(c,shift_lookup,ct))
    def ec(row):
        sc=str(row["Shift Code"]).strip().upper()
        return {"name":str(row["Associate Name"]),"shiftCode":sc,"color":SHIFT_COLORS.get(sc,"#64748b"),"timing":timing_str(sc),"supportTypes":str(row.get("All Support Str","N/A")),"location":str(row.get("Location","N/A")),"reason":get_employee_status(sc)}
    return jsonify({"hasData":True,"counts":{"active":len(td[td["RTS"]=="Active Now"]),"upcoming":len(td[td["RTS"]=="Upcoming Shift"]),"offDuty":len(td[td["RTS"]=="Off Duty"]),"unknown":len(td[td["RTS"]=="Unknown Shift"])},
        "active":[ec(r) for _,r in td[td["RTS"]=="Active Now"].iterrows()],"upcoming":[ec(r) for _,r in td[td["RTS"]=="Upcoming Shift"].iterrows()],"offDuty":[ec(r) for _,r in td[td["RTS"]=="Off Duty"].iterrows()]})

@app.route("/api/analytics")
def api_analytics():
    d=request.args.get("date",date.today().isoformat()); ad=date.fromisoformat(d); dd=shift_data[shift_data["Date"]==ad].copy()
    if dd.empty: return jsonify({"hasData":False})
    dist=dd["Shift Code"].value_counts().reset_index(); dist.columns=["code","count"]; total=dist["count"].sum()
    sd=[{"code":r["code"],"count":int(r["count"]),"percentage":round(r["count"]/total*100,1),"color":SHIFT_COLORS.get(r["code"],"#64748b"),"timing":timing_str(r["code"])} for _,r in dist.iterrows()]
    sb=[]
    if "Support Type" in dd.columns:
        g=dd.groupby(["Support Type","Shift Code"]).size().reset_index(name="count")
        sb=[{"supportType":str(r["Support Type"]),"shiftCode":str(r["Shift Code"]),"count":int(r["count"]),"color":SHIFT_COLORS.get(str(r["Shift Code"]),"#64748b")} for _,r in g.iterrows()]
    lb=[]
    if "Location" in dd.columns:
        av=dd[dd["Shift Code"].apply(is_available)]
        if not av.empty:
            loc=av.groupby("Location").size().reset_index(name="count")
            lb=[{"location":str(r["Location"]),"count":int(r["count"])} for _,r in loc.iterrows()]
    return jsonify({"hasData":True,"shiftDistribution":sd,"supportBreakdown":sb,"locationBreakdown":lb})

@app.route("/api/smart-filter")
def api_smart_filter():
    d=request.args.get("date",date.today().isoformat()); shifts=request.args.getlist("shift"); supports=request.args.getlist("support")
    locations=request.args.getlist("location"); oa=request.args.get("available","true")=="true"; fd=date.fromisoformat(d); ct=datetime.now().time()
    f=shift_data[shift_data["Date"]==fd].copy()
    if shifts: f=f[f["Shift Code"].str.upper().isin([s.upper() for s in shifts])]
    if supports: f=f[f["All Support Types"].apply(lambda t:any(x.upper() in [s.upper() for s in supports] for x in t) if isinstance(t,list) else False)]
    if locations: f=f[f["Location"].str.upper().isin([l.upper() for l in locations])]
    if oa: f=f[f["Shift Code"].apply(is_available)]
    res=[]
    for _,row in f.iterrows():
        sc=str(row["Shift Code"]).strip().upper()
        res.append({"name":str(row["Associate Name"]),"shiftCode":sc,"supportTypes":str(row.get("All Support Str","N/A")),"location":str(row.get("Location","N/A")),
            "reportingTo":str(row.get("Reporting Manager","N/A")),"timing":timing_str(sc),"status":get_employee_status(sc),"realTime":classify_real_time(sc,shift_lookup,ct),"color":SHIFT_COLORS.get(sc,"#64748b")})
    return jsonify({"count":len(res),"results":res})

@app.route("/api/reload",methods=["POST"])
def api_reload():
    global employee_master,shift_data,shift_timings,shift_lookup,all_employees,all_shifts,all_support_types,all_locations,all_dates
    employee_master,shift_data,shift_timings,shift_lookup=load_and_process_all(EXCEL_PATH)
    all_employees=sorted(shift_data["Associate Name"].unique().tolist()) if not shift_data.empty else []
    all_shifts=sorted([c for c in shift_data["Shift Code"].unique() if c and c not in ("","NAN","NONE")]) if not shift_data.empty else []
    all_support_types=get_all_support_types(employee_master) if not employee_master.empty else []
    all_locations=sorted([l for l in shift_data["Location"].unique() if l!="N/A"]) if "Location" in shift_data.columns else []
    all_dates=sorted(shift_data["Date"].dropna().unique().tolist()) if not shift_data.empty else []
    return jsonify({"success":True})

if __name__=="__main__":
    print("⚡ ShiftPulse starting on http://localhost:5000")
    app.run(host="0.0.0.0",port=5000,debug=True)
