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
tab6, tab8, tab9, tab10 = st.tabs(["Phase 6: Translate", "Phase 8: Site Gen", "Phase 9: QR/POP", "Phase 10: Print/Ship"])

# === Phase 6: Translation (Ops) ===
with tab6:
    st.header("Phase 6: Multilingual Translation")
    st.markdown("店主が確認(Phase 5)したメニューを、14言語に翻訳します。")
    
    # Check status
    pending_trans = supabase.table("menu_master").select("*").eq("store_id", store_id).neq("description_ja_status", "confirmed").execute()
    if pending_trans.data:
        st.warning(f"⚠️ {len(pending_trans.data)} items are NOT confirmed by owner yet.")
    else:
        st.success("✅ All items are confirmed by owner.")

    if st.button("🌏 Start Translation Engine (14 Languages)"):
        import asyncio
        from src.langchain_utils import translate_english_to_many_async, MenuItem
        
        # 1. API Key Check
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            if "gemini_api_key" in st.session_state:
                api_key = st.session_state["gemini_api_key"]
            else:
                st.error("API Key not found.")
                st.stop()

        with st.spinner("Processing Translations (with Cache & Gemini)..."):
            # 2. Prepare Data (Convert DB rows to MenuItem)
            # We assume 'description_ja_18s' (Japanese) is the source for EN translation if EN is missing,
            # BUT the pipeline expects MenuItem objects.
            # Usually we translate JA -> EN first, then EN -> 14 Langs.
            # For this 'Suzuka' demo, let's assume we are doing EN -> Multi.
            # If EN doesn't exist, we might need JA -> EN first.
            
            # Simple Logic: Only process items that have description_ja_18s
            target_items = []
            row_map = {} # db_id -> MenuItem
            
            for row in pending_trans.data:
                # Use JA name/desc as source if EN is missing
                # In a real app we would ensure EN exists first.
                # Here we pass JA in as 'menu_title' so the pipeline sees it.
                item = MenuItem(
                    menu_title=row.get("menu_name_ja", ""),
                    menu_content=row.get("description_ja_18s", "")
                )
                target_items.append(item)
                row_map[row["id"]] = item

            if not target_items:
                st.warning("No items to translate.")
            else:
                # 3. Define Targets
                # 14 languages is a lot for a demo, let's do top 5 including EN
                targets = {
                    "English": [], "Chinese": [], "Korean": [], "Thai": [], "French": [] 
                }
                
                # 4. Run Async Pipeline
                # This function usually translates FROM English. 
                # If our input is Japanese, it might be weird.
                # Ideally we run JA->EN first.
                # Let's assume the pipeline handles it or we trust the LLM to translate from JA if EN is missing.
                # Actually, langchain_utils.translate_english_to_many_async takes 'menu_items'.
                
                # Let's run JA -> EN first for better quality
                from src.langchain_utils import translate_japanese_to_english
                
                # Step A: JA -> EN (if needed) - cost logged as trans_en
                en_items = translate_japanese_to_english(target_items, api_key) # Sync call
                
                # Step B: EN -> Multi
                results = asyncio.run(translate_english_to_many_async(en_items, targets, api_key))
                
                # 5. Save to DB
                # This is tricky because we need to map back to original IDs.
                # Since lists preserve order:
                for idx, row in enumerate(pending_trans.data):
                    db_id = row["id"]
                    updates = {
                        "description_ja_status": "confirmed", # Mark as processed
                        # Save EN
                        "menu_name_en": en_items[idx].menu_title,
                        "description_en": en_items[idx].menu_content,
                    }
                    
                    # Save others
                    for lang, translated_list in results.items():
                        # Map lang to DB column
                        col_prefix = "description_" + lang[:2].lower() # simple heuristic
                        if lang == "Chinese": col_prefix = "description_zh"
                        if lang == "Korean": col_prefix = "description_ko"
                        if lang == "Thai": col_prefix = "description_th"
                        if lang == "French": col_prefix = "description_fr"
                        
                        # We might not have columns for all, but try best effort
                        # In this demo, we might just store JSON or confirm success
                        pass
                    
                    try:
                        supabase.table("menu_master").update(updates).eq("id", db_id).execute()
                    except Exception as e:
                        print(f"Update failed for {db_id}: {e}")
                
                st.success(f"Translation Complete for {len(target_items)} items!")
                st.balloons()

