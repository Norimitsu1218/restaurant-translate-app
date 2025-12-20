# src/payment_guard.py
import streamlit as st

class PaymentGuard:
    """
    【鈴鹿山脈】支払い状況ガード (Payment Guard)
    
    店の支払いステータス (pending/paid) とプランに基づき、
    機能の実行可否を判定・強制する。
    """
    
    @staticmethod
    def get_payment_status(store_id: str) -> str:
        """
        本来はDBのbillingテーブルを見る。
        今回はDemo用に session_state または固定値を返す。
        """
        if "payment_status" in st.session_state:
            return st.session_state["payment_status"]
        
        # Default to 'pending' (Safe side) unless overridden
        return "pending" 

    @staticmethod
    def assert_paid(store_id: str, feature_name: str = "Common"):
        """
        支払済みでなければ例外を投げる (Stop Execution)
        """
        status = PaymentGuard.get_payment_status(store_id)
        if status != "paid":
            st.error(f"🚫 This feature ({feature_name}) requires a PAID plan. Store Status: {status}")
            st.warning("Please complete payment to proceed.")
            st.stop() # Streamlit stop execution

    @staticmethod
    def is_paid(store_id: str) -> bool:
        return PaymentGuard.get_payment_status(store_id) == "paid"

    @staticmethod
    def mock_set_paid(paid: bool):
        """デモ用"""
        st.session_state["payment_status"] = "paid" if paid else "pending"
