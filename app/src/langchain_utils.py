# langchain_utils.py

from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import json
from typing import List, Dict, Tuple
import asyncio
from .models import MenuItem
from langchain.output_parsers import StructuredOutputParser
from langchain.output_parsers import ResponseSchema

# スキーマの定義
response_schemas = [
    ResponseSchema(name="menu_title", description="メニューのタイトル"),
    ResponseSchema(name="menu_content", description="メニューの説明文")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# --------------------------------------------------------------------
# 1) 不要部分削除のためのプロンプト & チェーン作成
# --------------------------------------------------------------------
cleanup_template = """
外国人観光客向けに、レストランのメニューの翻訳を行います。
前準備として、以下の日本語テキストから、不要な自己アピールや頑張りに関する言葉などを削除し、料理の説明や歴史・食べ方など利用者に有益な情報は残してください。
また、文化や歴史的な背景情報が必要な情報があれば、内容の中に適宜追加してください。

{format_instructions}

【原文】
{original_text}

【不要部分削除後】
"""

cleanup_prompt = PromptTemplate(
    input_variables=["original_text"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()},
    template=cleanup_template
)

# --------------------------------------------------------------------
# 2) 日本語 → 英語翻訳のためのプロンプト
# --------------------------------------------------------------------
ja_to_en_template = """
外国人観光客向けに、以下の日本語メニューを自然な英語に翻訳してください。

{format_instructions}

【日本語】
{cleaned_japanese_text}

【英語訳】
"""

ja_to_en_prompt = PromptTemplate(
    input_variables=["cleaned_japanese_text"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()},
    template=ja_to_en_template
)

# --------------------------------------------------------------------
# 3) 英語 → 多言語翻訳のためのプロンプト
# --------------------------------------------------------------------
multi_trans_template = """
以下の英語テキストを {target_language} に翻訳してください。

{format_instructions}

【英語原文】
{english_text}

【{target_language}訳】
"""

multi_trans_prompt = PromptTemplate(
    input_variables=["english_text", "target_language"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()},
    template=multi_trans_template
)

def create_cleanup_chain(api_key: str, temperature: float = 0.0) -> LLMChain:
    """不要部分の削除を行うChainを作成して返す"""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
    )
    return LLMChain(llm=llm, prompt=cleanup_prompt)

def create_ja_to_en_chain(api_key: str, temperature: float = 0.0) -> LLMChain:
    """日本語から英語への翻訳Chainを作成して返す"""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
    )
    return LLMChain(llm=llm, prompt=ja_to_en_prompt)

def create_multi_trans_chain(api_key: str, temperature: float = 0.0) -> LLMChain:
    """英語から指定言語へ翻訳するChainを作成して返す"""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
    )
    return LLMChain(llm=llm, prompt=multi_trans_prompt)

def remove_unnecessary_parts(text_list: List[MenuItem], api_key: str) -> List[MenuItem]:
    """
    text_list: MenuItemのリストを想定
    1件ずつ不要部分削除を行い、結果をMenuItemのリストで返す
    """
    chain = create_cleanup_chain(api_key=api_key, temperature=0.0)
    results = []
    
    progress_text = "✒️ 日本語校正"
    my_bar = st.progress(0, text=progress_text)
    total_items = len(text_list)
    
    for i, menu_item in enumerate(text_list, 1):
        try:
            input_text = {
                "menu_title": menu_item.menu_title,
                "menu_content": menu_item.menu_content
            }
            cleaned_text = chain.run(original_text=json.dumps(input_text, ensure_ascii=False))
            # OutputParserを使用してパース
            parsed_output = output_parser.parse(cleaned_text)
            menu_item = MenuItem(
                menu_title=parsed_output["menu_title"],
                menu_content=parsed_output["menu_content"]
            )
            results.append(menu_item)
            
            # 進捗を更新
            progress = int(i / total_items * 100)
            my_bar.progress(progress, text=f"{progress_text} ({i}/{total_items})")
            
        except Exception as e:
            error_msg = f"日本語校正中にエラーが発生しました: {e}"
            st.error(error_msg)
            st.error(f"エラー詳細: {type(e).__name__}")
            results.append(MenuItem.create_error(str(e)))
    
    my_bar.progress(100, text=f"✅ 日本語校正完了")
    return results

def translate_japanese_to_english(menu_items: List[MenuItem], api_key: str) -> List[MenuItem]:
    """
    日本語のMenuItemリストを英語に翻訳し、結果をMenuItemのリストで返す
    """
    chain = create_ja_to_en_chain(api_key=api_key, temperature=0.0)
    results = []
    
    progress_text = "🔤 英語翻訳"
    my_bar = st.progress(0, text=progress_text)
    total_items = len(menu_items)
    
    for i, menu_item in enumerate(menu_items, 1):
        try:
            # 文字列の場合はMenuItemに変換
            if isinstance(menu_item, str):
                try:
                    # 文字列をJSONとしてパース
                    data = json.loads(menu_item)
                    menu_item = MenuItem(
                        menu_title=data["menu_title"],
                        menu_content=data["menu_content"]
                    )
                except json.JSONDecodeError:
                    st.error("文字列をJSONとしてパースできませんでした")
                    results.append(MenuItem.create_error("Invalid JSON format"))
                    continue
            
            # MenuItemの内容を辞書形式で渡す
            input_text = {
                "menu_title": menu_item.menu_title,
                "menu_content": menu_item.menu_content
            }
            
            en_text = chain.run(cleaned_japanese_text=json.dumps(input_text, ensure_ascii=False))
            
            # OutputParserを使用してパース
            parsed_output = output_parser.parse(en_text)
            translated_item = MenuItem(
                menu_title=parsed_output["menu_title"],
                menu_content=parsed_output["menu_content"]
            )
            results.append(translated_item)
            
            # 進捗を更新
            progress = int(i / total_items * 100)
            my_bar.progress(progress, text=f"{progress_text} ({i}/{total_items})")
            
        except Exception as e:
            error_msg = f"英語翻訳中にエラーが発生しました: {e}"
            st.error(error_msg)
            st.error(f"エラー詳細: {type(e).__name__}")
            results.append(MenuItem.create_error(str(e)))
    
    my_bar.progress(100, text=f"✅ 英語翻訳完了")
    return results

