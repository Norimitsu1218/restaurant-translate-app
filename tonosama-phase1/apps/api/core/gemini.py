import os
import json
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from .models import MenuItem, Price, PreviewItem, GenerateItemContent

MODEL_NAME = "gemini-2.0-flash-exp" # Fast & Cheap

def get_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=0.2,
        max_output_tokens=8192,
    )

async def extract_menu_items(image_bytes: bytes, mime_type: str) -> List[MenuItem]:
    llm = get_llm()
    
    # Base64 encode
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = """
    Extract menu items from the image.
    Rules:
    - Extract max 10 items.
    - Name (Japanese), Price (Number JPY), Category.
    - Output JSON list.
    - Ignore sets or drinks if main dishes are available.
    
    JSON Schema:
    [
      {
        "name_ja": "string",
        "price_val": 1000,
        "price_raw": "1000 yen",
        "category_ja": "string"
      }
    ]
    """
    
    msg = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}}
    ])
    
    try:
        res = await llm.ainvoke([msg])
        # Simple parsing logic
        content = res.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        data = json.loads(content)
        
        items = []
        for i, d in enumerate(data):
            if i >= 10: break
            items.append(MenuItem(
                tmp_item_id=f"it_{i:02d}",
                name_ja=d.get("name_ja", "Unknown"),
                price=Price(
                    amount=d.get("price_val"),
                    raw=d.get("price_raw", str(d.get("price_val", "")))
                ),
                category_ja=d.get("category_ja", "Other")
            ))
        return items
    except Exception as e:
        print(f"Extraction Error: {e}")
        return []

async def generate_preview_content(items: List[MenuItem], langs: List[str]) -> List[PreviewItem]:
    # Mocking for speed in Phase 1 Demo
    # In real imp, this would call Gemini 2.5 with specific prompt
    results = []
    
    for item in items:
        # Dummy content for demo stability
        results.append(PreviewItem(
            tmp_item_id=item.tmp_item_id,
            ja=GenerateItemContent(
                name=item.name_ja,
                review_18s=f"【AI生成サンプル】{item.name_ja}は、素材の味を最大限に引き出した一品です。口に入れた瞬間の香りと、噛むほどに広がる旨味が特徴です。",
                how_to_eat="まずはそのまま、温かいうちにお召し上がりください。",
                pairing="辛口の日本酒"
            ),
            en=GenerateItemContent(
                name=item.name_ja, # Transliteration ideally
                review_18s="[AI Sample] This dish maximizes the flavor of the ingredients. Provides great aroma and savory taste.",
                how_to_eat="Eat while hot.",
                pairing="Dry Sake"
            )
            # Add other langs as needed
        ))
    return results
