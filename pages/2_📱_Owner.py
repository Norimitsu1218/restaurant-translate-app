import streamlit as st
import streamlit.components.v1 as components
import json
import os

st.set_page_config(
    page_title="Menu Check", 
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. Auth & Data Fetching (Python Side) ---
if "supabase" not in st.session_state:
    st.error("Please login from the main page.")
    st.stop()

supabase = st.session_state["supabase"]
store_name = st.session_state.get("store_name", "")

# Store Selector (Hidden in sidebar if already selected, but available if needed)
st.sidebar.title("Store Selector")
try:
    stores_res = supabase.table("stores").select("id, store_name").execute()
    stores_dict = {s["store_name"]: s["id"] for s in stores_res.data}
except:
    stores_dict = {}

if not store_name:
    store_name = st.sidebar.selectbox("Select Store", [""] + list(stores_dict.keys()))
    if store_name:
        st.session_state["store_name"] = store_name
        st.rerun()

if not store_name:
    st.warning("👈 Please select a store from the sidebar to start.")
    st.stop()

store_id = stores_dict.get(store_name)

# Fetch Menu Items
menu_res = supabase.table("menu_master").select("*").eq("store_id", store_id).order("created_at").execute()
raw_items = menu_res.data

# Transform to JS format
js_items = []
for item in raw_items:
    js_items.append({
        "id": item["id"],
        "name": item.get("menu_name_ja") or item.get("detected_name") or "No Name",
        "price": f"{item.get('price', 0)}円", # Format for display
        "price_val": item.get("price", 0), # Keep raw for logical update if needed
        "description": item.get("description_ja_18s", "（AIによる説明文生成待ち...）"),
        "image": item.get("image_url", None) # Base64 or URL
    })

json_items = json.dumps(js_items, ensure_ascii=False)

# Get Supabase Config for JS Client
# Try to get from st.secrets, otherwise Env var
try:
    SB_URL = st.secrets["SUPABASE_URL"]
    SB_KEY = st.secrets["SUPABASE_KEY"]
except:
    try:
        SB_URL = os.environ.get("SUPABASE_URL", "")
        SB_KEY = os.environ.get("SUPABASE_KEY", "")
    except:
        st.error("Supabase Keys not found.")
        st.stop()

# --- 2. Custom HTML/JS Embedding ---
# User's HTML modified to accept Python variables and Save to Supabase
custom_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>メニュー内容確認 - TONOSAMA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <style>
        /* (USER'S CSS COPIED AS IS) */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans JP', sans-serif;
            background: linear-gradient(180deg, #5C94FC 0%, #87CEEB 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }}
        .cloud {{
            position: fixed;
            background: white;
            border-radius: 100px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            z-index: 0;
            opacity: 0.9;
        }}
        .cloud::before, .cloud::after {{ content: ''; position: absolute; background: white; border-radius: 100px; }}
        .cloud-1 {{ width: 100px; height: 40px; top: 10%; left: 10%; animation: float 20s ease-in-out infinite; }}
        .cloud-1::before {{ width: 50px; height: 40px; top: -20px; left: 10px; }}
        .cloud-1::after {{ width: 60px; height: 35px; top: -15px; right: 10px; }}
        .cloud-2 {{ width: 80px; height: 35px; top: 20%; right: 15%; animation: float 25s ease-in-out infinite 5s; }}
        .cloud-2::before {{ width: 40px; height: 35px; top: -15px; left: 10px; }}
        .cloud-2::after {{ width: 50px; height: 30px; top: -12px; right: 10px; }}
        .cloud-3 {{ width: 120px; height: 45px; bottom: 15%; left: 5%; animation: float 30s ease-in-out infinite 10s; }}
        .cloud-3::before {{ width: 60px; height: 45px; top: -22px; left: 15px; }}
        .cloud-3::after {{ width: 70px; height: 40px; top: -18px; right: 15px; }}
        @keyframes float {{ 0%, 100% {{ transform: translateX(0) translateY(0); }} 50% {{ transform: translateX(30px) translateY(-20px); }} }}
        .container {{ max-width: 500px; width: 100%; position: relative; z-index: 1; }}
        .header {{ text-align: center; color: white; margin-bottom: 20px; text-shadow: 3px 3px 0px rgba(0, 0, 0, 0.3); }}
        .header h1 {{ font-family: 'Press Start 2P', cursive; font-size: 20px; margin-bottom: 10px; line-height: 1.6; letter-spacing: 2px; }}
        .progress {{ background: white; border: 4px solid #F4D03F; border-radius: 15px; padding: 15px; margin-bottom: 20px; text-align: center; font-size: 18px; font-weight: bold; color: #1C1C1C; box-shadow: 0 4px 0 #D4AC0D, 0 8px 15px rgba(0, 0, 0, 0.2); position: relative; }}
        .progress::before {{ content: '⭐'; position: absolute; left: 15px; font-size: 24px; animation: spin 3s linear infinite; }}
        .progress::after {{ content: '⭐'; position: absolute; right: 15px; font-size: 24px; animation: spin 3s linear infinite reverse; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        .encouragement {{ background: linear-gradient(to bottom, #D89048 0%, #D89048 48%, #A85038 48%, #A85038 100%); border: 3px solid #784800; border-radius: 8px; padding: 18px; margin-bottom: 15px; text-align: center; font-size: 15px; color: white; font-weight: bold; animation: fadeInBounce 0.5s ease; box-shadow: 0 4px 0 #784800, 0 8px 15px rgba(0, 0, 0, 0.2); text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.3); }}
        @keyframes fadeInBounce {{ 0% {{ opacity: 0; transform: translateY(-20px) scale(0.9); }} 60% {{ transform: translateY(5px) scale(1.05); }} 100% {{ opacity: 1; transform: translateY(0) scale(1); }} }}
        .instruction {{ background: linear-gradient(to bottom, #FCB838 0%, #FCB838 48%, #F09048 48%, #F09048 100%); border: 3px solid #D87800; border-radius: 8px; padding: 20px; margin-bottom: 20px; line-height: 1.8; color: white; box-shadow: 0 4px 0 #D87800, 0 8px 15px rgba(0, 0, 0, 0.2); text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.2); }}
        .instruction strong {{ color: white; font-size: 18px; text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.3); }}
        .instruction p {{ margin: 10px 0; }}
        .card-container {{ position: relative; width: 100%; min-height: auto; perspective: 1000px; margin-bottom: 20px; }}
        .card {{ width: 100%; background: white; border: 5px solid #48D850; border-radius: 20px; padding: 30px; box-shadow: 0 0 0 3px #00A800, 0 10px 30px rgba(0, 0, 0, 0.3); transition: transform 0.3s ease, opacity 0.3s ease; position: relative; }}
        .card::before {{ content: ''; position: absolute; top: -3px; left: -3px; right: -3px; bottom: -3px; background: linear-gradient(to right, #48D850 50%, #00A800 50%); border-radius: 20px; z-index: -1; }}
        .dish-name {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; color: #1C1C1C; }}
        .dish-price {{ font-size: 20px; color: #F09048; margin-bottom: 20px; font-weight: bold; }}
        .dish-price::before {{ content: '🪙 '; }}
        .image-upload-section {{ margin-bottom: 20px; }}
        .image-upload-label {{ font-size: 14px; color: #666; margin-bottom: 10px; display: block; }}
        .image-upload-buttons {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 15px; }}
        .image-upload-buttons.hidden {{ display: none; }}
        .upload-button {{ padding: 15px 10px; border: 3px solid #D4AC0D; border-radius: 8px; background: linear-gradient(to bottom, #FCB838 0%, #FCB838 48%, #F09048 48%, #F09048 100%); cursor: pointer; text-align: center; transition: all 0.2s; font-size: 14px; font-weight: bold; color: white; display: flex; flex-direction: column; align-items: center; gap: 8px; min-height: 90px; justify-content: center; box-shadow: 0 3px 0 #D87800, 0 6px 10px rgba(0, 0, 0, 0.2); text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.2); }}
        .upload-button:active {{ transform: translateY(3px); box-shadow: 0 0 0 #D87800, 0 3px 5px rgba(0, 0, 0, 0.2); }}
        .upload-button .icon {{ font-size: 28px; filter: drop-shadow(1px 1px 0px rgba(0, 0, 0, 0.2)); }}
        .upload-button .label {{ font-size: 12px; line-height: 1.3; }}
        .image-preview-container {{ display: none; position: relative; border-radius: 15px; overflow: hidden; margin-top: 10px; border: 4px solid #48D850; box-shadow: 0 0 0 2px #00A800; }}
        .image-preview-container.has-image {{ display: block; }}
        .image-preview {{ width: 100%; max-height: 250px; object-fit: cover; border-radius: 10px; cursor: pointer; }}
        .image-actions {{ position: absolute; bottom: 10px; right: 10px; display: flex; gap: 10px; }}
        .image-action-btn {{ background: rgba(0, 0, 0, 0.8); color: white; border: 2px solid white; border-radius: 8px; padding: 8px 12px; font-size: 14px; font-weight: bold; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); }}
        .image-action-btn:active {{ transform: scale(0.95); }}
        .dish-description {{ font-size: 16px; line-height: 1.8; color: #333; padding: 15px; background: #f9f9f9; border: 2px solid #ddd; border-radius: 10px; margin-bottom: 15px; cursor: pointer; transition: all 0.3s; min-height: 100px; }}
        .dish-description:active {{ background: #f0f0f0; border-color: #F09048; }}
        .edit-hint {{ font-size: 14px; color: #999; text-align: center; margin-top: 5px; }}
        .edit-area {{ display: none; margin-top: 15px; }}
        .edit-area.active {{ display: block; }}
        .edit-area textarea {{ width: 100%; padding: 15px; border: 3px solid #48D850; border-radius: 10px; font-size: 16px; line-height: 1.8; resize: vertical; min-height: 150px; font-family: inherit; box-shadow: 0 0 0 2px #00A800; }}
        .edit-area textarea:focus {{ outline: none; border-color: #00A800; }}
        .edit-buttons {{ display: flex; gap: 10px; margin-top: 10px; }}
        .edit-button {{ flex: 1; padding: 15px; border: 3px solid; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: all 0.2s; box-shadow: 0 4px 0; }}
        .edit-button:active {{ transform: translateY(4px); box-shadow: 0 0 0; }}
        .cancel-button {{ background: #E0E0E0; border-color: #999; color: #666; box-shadow: 0 4px 0 #999; }}
        .save-button {{ background: linear-gradient(to bottom, #FCB838 0%, #F09048 100%); border-color: #D87800; color: white; box-shadow: 0 4px 0 #D87800; text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.2); }}
        .buttons {{ display: flex; justify-content: center; gap: 20px; margin-top: 30px; flex-wrap: wrap; position: relative; }}
        .button {{ width: 100px; height: 100px; border-radius: 50%; border: 5px solid; font-size: 18px; font-weight: bold; cursor: pointer; transition: all 0.2s; box-shadow: 0 6px 0, 0 10px 20px rgba(0, 0, 0, 0.3); display: flex; align-items: center; justify-content: center; position: relative; text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.2); }}
        .button::before {{ content: ''; position: absolute; top: 15%; left: 20%; width: 25px; height: 15px; background: rgba(255, 255, 255, 0.4); border-radius: 50%; filter: blur(3px); }}
        .button:active {{ transform: translateY(6px); box-shadow: 0 0 0, 0 4px 10px rgba(0, 0, 0, 0.3); }}
        .button-back {{ background: radial-gradient(circle at 35% 35%, #ff4444, #cc0000); border-color: #990000; color: white; box-shadow: 0 6px 0 #990000, 0 10px 20px rgba(0, 0, 0, 0.3); }}
        .button-reject {{ background: radial-gradient(circle at 35% 35%, #ffff44, #ffdd00); border-color: #ccaa00; color: #000000; box-shadow: 0 6px 0 #ccaa00, 0 10px 20px rgba(0, 0, 0, 0.3); }}
        .button-approve {{ background: radial-gradient(circle at 35% 35%, #4444ff, #0000cc); border-color: #000099; color: white; box-shadow: 0 6px 0 #000099, 0 10px 20px rgba(0, 0, 0, 0.3); }}
        .complete-screen {{ display: none; text-align: center; background: white; padding: 60px 40px; border-radius: 25px; border: 5px solid #48D850; box-shadow: 0 0 0 3px #00A800, 0 10px 40px rgba(0, 0, 0, 0.3); }}
        .complete-screen h2 {{ font-family: 'Press Start 2P', cursive; font-size: 24px; margin-bottom: 30px; color: #1C1C1C; line-height: 1.8; }}
        .complete-screen p {{ font-size: 18px; margin-bottom: 30px; line-height: 1.8; }}
        .complete-button {{ padding: 20px 50px; font-size: 20px; background: linear-gradient(to bottom, #48D850 0%, #00A800 100%); color: white; border: 4px solid #006400; border-radius: 15px; cursor: pointer; font-weight: bold; transition: all 0.2s; box-shadow: 0 6px 0 #006400, 0 10px 20px rgba(0, 0, 0, 0.3); text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.2); }}
        .complete-button:active {{ transform: translateY(6px); box-shadow: 0 0 0 #006400, 0 4px 10px rgba(0, 0, 0, 0.3); }}
        .toast {{ position: fixed; top: 20px; left: 50%; transform: translateX(-50%) translateY(-100px); background: linear-gradient(to bottom, #FCB838 0%, #F09048 100%); color: white; padding: 15px 30px; border: 3px solid #D87800; border-radius: 15px; font-size: 16px; font-weight: bold; z-index: 1000; opacity: 0; transition: all 0.3s ease; box-shadow: 0 4px 0 #D87800, 0 8px 15px rgba(0, 0, 0, 0.3); text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.2); }}
        .toast.show {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.9); z-index: 1000; align-items: center; justify-content: center; cursor: pointer; }}
        .modal img {{ max-width: 90%; max-height: 90%; object-fit: contain; border: 4px solid white; border-radius: 10px; }}
        .close-modal {{ position: absolute; top: 20px; right: 30px; color: white; font-size: 50px; cursor: pointer; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.7); border: 3px solid white; border-radius: 50%; }}
        .loading-spinner {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: 2000; align-items: center; justify-content: center; }}
        .loading-spinner.active {{ display: flex; }}
        .spinner {{ border: 6px solid #FCB838; border-top: 6px solid #F09048; border-radius: 10px; width: 60px; height: 60px; animation: spin-block 1s linear infinite; }}
        @keyframes spin-block {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        @media (max-width: 480px) {{
            .header h1 {{ font-size: 16px; }}
            .buttons {{ gap: 15px; }}
            .button {{ width: 90px; height: 90px; font-size: 16px; }}
            .cloud {{ opacity: 0.6; }}
        }}
    </style>
</head>
<body>
    <div class="cloud cloud-1"></div>
    <div class="cloud cloud-2"></div>
    <div class="cloud cloud-3"></div>

    <div class="container">
        <div class="header">
            <h1>🍱 MENU CHECK ({store_name})<br>メニュー確認</h1>
        </div>

        <div class="progress" id="progress">1 / 3 品目</div>

        <div class="encouragement" id="encouragement">
            それでは1品目から始めましょう！
        </div>

        <div class="instruction">
            <strong>⚠️ 重要</strong>
            <p>ここで確認いただく内容が、<strong>最終的にお客様に表示される文章</strong>になります。</p>
            <p>
                <span style="color: white;">🔴 戻る</span>
                <span style="background: rgba(255,255,255,0.3); padding: 2px 8px; border-radius: 5px;">🟡 訂正</span>
                <span style="color: white;">🔵 OK</span>
            </p>
        </div>

        <div class="card-container" id="cardContainer">
             <!-- Card injected by JS -->
        </div>

        <div class="buttons" id="actionButtons">
            <button class="button button-back" onclick="goBack()">← 戻る</button>
            <button class="button button-reject" onclick="reject()">訂正</button>
            <button class="button button-approve" onclick="approve()">OK</button>
        </div>

        <div class="complete-screen" id="completeScreen">
            <h2>🎉 COMPLETE!<br>確認完了！</h2>
            <p>全ての品目を確認いただきました。<br>ご協力ありがとうございます。</p>
            <button class="complete-button" onclick="submit()">🏁 確定して送信</button>
        </div>
    </div>

    <div class="toast" id="toast"></div>
    <div class="loading-spinner" id="loadingSpinner"><div class="spinner"></div></div>
    <div class="modal" id="imageModal" onclick="closeModal()">
        <span class="close-modal">&times;</span>
        <img id="modalImage" src="" alt="">
    </div>

    <input type="file" id="cameraInput" accept="image/*" capture="environment" style="display: none;">
    <input type="file" id="photoInput" accept="image/*" style="display: none;">
    <input type="file" id="folderInput" accept="image/*" style="display: none;">

    <script>
        // --- Injected Data ---
        const menuItems = {json_items}; // Python List injected here
        const SB_URL = "{SB_URL}";
        const SB_KEY = "{SB_KEY}";
        
        let currentIndex = 0;
        let decisions = [];
        let isEditing = false;
        let isProcessing = false;
        let supabase = null;

        const encouragementMessages = {{
            start: 'それでは1品目から始めましょう！',
            quarter: 'いい調子です！あと少しです 💪',
            half: 'ちょうど半分まできました！⭐',
            threeQuarter: 'もうすぐ終わります！あと少し 🚀',
            almostDone: 'あと1品です！頑張りましょう 🏁',
        }};

        function init() {{
            if (SB_URL && SB_KEY) {{
                supabase = window.supabase.createClient(SB_URL, SB_KEY);
            }}
            
            // Initialize decisions from fetched items
            decisions = menuItems.map(item => ({{ ...item, approved: false, modified: false }}));
            
            document.getElementById('cameraInput').addEventListener('change', e => handleImageUpload(e, 'camera'));
            document.getElementById('photoInput').addEventListener('change', e => handleImageUpload(e, 'photo'));
            document.getElementById('folderInput').addEventListener('change', e => handleImageUpload(e, 'folder'));
            
            if (menuItems.length === 0) {{
                 document.getElementById('cardContainer').innerHTML = "<div class='card'>メニューがまだありません。Store RegisterまたはMenu Makerで登録してください。</div>";
                 document.getElementById('actionButtons').style.display = 'none';
            }} else {{
                showCard();
            }}
        }}

        function showCard() {{
            if (currentIndex >= menuItems.length) {{
                showComplete();
                return;
            }}

            const item = menuItems[currentIndex];
            const hasImage = !!item.image;
            
            document.getElementById('cardContainer').innerHTML = `
                <div class="card">
                    <div class="dish-name">${{item.name}}</div>
                    <div class="dish-price">${{item.price}}</div>
                    
                    <div class="image-upload-section">
                        <div class="image-upload-label">料理の写真（任意）</div>
                        
                        <div class="image-upload-buttons ${{hasImage ? 'hidden' : ''}}">
                            <div class="upload-button" onclick="triggerCamera()">
                                <span class="icon">📸</span>
                                <span class="label">撮影</span>
                            </div>
                            <div class="upload-button" onclick="triggerPhoto()">
                                <span class="icon">📷</span>
                                <span class="label">写真から<br>選択</span>
                            </div>
                            <div class="upload-button" onclick="triggerFolder()">
                                <span class="icon">📁</span>
                                <span class="label">フォルダから<br>選択</span>
                            </div>
                        </div>
                        
                        <div class="image-preview-container ${{hasImage ? 'has-image' : ''}}">
                            <img src="${{item.image || ''}}" class="image-preview" onclick="openModal('${{item.image || ''}}')" alt="${{item.name}}">
                            <div class="image-actions">
                                <button class="image-action-btn" onclick="event.stopPropagation(); triggerFolder()">📷 変更</button>
                                <button class="image-action-btn" onclick="event.stopPropagation(); removeImage()">🗑️ 削除</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dish-description" onclick="enableEdit()">${{item.description}}</div>
                    <div class="edit-hint">タップして編集</div>
                    
                    <div class="edit-area">
                        <textarea id="editText">${{item.description}}</textarea>
                        <div class="edit-buttons">
                            <button class="edit-button cancel-button" onclick="cancelEdit()">キャンセル</button>
                            <button class="edit-button save-button" onclick="saveEdit()">保存</button>
                        </div>
                    </div>
                </div>
            `;

            isEditing = false;
            updateProgress();
            updateEncouragement();
            document.querySelector('.button-back').style.display = currentIndex === 0 ? 'none' : 'flex';
        }}

        function updateProgress() {{
            document.getElementById('progress').textContent = `${{currentIndex + 1}} / ${{menuItems.length}} 品目`;
        }}

        function updateEncouragement() {{
            const progress = (currentIndex + 1) / menuItems.length;
            let message = currentIndex === 0 ? encouragementMessages.start :
                         progress >= 0.9 ? encouragementMessages.almostDone :
                         progress >= 0.75 ? encouragementMessages.threeQuarter :
                         progress >= 0.5 ? encouragementMessages.half :
                         progress >= 0.25 ? encouragementMessages.quarter : '';
            
            if (message) {{
                const el = document.getElementById('encouragement');
                el.textContent = message;
                el.style.animation = 'none';
                setTimeout(() => el.style.animation = 'fadeInBounce 0.5s ease', 10);
            }}
        }}

        function showToast(msg) {{
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }}

        function triggerCamera() {{ document.getElementById('cameraInput').click(); }}
        function triggerPhoto() {{ document.getElementById('photoInput').click(); }}
        function triggerFolder() {{ document.getElementById('folderInput').click(); }}

        function handleImageUpload(e, source) {{
            // ... (Same image logic)
            const file = e.target.files[0];
            if (!file || isProcessing) return;
            
            isProcessing = true;
            showLoading();
            const reader = new FileReader();
            reader.onload = ev => {{
                menuItems[currentIndex].image = ev.target.result; // Base64
                // Update decision tracker
                decisions[currentIndex].image = ev.target.result;
                decisions[currentIndex].modified = true;
                
                hideLoading();
                isProcessing = false;
                showToast({{ camera: '📸 素敵な写真ですね！', photo: '📷 写真を選択しました！', folder: '📁 ファイルをアップロードしました！' }}[source]);
                showCard();
            }};
            reader.onerror = () => {{ hideLoading(); isProcessing = false; showToast('❌ 読み込み失敗'); }};
            reader.readAsDataURL(file);
            e.target.value = '';
        }}

        function removeImage() {{
            if (confirm('この写真を削除しますか？')) {{
                menuItems[currentIndex].image = null;
                decisions[currentIndex].image = null;
                decisions[currentIndex].modified = true;
                showToast('🗑️ 写真を削除しました');
                showCard();
            }}
        }}

        function openModal(src) {{
            if (!src) return;
            document.getElementById('imageModal').style.display = 'flex';
            document.getElementById('modalImage').src = src;
        }}

        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}

        function enableEdit() {{
            if (isEditing) return;
            isEditing = true;
            document.querySelector('.dish-description').style.display = 'none';
            document.querySelector('.edit-hint').style.display = 'none';
            document.querySelector('.edit-area').classList.add('active');
            setTimeout(() => document.getElementById('editText').focus(), 100);
            showToast('✏️ お気軽に修正してください');
        }}

        function cancelEdit() {{
            isEditing = false;
            document.querySelector('.dish-description').style.display = 'block';
            document.querySelector('.edit-hint').style.display = 'block';
            document.querySelector('.edit-area').classList.remove('active');
            document.getElementById('editText').value = menuItems[currentIndex].description;
        }}

        function saveEdit() {{
            const text = document.getElementById('editText').value.trim();
            if (!text) {{ alert('説明文を入力してください'); return; }}
            
            menuItems[currentIndex].description = text;
            decisions[currentIndex].description = text;
            decisions[currentIndex].modified = true;
            isEditing = false;
            
            document.querySelector('.dish-description').textContent = text;
            document.querySelector('.dish-description').style.display = 'block';
            document.querySelector('.edit-hint').style.display = 'block';
            document.querySelector('.edit-area').classList.remove('active');
            showToast('💾 保存しました！');
        }}

        function goBack() {{
            if (currentIndex > 0) {{
                if (isEditing && !confirm('編集中の内容は破棄されますがよろしいですか？')) return;
                currentIndex--;
                showCard();
                showToast('⏪ 前の品目に戻りました');
            }}
        }}

        function reject() {{ enableEdit(); }}

        function approve() {{
            if (isEditing) {{ alert('編集を保存してからOKボタンを押してください'); return; }}
            decisions[currentIndex].approved = true;
            showToast('✅ ありがとうございます！');
            currentIndex++;
            const card = document.querySelector('.card');
            card.style.transform = 'translateX(150%) rotate(20deg)';
            card.style.opacity = '0';
            setTimeout(() => showCard(), 300);
        }}

        function showComplete() {{
            document.querySelector('.card-container').style.display = 'none';
            document.querySelector('.buttons').style.display = 'none';
            document.querySelector('.instruction').style.display = 'none';
            document.querySelector('.progress').style.display = 'none';
            document.querySelector('.encouragement').style.display = 'none';
            document.getElementById('completeScreen').style.display = 'block';
            showToast('🎉 お疲れさまでした！');
        }}

        async function submit() {{
            showLoading();
            
            if (!supabase) {{
                alert("データベース接続情報が見つかりません。");
                hideLoading();
                return;
            }}
            
            // Upsert all decisions to Supabase
            // We loop and upsert (inefficient but safe for small batches)
            let successCount = 0;
            // Filter only approved or modified items, or just upsert all to confirm status?
            // Upsert only items that we processed
            const itemsToSave = decisions; 
            
            for (const item of itemsToSave) {{
                const updateData = {{
                   description_ja_18s: item.description,
                   description_ja_status: 'confirmed',
                   image_url: item.image // Saving Base64 directly
                }};
                
                const {{ error }} = await supabase
                    .from('menu_master')
                    .update(updateData)
                    .eq('id', item.id);
                    
                if (error) {{
                    console.error("Save error", error);
                }} else {{
                    successCount++;
                }}
            }}
            
            setTimeout(() => {{
                hideLoading();
                alert(`保存完了！ (${{successCount}}/${{itemsToSave.length}})\n\nご協力ありがとうございました。`);
                // Reload page or done
                location.reload(); 
            }}, 1000);
        }}

        function showLoading() {{ document.getElementById('loadingSpinner').classList.add('active'); }}
        function hideLoading() {{ document.getElementById('loadingSpinner').classList.remove('active'); }}

        init();
    </script>
</body>
</html>
"""

# Render full screen
components.html(custom_html, height=800, scrolling=True)

# --- 3. Completion Check & Navigation ---
# Check if all items are confirmed to show the "Next Step" button
confirmed_count = supabase.table("menu_master").select("*", count="exact").eq("store_id", store_id).eq("description_ja_status", "confirmed").execute().count
total_count = len(raw_items)

if total_count > 0 and confirmed_count == total_count:
    st.balloons()
    st.success("✅ 全てのメニューの確認が完了しました！")
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <h3>お疲れ様でした！</h3>
        <p>素晴らしいメニューデータが出来上がりました。<br>最後に、このデータを活用するためのプランを選択してください。</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("💎 プラン選択へ進む (Proceed to Selection)", type="primary", use_container_width=True):
        st.switch_page("pages/3_💎_Plan_Selection.py")
