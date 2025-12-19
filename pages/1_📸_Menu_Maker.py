import streamlit as st
import pandas as pd
from PIL import Image
import os
import json
import io
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

st.title("📸 Menu Maker (Beta)")
st.markdown("""
**「メニューの写真」から、翻訳用のCSVを一発作成します。**
Gemini 2.5 Flash が画像を解析し、メニュー名・価格だけでなく、
**「食欲をそそる食レポ」「ペアリング」「食べ方」** まで自動で創作します。
""")

# APIキーの確認
try:
    # 1. st.secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        # 2. st.session_state (main.pyで入力済みの場合)
        if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"]:
            api_key = st.session_state["gemini_api_key"]
        else:
            # 3. DB (app_data) はここでは簡易化のためスキップ（必要なら追加）
            api_key = None
except Exception:
    api_key = None

if not api_key:
    st.warning("⚠️ APIキーが見つかりません。メインページでログインまたは設定を行ってください。")
    st.stop()

# --- モデル設定 ---
# 画像解析には Gemini 2.5 Flash を使用
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def get_vision_model(api_key):
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=0.7, # 創作性を出すため少し上げる
    )

# --- Pydantic Schema for Structured Output ---
# 48列のうち、AIが埋めるべき情報を定義
class MenuItemExtracted(BaseModel):
    menu_name_jp: str = Field(description="日本語のメニュー名")
    price: str = Field(description="価格（数字のみ、または 'Ask'）")
    category: str = Field(description="推測されるカテゴリ（例：前菜、メイン、ドリンク）")
    description_rich: str = Field(description="【重要】18秒で読める魅力的な食レポ＋おすすめの食べ方＋ペアリングの提案を含んだ日本語の説明文")
    # アレルゲン (True/False)
    wheat: bool = Field(default=False, description="小麦")
    crustacean: bool = Field(default=False, description="甲殻類")
    egg: bool = Field(default=False, description="卵")
    fish: bool = Field(default=False, description="魚")
    soy: bool = Field(default=False, description="大豆")
    peanut: bool = Field(default=False, description="ピーナッツ")
    milk: bool = Field(default=False, description="牛乳")
    walnut: bool = Field(default=False, description="くるみ")
    celery: bool = Field(default=False, description="セロリ")
    mustard: bool = Field(default=False, description="マスタード")
    sesame: bool = Field(default=False, description="ゴマ")
    sulfite: bool = Field(default=False, description="亜硫酸塩")
    lupinus: bool = Field(default=False, description="ルピナス")
    mollusc: bool = Field(default=False, description="貝")

class MenuExtractionResult(BaseModel):
    items: List[MenuItemExtracted]

# --- メイン処理 ---
st.sidebar.header("🔧 設定 (Settings)")

# 1. ペルソナ選択
persona_options = {
    "東京カレンダー風 (艶やか)": "文体は『東京カレンダー』のような、少し艶っぽく洗練されたトーンで。情景が浮かぶような情緒的な表現を使ってください。",
    "居酒屋の大将風 (元気)": "文体は『元気のいい居酒屋の大将』のように、親しみやすく活気のあるトーンで。「〜だぜ」「〜だよな」など、威勢のいい言葉遣いを使ってください。",
    "高級料亭風 (厳格)": "文体は『老舗料亭の女将』のように、丁寧かつ格式高いトーンで。「〜でございます」「〜いたします」など、上品な言葉遣いを使ってください。",
    "標準 (丁寧)": "文体は一般的なレストランメニューのように、丁寧でわかりやすいトーンで書いてください。"
}
selected_persona = st.sidebar.radio("🎭 食レポの文体 (Persona)", list(persona_options.keys()))
persona_instruction = persona_options[selected_persona]
# 2. 店舗設定 (Store Settings)
# store_name がないとDB登録できないため必須化
store_name_input = st.sidebar.text_input("🏠 店舗名 (Store Name)", value="Test Store", help="この名前でデータベースに登録されます")

# 3. 店舗URL (コンテクスト)
store_url = st.sidebar.text_input("🔗 店舗のURL (コンテクスト解析用)", placeholder="https://tabelog.com/...")
store_context = ""
supabase = st.session_state.get("supabase")

