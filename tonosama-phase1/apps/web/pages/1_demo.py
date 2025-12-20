import streamlit as st
import os
import uuid
from apps.web.ui_mario.components import render_mario_ui

st.set_page_config(page_title="Sales Demo", page_icon="👔", layout="centered")

# Environment
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# Session State for Demo Session
if "demo_session_id" not in st.session_state:
    # In real flow, this comes from URL or Sales Portal
    # For now, generate a mock one
    st.session_state["demo_session_id"] = f"demo_{uuid.uuid4().hex[:8]}"

demo_id = st.session_state["demo_session_id"]
st.sidebar.caption(f"Session: {demo_id}")

# --- Header ---
st.markdown("### 👔 Sales Demo Experience")

# --- Logic ---
# Check connectivity (Mock ping)
# For now, we assume API is up or client JS handles errors.

# --- Render Mario UI ---
# This single component handles the entire Step 0 -> Step 1 -> Step 2 Flow
render_mario_ui(
    api_base=API_BASE,
    demo_session_id=demo_id,
    default_plan=39,
    preview_preset="friendly_nations", 
    height=900
)

# --- Debug Info (Optional) ---
with st.expander("Debug Info"):
    st.write(f"API: {API_BASE}")
    st.write(f"ID: {demo_id}")
