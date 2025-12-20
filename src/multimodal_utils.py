import os
import json
import base64
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from .observability import log_api_cost
from .models import MenuItem

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
# User requested "Gemini 3.0" capabilities. 
# We default to the latest available Experimental or Pro model.
DEFAULT_MODEL = "gemini-2.0-flash-exp" 

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
# User requested "Gemini 3.0" capabilities. 
# We default to the latest available Experimental or Pro model.
DEFAULT_MODEL = "gemini-2.0-flash-exp" 

class RichMenuItem(BaseModel):
    menu_name_jp: str = Field(description="Name of the dish in Japanese")
    price: str = Field(description="Price of the dish (numeric string)")
    category: str = Field(description="Category of the dish (e.g., Appetizer, Main, Drink)")
    description_rich: str = Field(description="A captivating 18-second food report describing the taste, texture, and appeal. MUST be in Japanese.")

class MenuExtractionResult(BaseModel):
    items: List[RichMenuItem] = Field(description="List of extracted menu items")

def get_vision_model(api_key: str, model_name: str = DEFAULT_MODEL):
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.2, # Slight creativity for description, but grounded
        max_output_tokens=8192,
    )

def parse_menu_image(
    image_bytes: bytes, 
    api_key: str, 
    persona: str = "標準",
    store_id: str = "unknown_store"
) -> List[dict]:
    """
    Sends the image directly to Gemini to extract menu items as structured JSON.
    Returns a list of dicts compatible with the Menu Maker UI.
    """
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    llm = get_vision_model(api_key, model_name)
    parser = JsonOutputParser(pydantic_object=MenuExtractionResult)

    # Convert bytes to base64 for LangChain
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_data = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}

    prompt_text = f"""
    You are an expert food writer and menu digitizer. 
    Analyze the provided menu image and extract all menu items into a structured JSON list.

    Persona Setting: {persona} (Reflect this tone in 'description_rich')

    Rules:
    1. **menu_name_jp**: Extract the exact Japanese name.
    2. **price**: Extract the price as a number (remove 'yen', ',', etc).
    3. **category**: Infer the category (Appetizer, Main, Drink, Dessert, etc.) from placement.
    4. **description_rich**: Generate a specialized food report (18-second read).
       - If the menu has a description, enhance it.
       - If NO description exists, GENERATE a creative, appetizing description based on the visual/name.
       - Include taste notes, texture, and pairing suggestions if appropriate.
    5. Handle vertical text and handwritten text naturally.
    
    Format:
    {parser.get_format_instructions()}
    """

    prompt = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            image_data
        ]
    )

    try:
        # Invoke Gemini
        response = llm.invoke([prompt])
        
        # Observability: Log Cost
        if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
            usage = response.response_metadata["token_usage"]
            log_api_cost(
                store_id=store_id,
                phase="vision_extraction",
                model_name=model_name,
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0)
            )

        # Parse Result
        parsed = parser.parse(response.content)
        
        # Normalize to List[dict]
        raw_items = parsed.get("items", []) if isinstance(parsed, dict) else parsed
        
        # Return raw dicts for easy dataframe usage
        return raw_items

    except Exception as e:
        print(f"Error in parse_menu_image: {e}")
        # Return a single error item
        return [{
            "menu_name_jp": "Error",
            "price": "0",
            "category": "Error",
            "description_rich": f"AI Vision Error: {str(e)}"
        }]
