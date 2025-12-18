import streamlit as st
import csv
import io
from src.csv_utils import is_valid_row
from src.supabase_client import get_supabase
from src.st_auth import supabase_auth_widget
import src.st_utils as st_utils
import src.langchain_utils as langchain_utils
from src.models import MenuItem
from typing import Dict, List
import json
import asyncio

# セッション状態の型を定義
target_contents: List[MenuItem] = []
cleaned_contents: List[MenuItem] = []
translated_contents: List[MenuItem] = []
translated_contents_many: Dict[str, List[MenuItem]] = {
    "韓国語": [],
    "中国語": [],
    "台湾語": [],
    "広東語": [],
    "タイ語": [],
    "フィリピン語": [],
    "ベトナム語": [],
    "インドネシア語": [],
    "スペイン語": [],
    "ドイツ語": [],
    "フランス語": [],
    "イタリア語": [],
    "ポルトガル語": [],
}

# セッション状態の初期化
if "supabase" not in st.session_state:
    st.session_state["supabase"] = get_supabase()

if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = ""

if "target_contents" not in st.session_state:
    st.session_state["target_contents"] = []

if "cleaned_contents" not in st.session_state:
    st.session_state["cleaned_contents"] = []

if "translated_contents" not in st.session_state:
    st.session_state["translated_contents"] = []

if "translated_contents_many" not in st.session_state:
    st.session_state["translated_contents_many"] = translated_contents_many

# 認証ウィジェットの実行
supabase_auth_widget()

# サイドバーの構築
with st.sidebar:
    st.divider()
    # APIキーが未取得の場合のみSupabaseから取得
    if not st.session_state["gemini_api_key"]:
        st.session_state["gemini_api_key"] = st_utils.get_gemini_api_key()
    
    # APIキーの入力
    new_key = st.text_input(
        "Gemini API Key", 
        value=st.session_state["gemini_api_key"], 
        type="password", 
        key="gemini_key_input"
    )
    
    if st.button("🔑鍵を更新", key="update_key_button"):
        st_utils.set_gemini_api_key(new_key)
        st.session_state["gemini_api_key"] = new_key
        st.success("APIキーを更新しました")


st.title("レストランメニュー翻訳アプリ")
uploaded_file = st.file_uploader("⬆️csvをアップロード", type="csv")
target_contents: List[MenuItem] = []

if uploaded_file is not None:
    try:
        # バイトストリームをテキストストリームに変換
        text_io = io.TextIOWrapper(uploaded_file, encoding='utf-8')
        reader = csv.reader(text_io, delimiter=",")
        
        for row in reader:
            if is_valid_row(row, ["キーワードは無し(メニューのみ翻訳)"]):
                # 有効な行からMenuItemを作成
                menu_item = MenuItem(
                    menu_title=row[1],
                    menu_content=row[2]
                )
                target_contents.append(menu_item)
                
        if not target_contents:
            st.warning("有効なメニュー項目が見つかりませんでした。")
        else:
            st.success(f"{len(target_contents)}件のメニュー項目を読み込みました。")
            
    except Exception as e:
        st.error(f"アップロードされたファイルを処理できませんでした。: {e}")
    
    # セッション状態に保存
    st.session_state["target_contents"] = target_contents


