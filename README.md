# ⚡ ShiftPulse — Workforce Manager

A premium Shift Management & Workforce Availability Dashboard built with Streamlit.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install streamlit pandas openpyxl plotly
```

### 2. Run the App
```bash
cd "c:\Users\sudik\OneDrive\Documents\KHUSHI\Antigravity\Roster Draft"
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## 📁 File Structure

```
Roster Draft/
├── app.py                  # Main Streamlit application (UI + features)
├── data_loader.py          # Data loading, cleaning, and processing module
├── requirements.txt        # Python dependencies
├── Shift draft (1).xlsx    # Source Excel data
└── README.md               # This file
```

## 🎯 Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Employee Lookup** | Search any employee, see today's shift, timing, and status |
| 2 | **Calendar View** | Full month color-coded shift calendar per employee |
| 3 | **Shift & Availability** | See who's in which shift, with availability summary |
| 4 | **Real-Time Status** | Live classification: Active Now / Upcoming / Off Duty |
| 5 | **Analytics** | Shift distribution charts, support-type sunburst, location breakdown |
| 6 | **Smart Multi-Filter** | Combine Date + Shift + Support Type + Location filters |

## 🎨 Color Coding

| Code | Color | Meaning |
|------|-------|---------|
| G | 🟢 Green | General Shift |
| A | 🔵 Blue | Afternoon Shift |
| B | 🟣 Purple | Night Shift |
| WO | ⚪ Grey | Week Off |
| HO | 🟠 Orange | Holiday |
| LEAVE | 🔴 Red | Leave |

## 📊 Excel File Format

The app auto-detects three sheets:

1. **Employee Master** — Associate Name, Support Type, Reporting Manager, Location
2. **Shift Allocation** — Employee rows × Date columns, values are shift codes
3. **Shift Timings** — Shift Code, Start Time, End Time
