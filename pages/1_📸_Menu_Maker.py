import streamlit as st
import pandas as pd
from PIL import Image
import os
import json
import io
import time
from typing import List, Dict, Any

# Rootのモジュールを読み込めるようにする
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# ページ設定
st.set_page_config(
    page_title="Menu Maker",
    page_icon="📸",
    layout="wide"
)

st.title("📸 Menu Maker (The Experience)")
st.markdown("""
**AIが「メニュー画像」から、あなたの店の魅力を最大限に引き出すデータを生成します。**
まずは解析を行い、プランごとの違いを体験してください。
""")

# APIキーの確認
try:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"]:
            api_key = st.session_state["gemini_api_key"]
        else:
            api_key = None
except Exception:
    api_key = None

if not api_key:
    st.warning("⚠️ APIキーが見つかりません。メインページでログインまたは設定を行ってください。")
    st.stop()

# --- モデル設定 ---
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def get_vision_model(api_key):
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=0.7,
    )

class MenuItemExtracted(BaseModel):
    menu_name_jp: str = Field(description="日本語のメニュー名")
    price: str = Field(description="価格（数字のみ）")
    category: str = Field(description="推測されるカテゴリ（例：前菜、メイン、ドリンク）")
    description_rich: str = Field(description="【重要】18秒で読める魅力的な食レポ＋おすすめの食べ方＋ペアリングの提案を含んだ日本語の説明文")
    # アレルゲン (略)
    wheat: bool = Field(default=False)
    # ... (省略: Pydantic定義は長いので、プロンプトで制御するだけで十分かもしれないが、精度向上のため残すのがベターだが、ここでは簡略化してDictで受ける運用にする)
    # 実際にはプロンプト内でJSON形式を指定するだけに留める（コード量を減らすため）

# --- メイン処理 ---
st.sidebar.header("🔧 設定 (Settings)")

# 1. ペルソナ選択
persona_options = {
    "東京カレンダー風 (艶やか)": "文体は『東京カレンダー』のような、少し艶っぽく洗練されたトーンで。",
    "居酒屋の大将風 (元気)": "文体は『元気のいい居酒屋の大将』のように、親しみやすく活気のあるトーンで。",
    "高級料亭風 (厳格)": "文体は『老舗料亭の女将』のように、丁寧かつ格式高いトーンで。",
    "標準 (丁寧)": "文体は一般的なレストランメニューのように、丁寧でわかりやすいトーンで。"
}
selected_persona = st.sidebar.radio("🎭 食レポの文体 (Persona)", list(persona_options.keys()))
persona_instruction = persona_options[selected_persona]

# 2. 店舗設定
store_name_input = st.sidebar.text_input("🏠 店舗名 (Store Name)", value=st.session_state.get("store_name", ""), help="この名前でデータベースに登録されます")
if store_name_input:
    st.session_state["store_name"] = store_name_input

store_url = st.sidebar.text_input("🔗 店舗のURL (コンテクスト解析用)", placeholder="https://tabelog.com/...")
store_context = ""
supabase = st.session_state.get("supabase")

if not supabase:
    st.error("Supabase client is not initialized.")
    st.stop()

def register_store_if_needed(name: str, url: str) -> str:
    try:
        res = supabase.table("stores").select("id").eq("store_name", name).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["id"]
        
        # 新規登録時はデフォルト 'standard' で登録して、後で選ばせる
        new_store = {"store_name": name, "store_url": url, "plan_code": "standard"}
        res = supabase.table("stores").insert(new_store).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["id"]
        return None
    except Exception as e:
        return None

def save_menu_to_db(store_id: str, items: List[dict], persona: str):
    db_rows = []
    for item in items:
        # price cleaning
        raw_price = str(item.get("price", "0"))
        import re
        price_match = re.search(r'\d+', raw_price)
        price_val = int(price_match.group()) if price_match else 0
        
        row = {
            "store_id": store_id,
            "category": item.get("category"),
            "detected_name": item.get("menu_name_jp", item.get("name", "")),
            "price": price_val,
            "menu_name_ja": item.get("menu_name_jp", item.get("name", "")),
            "description_ja_18s": item.get("description_rich", item.get("description", "")),
            "description_ja_status": "generated",
            "persona": persona,
            "is_recommended": False
        }
        db_rows.append(row)
    
    if db_rows:
        supabase.table("menu_master").insert(db_rows).execute()

# --- Image Logic ---
uploaded_file = st.file_uploader("メニューの写真をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Menu", use_container_width=True)

    if st.button("🚀 AI解析開始 (Generate Experience)"):
        with st.spinner(f"Highest Quality AI Model ({MODEL_NAME}) is analyzing with Vision..."):
            try:
                # Use the new centralized Multimodal Utils
                from src.multimodal_utils import parse_menu_image
                import io

                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()

                # Execute Vision Extraction
                # Note: persona_instruction comes from sidebar
                items_data = parse_menu_image(
                    image_bytes=img_bytes, 
                    api_key=api_key, 
                    persona=persona_instruction,
                    store_id=st.session_state.get("store_name", "uknown_store")
                )
                
                # Check for errors
                if items_data and "Error" in items_data[0].get("menu_name_jp", ""):
                    st.error(items_data[0]["description_rich"])
                else:
                    st.session_state["extracted_items"] = items_data
                    st.toast("Analysis Complete!", icon="✨")
                
            except Exception as e:
                st.error(f"Error during AI Analysis: {e}")

# --- Result Display (The Comparison) ---
if "extracted_items" in st.session_state and st.session_state["extracted_items"]:
    items = st.session_state["extracted_items"]
    
    st.markdown("---")
    st.subheader("📊 Plan Comparison (Experience)")
    st.markdown("どちらのプランで運用するか、イメージしてください。")
    
    tab_eco, tab_std = st.tabs(["🔴 Economy Plan (39,800円)", "✨ Standard Plan (69,800円)"])
    
    with tab_eco:
        st.warning("Economy Planでは、AIによる食レポ生成は行われません。以下のように事実情報のみ抽出されます。")
        # Strip descriptions for display
        eco_data = []
        for item in items:
            eco_data.append({
                "Menu Name": item.get("menu_name_jp"),
                "Price": item.get("price"),
                "Category": item.get("category"),
                "Description": "(No Description / Manual Input Required)"
            })
        st.dataframe(pd.DataFrame(eco_data), use_container_width=True)
    
    with tab_std:
        st.success("Standard Planなら、AIが魅力的な文章を自動生成します。")
        # Full data
        std_data = []
        for item in items:
            std_data.append({
                "Menu Name": item.get("menu_name_jp"),
                "Price": item.get("price"),
                "Category": item.get("category"),
                "Description (AI Generated)": item.get("description_rich")
            })
        st.dataframe(pd.DataFrame(std_data), use_container_width=True)
        
        st.markdown("### 🚀 Next Step")
        st.markdown("**Standard Plan** のデータを使って、あなたの店がどう見えるかプレビューしましょう。")
        
        if st.button("📱 自分の店のページを確認する (Preview Store)", type="primary"):
            if not store_name_input:
                st.error("Store Name is required in sidebar.")
            else:
                with st.spinner("Saving data and building preview..."):
                    store_id = register_store_if_needed(store_name_input, store_url)
                    if store_id:
                        # Save Standard Data (The Good Stuff)
                        save_menu_to_db(store_id, items, selected_persona)
                        st.session_state["store_name"] = store_name_input # Carry over
                        time.sleep(1)
                        st.switch_page("pages/2_📱_Owner.py")
                    else:
                        st.error("Failed to register store.")

