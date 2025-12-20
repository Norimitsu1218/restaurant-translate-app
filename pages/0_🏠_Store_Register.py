import streamlit as st
import time
from src.payment_guard import PaymentGuard

st.set_page_config(
    page_title="Store Register", 
    page_icon="🏠",
    layout="wide"
)

# --- 1. Sales Handoff (URL Params) ---
# Sales Rep generates URL with extensive params
query_params = st.query_params
pre_store_name = query_params.get("store_name", "")
pre_plan_code = query_params.get("plan", "standard")
pre_corp_name = query_params.get("corp_name", "")
pre_rep_name = query_params.get("rep_name", "")
pre_email = query_params.get("email", "")
pre_tone = query_params.get("tone", "standard")

if pre_store_name:
    st.title(f"🏠 Welcome to TONOSAMA, {pre_store_name} 様")
    st.info("営業担当との打ち合わせ内容に基づき、初期情報を自動入力しています。内容を確認し、登録を完了させてください。")
else:
    st.title("🏠 Store Registration (Phase 1)")
    st.markdown("店舗様向け登録画面です。営業担当から受け取ったURLからアクセスすることを推奨します。")

# --- Auth Check ---
if "supabase" not in st.session_state:
    st.error("認証接続エラー: Mainページからリロードしてください。")
    st.stop()
supabase = st.session_state["supabase"]

# --- Input Form ---
with st.form("register_form"):
    st.subheader("1. 契約情報 (Billing Info)")
    st.markdown("法令および請求業務に必要なため、必ず正式名称でご入力ください。")
    
    col1, col2 = st.columns(2)
    with col1:
        store_name = st.text_input("店舗名 (Store Name)", value=pre_store_name, placeholder="居酒屋 TONOSAMA")
        corporate_name = st.text_input("運営会社名 (Corporate Name) *必須", value=pre_corp_name, placeholder="株式会社トノサマ")
    with col2:
        rep_name = st.text_input("契約責任者名 (Representative) *必須", value=pre_rep_name, placeholder="山田 太郎")
        address = st.text_input("所在地 (Address) *必須", placeholder="東京都千代田区...")

    st.markdown("---")
    st.subheader("2. アカウント情報 & プラン")
    
    col3, col4 = st.columns(2)
    with col3:
        email = st.text_input("オーナーメールアドレス *必須", value=pre_email, placeholder="owner@example.com")
    with col4:
        # Plan is locked if invitation
        if pre_store_name:
            st.text_input("選択プラン (Plan)", value=pre_plan_code, disabled=True)
            plan_code_val = pre_plan_code
        else:
            plan_code_val = st.selectbox("プラン (Plan)", ["standard", "premium", "entry"])

    # Hidden Prefs Display
    if pre_tone:
        st.caption(f"📝 設定済みAI口調: {pre_tone}")

    # Terms
    st.markdown("---")
    st.markdown("#### 利用規約 と お支払い")
    terms_agreed = st.checkbox("利用規約 (Terms of Service) に同意する", value=False)
    
    # Mock Stripe
    st.info("💳 登録完了後、Stripe決済画面へ遷移します (デモではスキップ)。")

    submitted = st.form_submit_button("🚀 規約に同意して決済へ進む", type="primary")

if submitted:
    if not terms_agreed:
        st.error("利用規約への同意が必要です。")
        st.stop()
    
    if not (store_name and corporate_name and rep_name and address and email):
        st.error("必須項目 (*) が入力されていません。")
        st.stop()

    try:
        with st.spinner("契約情報を登録中..."):
            # A. Stores Table Upsert
            store_data = {
                "store_name": store_name,
                "corporate_name": corporate_name,
                "representative_name": rep_name,
                "address": address,
                "owner_email": email,
                "plan_code": plan_code_val,
                "payment_status": "paid", # Demo: Auto-pay for smooth UX
                "terms_agreed_at": "now()"
            }
            
            # Use Metadata for Tone preferences (Mocking JSONB)
            # In real DB, we would save to 'preferences' column.
            
            existing = supabase.table("stores").select("id").eq("store_name", store_name).execute()
            if existing.data:
                sid = existing.data[0]["id"]
                supabase.table("stores").update(store_data).eq("id", sid).execute()
            else:
                res = supabase.table("stores").insert(store_data).execute()
                sid = res.data[0]["id"]
            
            if sid:
                # B. Menu Item (Dummy if needed, or skip)
                # If demo created items, we might want to carry them over, 
                # but currently demo is stateless. We start fresh or could pass item via params (too long).
                # Keep it simple: Start fresh.
                
                st.success("✅ アカウント登録 & 決済が完了しました！")
                st.balloons()
                
                # Set Session
                st.session_state["store_name"] = store_name
                st.session_state["payment_status"] = "paid"
                
                # Transition
                st.markdown("### Next Step")
                st.markdown("管理画面へ移動します。")
                if st.button("📱 管理画面 (Owner Dashboard) へ"):
                    st.switch_page("pages/2_📱_Owner.py")

    except Exception as e:
        st.error(f"System Error: {e}")

