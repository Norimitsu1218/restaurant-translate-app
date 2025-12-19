import streamlit as st
import pandas as pd
import time
import asyncio
import json
import sys
import os

# Root path adjustment to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.langchain_utils import MenuItem, translate_japanese_to_english, translate_english_to_many_async
from src.st_utils import get_gemini_api_key

st.set_page_config(
    page_title="Owner Dashboard", 
    page_icon="📱",
    layout="wide"
)

st.title("📱 Owner Dashboard (Phase 5)")
st.markdown("""
**店主様確認画面**
AIが生成したメニュー情報（食レポなど）を確認・修正できます。
ここで「確定」された内容が、世界14言語へ翻訳されます。
""")

# --- auth check ---
if "supabase" not in st.session_state:
    st.error("認証クライアントが初期化されていません。Mainページからログインしてください。")
    st.stop()

supabase = st.session_state["supabase"]

# --- Sidebar: Login ---
st.sidebar.header("Store Login")
store_name = st.sidebar.text_input("店舗名 (Store Name)", value="Test Store")

def get_store(name):
    try:
        res = supabase.table("stores").select("*").eq("store_name", name).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        st.error(f"Error fetching store: {e}")
    return None

if not store_name:
    st.warning("店舗名を入力してください")
    st.stop()

store_info = get_store(store_name)

if not store_info:
    st.warning(f"店舗 '{store_name}' が見つかりません。Menu Makerで登録してください。")
    st.stop()

store_id = store_info["id"]
st.sidebar.success(f"Login: {store_info['store_name']}")

