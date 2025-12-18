# langchain_utils.py

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import json
from typing import List, Dict, Tuple
import asyncio
from .models import MenuItem
from langchain_classic.output_parsers import StructuredOutputParser, ResponseSchema

# スキーマの定義
response_schemas = [
    ResponseSchema(name="menu_title", description="メニューのタイトル"),
    ResponseSchema(name="menu_content", description="メニューの説明文")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# --------------------------------------------------------------------
# 1) 不要部分削除のためのプロンプト
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

def get_llm(api_key: str, temperature: float = 0.0):
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
    )

def remove_unnecessary_parts(text_list: List[MenuItem], api_key: str) -> List[MenuItem]:
    """1件ずつ不要部分削除を行い、結果をMenuItemのリストで返す"""
    llm = get_llm(api_key)
    chain = cleanup_prompt | llm | output_parser
    
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
            # LCEL invoke
            parsed_output = chain.invoke({"original_text": json.dumps(input_text, ensure_ascii=False)})
            
            new_item = MenuItem(
                menu_title=parsed_output["menu_title"],
                menu_content=parsed_output["menu_content"]
            )
            results.append(new_item)
            
            progress = int(i / total_items * 100)
            my_bar.progress(progress, text=f"{progress_text} ({i}/{total_items})")
            
        except Exception as e:
            st.error(f"日本語校正中にエラーが発生しました: {e}")
            results.append(MenuItem.create_error(str(e)))
    
    my_bar.progress(100, text=f"✅ 日本語校正完了")
    return results

def translate_japanese_to_english(menu_items: List[MenuItem], api_key: str) -> List[MenuItem]:
    """日本語のMenuItemリストを英語に翻訳し、結果をMenuItemのリストで返す"""
    llm = get_llm(api_key)
    chain = ja_to_en_prompt | llm | output_parser
    
    results = []
    progress_text = "🔤 英語翻訳"
    my_bar = st.progress(0, text=progress_text)
    total_items = len(menu_items)
    
    for i, menu_item in enumerate(menu_items, 1):
        try:
            input_text = {
                "menu_title": menu_item.menu_title,
                "menu_content": menu_item.menu_content
            }
            # LCEL invoke
            parsed_output = chain.invoke({"cleaned_japanese_text": json.dumps(input_text, ensure_ascii=False)})
            
            translated_item = MenuItem(
                menu_title=parsed_output["menu_title"],
                menu_content=parsed_output["menu_content"]
            )
            results.append(translated_item)
            
            progress = int(i / total_items * 100)
            my_bar.progress(progress, text=f"{progress_text} ({i}/{total_items})")
            
        except Exception as e:
            st.error(f"英語翻訳中にエラーが発生しました: {e}")
            results.append(MenuItem.create_error(str(e)))
    
    my_bar.progress(100, text=f"✅ 英語翻訳完了")
    return results

async def translate_english_to_many_async(menu_items: List[MenuItem], target_languages: Dict[str, List[MenuItem]], api_key: str) -> Dict[str, List[MenuItem]]:
    """英語から指定言語への翻訳を非同期で並列実行"""
    llm = get_llm(api_key)
    chain = multi_trans_prompt | llm | output_parser
    
    error_messages = []
    rate_limit_status = {"is_waiting": False}
    
    async def translate_with_retry(input_dict: dict, lang: str, max_retries: int = 5, initial_wait: float = 10.0) -> dict:
        wait_time = initial_wait
        for attempt in range(max_retries):
            try:
                if rate_limit_status["is_waiting"]:
                    await asyncio.sleep(1)
                # LCEL ainvoke
                return await chain.ainvoke({
                    "english_text": json.dumps(input_dict, ensure_ascii=False),
                    "target_language": lang
                })
            except Exception as e:
                error_msg = str(e).lower()
                if "rate_limit" in error_msg and attempt < max_retries - 1:
                    if not rate_limit_status["is_waiting"]:
                        rate_limit_status["is_waiting"] = True
                        with st.status(f"⏳ レート制限待機中({int(wait_time)}秒)...") as status:
                            await asyncio.sleep(wait_time)
                            status.update(label="✅ 再開します")
                        rate_limit_status["is_waiting"] = False
                    wait_time *= 2
                    continue
                raise e

    async def translate_menu_item(menu_item: MenuItem, lang: str) -> Tuple[str, MenuItem]:
        try:
            input_text = {"menu_title": menu_item.menu_title, "menu_content": menu_item.menu_content}
            parsed_output = await translate_with_retry(input_text, lang)
            return lang, MenuItem(menu_title=parsed_output["menu_title"], menu_content=parsed_output["menu_content"])
        except Exception as e:
            error_messages.append(f"🚫 {lang}の翻訳エラー: {e}")
            return lang, MenuItem.create_error(str(e))

    async def translate_language(lang: str) -> Tuple[str, List[MenuItem]]:
        progress_text = f"🔄 {lang}の翻訳"
        my_bar = st.progress(0, text=progress_text)
        
        batch_size = 3 # 並列数を少し抑えて安定させる
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
        return lang, [item[1] for item in translated_items]

    translation_tasks = [translate_language(lang) for lang in target_languages.keys()]
    translation_results = await asyncio.gather(*translation_tasks)
    
    results = dict(translation_results)
    if error_messages:
        with st.expander("⚠️ エラー詳細", expanded=False):
            for msg in error_messages:
                st.error(msg)
    return results