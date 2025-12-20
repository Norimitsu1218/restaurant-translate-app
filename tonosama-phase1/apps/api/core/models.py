from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Any

# --- Common ---
class Price(BaseModel):
    amount: Optional[int]
    currency: str = "JPY"
    raw: str

class MenuItem(BaseModel):
    tmp_item_id: str
    name_ja: str
    price: Price
    category_ja: Optional[str] = None
    confidence: float = 1.0
    warnings: List[str] = []

# --- Requests ---
class ExtractRequest(BaseModel):
    demo_session_id: str
    image: Dict[str, str]  # { "mime_type": "...", "base64": "..." }

class SelectItemsRequest(BaseModel):
    demo_session_id: str
    selected_tmp_item_ids: List[str]

class UploadItemImageRequest(BaseModel):
    demo_session_id: str
    tmp_item_id: str
    image: Dict[str, str]

class GeneratePreviewRequest(BaseModel):
    demo_session_id: str
    plan_code: int
    preview_langs: List[str]
    tone_style: str = "standard"

class CompleteDemoRequest(BaseModel):
    demo_session_id: str
    plan: int
    selected_tmp_item_ids: List[str]
    item_images_count: int

# --- Responses ---
class ExtractResponse(BaseModel):
    demo_session_id: str
    items: List[MenuItem]
    policy: Dict[str, Any]

class GenerateItemContent(BaseModel):
    name: str
    review_18s: str
    how_to_eat: Optional[str] = None
    pairing: Optional[str] = None

class GeneratePreviewResponse(BaseModel):
    demo_session_id: str
    plan_code: int
    items: List[Dict[str, Dict[str, str]]] # Simplified for demo { "it_01": { "ja": {...} } }
    # Actually, S1-33d defines structure: items: [ { tmp_item_id, ja: {...}, en: {...} } ]
    # Let's match strict spec
    
class PreviewItem(BaseModel):
    tmp_item_id: str
    ja: Optional[GenerateItemContent] = None
    en: Optional[GenerateItemContent] = None
    zh_Hant: Optional[GenerateItemContent] = Field(None, alias="zh-Hant")
    de: Optional[GenerateItemContent] = None
    fr: Optional[GenerateItemContent] = None
    ko: Optional[GenerateItemContent] = None
    cache: Optional[Dict[str, Any]] = None

class GeneratePreviewResponseStrict(BaseModel):
    demo_session_id: str
    plan_code: int
    items: List[PreviewItem]
    cache: Optional[Dict[str, Any]] = None

# --- Phase 2: Intake Models ---
class IntakeItem(BaseModel):
    tmp_item_id: str
    name_ja_raw: str
    price_val: Optional[int]
    price_raw: str
    currency: str = "JPY"
    category_raw: str
    is_set: bool = False
    confidence: float = 1.0
    source_page: int = 1
    bbox: Optional[List[float]] = None # [ymin, xmin, ymax, xmax]

class PageMeta(BaseModel):
    page_no: int
    layout_type: str = "unknown" # list, grid, mixed
    warnings: List[str] = []

class IntakeResponse(BaseModel):
    session_id: str
    items: List[IntakeItem]
    meta: List[PageMeta]


    meta: List[PageMeta]


# --- Phase 3: Hearing Models ---
class HearingItem(IntakeItem):
    # Confirmed fields (S3-09)
    name_ja_confirmed: Optional[str] = None
    price_val_confirmed: Optional[int] = None
    category_confirmed: Optional[str] = None
    
    # Status
    confirm_status: str = "pending" # pending, confirmed, ignored
    
    # Recommendation
    is_recommended: bool = False # Linked to store_recommended_item
    recommended_status: str = "none" # none, linked, needs_review

class HearingSession(BaseModel):
    session_id: str
    items: List[HearingItem]
    cursor_index: int = 0
    mode: str = "normal" # normal, shortcut
    plan: int = 39 # 39, 69, 99
    
    # Recommended Item (Registered)
    registered_recommended_name: str
    linked_item_id: Optional[str] = None

class HearingActionResponse(BaseModel):
    success: bool
    next_item: Optional[HearingItem] = None
    completed: bool = False
    message: Optional[str] = None

class HearingSessionStartRequest(BaseModel):
    intake_items: List[HearingItem]
    menu_master_recommended_name: str
    mode: str = "normal"
