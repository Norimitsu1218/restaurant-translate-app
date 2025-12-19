import streamlit as st

class PaymentGuard:
    """
    鈴鹿山脈の関所 (Payment Guard)
    プランや支払い状況に応じて機能制限を行うクラス
    """
    
    FREE_LIMIT = 5
    
    def __init__(self, supabase):
        self.supabase = supabase

    def check_item_limit(self, store_id: str) -> dict:
        """
        現在のアイテム数と、追加可能かどうかを判定する
        Return: {
            "allowed": bool,
            "current_count": int,
            "limit": int,
            "is_paid": bool
        }
        """
        try:
            # 1. Store情報の取得 (Payment Status)
            store_res = self.supabase.table("stores").select("payment_status, plan_code").eq("id", store_id).execute()
            if not store_res.data:
                return {"allowed": False, "reason": "Store not found"}
            
            store = store_res.data[0]
            is_paid = store.get("payment_status") == "paid"
            
            if is_paid:
                # 支払い済みなら無制限
                return {
                    "allowed": True, 
                    "current_count": 0, # Don't care
                    "limit": 9999,
                    "is_paid": True
                }
            
            # 2. 現在のアイテム数確認
            # countオプションを使うのが効率的
            count_res = self.supabase.table("menu_master").select("id", count="exact").eq("store_id", store_id).execute()
            current_count = count_res.count if count_res.count is not None else len(count_res.data)
            
            remaining = self.FREE_LIMIT - current_count
            
            return {
                "allowed": remaining > 0,
                "current_count": current_count,
                "limit": self.FREE_LIMIT,
                "remaining": max(0, remaining),
                "is_paid": False
            }
            
        except Exception as e:
            print(f"PaymentGuard Error: {e}")
            # 安全側に倒す（エラー時は制限しない、あるいはエラー表示）
            # ここではFalseにしておく
            return {"allowed": False, "reason": str(e)}

    def render_upsell_message(self):
        """制限到達時のメッセージを表示"""
        st.warning(f"🔒 **無料プランの上限({self.FREE_LIMIT}品)に達しました**")
        st.markdown(f"""
        これ以上登録するには、プランのアップグレードが必要です。
        
        **【TONOSAMA Standard Plan】**
        *   無制限のメニュー登録
        *   14言語へのAI翻訳
        *   専任コンサルタントによるサポート
        
        [👉 アップグレードはこちら (39,800円〜)](https://example.com/upgrade)
        """)