# タブを作成
if st.session_state["target_contents"]:
    tab1, tab2, tab3, tab4 = st.tabs(["オリジナルコンテンツ", "日本語校正", "英語翻訳", "多言語に翻訳"])
    
    with tab1:
        for i, content in enumerate(st.session_state["target_contents"]):
            st.markdown(f"### コンテンツ {i+1}")
            st.markdown(f"**メニュー名**  \n{content.menu_title}")
            st.markdown(f"**説明文**  \n{content.menu_content}")
            st.divider()
    
    with tab2:
        if st.button("✒️日本語の修正実行"):
            with st.spinner("日本語を修正中..."):
                cleaned_contents = langchain_utils.remove_unnecessary_parts(st.session_state["target_contents"], st.session_state["gemini_api_key"])
                st.session_state["cleaned_contents"] = cleaned_contents

        edited_contents = []
        if st.session_state["cleaned_contents"]:
            for i, content in enumerate(st.session_state["cleaned_contents"]):
                st.write(f"### コンテンツ {i+1}")
                left_col, right_col = st.columns([1, 1])
                
                # 左側にオリジナルコンテンツを表示
                with left_col:
                    st.markdown("**オリジナル：**")
                    st.markdown(f"**メニュー名**  \n{st.session_state['target_contents'][i].menu_title}")
                    st.markdown(f"**説明文**  \n{st.session_state['target_contents'][i].menu_content}")

                # 右側に編集可能なコンテンツを表示
                with right_col:
                    st.markdown("**校正後：**")
                    edited_title = st.text_input(
                        "メニュー名",
                        value=content.menu_title if hasattr(content, 'menu_title') else "",
                        key=f"edited_title_{i}"
                    )
                    edited_content = st.text_area(
                        "説明文",
                        value=content.menu_content if hasattr(content, 'menu_content') else "",
                        key=f"edited_content_{i}",
                        height=150
                    )
                    edited_contents.append(MenuItem(
                        menu_title=edited_title,
                        menu_content=edited_content
                    ))
                
                st.divider()
            
            if st.button("変更を確定", key="confirm_japanese_button"):
                st.session_state["cleaned_contents"] = edited_contents
                st.success("変更が確定されました！")

    with tab3:
        if st.button("英語翻訳実行"):
            with st.spinner("英語翻訳中..."):
                translated_contents = langchain_utils.translate_japanese_to_english(st.session_state["cleaned_contents"], st.session_state["gemini_api_key"])
                st.session_state["translated_contents"] = translated_contents
        
        edited_translated_contents = []
        if st.session_state["translated_contents"]:
            for i, content in enumerate(st.session_state["translated_contents"]):
                st.write(f"### コンテンツ {i+1}")
                left_col, right_col = st.columns([4, 5])
                
                # 左側に校正済み日本語コンテンツを表示
                with left_col:
                    st.markdown("**校正済み日本語：**")
                    st.markdown(f"**メニュー名**  \n{st.session_state['cleaned_contents'][i].menu_title}")
                    st.markdown(f"**説明文**  \n{st.session_state['cleaned_contents'][i].menu_content}")

                # 右側に編集可能な英訳コンテンツを表示
                with right_col:
                    st.markdown("**英訳：**")
                    translated_title = st.text_input(
                        "Menu Name",
                        value=content.menu_title if hasattr(content, 'menu_title') else "",
                        key=f"translated_title_{i}"
                    )
                    translated_content = st.text_area(
                        "Description",
                        value=content.menu_content if hasattr(content, 'menu_content') else "",
                        key=f"translated_content_{i}",
                        height=150
                    )
                    edited_translated_contents.append(MenuItem(
                        menu_title=translated_title,
                        menu_content=translated_content
                    ))
                
                st.divider()
            
            if st.button("変更を確定", key="confirm_english_button"):
                st.session_state["translated_contents"] = edited_translated_contents
                st.success("変更が確定されました！")
    
    with tab4:
        if st.button("🌏多言語翻訳実行"):
            with st.spinner("多言語翻訳中..."):
                try:
                    st.write("翻訳開始...")
                    st.write(f"翻訳対象データ数: {len(st.session_state['translated_contents'])}件")
                    
                    # 非同期翻訳の実行
                    results = asyncio.run(langchain_utils.translate_english_to_many_async(
                        menu_items=st.session_state["translated_contents"],
                        target_languages=st.session_state["translated_contents_many"],
                        api_key=st.session_state["gemini_api_key"]
                    ))
                    
                    # 結果をセッション状態に保存
                    st.session_state["translated_contents_many"].update(results)
                    st.success("全言語の翻訳が完了しました！")
                    
                except Exception as e:
                    st.error(f"翻訳処理中にエラーが発生しました: {e}")
                    st.error(f"エラーの詳細: {type(e)}")
                    import traceback
                    st.error(f"スタックトレース: {traceback.format_exc()}")
        
        # 翻訳結果の表示（アコーディオン形式）
        if any(st.session_state["translated_contents_many"].values()):
            st.write("### 翻訳結果")
            for lang, translations in st.session_state["translated_contents_many"].items():
                with st.expander(f"🌐 {lang}"):
                    for i, menu_item in enumerate(translations, 1):
                        st.markdown(f"**{i}. {menu_item.menu_title}**")
                        st.write(menu_item.menu_content)
                        st.divider()
        
        # CSVダウンロードボタン
        if any(st.session_state["translated_contents_many"].values()):
            if st.button("📊csvファイルを作成"):
                # CSVデータの作成
                output = io.StringIO()
                writer = csv.writer(output, lineterminator='\n')
                
                # ヘッダー行の作成
                headers = ["日本語メニュー名", "日本語説明", "英語メニュー名", "英語説明"]
                for lang in st.session_state["translated_contents_many"].keys():
                    headers.extend([f"{lang}メニュー名", f"{lang}説明"])
                writer.writerow(headers)
                
                # データ行の作成
                for i in range(len(st.session_state["cleaned_contents"])):
                    row = []
                    try:
                        # 日本語
                        japanese_item = st.session_state["cleaned_contents"][i]
                        row.extend([japanese_item.menu_title, japanese_item.menu_content])
                        
                        # 英語
                        english_item = st.session_state["translated_contents"][i]
                        row.extend([english_item.menu_title, english_item.menu_content])
                        
                        # 他言語
                        for lang in st.session_state["translated_contents_many"].keys():
                            menu_item = st.session_state["translated_contents_many"][lang][i]
                            row.extend([menu_item.menu_title, menu_item.menu_content])
                            
                    except (IndexError, AttributeError) as e:
                        st.error(f"{i+1}番目のメニューの処理中にエラーが発生しました: {e}")
                        # エラーが発生した場合は空文字を追加
                        row.extend(["", ""] * (len(st.session_state["translated_contents_many"]) + 2 - len(row) // 2))
                    
                    writer.writerow(row)
                
                # BOMを追加してUTF-8で保存
                csv_data = '\ufeff' + output.getvalue()
                
                # ダウンロードボタンの作成
                st.download_button(
                    label="⬇️CSVファイルをダウンロード",
                    data=csv_data,
                    file_name="translated_menu.csv",
                    mime="text/csv",
                )