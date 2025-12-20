import streamlit as st
import requests
import json
from pathlib import Path

# Adjust path for component import
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from apps.web.ui_mario.components import render_mario_ui

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

intake_items = st.session_state["intake_results"]
if not intake_items:
    st.warning("Intake result is empty.")
    st.stop()
    
# --- Session Setup ---
if "hearing_session_id" not in st.session_state:
    st.info(f"Initializing Session with {len(intake_items)} items...")
    
    # Needs a registered recommended name to test auto-linking
    rec_name = st.text_input("Recommended Item Name (for testing)", value="Yakitori")
    
    if st.button("Start Hearing Session", type="primary"):
        try:
            # Pydantic models to dict
            items_payload = [item.dict() for item in intake_items]
            
            payload = {
                "intake_items": items_payload,
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
