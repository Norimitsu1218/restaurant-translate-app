from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="TONOSAMA API", version="2025.12.19")

# CORS (Allow Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes import demo, billing

app.include_router(demo.router)
app.include_router(billing.router)

@app.get("/")
def health_check():
    return {"status": "ok", "version": "2025.12.19"}
