from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

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
    policy: Dict[str, any]

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
    cache: Optional[Dict[str, any]] = None

class GeneratePreviewResponseStrict(BaseModel):
    demo_session_id: str
    plan_code: int
    items: List[PreviewItem]
    cache: Optional[Dict[str, any]] = None

