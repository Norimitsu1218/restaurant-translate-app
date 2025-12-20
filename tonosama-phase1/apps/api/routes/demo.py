from fastapi import APIRouter, HTTPException
from typing import Dict
import base64

from ..core.models import (
    ExtractRequest, ExtractResponse,
    SelectItemsRequest,
    UploadItemImageRequest,
    GeneratePreviewRequest, GeneratePreviewResponseStrict,
    CompleteDemoRequest
)
from ..core.gemini import extract_menu_items, generate_preview_content

router = APIRouter(prefix="/api/demo", tags=["demo"])

# In-memory session store for Demo (Phase 1)
# In prod, use Redis/DB
SESSIONS: Dict[str, dict] = {}

@router.post("/extract_items", response_model=ExtractResponse)
async def extract_items_endpoint(req: ExtractRequest):
    # Decode image
    try:
        image_bytes = base64.b64decode(req.image["base64"])
    except:
        raise HTTPException(status_code=400, detail="Invalid base64")

    # Call Gemini
    items = await extract_menu_items(image_bytes, req.image.get("mime_type", "image/jpeg"))

    # Save to session (Create if not exists)
    if req.demo_session_id not in SESSIONS:
        SESSIONS[req.demo_session_id] = {}
    
    # Store full items map for later lookup
    SESSIONS[req.demo_session_id]["extracted"] = {it.tmp_item_id: it for it in items}

    return ExtractResponse(
        demo_session_id=req.demo_session_id,
        items=items,
        policy={"max_items": 10, "truncated": len(items) >= 10}
    )

@router.post("/select_items")
async def select_items_endpoint(req: SelectItemsRequest):
    if len(req.selected_tmp_item_ids) != 3:
        raise HTTPException(status_code=422, detail="Must select exactly 3 items")
    
    if req.demo_session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    SESSIONS[req.demo_session_id]["selected_ids"] = req.selected_tmp_item_ids
    return {"status": "ok", "selected": req.selected_tmp_item_ids}

@router.post("/upload_item_image")
async def upload_item_image(req: UploadItemImageRequest):
    # Save image to staging (In-memory for now)
    # In real app, save to S3/Drive
    return {"status": "ok", "tmp_item_id": req.tmp_item_id}

@router.post("/generate_preview", response_model=GeneratePreviewResponseStrict)
async def generate_preview(req: GeneratePreviewRequest):
    sess = SESSIONS.get(req.demo_session_id)
    if not sess or "extracted" not in sess or "selected_ids" not in sess:
        # Fallback for dev/debug if session lost
        # raise HTTPException(status_code=404, detail="Session state missing")
        pass 

    # Retrieve selected items
    selected_items = []
    if sess:
        full_map = sess.get("extracted", {})
        for mid in sess.get("selected_ids", []):
            if mid in full_map:
                selected_items.append(full_map[mid])
    
    # If empty (debug mode), create dummy
    if not selected_items:
        from ..core.models import MenuItem, Price
        selected_items = [MenuItem(tmp_item_id="it_99", name_ja="Debug Item", price=Price(amount=0, raw="0"))]

    # Call Generation Logic
    preview_items = await generate_preview_content(selected_items, req.preview_langs)
    
    return GeneratePreviewResponseStrict(
        demo_session_id=req.demo_session_id,
        plan_code=req.plan_code,
        items=preview_items,
        cache={"hit": False}
    )

@router.post("/complete")
async def complete_demo(req: CompleteDemoRequest):
    # Log completion
    return {"status": "ok"}
