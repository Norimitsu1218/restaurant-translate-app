import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image

st.set_page_config(
    page_title="Admin Ops", 
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 TONOSAMA Admin (Hotel Bell)")
st.markdown("ここで **店主が見ない裏作業 (Phase 8, 9, 10)** を実行します。")

# --- Auth Guard (Simple) ---
# 本来は管理者権限チェックが必要。簡易的に "admin" パラメータなどで隠蔽、
# または単にこのページへのリンクを他に出さない運用とする。
# ここでは一旦チェックなし（開発用）

if "supabase" not in st.session_state:
    st.error("DB connection checked out. Please login from main.")
    st.stop()
supabase = st.session_state["supabase"]

# --- Store Selector ---
st.sidebar.header("Target Store")
try:
    stores_res = supabase.table("stores").select("id, store_name, plan_code").execute()
    stores = stores_res.data
except Exception as e:
    st.error(f"Error fetching stores: {e}")
    st.stop()

if not stores:
    st.warning("No stores found.")
    st.stop()

store_options = {s["store_name"]: s for s in stores}
selected_store_name = st.sidebar.selectbox("Select Store", list(store_options.keys()))
selected_store = store_options[selected_store_name]
store_id = selected_store["id"]
plan = selected_store.get("plan_code", "standard")

st.sidebar.info(f"ID: {store_id}\nPlan: {plan}")

# --- Tabs ---
tab8, tab9, tab10 = st.tabs(["Phase 8: Site Gen", "Phase 9: QR/POP", "Phase 10: Print/Ship"])

# --- Shared Asset Logic ---
def create_asset_package(store_name, store_id):
    import zipfile
    
    # 1. Fetch Data
    menu_res = supabase.table("menu_master").select("*").eq("store_id", store_id).execute()
    menu_data = menu_res.data
    
    # 2. Identify Recommended Item
    rec_item = next((x for x in menu_data if x.get("is_recommended")), None)
    
    # 3. Create ZIP in memory
    zip_buffer = BytesIO()
    folder_prefix = f"★{store_name}/"
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        # A. CSV / Excel (JSON for now, CSV via pandas)
        if menu_data:
            df = pd.DataFrame(menu_data)
            csv_data = df.to_csv(index=False).encode('utf-8_sig')
            zf.writestr(f"{folder_prefix}menu_data.csv", csv_data)
            
        # B. Recommended Item TXT
        if rec_item:
            target_url = f"https://tonosama-demo.streamlit.app/menu?id={store_id}"
            txt_content = f"""【TONOSAMA POP作成依頼書】
店舗名: {store_name}
店舗URL: {target_url}

■おすすめの一品
商品名: {rec_item.get('menu_name_ja')}
価格: ¥{rec_item.get('price')}
キャッチコピー(理由):
{rec_item.get('recommendation_reason')}

■AI食レポ(参考):
{rec_item.get('description_ja_18s', '')}

■翻訳ステータス: {rec_item.get('translations', {}).keys()}
"""
            zf.writestr(f"{folder_prefix}recommendation.txt", txt_content)
        
        # C. Images (Placeholder)
        # 実装上、画像バイナリがDBにないため、READMEで代替
        zf.writestr(f"{folder_prefix}images/README.txt", "画像ファイルは別途Box/Google Drive等から取得してください(未連携)")

    return zip_buffer.getvalue()

# === Phase 8 & 9: Asset Handoff (Shota & Totsuka) ===
# 成果物は同じなので、タブを統合あるいは同じ機能を提供
with tab8:
    st.header("Phase 8 & 9: Asset Handoff")
    st.markdown("""
    **正太さん(Phase 8) & 戸塚さん(Phase 9) への共有フロー**
    
    1. 以下のボタンで「提出用アセット (★フォルダ)」を一括ダウンロードします。
    2. これをクラウド(Box/Drive)に上げ、そのURLを発行します。
    3. 下のメールテンプレートを使って、正太さん・戸塚さんに送信してください。
    """)
    
    if st.button("📦 Generate Asset Package (★Folder)"):
        zip_bytes = create_asset_package(selected_store_name, store_id)
        st.download_button(
            label=f"Download ★{selected_store_name}.zip",
            data=zip_bytes,
            file_name=f"★{selected_store_name}.zip",
            mime="application/zip"
        )
    
    st.subheader("✉️ Email Template")
    mock_url = f"https://box.com/shared/tonosama/{store_id}"
    email_body = f"""
To: 正太さん, 戸塚さん
Subject: 【TONOSAMA】新規店舗素材の共有 ({selected_store_name})

お疲れ様です。
新規店舗「{selected_store_name}」の素材一式を格納しました。

■格納先 (★{selected_store_name})
{mock_url}

■依頼内容
【正太さん】専用サイトの登録をお願いします。
【戸塚さん】QRコードとPOPの作成をお願いします。(オススメ一品のtxtはフォルダ内にあります)

よろしくお願いいたします。
"""
    st.text_area("Draft Email", email_body, height=250)


# === Phase 10: Printing (Shota-san) ===
with tab10:
    st.header("Phase 10: Printing Completion (by Shota-san)")
    st.markdown("正太さんが印刷手配を完了したら、ここでステータスを更新します。")
    st.caption("※戸塚さんとの連絡は電話で行うため、システム通知は不要です。")
    
    # Current Status (Mock)
    is_done = st.checkbox("印刷手配完了 (Printing Arrangement Competed)", key="print_done")
    
    if st.button("Update Status"):
        if is_done:
            st.success(f"✅ {selected_store_name} の印刷手配を完了としました！")
            st.balloons()
        else:
            st.info("まだ未完了です。")

# Remove Tab 9 content as it is merged into logic above or user requested same flow
with tab9:
    st.info("Phase 9 (Qr/POP) は 'Phase 8: Site Gen' タブに統合しました（共有素材が同一のため）。")

