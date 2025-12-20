from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import List
from ..core.gemini import extract_full_page
from ..core.normalization import normalize_price, normalize_category
from ..core.observability import log_api_usage
from ..core.models import IntakeResponse, IntakeItem, PageMeta

router = APIRouter(prefix="/api/intake", tags=["intake"])

@router.post("/extract_page", response_model=IntakeResponse)
async def extract_page(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    page_no: int = Form(1)
):
    """
    Process a single menu page image.
    1. Read bytes.
    2. Call Gemini (S2-04).
    3. Normalize Data.
    4. Log Observability (S2-08).
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/heic", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        content = await file.read()
        
        # 1. Extraction
        raw_items, raw_meta = await extract_full_page(content, file.content_type, page_no)
        
        # 2. Normalization
        final_items = []
        for it in raw_items:
            # Normalize Price
            p_val, currency = normalize_price(it.price_raw)
            if p_val:
                it.price_val = p_val
                it.currency = currency
            
            # Normalize Category
            it.category_raw = normalize_category(it.category_raw)
            
            # Apply Confidence Rules (S2-04-3)
            # If price missing, lower confidence
            if not it.price_val:
                it.confidence = min(it.confidence, 0.5)
                
            final_items.append(it)

        # 3. Observability
        log_api_usage(
            store_id=session_id, # Use session as store_id for now
            phase="phase2",
            feature="full_page_extract",
            input_type=file.content_type,
            pages=1,
            # Tokens are unknown in simple version, assume avg
            tokens_in=1000, 
            tokens_out=500,
            status="ok"
        )
        
        return IntakeResponse(
            session_id=session_id,
            items=final_items,
            meta=[raw_meta]
        )

    except Exception as e:
        log_api_usage(status="error", error_msg=str(e))
        raise HTTPException(status_code=500, detail=str(e))
