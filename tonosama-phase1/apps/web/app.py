import streamlit as st
import os

st.set_page_config(page_title="TONOSAMA Sales Demo", page_icon="🍱", layout="centered")

st.title("🍱 TONOSAMA Phase 1")
st.write("Architecture initialized.")

api_base = os.getenv("API_BASE", "http://localhost:8000")
st.write(f"API Base: {api_base}")

st.info("Please navigate to the sidebar to start the Sales Demo.")