async def translate_english_to_many_async(menu_items: List[MenuItem], target_languages: Dict[str, List[MenuItem]], api_key: str) -> Dict[str, List[MenuItem]]:
    """
    英語から指定言語への翻訳を非同期で並列実行
    
    Args:
        menu_items: 翻訳対象の英語MenuItemリスト
        target_languages: 翻訳先言語と結果を格納する辞書
        api_key: OpenAI APIキー
    
    Returns:
        Dict[str, List[MenuItem]]: 言語ごとの翻訳結果を格納した辞書
    """
    results = {}
    chain = create_multi_trans_chain(api_key=api_key, temperature=0.0)
    error_messages = []  # エラーメッセージを格納するリスト
    rate_limit_status = {"is_waiting": False}  # Rate Limitの状態を管理
    
    async def translate_with_retry(input_text: str, lang: str, max_retries: int = 10, initial_wait: float = 10.0) -> str:
        """リトライロジックを含む翻訳実行"""
        wait_time = initial_wait
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if rate_limit_status["is_waiting"]:
                    await asyncio.sleep(1)  # 他の処理を待機中の場合は少し待つ
                return await chain.arun(
                    english_text=input_text,
                    target_language=lang
                )
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Rate Limitエラーの処理
                if "rate_limit_exceeded" in error_msg and attempt < max_retries - 1:
                    if not rate_limit_status["is_waiting"]:
                        rate_limit_status["is_waiting"] = True
                        with st.status(f"⏳ APIのレート制限に達しました。{int(wait_time)}秒待機中...") as status:
                            await asyncio.sleep(wait_time)
                            status.update(label="✅ 待機完了、翻訳を再開します")
                        rate_limit_status["is_waiting"] = False
                    wait_time *= 1.5
                    continue
                
                # Connection errorの処理
                if "connection" in error_msg and attempt < max_retries - 1:
                    wait_time = min(wait_time * 1.5, 30.0)  # 最大30秒まで待機時間を増やす
                    with st.status(f"🔌 接続エラーが発生しました。{int(wait_time)}秒後に再試行 ({attempt + 1}/{max_retries})") as status:
                        await asyncio.sleep(wait_time)
                        status.update(label="🔄 接続を再試行します")
                    continue
                
                raise last_error
    
    async def translate_menu_item(menu_item: MenuItem, lang: str) -> Tuple[str, MenuItem]:
        """1つのメニュー項目を指定された言語に翻訳"""
        try:
            input_text = {
                "menu_title": menu_item.menu_title,
                "menu_content": menu_item.menu_content
            }
            
            translated_text = await translate_with_retry(
                json.dumps(input_text, ensure_ascii=False),
                lang
            )
            
            parsed_output = output_parser.parse(translated_text)
            translated_item = MenuItem(
                menu_title=parsed_output["menu_title"],
                menu_content=parsed_output["menu_content"]
            )
            return lang, translated_item
            
        except Exception as e:
            error_msg = f"🚫 {lang}の翻訳中にエラー: {str(e)}"
            if "rate_limit_exceeded" not in str(e):  # Rate Limit以外のエラーのみを表示
                error_messages.append(error_msg)
            return lang, MenuItem.create_error(str(e))
    
    async def translate_language(lang: str) -> Tuple[str, List[MenuItem]]:
        """1つの言語に対する全メニュー項目の翻訳"""
        progress_text = f"🔄 {lang}の翻訳"
        my_bar = st.progress(0, text=progress_text)
        
        # 同時実行数を制限（5件ずつ処理）
        batch_size = 5
        tasks = [translate_menu_item(item, lang) for item in menu_items]
        translated_items = []
        total_items = len(tasks)
        
        for i in range(0, total_items, batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch)
            translated_items.extend(batch_results)
            progress = int(min((i + batch_size), total_items) / total_items * 100)
            my_bar.progress(progress, text=f"{progress_text} ({min(i + batch_size, total_items)}/{total_items})")
        
        my_bar.progress(100, text=f"✅ {lang}の翻訳完了")
        lang_results = [item[1] for item in translated_items]
        return lang, lang_results
    
    # 全言語の翻訳を並列実行
    translation_tasks = [translate_language(lang) for lang in target_languages.keys()]
    translation_results = await asyncio.gather(*translation_tasks)
    
    # 結果を辞書にまとめる
    results = dict(translation_results)
    
    # エラーメッセージがある場合、まとめて表示
    if error_messages:
        with st.expander("⚠️ 翻訳中に発生したエラー", expanded=False):
            for msg in error_messages:
                st.error(msg)
    
    return results