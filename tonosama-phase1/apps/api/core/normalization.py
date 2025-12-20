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
    Clean category names.
    "【Main Dish】" -> "Main Dish"
    """
    if not raw:
        return "未分類"
    clean = raw.strip().strip("【】[]「」")
    return clean if clean else "未分類"
