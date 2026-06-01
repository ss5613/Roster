"""
data_loader.py — Loads and processes Excel data for Shift Management App.

Handles:
  - Reading exact sheet structure: 'Employee Details', 'April 2026', 'Timings'
  - Employee master with Support 1–11 columns (multiple support types per employee)
  - Shift timings in combined format: "9:00 AM - 6:00 PM"
  - Shift allocation as datetime columns
  - Reshaping shift allocation from wide to long (melted) format
  - Filtering and availability logic
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, date
from typing import Optional, Tuple, Dict, List
import os
import re


# ─── Shift Code Constants ───
UNAVAILABLE_CODES = {"WO", "HO", "LEAVE", "L", "OFF", "NA", ""}
SHIFT_COLORS = {
    "G":     "#22c55e",   # Green
    "A":     "#3b82f6",   # Blue
    "B":     "#a855f7",   # Purple
    "LEAVE": "#ef4444",   # Red
    "L":     "#ef4444",   # Red
    "WO":    "#6b7280",   # Grey
    "HO":    "#f97316",   # Orange
    "GN":    "#10b981",   # Emerald (General Night variant)
    "AN":    "#2563eb",   # Darker Blue (Afternoon Night variant)
    "R":     "#ec4899",   # Pink (Rotational)
}
SHIFT_COLOR_BG = {
    "G":     "rgba(34,197,94,0.15)",
    "A":     "rgba(59,130,246,0.15)",
    "B":     "rgba(168,85,247,0.15)",
    "LEAVE": "rgba(239,68,68,0.15)",
    "L":     "rgba(239,68,68,0.15)",
    "WO":    "rgba(107,114,128,0.15)",
    "HO":    "rgba(249,115,22,0.15)",
    "GN":    "rgba(16,185,129,0.15)",
    "AN":    "rgba(37,99,235,0.15)",
    "R":     "rgba(236,72,153,0.15)",
}


def load_excel(filepath: str) -> Dict[str, pd.DataFrame]:
    """Load all sheets from the Excel file into a dictionary of DataFrames."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Excel file not found: {filepath}")
    return pd.read_excel(filepath, sheet_name=None, engine="openpyxl")


def clean_employee_master(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean employee master from 'Employee Details' sheet.
    
    Actual columns: SL No, Associate Name, Gender, Support 1-11, Reporting To, Location
    We combine Support 1–11 into a single 'Support Types' list and keep first as primary.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Associate Name", "Support Type", "All Support Types",
            "Gender", "Reporting Manager", "Location"
        ])
    
    df = df.copy()
    
    # Standardize known columns
    col_map = {}
    for col in df.columns:
        cl = str(col).lower().strip()
        if cl == "associate name" or cl == "employee name":
            col_map[col] = "Associate Name"
        elif cl == "reporting to" or cl == "reporting manager":
            col_map[col] = "Reporting Manager"
        elif cl == "location":
            col_map[col] = "Location"
        elif cl == "gender":
            col_map[col] = "Gender"
    
    df = df.rename(columns=col_map)
    
    # Find all Support columns (Support 1, Support 2, ..., Support 11)
    support_cols = [c for c in df.columns if str(c).lower().startswith("support")]
    
    # Combine all support types into a list, taking the first non-null as primary
    def get_support_types(row):
        types = []
        for col in support_cols:
            val = str(row[col]).strip() if pd.notna(row[col]) else ""
            if val and val.lower() not in ("nan", "none", ""):
                types.append(val)
        return types
    
    df["All Support Types"] = df.apply(get_support_types, axis=1)
    df["Support Type"] = df["All Support Types"].apply(
        lambda x: x[0] if x else "N/A"
    )
    df["All Support Str"] = df["All Support Types"].apply(
        lambda x: ", ".join(x) if x else "N/A"
    )
    
    # Ensure required columns exist
    for col in ["Associate Name", "Reporting Manager", "Location", "Gender"]:
        if col not in df.columns:
            df[col] = "N/A"
    
    # Clean string columns
    for col in ["Associate Name", "Reporting Manager", "Location", "Gender"]:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": "N/A", "None": "N/A", "": "N/A"})
    
    # Drop rows where name is N/A
    df = df[df["Associate Name"] != "N/A"].reset_index(drop=True)
    
    return df


