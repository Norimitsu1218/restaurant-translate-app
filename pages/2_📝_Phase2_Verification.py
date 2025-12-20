import streamlit as st
import os
import requests
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Menu Intake", page_icon="📝", layout="wide")

st.info("ℹ️ This page verifies the Phase 2 implementation by connecting to the backend API (`/api/intake/extract_page`).")

# Env
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.title("📝 Menu Intake (Phase 2 Verification)")
st.caption("Multimodal Extraction powered by Gemini 3")

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

def call_extraction_api(file, page_no):
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {"session_id": "manual_intake", "page_no": page_no}
        
        try:
            resp = requests.post(f"{API_BASE}/api/intake/extract_page", files=files, data=data, timeout=30)
        except requests.exceptions.ConnectionError:
            return None, "API Connection Failed. Is the backend running at localhost:8000?"

        if resp.status_code != 200:
            return None, f"Error {resp.status_code}: {resp.text}"
        return resp.json(), None
    except Exception as e:
        return None, str(e)

if uploaded_files:
    if st.button(f"🔍 Scan {len(uploaded_files)} Pages"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Scanning {file.name}...")
            data, err = call_extraction_api(file, i+1)
            
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
