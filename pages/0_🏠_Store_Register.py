import streamlit as st
import time

st.set_page_config(
    page_title="Store Register", 
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Store Registration (Phase 1)")
st.markdown("""
**TONOSAMAの世界へようこそ。**
まずはあなたの店舗情報と、**「これだけは食べてほしい」という自慢の一品** を教えてください。
""")

# --- auth check ---
if "supabase" not in st.session_state:
    st.error("認証クライアントが初期化されていません。Mainページからログインしてください。")
    st.stop()

supabase = st.session_state["supabase"]

# --- Input Form ---
with st.form("register_form"):
    st.subheader("1. 店舗情報 (Basic Info)")
    col1, col2 = st.columns(2)
    with col1:
        store_name = st.text_input("店舗名 (Store Name)", placeholder="居酒屋 TONOSAMA")
        owner_email = st.text_input("オーナーメールアドレス (任意)", placeholder="owner@example.com")
    with col2:
        store_url = st.text_input("店舗URL (任意/コンテクスト用)", placeholder="https://tabelog.com/...")
    
    st.markdown("---")
    st.subheader("2. 自慢の一品 (Signature Dish)")
    st.caption("まずは1品だけで構いません。最も自信のあるメニューを登録してください。")
    
    rec_name = st.text_input("メニュー名", placeholder="例：特選和牛のすき焼き")
    rec_price = st.number_input("価格 (税込)", min_value=0, step=100)
    rec_reason = st.text_area("おすすめの理由 (Why?)", placeholder="創業以来の秘伝のタレを使用しており...", height=100)
    
    submitted = st.form_submit_button("🚀 TONOSAMAをはじめる (Register)", type="primary")

if submitted:
    if not store_name or not rec_name:
        st.error("店舗名とメニュー名は必須です。")
    else:
        try:
            with st.spinner("登録中..."):
                # 1. Store Registration
                # 既存チェック (同名店舗があればID取得、なければ作成)
                store_id = None
                res = supabase.table("stores").select("id").eq("store_name", store_name).execute()
                if res.data:
                    store_id = res.data[0]["id"]
                    # URLなどの更新 (Upsert的な挙動)
                    supabase.table("stores").update({
                        "store_url": store_url, 
                        "owner_email": owner_email
                    }).eq("id", store_id).execute()
                else:
                    new_store = {
                        "store_name": store_name, 
                        "store_url": store_url, 
                        "owner_email": owner_email,
                        "plan_code": "standard" # Default
                    }
                    res_ins = supabase.table("stores").insert(new_store).execute()
                    if res_ins.data:
                        store_id = res_ins.data[0]["id"]
                
                if store_id:
                    # 2. Recommended Item Registration
                    # 既存のおすすめがあるかもしれないが、Phase1からの登録は常に追加(または名前で重複チェック)とする
                    # ここではシンプルに追加し、Owner Dashboardで整理してもらうスタイル
                    
                    item_data = {
                        "store_id": store_id,
                        "menu_name_ja": rec_name,
                        "detected_name": rec_name, # 手入力なので同じ
                        "price": int(rec_price),
                        "recommendation_reason": rec_reason,
                        "is_recommended": True,
                        "category": "フード", # デフォルト（後で変更可）
                        "description_ja_status": "pending", # まだAI生成していない
                        "persona": "standard"
                    }
                    
                    supabase.table("menu_master").insert(item_data).execute()
                    
                    st.success(f"ようこそ、{store_name} 様！ 「{rec_name}」を登録しました。")
                    st.session_state["store_name"] = store_name # 他ページへの引き継ぎ
                    
                    time.sleep(1.5)
                    st.switch_page("pages/1_📸_Menu_Maker.py")
                else:
                    st.error("店舗登録に失敗しました。")
                    
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

