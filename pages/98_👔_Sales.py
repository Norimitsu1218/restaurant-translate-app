import streamlit as st
import urllib.parse
import uuid

st.set_page_config(page_title="Sales Ops", page_icon="👔")

st.title("👔 TONOSAMA Sales Ops")
st.markdown("営業担当用：新規店舗への招待URLを発行します。")

# --- Form ---
with st.form("sales_invite_form"):
    st.subheader("基本情報 (Sales Input)")
    store_name = st.text_input("店舗名 (Store Name)", placeholder="居酒屋 TONOSAMA")
    plan_code = st.selectbox("プラン (Plan)", ["Entry (39,800)", "Standard (69,800)", "Premium (99,800)"])
    
    # Generate a temporary token or just embed basics
    # For a real app, we would create a 'invite_token' in DB to secure this.
    # For demo, we just encode params.
    
    submitted = st.form_submit_button("🔗 招待リンクを発行 (Generate Invite)")

if submitted:
    if not store_name:
        st.error("店舗名は必須です。")
    else:
        # Encode for URL
        params = {
            "store_name": store_name,
            "plan": plan_code.split(" ")[0].lower(),
            "ref": "sales_rep_A" # Audit trail
        }
        query_string = urllib.parse.urlencode(params)
        
        # In a real deployed Streamlit app, base URL varies.
        # We assume localhost for dev or the deployed URL.
        base_url = "http://localhost:8501" # Or https://tonosama-demo.streamlit.app
        invite_url = f"{base_url}/Store_Register?{query_string}"
        
        st.success("招待URLを発行しました！ iPadで開くか、店主に送信してください。")
        st.code(invite_url, language="text")
        st.caption("※このURLを開くと、店主用登録画面が『店舗名入力済み』の状態で開きます。")