def clean_shift_timings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean shift timings from 'Timings' sheet.
    
    Actual columns: 'Shift', 'Timings'
    Timings format expected: "9:00 AM - 6:00 PM" or "09:00 - 18:00" etc.
    """
    if df is None or df.empty:
        # Return default shift timings
        return pd.DataFrame({
            "Shift Code": ["G", "A", "B"],
            "Start Time": [time(9, 0), time(14, 0), time(22, 0)],
            "End Time":   [time(18, 0), time(23, 0), time(7, 0)],
            "Start Str":  ["09:00 AM", "02:00 PM", "10:00 PM"],
            "End Str":    ["06:00 PM", "11:00 PM", "07:00 AM"],
            "Timing Str": ["09:00 AM - 06:00 PM", "02:00 PM - 11:00 PM", "10:00 PM - 07:00 AM"],
        })
    
    df = df.copy()
    
    # Standardize column names
    col_map = {}
    for col in df.columns:
        cl = str(col).lower().strip()
        if cl in ("shift", "shift code", "code"):
            col_map[col] = "Shift Code"
        elif cl in ("timings", "timing", "time", "shift timing", "shift timings"):
            col_map[col] = "Timing Str"
    
    df = df.rename(columns=col_map)
    
    # Ensure we have the required columns
    if "Shift Code" not in df.columns:
        df["Shift Code"] = df.iloc[:, 0]
    if "Timing Str" not in df.columns:
        df["Timing Str"] = df.iloc[:, 1] if len(df.columns) > 1 else ""
    
    # Clean shift code
    df["Shift Code"] = df["Shift Code"].astype(str).str.strip().str.upper()
    df["Timing Str"] = df["Timing Str"].astype(str).str.strip()
    
    # Drop empty/invalid rows
    df = df[
        df["Shift Code"].notna() & 
        (df["Shift Code"] != "") & 
        (df["Shift Code"] != "NAN") &
        (df["Shift Code"] != "NONE")
    ].reset_index(drop=True)
    
    # Parse the combined Timings string into Start Time and End Time
    def parse_timing_str(timing_str: str):
        """Parse '9:00 AM - 6:00 PM' or '09:00 - 18:00' into (start_time, end_time)."""
        timing_str = str(timing_str).strip()
        
        if not timing_str or timing_str.lower() in ("nan", "none", ""):
            return time(0, 0), time(0, 0), "", ""
        
        # Try splitting by common separators: " - ", " – ", " to ", "-", "–"
        parts = None
        for sep in [" - ", " – ", " — ", " to ", "-", "–"]:
            if sep in timing_str:
                parts = timing_str.split(sep, 1)
                break
        
        if not parts or len(parts) != 2:
            return time(0, 0), time(0, 0), timing_str, timing_str
        
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        
        def parse_single_time(val: str) -> time:
            """Parse a single time string to a time object."""
            val = val.strip()
            # Try multiple formats
            for fmt in [
                "%I:%M %p", "%I:%M%p", "%I:%M:%S %p",   # 12-hour
                "%H:%M:%S", "%H:%M",                       # 24-hour
                "%I %p", "%I%p",                            # Hour-only
            ]:
                try:
                    return datetime.strptime(val, fmt).time()
                except (ValueError, TypeError):
                    continue
            
            # Try extracting numbers manually
            nums = re.findall(r'\d+', val)
            has_pm = 'pm' in val.lower() or 'PM' in val
            has_am = 'am' in val.lower() or 'AM' in val
            
            if nums:
                hour = int(nums[0])
                minute = int(nums[1]) if len(nums) > 1 else 0
                if has_pm and hour != 12:
                    hour += 12
                elif has_am and hour == 12:
                    hour = 0
                return time(hour % 24, minute)
            
            return time(0, 0)
        
        start_time = parse_single_time(start_str)
        end_time = parse_single_time(end_str)
        
        return start_time, end_time, start_str, end_str
    
    # Apply parsing
    parsed = df["Timing Str"].apply(parse_timing_str)
    df["Start Time"] = parsed.apply(lambda x: x[0])
    df["End Time"] = parsed.apply(lambda x: x[1])
    df["Start Str"] = parsed.apply(lambda x: x[2])
    df["End Str"] = parsed.apply(lambda x: x[3])
    
    # Create formatted string versions if they're empty
    df["Start Str"] = df.apply(
        lambda r: r["Start Str"] if r["Start Str"] else r["Start Time"].strftime("%I:%M %p"),
        axis=1
    )
    df["End Str"] = df.apply(
        lambda r: r["End Str"] if r["End Str"] else r["End Time"].strftime("%I:%M %p"),
        axis=1
    )
    
    return df


def melt_shift_allocation(df: pd.DataFrame, sheet_name: str = "") -> pd.DataFrame:
    """
    Reshape shift allocation from wide (employees × dates) to long format.
    
    Actual structure: First col = 'Associate Name', rest = datetime columns for each day.
    Returns DataFrame with columns: [Associate Name, Date, Shift Code]
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["Associate Name", "Date", "Shift Code"])
    
    df = df.copy()
    
    # Find the name column
    name_col = None
    for col in df.columns:
        cl = str(col).lower().strip()
        if "name" in cl or "associate" in cl or "employee" in cl:
            name_col = col
            break
    
    if name_col is None:
        name_col = df.columns[0]
    
    # Identify date columns (datetime objects or parseable dates)
    date_cols = []
    date_mapping = {}
    
    for col in df.columns:
        if col == name_col:
            continue
        
        if isinstance(col, datetime):
            date_cols.append(col)
            date_mapping[col] = col.date()
        elif isinstance(col, date):
            date_cols.append(col)
            date_mapping[col] = col
        else:
            # Try to parse as date
            try:
                d = pd.to_datetime(str(col)).date()
                date_cols.append(col)
                date_mapping[col] = d
            except Exception:
                # Try numeric day
                try:
                    day = int(float(str(col).strip()))
                    if 1 <= day <= 31:
                        # Extract month/year from sheet name
                        year = datetime.now().year
                        month = datetime.now().month
                        month_names = {
                            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
                        }
                        for mname, mnum in month_names.items():
                            if mname in sheet_name.lower():
                                month = mnum
                                break
                        year_match = re.search(r'20\d{2}', sheet_name)
                        if year_match:
                            year = int(year_match.group())
                        try:
                            d = date(year, month, day)
                            date_cols.append(col)
                            date_mapping[col] = d
                        except ValueError:
                            pass
                except (ValueError, TypeError):
                    pass
    
    if not date_cols:
        return pd.DataFrame(columns=["Associate Name", "Date", "Shift Code"])
    
    # Melt the dataframe
    melted = df.melt(
        id_vars=[name_col],
        value_vars=date_cols,
        var_name="DateCol",
        value_name="Shift Code"
    )
    
    # Map to actual dates
    melted["Date"] = melted["DateCol"].map(date_mapping)
    melted = melted.rename(columns={name_col: "Associate Name"})
    
    # Clean up
    melted["Associate Name"] = melted["Associate Name"].astype(str).str.strip()
    melted["Shift Code"] = melted["Shift Code"].astype(str).str.strip().str.upper()
    melted["Shift Code"] = melted["Shift Code"].replace({"NAN": "", "NONE": "", "NA": ""})
    
    # Drop rows where name is empty/nan
    melted = melted[
        melted["Associate Name"].notna() & 
        (melted["Associate Name"] != "") & 
        (melted["Associate Name"] != "NAN") &
        (melted["Associate Name"] != "NONE")
    ].reset_index(drop=True)
    
    # Keep only relevant columns
    melted = melted[["Associate Name", "Date", "Shift Code"]]
    
    return melted


