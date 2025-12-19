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
                prompt_text = """
                あなたはプロのフードライター兼メニューエンジニアです。
                このメニュー画像を分析し、記載されている料理をリストアップしてください。
                
                各料理について、以下の情報を抽出・創作してください：
                1. 【重要】メニュー名（日本語）
                   - 画像から正確に読み取ってください。読み取れない場合も「料理名不明」とせず、見た目から推測される具体的な料理名を入れてください。
                
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
                   - 文体は「東京カレンダー」のような、少し艶っぽく洗練されたトーンでお願いします。
                
                5. アレルギー物質の推測:
                   - メニュー名や見た目から、含まれている可能性が高いアレルゲン（小麦、卵、エビカニ等）をTrueにしてください。
                
                出力は必ず指定されたJSON形式で行ってください。
                """
                
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{os.base64.b64encode(img_bytes).decode('utf-8') if hasattr(os, 'base64') else ''}"} 
                            # 注意: langchain_google_genai のバージョンによっては画像の渡し方が異なるため、
                            # 最も汎用的な `image_url` 形式 (base64) か、ライブラリ固有の方法を使う。
                            # ここでは安全策として、一旦PILイメージを無視してテキストのみになってしまうリスクを避けるため
                            # 確実な google-genai SDK ではなく langchain 経由なので、
                            # 簡易的に画像メッセージを構築します。
                        }
                    ]
                )
                
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
                
                # DataFrameの作成 (48列)
                # カラム定義 (A-AV)
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
                for item in items_data:
                    # 1. 辞書型でない場合はスキップ
                    if not isinstance(item, dict):
                        continue
                    
                    # 2. メニュー名が空の場合はスキップ（カテゴリだけ入るのを防ぐ）
                    menu_name = item.get("menu_name_jp", "")
                    if not menu_name or menu_name.strip() == "":
                        continue

                    row = {col: "" for col in columns} # 初期化
                    
                    # AI抽出データのマッピング
                    row["税込み価格"] = item.get("price", "")
                    row["カテゴリ"] = item.get("category", "")
                    
                    # アレルゲン
                    row["小麦"] = "TRUE" if item.get("wheat") else "FALSE"
                    row["甲殻類"] = "TRUE" if item.get("crustacean") else "FALSE"
                    row["卵"] = "TRUE" if item.get("egg") else "FALSE"
                    row["魚"] = "TRUE" if item.get("fish") else "FALSE"
                    row["大豆"] = "TRUE" if item.get("soy") else "FALSE"
                    row["ピーナッツ"] = "TRUE" if item.get("peanut") else "FALSE"
                    row["牛乳"] = "TRUE" if item.get("milk") else "FALSE"
                    row["くるみ"] = "TRUE" if item.get("walnut") else "FALSE"
                    row["セロリ"] = "TRUE" if item.get("celery") else "FALSE"
                    row["マスタード"] = "TRUE" if item.get("mustard") else "FALSE"
                    row["ゴマ"] = "TRUE" if item.get("sesame") else "FALSE"
                    row["亜硫酸塩"] = "TRUE" if item.get("sulfite") else "FALSE"
                    row["ルピナス"] = "TRUE" if item.get("lupinus") else "FALSE"
                    row["貝"] = "TRUE" if item.get("mollusc") else "FALSE"
                    
                    # メインコンテンツ
                    row["日本語メニュー名"] = menu_name
                    row["日本語説明"] = item.get("description_rich", "")
                    
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
