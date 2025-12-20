import streamlit as st
import sys
import os
from pathlib import Path

# Title
st.set_page_config(page_title="Suzuka v2 Demo", page_icon="🚀", layout="centered")
st.title("🚀 Phase 1: Suzuka Architecture v2")
st.caption("New Architecture (Web/API Split) Preview")

# --- Bridge Logic ---
# Add the new architecture root to python path so we can import from it
current_dir = Path(os.getcwd())
phase1_root = current_dir / "tonosama-phase1"

if str(phase1_root) not in sys.path:
    sys.path.append(str(phase1_root))

try:
    from apps.web.ui_mario.components import render_mario_ui
    
    # Check if API is running (Warning)
    st.warning("⚠️ This UI requires the FastAPI backend running at `localhost:8000` (or configured API_BASE). If running on Cloud without the API sidecar, buttons may error.", icon="⚠️")

    api_base = os.getenv("API_BASE", "http://localhost:8000")
    
    # Render
    render_mario_ui(
        api_base=api_base,
        demo_session_id="succes_demo_bridge",
        default_plan=39,
        preview_preset="friendly_nations"
    )

except ImportError as e:
    st.error(f"Could not import Phase 1 components. Path issue? {e}")
    st.write(sys.path)