def build_shift_lookup(shift_timings: pd.DataFrame) -> Dict[str, Dict]:
    """Create a lookup dictionary from shift code to timing details."""
    lookup = {}
    for _, row in shift_timings.iterrows():
        code = str(row["Shift Code"]).strip().upper()
        lookup[code] = {
            "start": row["Start Time"],
            "end": row["End Time"],
            "start_str": row.get("Start Str", ""),
            "end_str": row.get("End Str", ""),
            "timing_str": row.get("Timing Str", ""),
        }
    return lookup


def get_all_support_types(employee_master: pd.DataFrame) -> List[str]:
    """Extract all unique support types across all Support columns."""
    all_types = set()
    if "All Support Types" in employee_master.columns:
        for types_list in employee_master["All Support Types"]:
            if isinstance(types_list, list):
                all_types.update(types_list)
    return sorted([t for t in all_types if t and t != "N/A"])


def get_employee_status(shift_code: str) -> str:
    """Determine employee status from shift code."""
    code = str(shift_code).strip().upper()
    if code in ("WO",):
        return "Week Off"
    elif code in ("HO",):
        return "Holiday"
    elif code in ("LEAVE", "L"):
        return "Leave"
    elif code in ("", "NAN", "NONE", "NA"):
        return "No Data"
    else:
        return "Working"


