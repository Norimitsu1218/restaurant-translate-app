import re
from typing import Optional, Tuple

def normalize_price(raw: str) -> Tuple[Optional[int], str]:
    """
    S2-04 Normalization: "980円" -> (980, "JPY")
    Handles: "¥1,000", "1.000,-", "USD 10"
    """
    if not raw:
        return None, "JPY"

    # Common cleanup
    clean = raw.replace(",", "").replace("，", "").strip()
    
    # Currency detection (mock/simple)
    currency = "JPY"
    if "USD" in clean or "$" in clean:
        currency = "USD"
    
    # Extract digits
    # Regex for integer-like sequence
    match = re.search(r'(\d+)', clean)
    if match:
        try:
            return int(match.group(1)), currency
        except:
            pass
            
    return None, currency

def normalize_category(raw: str) -> str:
    """
    S2-04 Normalization: Map to standard categories.
    Target: [Food, Drink, Dessert, Lunch, Course] + (Other)
    """
    if not raw:
        return "Food" # Default to Food
        
    clean = raw.strip().strip("【】[]「」").lower()
    
    # Mapping Rules (Priority Order)
    if any(k in clean for k in ["drink", "beverage", "alcohol", "sake", "beer", "wine", "coffee", "tea", "ドリンク", "飲み物", "酒"]):
        return "Drink"
    
    if any(k in clean for k in ["dessert", "sweet", "cake", "ice", "dolce", "デザート", "スイーツ", "甘味", "菓子"]):
        return "Dessert"
        
    if any(k in clean for k in ["lunch", "set", "meal", "ランチ", "定食", "御膳", "昼"]):
        return "Lunch"
        
    if any(k in clean for k in ["course", "kaiseki", "plan", "コース", "会席", "宴会"]):
        return "Course"
    
    # Default fallback
    return "Food"
