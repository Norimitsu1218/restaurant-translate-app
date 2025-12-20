import json
import os
import datetime
from pathlib import Path

# Paths
# Logging to Phase 1 data dir for now
LOG_DIR = Path("/app/data/logs") if os.path.exists("/app/data") else Path("data/logs")
LOG_FILE = LOG_DIR / "api_usage_log.jsonl"

def ensure_log_dir():
    if not LOG_DIR.exists():
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except:
            pass

def log_api_usage(
    tenant_id: str = "default",
    store_id: str = "unknown",
    phase: str = "phase2",
    feature: str = "multimodal_extract",
    model: str = "gemini-2.0-flash-exp",
    input_type: str = "image",
    pages: int = 1,
    tokens_in: int = 0,
    tokens_out: int = 0,
    status: str = "ok",
    error_msg: str = ""
):
    """
    S2-08: Log API usage to JSONL.
    """
    ensure_log_dir()
    
    # Simple cost calc (Flash approx: Input $0.10/1M, Output $0.40/1M) -> JPY
    # $1 = 150 JPY
    cost_usd = (tokens_in / 1_000_000 * 0.10) + (tokens_out / 1_000_000 * 0.40)
    cost_jpy = cost_usd * 150
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tenant_id": tenant_id,
        "store_id": store_id,
        "phase": phase,
        "feature": feature,
        "model": model,
        "input_type": input_type,
        "pages": pages,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_jpy_est": round(cost_jpy, 4),
        "status": status,
        "error": error_msg
    }
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}")