def is_available(shift_code: str) -> bool:
    """Check if employee is available (not on leave/WO/HO)."""
    code = str(shift_code).strip().upper()
    return code not in UNAVAILABLE_CODES and code != "NAN" and code != "NONE"


def classify_real_time(shift_code: str, shift_lookup: Dict, current_time: time) -> str:
    """
    Classify employee as Active Now / Upcoming Shift / Off Duty based on current time.
    """
    code = str(shift_code).strip().upper()
    
    if not is_available(code):
        return "Off Duty"
    
    if code not in shift_lookup:
        return "Unknown Shift"
    
    start = shift_lookup[code]["start"]
    end = shift_lookup[code]["end"]
    
    # Handle overnight shifts (e.g., B shift: 22:00 - 07:00)
    if start <= end:
        # Normal shift (e.g., 09:00 - 18:00)
        if start <= current_time <= end:
            return "Active Now"
        elif current_time < start:
            return "Upcoming Shift"
        else:
            return "Off Duty"
    else:
        # Overnight shift (e.g., 22:00 - 07:00)
        if current_time >= start or current_time <= end:
            return "Active Now"
        elif current_time < start:
            return "Upcoming Shift"
        else:
            return "Off Duty"


def load_and_process_all(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    """
    Master function: Load Excel, process all sheets, return cleaned dataframes.
    
    Returns:
        employee_master: Cleaned employee master dataframe
        shift_data: Melted shift allocation (long format) merged with employee details
        shift_timings: Cleaned shift timings
        shift_lookup: Dict of shift code -> timing info
    """
    sheets = load_excel(filepath)
    
    # ── Detect sheets by name patterns ──
    emp_raw = None
    alloc_raw = None
    timings_raw = None
    alloc_name = ""
    
    for name, df in sheets.items():
        name_lower = name.lower().strip()
        
        # Timings sheet
        if "timing" in name_lower or "time" in name_lower:
            timings_raw = df
            continue
        
        # Employee details / master
        if "employee" in name_lower or "detail" in name_lower or "master" in name_lower:
            emp_raw = df
            continue
        
        # Shift allocation (monthly sheet — matches month names or has many date columns)
        month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                       "jul", "aug", "sep", "oct", "nov", "dec"]
        is_month_sheet = any(m in name_lower for m in month_names)
        
        # Also check if many columns are datetime objects
        datetime_cols = sum(1 for c in df.columns if isinstance(c, (datetime, date)))
        
        if is_month_sheet or datetime_cols >= 10:
            alloc_raw = df
            alloc_name = name
            continue
        
        # Fallback: if sheet has many columns, assume it's shift allocation
        if len(df.columns) > 15 and alloc_raw is None:
            alloc_raw = df
            alloc_name = name
    
    # ── Process each sheet ──
    employee_master = clean_employee_master(emp_raw)
    shift_timings = clean_shift_timings(timings_raw)
    shift_data = melt_shift_allocation(alloc_raw, alloc_name)
    shift_lookup = build_shift_lookup(shift_timings)
    
    # ── Merge employee details into shift data ──
    if not employee_master.empty and not shift_data.empty:
        # Select relevant columns from employee master for merge
        merge_cols = ["Associate Name", "Support Type", "All Support Types",
                      "All Support Str", "Reporting Manager", "Location", "Gender"]
        merge_cols = [c for c in merge_cols if c in employee_master.columns]
        
        shift_data = shift_data.merge(
            employee_master[merge_cols],
            on="Associate Name",
            how="left"
        )
        # Fill missing values
        for col in ["Support Type", "Reporting Manager", "Location", "Gender", "All Support Str"]:
            if col in shift_data.columns:
                shift_data[col] = shift_data[col].fillna("N/A")
        if "All Support Types" in shift_data.columns:
            shift_data["All Support Types"] = shift_data["All Support Types"].apply(
                lambda x: x if isinstance(x, list) else []
            )
    else:
        for col in ["Support Type", "Reporting Manager", "Location", "Gender", "All Support Str"]:
            if col not in shift_data.columns:
                shift_data[col] = "N/A"
        if "All Support Types" not in shift_data.columns:
            shift_data["All Support Types"] = [[] for _ in range(len(shift_data))]
    
    return employee_master, shift_data, shift_timings, shift_lookup