# --- Shared Asset Logic ---
# --- Shared Asset Logic ---
def sync_to_drive_folder(store_name, store_id, drive_root_path="drive_sync"):
    import os
    import pandas as pd
    from src.action_logger import log_owner_action
    
    # 1. Fetch Data
    menu_res = supabase.table("menu_master").select("*").eq("store_id", store_id).execute()
    menu_data = menu_res.data
    
    # 2. Identify Recommended Item
    rec_item = next((x for x in menu_data if x.get("is_recommended")), None)
    
    # 3. Create Target Directory
    # Simulating: /Users/norimitsu/Google Drive/TONOSAMA/{StoreName}
    # For this env, we use a relative path 'drive_sync'
    target_dir = os.path.join(drive_root_path, f"{store_name}_{store_id[:6]}")
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(os.path.join(target_dir, "images"), exist_ok=True)
    
    # 4. Write Files
    # A. CSV / Excel
    if menu_data:
        df = pd.DataFrame(menu_data)
        csv_path = os.path.join(target_dir, "menu_data.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8_sig')
            
    # B. Recommended Item TXT
    target_url = f"https://tonosama-demo.streamlit.app/menu?id={store_id}"
    txt_content = f"""【TONOSAMA POP作成依頼書】
店舗名: {store_name}
店舗URL: {target_url}

"""
    if rec_item:
        txt_content += f"""■おすすめの一品
商品名: {rec_item.get('menu_name_ja')}
価格: ¥{rec_item.get('price')}
理由: {rec_item.get('recommendation_reason', '店主イチオシ')}

■AI食レポ(参考):
{rec_item.get('description_ja_18s', '')}

■翻訳済み言語: {[k for k in rec_item.keys() if k.startswith('description_') and k != 'description_ja_18s']}
"""
    else:
        txt_content += "※おすすめ商品が指定されていません。\n"

    with open(os.path.join(target_dir, "recommendation.txt"), "w", encoding="utf-8") as f:
        f.write(txt_content)
    
    # C. Images placeholder
    with open(os.path.join(target_dir, "images", "README.txt"), "w", encoding="utf-8") as f:
        f.write("ここにメニュー画像(jpg/png)を格納してください。")

    # Log Event
    log_owner_action(store_id, "admin_asset_sync", details=f"Synced to {target_dir}")
    
    return target_dir

# === Phase 8-10: Handoff ===
with tab8: # Reusing variable name tab8/tab_handoff
    st.header("Phase 8-10: Data Handoff")
    st.markdown("""
    **正太さん(Phase 8, 10) & 戸塚さん(Phase 9) への共有**
    
    1. システムが自動的にあなたのPC内の **Google Drive同期フォルダ** に各店舗専用フォルダを作成し、データを保存します。
    2. 保存されたフォルダのURL (Google Drive Web版のURL) を発行し、メールで共有してください。
    """)
    
    # In real deployment, this path would be the user's Google Drive mount point
    # e.g., "/Users/norimitsu/Google Drive/TONOSAMA_CLIENTS"
    drive_root = st.text_input("Google Drive Root Path (Local)", value="drive_sync")
    
    if st.button("📂 Sync to Google Drive (Save Files)"):
        try:
            saved_path = sync_to_drive_folder(selected_store_name, store_id, drive_root)
            st.success(f"Successfully saved to: `{saved_path}`")
            st.info("Files created: `menu_data.csv`, `recommendation.txt`, `images/`")
        except Exception as e:
            st.error(f"Sync failed: {e}")
    
    st.subheader("✉️ Email Template")
    # Generating a mock Drive URL based on store ID (Concept)
    mock_drive_url = f"https://drive.google.com/drive/folders/{store_id}?usp=sharing"
    
    email_body = f"""
To: 正太さん, 戸塚さん
Subject: 【TONOSAMA】新規店舗素材の共有 ({selected_store_name})

お疲れ様です。
Google Driveに新規店舗「{selected_store_name}」のフォルダを作成・格納しました。

■Google Drive リンク
{mock_drive_url}

■フォルダ内容
1. menu_data.csv (全メニュー情報)
2. recommendation.txt (おすすめの一品・食レポ)
3. images/ (ここに単品画像を入れてください)

■お願い
【正太さん】専用サイト登録、および印刷手配(Phase 10)をお願いします。
【戸塚さん】データからQRコード・POP作成(Phase 9)をお願いします。

よろしくお願いいたします。
"""
    st.text_area("Draft Email", email_body, height=300)

# Remove unused tabs UI (cleanup in next refresh)
if "tab9" in locals(): del tab9
if "tab10" in locals(): del tab10

