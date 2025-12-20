import streamlit as st
import os
import requests
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Menu Intake", page_icon="📝", layout="wide")

st.info("ℹ️ This page verifies the Phase 2 implementation by connecting to the backend API (`/api/intake/extract_page`).")

import asyncio
import sys

# Add path for direct import
if "tonosama-phase1" not in sys.path:
    sys.path.append("tonosama-phase1")

try:
    from apps.api.core.gemini import extract_full_page
    from apps.api.core.normalization import normalize_price, normalize_category
except ImportError:
    st.error("Could not import backend logic directly. Checked path: tonosama-phase1/")

# S2-03: Mode Toggle
mode = st.radio("Mode", ["Quick (10 items)", "Full Scan"], horizontal=True)
st.divider()

# S2-02: Multi-File Uploader
uploaded_files = st.file_uploader(
    "Upload Menu Images (JPG, PNG, PDF)",
    type=["jpg", "png", "heic", "pdf"],
    accept_multiple_files=True
)

if "intake_results" not in st.session_state:
    st.session_state["intake_results"] = []

def process_file_directly(file, page_no):
    """
    Simulated API logic running directly in-process.
    """
    try:
        # Read bytes
        content = file.getvalue()
        mime_type = file.type
        
        # Call Gemini Logic (Async wrapper)
        async def _run():
             return await extract_full_page(content, mime_type, page_no)
        
        raw_items, raw_meta = asyncio.run(_run())
        
        # Normalization Logic (Same as API)
        final_items = []
        for it in raw_items:
            # Normalize Price
            p_val, currency = normalize_price(it.price_raw)
            if p_val:
                it.price_val = p_val
                it.currency = currency
            
            # Normalize Category
            it.category_raw = normalize_category(it.category_raw)
            
            # Apply Confidence Rules
            if not it.price_val:
                it.confidence = min(it.confidence, 0.5)
                
            final_items.append(it)
            
        # Return dict structure similar to API response for compatibility
        return {
            "items": [it.dict() for it in final_items]
        }, None
        
    except Exception as e:
        return None, str(e)

if uploaded_files:
    if st.button(f"🔍 Scan {len(uploaded_files)} Pages (Direct Mode)"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Scanning {file.name}...")
            
            # DIRECT PROCESS instead of Call API
            data, err = process_file_directly(file, i+1)
            
            if err:
                st.error(f"Failed to scan {file.name}: {err}")
            elif data:
                # Flat mapping for table
                for item in data.get("items", []):
                    results.append({
                        "File": file.name,
                        "Page": item.get("source_page"),
                        "Name": item.get("name_ja_raw"),
                        "Price": item.get("price_val") or item.get("price_raw"),
                        "Category": item.get("category_raw"),
                        "Conf": item.get("confidence"),
                        "Set": "✅" if item.get("is_set") else ""
                    })
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        st.session_state["intake_results"] = results
        status_text.text("Scan Complete!")

# S2-07: Result Table
if st.session_state["intake_results"]:
    df = pd.DataFrame(st.session_state["intake_results"])
    
    st.markdown("### Extraction Results")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "Conf": st.column_config.ProgressColumn(
                "Confidence",
                help="AI Confidence Score",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    st.metric("Total Items", len(df))
    
    # S2-10: Low Confidence Filter
    low_conf = df[df["Conf"] < 0.8]
    if not low_conf.empty:
        st.warning(f"⚠️ {len(low_conf)} items need review (Confidence < 0.8)")
    
    if st.button("Save to MENU_MASTER"):
        st.toast("Saved to Database (Mock)!")