if not supabase:
    st.error("Supabase client is not initialized. Please login via main page.")
    st.stop()

def register_store_if_needed(name: str, url: str) -> str:
    """店舗名を検索し、なければ新規登録してIDを返す"""
    try:
        # 検索
        res = supabase.table("stores").select("id").eq("store_name", name).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["id"]
        
        # 新規登録
        new_store = {"store_name": name, "store_url": url, "plan_code": "standard"}
        res = supabase.table("stores").insert(new_store).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["id"]
        return None
    except Exception as e:
        st.error(f"Store registration failed: {e}")
        return None

def save_menu_to_db(store_id: str, items: List[dict], persona: str):
    """メニューデータをmenu_masterに保存"""
    db_rows = []
    for item in items:
        # Pydanticモデルから辞書へ変換済み前提
        # priceのクリーニング (数字のみ抽出)
        raw_price = str(item.get("price", "0"))
        import re
        price_match = re.search(r'\d+', raw_price)
        price_val = int(price_match.group()) if price_match else 0
        
        row = {
            "store_id": store_id,
            "category": item.get("category"),
            "detected_name": item.get("menu_name_jp", ""),
            "price": price_val,
            "menu_name_ja": item.get("menu_name_jp", ""), # 初期値は検出名と同じ
            "description_ja_18s": item.get("description_rich", ""),
            "description_ja_status": "generated",
            "persona": persona,
            "allergen_data": item.get("allergens", {}), # JSONB
            # 他言語はNULLでOK
        }
        db_rows.append(row)
    
    if db_rows:
        supabase.table("menu_master").insert(db_rows).execute()

# コストログ用 (langchain_utilsからimportしたいが、pagesフォルダなのでsys.path考慮が必要)
# 簡易的にここで定義、または src から import するが、一旦簡易実装
from src.langchain_utils import log_api_usage

