import streamlit as st
import pandas as pd
import time

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
    if st.button("🌍 翻訳を実行 (Phase 6 Start)"):
        # TODO: call translation function
        st.info("🔜 このボタンを押すと、確定したメニューが14言語に翻訳されます (実装準備中)")

st.divider()
st.caption("Note: 行を削除した場合、データベースからは物理削除されず残る場合があります（実装次第）。現在はUpsertのみ実装。")
