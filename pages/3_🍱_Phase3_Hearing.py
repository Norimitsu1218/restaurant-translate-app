import streamlit as st
import requests
import json
import os
import sys

# Path Setup for "tonosama-phase1" imports
if "tonosama-phase1" not in sys.path:
    # We are in ROOT/pages/, so tonosama-phase1 is in ROOT/tonosama-phase1
    # Adding ROOT to sys.path effectively allows finding tonosama-phase1 if we import it as a package, 
    # OR we append "tonosama-phase1" to path.
    # The verification page uses `sys.path.append("tonosama-phase1")`.
    # Let's verify where `main.py` is running. It's in ROOT.
    # So `tonosama-phase1` is a subdirectory.
    sys.path.append("tonosama-phase1")

# Import Mario UI Component
try:
    from apps.web.ui_mario.components import render_mario_ui
    from apps.api.core.models import HearingItem # Just for verification of import
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

st.set_page_config(page_title="Phase 3: Hearing", page_icon="🍱", layout="wide")

# API Configuration
API_BASE = "http://127.0.0.1:8001" 

st.title("🍱 Phase 3: Content Hearing")
st.caption("Game-like confirmation leveraging Gemini Logic")

# --- Debug / Verification State ---
if "intake_results" not in st.session_state:
    st.warning("No intake results found. Please go to 'Phase 2 Verification' first to extract items.")
    if st.button("Go to Verification"):
        st.switch_page("pages/2_📝_Phase2_Verification.py")
    st.stop()

# Convert Intake Result dicts back to Objects if needed, or just use as dicts for API
intake_data = st.session_state["intake_results"]
if not intake_data:
    st.warning("Intake result is empty.")
    st.stop()

# Convert flattened table data back to API schema structure?
# usage in Phase 2 Verification creates a FLATTENED list of dicts for the DataFrame.
# Need to reconstruct HearingItem compatible dicts.
# Phase 2 `results` structure:
# { "File", "Page", "Name", "Price", "Category", "Conf", "Set" ... }
# API expects IntakeItem / HearingItem structure:
# { "name_ja_raw": ..., "price_raw": ..., "category_raw": ..., "tmp_item_id": ... }

# Simulating reconstruction
reconstructed_items = []
for idx, row in enumerate(intake_data):
    # Safe convert
    price_val = row.get("Price")
    if isinstance(price_val, str):
        # Try parse if it's "1000" or "$10" (Already likely int from normalize)
        if price_val.isdigit(): price_val = int(price_val)
        else: price_val = None
        
    reconstructed_items.append({
        "tmp_item_id": f"item_{idx}",
        "name_ja_raw": row.get("Name"),
        "price_val": price_val if isinstance(price_val, int) else None,
        "price_raw": str(row.get("Price")),
        "category_raw": row.get("Category"),
        "confidence": row.get("Conf", 0.0),
        "source_page": row.get("Page", 1)
    })
    
# --- Session Setup ---
if "hearing_session_id" not in st.session_state:
    st.info(f"Initializing Session with {len(reconstructed_items)} items...")
    
    # Needs a registered recommended name to test auto-linking
    rec_name = st.text_input("Recommended Item Name (for testing)", value="Yakitori")
    
    if st.button("Start Hearing Session", type="primary"):
        try:
            payload = {
                "intake_items": reconstructed_items,
                "menu_master_recommended_name": rec_name,
                "mode": "normal"
            }
            
            resp = requests.post(f"{API_BASE}/api/phase3/session/start", json=payload)
            if resp.status_code == 200:
                session_data = resp.json()
                st.session_state["hearing_session_id"] = session_data["session_id"]
                st.session_state["hearing_session_data"] = session_data
                st.success("Session Started!")
                st.rerun()
            else:
                st.error(f"API Error: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Failed: {e}")

if "hearing_session_id" in st.session_state:
    sid = st.session_state["hearing_session_id"]
    
    # S3-11: Show Recommendation Match Status (Debug)
    # The UI will show the status bar, but showing debug info here is helpful
    sdata = st.session_state.get("hearing_session_data")
    if sdata and sdata.get("linked_item_id"):
        st.info(f"✨ Auto-linked recommended item: {sdata.get('registered_recommended_name')}")
    
    # Render Mario UI
    # We pass mode="hearing" to trigger Phase 3 logic in JS
    render_mario_ui(
        api_base=API_BASE,
        demo_session_id=sid, # Maps to session_id
        mode="hearing",
        default_plan=39,
        height=800
    )
    
    if st.button("Reset Session"):
        del st.session_state["hearing_session_id"]
        st.rerun()