if store_url:
    try:
        # 簡易スクレイピング
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(store_url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else ""
            # meta description
            meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            desc = meta.get('content') if meta else ""
            store_context = f"【店舗情報】\n店名/タイトル: {title}\n店舗概要: {desc}\nURL: {store_url}\n(この店舗の雰囲気やコンセプトに合わせて食レポを作成してください)"
            st.sidebar.success("✅ 店舗情報を取得しました")
        else:
            st.sidebar.warning(f"URL読み込み失敗: Status {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"URL読み込みエラー: {e}")

uploaded_file = st.file_uploader("メニューの写真をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Menu", use_container_width=True)

    if st.button("🚀 AI解析開始 (Gemini 2.5)"):
        with st.spinner("AIが画像を解析し、食レポを執筆中...（これには数秒かかります）"):
            try:
                # 画像のBase64エンコード等は ChatGoogleGenerativeAI がよしなにやってくれる場合もあるが、
                # ここでは langchain-google-genai の標準的な画像渡し方（message content list）を行う
                llm = get_vision_model(api_key)
                
                # 画像データをバイト列で取得
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_bytes = img_byte_arr.getvalue()

                # プロンプトの構築
                prompt_text = f"""
                あなたはプロのフードライター兼メニューエンジニアです。
                このメニュー画像を分析し、記載されている料理をリストアップしてください。
                
                # 参考知識 (Knowledge Base)
                - 日本の食材や料理に関する詳細な知識は、`https://japan-word.com/site-map.html` にあるような専門的かつ文化的な背景情報を参考にしてください。正確な食材の定義や文化的意義を反映させてください。
                
                # 店舗コンテクスト (Store Context)
                {store_context}
                
                各料理について、以下の情報を抽出・創作してください：
                1. 【重要】メニュー名（日本語）
                   - 画像から正確に読み取ってください。
                   - ★重要★ 文字が読み取れない、または料理画像しかない場合も、**絶対に空欄にしないでください**。見た目から「刺身の盛り合わせ」「季節のサラダ」のように具体的な名前を創作して埋めてください。
                
                2. 価格（数字のみ）
                
                3. カテゴリ（以下の5つから選択）：
                   - ドリンク
                   - フード
                   - ランチ
                   - コース
                   - デザート
                
                4. 【重要】日本語の説明文（menu_content）:
                   - ただの説明ではなく、読んだ人が「食べたい！」と思うような「食レポ」調で書いてください。
                   - 黙読で約18秒（60〜100文字程度）の長さにまとめること。
                   - その料理の「美味しい食べ方」や「おすすめのペアリング（お酒など）」も創作して盛り込んでください。
                   - {persona_instruction}
                
                5. アレルギー物質の推測:
                   - メニュー名や見た目から、含まれている可能性が高いアレルゲン（小麦、卵、エビカニ等）をTrueにしてください。
                
                出力は必ず指定されたJSON形式で行ってください。
                """
                
                # LangChainの画像入力仕様が頻繁に変わるため、あえて raw list を渡す形式にトライ
                # もしエラーが出る場合は google.generativeai を直接叩く方式に切り替えますが、まずはLECLで。
                
                # 訂正: LangChainで画像を送る際、base64変換は自前でやる必要があるケースが多い
                import base64
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/{image.format.lower()};base64,{b64_img}"
                        }
                    ]
                )

                # Output Parser
                parser = JsonOutputParser(pydantic_object=MenuExtractionResult)
                chain = llm | parser
                
                # 実行
                result = chain.invoke([message])
                
                # 結果の取得
                items_data = result["items"] if isinstance(result, dict) and "items" in result else result

                # --- デバッグ表示 ---
                with st.expander("🔍 AI解析データの生ログを確認する (Debug)"):
                    st.json(items_data)

                # --- データベースへの保存 ---
                if store_name_input:
                    try:
                        with st.spinner("💾 データベースに保存中..."):
                            # 1. Store ID 取得
                            store_id = register_store_if_needed(store_name_input, store_url)
                            
                            # 2. メニュー保存
                            if store_id:
                                # items_data は辞書のリスト、ただし allergens がフラットかネストかなど揺らぎがある
                                # Pydanticの `MenuExtractionResult` でパース済みなら形は綺麗だが、
                                # JsonOutputParserの出力は raw dict なので、ここで少し整形が必要
                                
                                # 整形用リスト
                                clean_items = []
                                for item in items_data:
                                    if not isinstance(item, dict): continue
                                    
                                    # アレルゲン整形
                                    base_allergens = item.get("allergens", item) # フラットかネストか
                                    # 必要なキーだけ抽出してJSONBへ
                                    allergen_keys = ["wheat","crustacean","egg","fish","soy","peanut","milk","walnut","celery","mustard","sesame","sulfite","lupinus","mollusc"]
                                    clean_allergen = {k: bool(base_allergens.get(k, False)) for k in allergen_keys}
                                    
                                    item["allergens"] = clean_allergen
                                    clean_items.append(item)
                                
                                save_menu_to_db(store_id, clean_items, selected_persona)
                                st.success(f"🎉 データベース(MENU_MASTER)への保存が完了しました！ Store: {store_name_input}")
                                
                                # Usage Log capture is tricky with LCEL invoke return value directly.
                                # For now, we rely on the implementation in langchain_utils if we were using it, 
                                # but here we used raw chain. The usage metadata might be lost in result dict.
                                # Future Work: Pass callbacks to capture token usage here using log_api_usage.
                                if hasattr(result, "response_metadata"):
                                     # JsonOutputParserを通すと response_metadata が消えることがあるため、
                                     # invokeの結果が Pydantic object なら良いが、dictだとない。
                                     # いったんここはスキップし、「翻訳フェーズ」でログを確実にとる運用とする。
                                     pass

                            else:
                                st.error("店舗IDの取得に失敗しました。")
                    except Exception as e:
                        st.error(f"DB保存エラー: {e}")
                
                # DataFrameの作成 (48列) - プレフィックス(A:など)を削除
                # カラム定義
                columns = [
                    "税込み価格", "画像", "カテゴリ", "おすすめ", 
                    "小麦", "甲殻類", "卵", "魚", "大豆", "ピーナッツ", "牛乳", "くるみ", "セロリ", "マスタード", "ゴマ", "亜硫酸塩", "ルピナス", "貝",
                    "日本語メニュー名", "日本語説明", 
                    "英語メニュー名", "英語説明", "韓国語メニュー名", "韓国語説明", "中国語メニュー名", "中国語説明",
                    "台湾語メニュー名", "台湾語説明", "広東語メニュー名", "広東語説明", "タイ語メニュー名", "タイ語説明",
                    "フィリピン語メニュー名", "フィリピン語説明", "ベトナム語メニュー名", "ベトナム語説明", "インドネシア語メニュー名", "インドネシア語説明",
                    "スペイン語メニュー名", "スペイン語説明", "ドイツ語メニュー名", "ドイツ語説明", "フランス語メニュー名", "フランス語説明",
                    "イタリア語メニュー名", "イタリア語説明", "ポルトガル語メニュー名", "ポルトガル語説明"
                ]
                
                csv_data = []
                skipped_count = 0
                
                for item in items_data:
                    # 1. 辞書型でない場合はスキップ
                    if not isinstance(item, dict):
                        skipped_count += 1
                        continue
                    
                    # 2. メニュー名を取得（揺らぎに対応：menu_name_jp, menu_name, name）
                    menu_name = item.get("menu_name_jp") or item.get("menu_name") or item.get("name") or ""
                    
                    # メニュー名が空の場合はスキップ（カテゴリだけ入るのを防ぐ）
                    if not menu_name or menu_name.strip() == "":
                        skipped_count += 1
                        continue

                    row = {col: "" for col in columns} # 初期化
                    
                    # AI抽出データのマッピング
                    row["税込み価格"] = item.get("price", "")
                    row["カテゴリ"] = item.get("category", "")
                    
                    # アレルゲン
                    # AIの出力が { "allergens": { "wheat": true } } のようなネスト構造の場合と
                    # { "wheat": true } のようなフラット構造の場合があるため両対応
                    allergens = item.get("allergens", item) # "allergens"キーがあればそれを使う、なければitemそのもの
                    
                    # アレルゲンキーのマッピング（AI出力キー → CSV列名）
                    # Debugログを見ると "wheat": true などの形式
                    row["小麦"] = "TRUE" if allergens.get("wheat") else "FALSE"
                    row["甲殻類"] = "TRUE" if (allergens.get("crustacean") or allergens.get("shrimp_crab")) else "FALSE"
                    row["卵"] = "TRUE" if allergens.get("egg") else "FALSE"
                    row["魚"] = "TRUE" if (allergens.get("fish") or allergens.get("fish_shellfish")) else "FALSE"
                    row["大豆"] = "TRUE" if (allergens.get("soy") or allergens.get("soybean")) else "FALSE"
                    row["ピーナッツ"] = "TRUE" if allergens.get("peanut") else "FALSE"
                    row["牛乳"] = "TRUE" if (allergens.get("milk") or allergens.get("dairy")) else "FALSE"
                    row["くるみ"] = "TRUE" if allergens.get("walnut") else "FALSE"
                    row["セロリ"] = "TRUE" if allergens.get("celery") else "FALSE"
                    row["マスタード"] = "TRUE" if allergens.get("mustard") else "FALSE"
                    row["ゴマ"] = "TRUE" if allergens.get("sesame") else "FALSE"
                    row["亜硫酸塩"] = "TRUE" if (allergens.get("sulfite") or allergens.get("sulphite")) else "FALSE"
                    row["ルピナス"] = "TRUE" if allergens.get("lupinus") else "FALSE"
                    row["貝"] = "TRUE" if (allergens.get("mollusc") or allergens.get("shellfish")) else "FALSE"
                    
                    # メインコンテンツ
                    # 説明文も揺らぎに対応
                    description = item.get("description_rich") or item.get("menu_content") or item.get("description") or ""
                    
                    row["日本語メニュー名"] = menu_name
                    row["日本語説明"] = description
                    
                    csv_data.append(row)
                
                df = pd.DataFrame(csv_data, columns=columns)
                
                st.success(f"✅ 解析完了！ {len(df)} 件のメニューを抽出しました。")
                st.dataframe(df)
                
                # CSVダウンロード
                csv_output = df.to_csv(index=False).encode('utf-8-sig') # Excelで文字化けしないようBOM付き
                st.download_button(
                    label="📥 CSVをダウンロード",
                    data=csv_output,
                    file_name="menu_ai_generated.csv",
                    mime="text/csv",
                )
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.write("詳細:", e)
