"""Quick diagnostic app to inspect the Excel file structure."""
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Excel Inspector", layout="wide")
st.title("🔍 Excel File Inspector")

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Shift draft (1).xlsx")

try:
    sheets = pd.read_excel(filepath, sheet_name=None, engine="openpyxl")
    
    st.success(f"✅ Loaded {len(sheets)} sheets: {list(sheets.keys())}")
    
    for name, df in sheets.items():
        st.markdown(f"---")
        st.markdown(f"## Sheet: `{name}`")
        st.markdown(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
        st.markdown(f"**Columns:** `{list(df.columns)}`")
        st.markdown(f"**Column dtypes:**")
        st.code(str(df.dtypes))
        st.markdown("**First 10 rows:**")
        st.dataframe(df.head(10), use_container_width=True)
        
except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
