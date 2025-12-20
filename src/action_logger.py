# src/action_logger.py
import os
import csv
from datetime import datetime
import threading

_LOCK_ACTION = threading.Lock()
ACTION_LOG_PATH = "logs/owner_actions.csv"

def log_owner_action(store_id: str, action_type: str, item_id: str = "", details: str = ""):
    """
    店主の操作ログを記録する
    
    Args:
        store_id: 店舗ID
        action_type: 操作種別 (e.g. "manual_edit", "swipe_approved", "upload_menu")
        item_id: 対象のMenuItem ID (optional)
        details: 変更内容や備考 (optional)
    """
    with _LOCK_ACTION:
        # ヘッダー作成
        if not os.path.exists(ACTION_LOG_PATH) or os.stat(ACTION_LOG_PATH).st_size == 0:
            os.makedirs("logs", exist_ok=True)
            with open(ACTION_LOG_PATH, "w", encoding="utf-8") as f:
                f.write("timestamp,store_id,action_type,item_id,details\n")
        
        now = datetime.now().isoformat()
        try:
            with open(ACTION_LOG_PATH, "a", encoding="utf-8") as f:
                # CSV escape for details
                clean_details = details.replace('"', '""').replace('\n', ' ')
                f.write(f'{now},{store_id},{action_type},{item_id},"{clean_details}"\n')
        except Exception as e:
            print(f"Action Log Error: {e}")
