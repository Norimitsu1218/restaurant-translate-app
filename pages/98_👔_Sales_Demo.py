import streamlit as st
import pandas as pd
from PIL import Image
import urllib.parse
from src.multimodal_utils import parse_menu_image
from src.models import MenuItem

st.set_page_config(page_title="Sales Demo", page_icon="👔", layout="wide")

# --- Session State Init ---
if "demo_step" not in st.session_state:
    st.session_state["demo_step"] = 1
if "extracted_items" not in st.session_state:
    st.session_state["extracted_items"] = []
if "selected_indices" not in st.session_state:
    st.session_state["selected_indices"] = []
if "store_info" not in st.session_state:
    st.session_state["store_info"] = {}

# --- CSS for Mario UI ---
st.markdown("""
<style>
.card-entry {
    border: 2px dashed #ccc; padding: 15px; border-radius: 10px; background: #f9f9f9; color: #555;
}
.card-standard {
    border: 2px solid #FF4B4B; padding: 15px; border-radius: 10px; background: #fff5f5;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.card-title { font-size: 1.2em; font-weight: bold; }
.card-price { font-size: 1.1em; color: #333; }
.ai-badge { 
    background: linear-gradient(45deg, #FF4B4B, #FF9051); 
    color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; 
}
</style>
""", unsafe_allow_html=True)

st.title("👔 TONOSAMA Sales Demo")

