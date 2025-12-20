import os
import csv
from datetime import datetime
from threading import Lock

# Thread-safe writing
_log_lock = Lock()

LOG_DIR = "logs"
API_LOG_FILE = os.path.join(LOG_DIR, "api_usage_log.csv")
OP_LOG_FILE = os.path.join(LOG_DIR, "operation_log.csv")

# Simplified Cost Model for Gemini (Adjust as needed for "Gemini 3.0" rates)
# Defaulting to Gemini 1.5 Pro/Flash mixed rates approximation for estimation
COST_MODEL = {
    "gemini-2.0-flash-exp": {"input": 0.05, "output": 0.20}, # Per 1M tokens
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "default": {"input": 0.10, "output": 0.40},
}
USD_JPY = 150.0

def _ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def _init_csv(filepath, headers):
    _ensure_log_dir()
    if not os.path.exists(filepath) or os.stat(filepath).st_size == 0:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def log_api_cost(store_id: str, phase: str, model_name: str, tokens_in: int, tokens_out: int):
    """
    Logs API usage and estimated cost.
    """
    try:
        _init_csv(API_LOG_FILE, ["timestamp", "store_id", "phase", "model", "tokens_in", "tokens_out", "cost_jpy"])
        
        # Determine rates
        rates = COST_MODEL.get(model_name, COST_MODEL["default"])
        # Simple lookup or heavy fallback
        if "flash" in model_name.lower():
            rates = COST_MODEL.get("gemini-1.5-flash") # Fallback estimate
        elif "pro" in model_name.lower():
             rates = COST_MODEL.get("gemini-1.5-pro")

        cost_usd = (tokens_in / 1_000_000 * rates["input"]) + (tokens_out / 1_000_000 * rates["output"])
        cost_jpy = cost_usd * USD_JPY

        with _log_lock:
            with open(API_LOG_FILE, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    store_id,
                    phase,
                    model_name,
                    tokens_in,
                    tokens_out,
                    f"{cost_jpy:.4f}"
                ])
    except Exception as e:
        print(f"[Observability] Failed to log API cost: {e}")

def log_op_action(store_id: str, user_id: str, action: str, details: str = ""):
    """
    Logs human operations (Owner/Staff actions).
    """
    try:
        _init_csv(OP_LOG_FILE, ["timestamp", "store_id", "user_id", "action", "details"])
        with _log_lock:
            with open(OP_LOG_FILE, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    store_id,
                    user_id,
                    action,
                    details
                ])
    except Exception as e:
        print(f"[Observability] Failed to log operation: {e}")
