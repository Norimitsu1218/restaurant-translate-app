import streamlit as st
import time

st.set_page_config(
    page_title="Select Plan", 
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("💎 プランの選択 (Select Plan)")
st.markdown("""
コンテンツの確認、お疲れ様でした！
最後に、TONOSAMAの利用プランを選択してください。
""")

# CSS for pricing table
st.markdown("""
<style>
.plan-card {
    border: 2px solid #ddd;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;
}
.plan-card:hover {
    transform: translateY(-5px);
    border-color: #D87800;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.plan-title {
    font-size: 24px;
    font-weight: bold;
    color: #333;
}
.plan-price {
    font-size: 32px;
    font-weight: bold;
    color: #D87800;
    margin: 15px 0;
}
.plan-features {
    text-align: left;
    margin-bottom: 20px;
    font-size: 14px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

if "supabase" not in st.session_state:
    st.error("Please login from main page.")
    st.stop()

supabase = st.session_state["supabase"]
store_name = st.session_state.get("store_name", "")

col1, col2, col3 = st.columns(3)

# --- Economy Plan ---
with col1:
    st.markdown("""
    <div class="plan-card">
        <div class="plan-title">梅 (Economy)</div>
        <div class="plan-price">¥39,800</div>
        <div class="plan-features">
            ✅ AI文字認識 (OCR)<br>
            ✅ 基本メニュー登録<br>
            ❌ <b>AI食レポ生成 (自分入力)</b><br>
            ❌ <b>多言語翻訳 (別料金)</b><br>
            ❌ <b>専任サポートなし</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("これにする (Economy)", key="eco"):
        with st.expander("⚠️ 本当によろしいですか？", expanded=True):
            st.warning("""
            Economyプランでは、**先ほど体験した「AI食レポ」は全て破棄されます。**
            ご自身で全ての紹介文を入力し直す必要がありますが、よろしいですか？
            """)
            if st.button("はい、苦労して入力します", type="secondary"):
                with st.spinner("Processing..."):
                    # Update DB to economy
                    supabase.table("stores").update({"plan_code": "economy"}).eq("store_name", store_name).execute()
                    # Logic to clear descriptions could go here
                    time.sleep(1)
                    st.success("プランを変更しました。")
                    st.switch_page("pages/99_🔧_Admin.py")

# --- Standard Plan ---
with col2:
    st.markdown("""
    <div class="plan-card" style="border-color: #D87800; border-width: 4px; background-color: #fffaf0;">
        <div class="plan-title">竹 (Standard)</div>
        <div class="plan-price">¥69,800</div>
        <div class="plan-features">
            ✅ AI文字認識 (OCR)<br>
            ✅ <b>AI食レポ生成 (Pro版)</b><br>
            ✅ <b>ペアリング提案</b><br>
            ✅ <b>14言語翻訳付き</b><br>
            ✅ <b>メールサポート</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ これにする (Standard)", type="primary", key="std"):
        with st.spinner("Setting up your plan..."):
            supabase.table("stores").update({"plan_code": "standard"}).eq("store_name", store_name).execute()
            time.sleep(1)
            st.balloons()
            st.success("ありがとうございます！ Standardプランで設定しました。")
            time.sleep(2)
            st.switch_page("pages/99_🔧_Admin.py")

# --- Full Plan ---
with col3:
    st.markdown("""
    <div class="plan-card">
        <div class="plan-title">松 (Premium)</div>
        <div class="plan-price">¥99,800</div>
        <div class="plan-features">
            ✅ <b>Standardの全機能</b><br>
            ✅ <b>専任コンサルタント</b><br>
            ✅ <b>写真撮影代行 (1回)</b><br>
            ✅ <b>優先サポート</b><br>
            ✅ <b>POP作成代行</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("相談する (Premium)", key="prem"):
        st.info("担当者 (Hotell Bell) からご連絡いたします。")

st.markdown("---")
st.caption(f"Current Store: {store_name}")