# ==========================================
# STEP 1: AUTH & CAPTURE
# ==========================================
if st.session_state["demo_step"] == 1:
    st.header("Step 1: Menu Capture")
    
    with st.sidebar:
        rep_id = st.text_input("Sales Rep ID", value="rep_001")
    
    uploaded_file = st.file_uploader("📸 Take a photo of the menu", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Menu", use_container_width=True)
        
        if st.button("🚀 Analyze Menu (Gemini Vision)"):
            with st.spinner("Analyzing menu structure..."):
                try:
                    # Helper needs API key
                    api_key = st.secrets.get("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")
                    if not api_key:
                        st.error("API Key missing.")
                        st.stop()
                    
                    # Reset stream
                    uploaded_file.seek(0)
                    img_bytes = uploaded_file.read()
                    
                    raw_items = parse_menu_image(img_bytes, api_key)
                    
                    # Convert to MenuItem objects for dot notation & consistency
                    # parse_menu_image returns dicts with: menu_name_jp, price, category, description_rich
                    items = []
                    for r in raw_items:
                        item = MenuItem(
                            menu_title=r.get("menu_name_jp", ""),
                            menu_content=r.get("description_rich", ""),
                            price=int(r.get("price", 0)) if str(r.get("price", "0")).isdigit() else 0,
                            category=r.get("category", "")
                        )
                        items.append(item)

                    if items:
                        st.session_state["extracted_items"] = items
                        st.session_state["demo_step"] = 2
                        st.rerun()
                    else:
                        st.error("No items detected. Try another photo.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# STEP 2: SELECT 3 ITEMS
# ==========================================
elif st.session_state["demo_step"] == 2:
    st.header("Step 2: Pick 3 Items for Demo")
    st.caption("店主と一緒に、最も自信のある3品を選んでください。")
    
    items = st.session_state["extracted_items"]
    
    # Checkbox list
    cols = st.columns(3)
    selected = []
    
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            # item is MenuItem object now
            is_checked = st.checkbox(f"{item.menu_title} (¥{item.price})", key=f"sel_{idx}")
            if is_checked:
                selected.append(idx)
    
    if len(selected) > 3:
        st.warning("⚠️ 3つまで選んでください。")
    
    if st.button("✨ Generate Mario Demo UI"):
        if 1 <= len(selected) <= 3:
            st.session_state["selected_indices"] = selected
            st.session_state["demo_step"] = 3
            st.rerun()
        else:
            st.error("1〜3品選んでください。")

# ==========================================
# STEP 3: MARIO DEMO UI (VALUE GAP)
# ==========================================
elif st.session_state["demo_step"] == 3:
    st.header("Step 3: The Experience")
    
    # Toggle Plan
    plan_mode = st.radio("Select Plan Mode", ["Entry Plan (39k)", "Standard Plan (69k)"], horizontal=True)
    is_standard = "Standard" in plan_mode
    
    st.divider()
    
    # Display Cards
    items = st.session_state["extracted_items"]
    indices = st.session_state["selected_indices"]
    
    cols = st.columns(len(indices))
    
    for i, idx in enumerate(indices):
        item = items[idx]
        with cols[i]:
            if is_standard:
                # Standard Plan Design (Rich)
                st.markdown(f"""
                <div class="card-standard">
                    <span class="ai-badge">✨ AI Transcreation</span>
                    <div class="card-title">{item.menu_title}</div>
                    <div class="card-price">¥{item.price}</div>
                    <hr>
                    <div style="font-size:0.9em;">
                        <b>[AI Food Report]</b><br>
                        {item.menu_content or "（AIが食感を生成します...）"}<br><br>
                        <b>[Pairing]</b><br>
                        🍺 Recommended with Asahi Super Dry
                    </div>
                    <hr>
                    <div style="color:blue; font-size:0.8em;">
                        🇬🇧 English: Succulent Wagyu Beef...<br>
                        🇰🇷 Korean: 입안에서 녹는 와규...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Mock AI Generation if empty
                if not item.menu_content:
                    if st.button(f"Generate Text for #{i+1}"):
                        item.menu_content = "口に入れた瞬間、肉汁が溢れ出す極上の食感。職人が一枚一枚丁寧に焼き上げました。"
                        st.rerun()
            
            else:
                # Entry Plan Design (Plain)
                st.markdown(f"""
                <div class="card-entry">
                    <div class="card-title">{item.menu_title}</div>
                    <div class="card-price">¥{item.price}</div>
                    <hr>
                    <div style="color:#aaa; font-style:italic;">
                        Information not available in Entry Plan.
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    st.info("💡 69,000円プランなら、AIが「食べたことのないお客様」にも魅力を伝える文章を自動生成します。")
    
    if st.button("🤝 Proceed to Intake (契約へ進む)"):
        st.session_state["demo_step"] = 4
        st.rerun()

# ==========================================
# STEP 4: INTAKE FORM
# ==========================================
elif st.session_state["demo_step"] == 4:
    st.header("Step 4: Intake Form")
    
    with st.form("intake_form"):
        st.subheader("1. 店舗・契約情報")
        c1, c2 = st.columns(2)
        store_name = c1.text_input("店舗名", value="居酒屋 デモ")
        corp_name = c2.text_input("運営会社名")
        rep_name = c1.text_input("代表者/契約責任者名")
        phone = c2.text_input("電話番号")
        email = c1.text_input("オーナー用メールアドレス")
        url = c2.text_input("店舗URL")
        
        st.subheader("2. 詳細設定 (Preferences)")
        tone = st.radio("AIの口調 (Tone)", ["東京カレンダー風 (Urban)", "友人口調 (Friendly)", "職人口調 (Artisan)"], horizontal=True)
        allergy = st.radio("アレルギー表記", ["希望する", "希望しない"], horizontal=True)
        wheelchair = st.radio("車椅子対応", ["可能", "補助が必要", "不可"], horizontal=True)
        
        st.subheader("3. プラン選択")
        final_plan = st.radio("決定プラン", ["Entry (39,800)", "Standard (69,800)", "Premium (99,800)"], index=1)
        
        submitted = st.form_submit_button("📩 招待メールを送信 (Generate Invite)")
    
    if submitted:
        if not (store_name and email):
            st.error("店舗名とメールアドレスは必須です。")
        else:
            # Generate Invite Link
            params = {
                "store_name": store_name,
                "corp_name": corp_name,
                "rep_name": rep_name,
                "email": email,
                "plan": final_plan.split(" ")[0].lower(),
                "tone": tone,
                "allergy": allergy,
                "ref": "demo_v1"
            }
            query_str = urllib.parse.urlencode(params)
            base_url = "http://localhost:8501" # Or deployed URL
            link = f"{base_url}/Store_Register?{query_str}"
            
            st.success("✅ 招待リンクが生成されました！")
            st.code(link, language="text")
            st.markdown(f"**To: {email}**")
            st.info("実際にはこのリンクがメールで送信されます。今は上記をコピーして開いてください。")