# --- Fetch Menu ---
def fetch_menu(s_id):
    try:
        # id, category, menu_name_ja, price, description_ja_18s, is_recommended, updated_at
        res = supabase.table("menu_master").select("*").eq("store_id", s_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching menu: {e}")
        return []

menu_data = fetch_menu(store_id)

if not menu_data:
    st.info("📝 メニューデータがありません。Menu Makerで写真をアップロードしてください。")
    st.stop()

# --- Data Editor ---
df = pd.DataFrame(menu_data)

# 表示・編集するカラムのみ抽出
# idはupdate用に保持するが、表示は隠すかReadOnlyにする
# session_stateを使って編集データを保持
if "editor_key" not in st.session_state:
    st.session_state["editor_key"] = 0

st.subheader(f"メニュー編集: {len(df)} 品")
st.caption("表のセルを直接クリックして修正できます。修正後は**必ず「保存」ボタン**を押してください。")

# 列設定
column_config = {
    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
    "category": st.column_config.SelectboxColumn("カテゴリ", options=["ドリンク", "フード", "ランチ", "コース", "デザート"], required=True),
    "menu_name_ja": st.column_config.TextColumn("メニュー名 (日本語)", required=True),
    "price": st.column_config.NumberColumn("価格", format="¥%d", min_value=0),
    "description_ja_18s": st.column_config.TextColumn("18秒食レポ (修正可)", width="large"),
    "is_recommended": st.column_config.CheckboxColumn("おすすめ", help="POPや特集に掲載されます"),
    "description_ja_status": st.column_config.SelectboxColumn("ステータス", options=["pending", "generated", "confirmed"], disabled=True),
}

# 編集用DF (必要な列のみ、かつIDは必須)
display_cols = ["id", "category", "menu_name_ja", "price", "description_ja_18s", "is_recommended", "description_ja_status"]
edit_df = df[display_cols].copy()

edited_df = st.data_editor(
    edit_df,
    key=f"data_editor_{st.session_state['editor_key']}",
    column_config=column_config,
    num_rows="dynamic", # 行追加・削除可能にする
    use_container_width=True,
    hide_index=True
)

# --- Save Logic ---
col1, col2 = st.columns([1, 3])

with col1:
    if st.button("💾 変更を保存 (Save Files)", type="primary"):
        try:
            # 1. 更新 (Modified items)
            # data_editor の全データを iterateして upsert するのが一番確実
            # (only diff is sent usually, but for simplicity we assume full sync or rely on 'edited_rows' if using session state callbacks, but full upsert is easier to implement)
            
            # DataFrame -> List check
            payload = []
            for index, row in edited_df.iterrows():
                # IDがある場合はUpdate, ない場合(新規行)はInsertだが、data_editorの新規行はIDが空/NaN
                
                item_data = {
                    "store_id": store_id,
                    "category": row["category"],
                    "menu_name_ja": row["menu_name_ja"],
                    "price": int(row["price"]) if pd.notnull(row["price"]) else 0,
                    "description_ja_18s": row["description_ja_18s"],
                    "is_recommended": bool(row["is_recommended"]),
                    "description_ja_status": "confirmed", # 保存したらconfirmed扱いにする
                    "updated_at": "now()"
                }
                
                # IDの判定
                row_id = row.get("id")
                if row_id and pd.notna(row_id) and str(row_id).strip() != "":
                     item_data["id"] = row_id
                
                payload.append(item_data)

            if payload:
                # Upsert (idがあればupdate, なければinsert)
                res = supabase.table("menu_master").upsert(payload).execute()
                st.success("✅ 保存しました！")
                time.sleep(1)
                st.rerun() # リロードして最新化
                
        except Exception as e:
            st.error(f"Save Error: {e}")

with col2:
    if st.button("🌍 翻訳を実行 (Phase 6 Start)", type="primary"):
        # 1. API Key Check
        api_key = get_gemini_api_key()
        if not api_key:
            st.error("Gemini API Keyが設定されていません。メインページでAPIキーを設定してください。")
            st.stop()
            
        # 2. 対象データ取得
        # confirmedかつ、translationsが未完了(空)のもの、あるいは全て再翻訳？
        # ここではシンプルに「表示されているデータ全て」を翻訳対象とする（Upsert済みのもの）
        # 最新のデータをDBから再取得
        current_menu = fetch_menu(store_id)
        if not current_menu:
            st.warning("翻訳するメニューがありません。")
            st.stop()
            
        # MenuItemオブジェクトへの変換
        menu_items_obj = []
        # DB IDとindexの紐付け用
        db_id_map = {} 
        
        for idx, row in enumerate(current_menu):
            # category: str, menu_name_ja: str, price: int, description_ja_18s: str ...
            item = MenuItem(
                menu_title=row.get("menu_name_ja", ""),
                menu_content=row.get("description_ja_18s", "")
            )
            menu_items_obj.append(item)
            db_id_map[idx] = row["id"]
            
        st.write(f"🚀 {len(menu_items_obj)} 品の翻訳を開始します... (これには時間がかかります)")
        progress_bar = st.progress(0, text="翻訳準備中...")
        
        # 3. 実行 (Async)
        try:
            # Phase 6a: Ja -> En
            st.toast("日本語 → 英語 翻訳中...")
            persona = current_menu[0].get("persona", "標準 (丁寧)") # 1件目のペルソナを採用
            
            # Sync function call
            english_results = translate_japanese_to_english(menu_items_obj, api_key, persona)
            
            # Phase 6b: En -> Multi-Lang
            st.toast("英語 → 14言語 展開中... (Suzuka Engine)")
            
            # 定義済みの14言語 (CSV定義準拠)
            # 韓国, 中国, 台湾, 広東, タイ, フィリピン, ベトナム, インドネシア, スペイン, ドイツ, フランス, イタリア, ポルトガル
            # (csv_utils.pyなどから共通化すべきだが、一旦ハードコード)
            target_langs = {
                "ko": [], "zh": [], "zh-TW": [], "yue": [], "th": [],
                "tl": [], "vi": [], "id": [], "es": [], "de": [], "fr": [], "it": [], "pt": []
            }
            # ※注: Geminiの言語コードに合わせてマッピングが必要だが、プロンプトで言語名を指定しているのでキーはそのままでOK
            
            # async実行のために event loop を作成/取得
            # Streamlit上でのasync実行は asyncio.run() でいける
            translated_multilang = asyncio.run(translate_english_to_many_async(english_results, target_langs, api_key, persona))
            
            # 4. 結果の結合とDB保存
            payload = []
            for idx, en_item in enumerate(english_results):
                row_id = db_id_map[idx]
                
                # 翻訳データの構築 structure: { "en": {title, content}, "fr": {title, content}, ... }
                trans_json = {
                    "en": {
                        "menu_title": en_item.menu_title,
                        "menu_content": en_item.menu_content
                    }
                }
                
                # 多言語分の追加
                for lang_code, items_list in translated_multilang.items():
                    # items_list[idx] が対応するアイテム
                    if idx < len(items_list):
                        m_item = items_list[idx]
                        trans_json[lang_code] = {
                            "menu_title": m_item.menu_title,
                            "menu_content": m_item.menu_content
                        }
                
                payload.append({
                    "id": row_id,
                    "store_id": store_id,
                    "translations": trans_json, # JSONB update
                    "description_ja_status": "translated",
                    "updated_at": "now()"
                })
            
            # DB更新
            supabase.table("menu_master").upsert(payload).execute()
            
            progress_bar.progress(100, text="✅ 全言語翻訳完了！")
            st.success("🎉 世界への扉が開かれました！ (翻訳データ保存完了)")
            time.sleep(2)
            st.rerun()

        except Exception as e:
            st.error(f"Translation Error: {e}")
            

st.divider()
st.caption("Note: 行を削除した場合、データベースからは物理削除されず残る場合があります（実装次第）。現在はUpsertのみ実装。")
