from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Optional
from uuid import uuid4
import json

from ..core.models import (
    HearingSession, HearingItem, HearingActionResponse,
    IntakeResponse, Price, HearingSessionStartRequest
)
from ..core.normalization import normalize_category

router = APIRouter(prefix="/api/phase3", tags=["phase3"])

# In-memory store (Mock DB for Phase 3)
SESSIONS = {} 

@router.post("/session/start", response_model=HearingSession)
async def start_session(payload: HearingSessionStartRequest):
    """
    Start a Hearing Session from Phase 2 results.
    Auto-links recommended item if match found.
    """
    session_id = str(uuid4())
    
    # Auto-link logic (S3-11a)
    linked_id = None
    target_name = payload.menu_master_recommended_name.strip().lower()
    
    for item in payload.intake_items:
        # Simple fuzzy match logic
        item_name = item.name_ja_raw.strip().lower() if item.name_ja_raw else ""
        if target_name and item_name and (target_name in item_name or item_name in target_name):
            item.is_recommended = True
            item.recommended_status = "linked"
            linked_id = item.tmp_item_id
            break # Link first match only for now
            
    # S3-04b Shortcut Mode: Move low confidence to front? 
    # For now, just store as is.
    
    session = HearingSession(
        session_id=session_id,
        items=payload.intake_items,
        cursor_index=0,
        mode=payload.mode,
        registered_recommended_name=payload.menu_master_recommended_name,
        linked_item_id=linked_id
    )
    SESSIONS[session_id] = session
    return session

@router.get("/session/{session_id}/next", response_model=HearingActionResponse)
async def get_next_item(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Find next pending item
    for i in range(session.cursor_index, len(session.items)):
        item = session.items[i]
        if item.confirm_status == "pending":
            session.cursor_index = i # Update cursor
            return HearingActionResponse(success=True, next_item=item)
            
    return HearingActionResponse(success=True, completed=True, message="All items reviewed")

@router.post("/item/{item_id}/approve", response_model=HearingActionResponse)
async def approve_item(session_id: str, item_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    target_item = next((it for it in session.items if it.tmp_item_id == item_id), None)
    if not target_item:
        raise HTTPException(404, "Item not found")
        
    # Apply Confirmation (Copy Raw to Confirmed if empty)
    if not target_item.name_ja_confirmed:
        target_item.name_ja_confirmed = target_item.name_ja_raw
    if not target_item.price_val_confirmed:
        target_item.price_val_confirmed = target_item.price_val
    if not target_item.category_confirmed:
        target_item.category_confirmed = normalize_category(target_item.category_raw) # S3-03 Auto-Categorize
        
    target_item.confirm_status = "confirmed"
    
    # Mock DB Update (Action Logger)
    print(f"[DB] Item {item_id} confirmed: {target_item.name_ja_confirmed}")
    
    return HearingActionResponse(success=True, message="Confirmed")

@router.post("/item/{item_id}/edit", response_model=HearingActionResponse)
async def edit_item(
    session_id: str, 
    item_id: str, 
    name: str = Form(...), 
    price: int = Form(...),
    category: str = Form(...)
):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    target_item = next((it for it in session.items if it.tmp_item_id == item_id), None)
    if not target_item:
        raise HTTPException(404, "Item not found")
        
    # Update Confirmed Fields
    target_item.name_ja_confirmed = name
    target_item.price_val_confirmed = price
    target_item.category_confirmed = category
    target_item.confirm_status = "confirmed"
    
    return HearingActionResponse(success=True, message="Updated and Confirmed")

@router.get("/session/{session_id}/export_recommended")
async def export_recommended(session_id: str):
    """
    S3-11b Generate recommended.txt
    """
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404)
        
    rec_item = next((it for it in session.items if it.is_recommended or it.tmp_item_id == session.linked_item_id), None)
    
    if not rec_item:
        return {"status": "no_link", "message": "No recommended item linked."}
        
    # Generate content (Mock)
    content = f"""
【おすすめの一品】
日本語品名: {rec_item.name_ja_confirmed or rec_item.name_ja_raw}
価格: {rec_item.price_val_confirmed or rec_item.price_val}円
    """.strip()
    
    # In real app, upload to Drive here
    return {"status": "success", "content": content}
