from __future__ import annotations

from typing import List, Dict, Tuple, Any
import asyncio
import json
import re
import os
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st

from .models import MenuItem

# LangChain v1系で output_parsers の場所が割れるので、ここは classic に固定して安定化
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
# --------------------------------------------------------------------
# 3) 英語 → 多言語翻訳のためのプロンプト
# --------------------------------------------------------------------
multi_trans_template = """
以下の英語テキストを {target_language} に翻訳してください。

{persona_instruction}

{format_instructions}

【英語原文】
{english_text}

【{target_language}訳】
"""

multi_trans_prompt = PromptTemplate(
    input_variables=["english_text", "target_language", "persona_instruction"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()},
    template=multi_trans_template
)

# ペルソナ定義（メインアプリと共通化検討だが、一旦ここに定義）
PERSONA_PROMPTS = {
    "東京カレンダー風 (艶やか)": "Translate in a sophisticated, alluring, and rich tone, similar to high-end lifestyle magazines (like Tokyo Calendar). Use evocative and emotional language.",
    "居酒屋の大将風 (元気)": "Translate in a friendly, energetic, and casual tone, like a lively Izakaya owner. Use punchy and welcoming language.",
    "高級料亭風 (厳格)": "Translate in a highly formal, polite, and respectful tone, typical of a luxury Ryotei. Use elegant and traditional phrasing.",
    "標準 (丁寧)": "Translate in a standard, polite, and clear tone.",
}

# ペルソナ定義（メインアプリと共通化検討だが、一旦ここに定義）
PERSONA_PROMPTS = {
    "東京カレンダー風 (艶やか)": "Translate in a sophisticated, alluring, and rich tone, similar to high-end lifestyle magazines (like Tokyo Calendar). Use evocative and emotional language.",
    "居酒屋の大将風 (元気)": "Translate in a friendly, energetic, and casual tone, like a lively Izakaya owner. Use punchy and welcoming language.",
    "高級料亭風 (厳格)": "Translate in a highly formal, polite, and respectful tone, typical of a luxury Ryotei. Use elegant and traditional phrasing.",
    "標準 (丁寧)": "Translate in a standard, polite, and clear tone.",
}

from .observability import log_api_cost

# Removed local COST_MODEL and log_api_usage integration
# Uses centralized observability module now.

# 言語別ローカライズペルソナ (Transcreation Prompts)
# 各言語の文化背景に合わせた「ライター人格」を定義
LANGUAGE_PERSONAS = {
    "English": "You are a friendly and knowledgeable 'New Yorker Foodie'. Use appetizing adjectives (crispy, savory, zest) and a welcoming tone suitable for a hip casual dining guide.",
    "Chinese": "You are a passionate 'Gourmand from Shanghai'. Use poetic and evocative four-character idioms where appropriate to describe texture and flavor depth. Tone should be enthusiastic and respectful.",
    "Korean": "You are a trend-conscious 'Seoul Influencer'. Use modern, punchy vocabulary that appeals to young travelers. Emphasize visual and flavor impact (spicy, chewy, refreshing).",
    "French": "You are an elegant 'Parisian Sommelier'. Focus on the harmony of flavors, ingredients, and potential pairings. Use sophisticated and descriptive language.",
    "Italian": "You are a cheerful 'Trattoria Owner'. Use warm, passionate language. Emphasize freshness of ingredients and the joy of eating (Buono!).",
    "Spanish": "You are a friendly 'Tapas Bar Host'. Use lively, inviting language. Invite the guest to enjoy a shared experience.",
    "Thai": "You are a helpful 'Local Food Guide'. Explain flavors clearly (sour, sweet, spicy) with a gentle, smiling tone.",
    "German": "You are a reliable 'Gourmet Critic'. Be descriptive, precise, and emphasize quality and craftsmanship of the dish.",
    "Vietnamese": "You are a 'Street Food Connoisseur'. Use warm, appetizing language that evokes the aroma and freshness of herbs and spices.",
    "Indonesian": "You are a 'Friendly Local Host'. Use warm, inviting language consistent with Indonesian hospitality.",
    "Taiwanese": "You are a 'Taipei Food Blogger'. Use traditional characters. Tone is friendly, relatable, and emphasizes 'Q-texture' and authentic flavors.",
    "HongKong": "You are a 'Cantonese Chef'. Use Cantonese stylistic nuances (written in Traditional Chinese). Emphasize 'Wok Hei' and freshness.",
}

def get_llm(api_key: str, temperature: float = 0.0):
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        temperature=temperature,
    )

def remove_unnecessary_parts(text_list: List[MenuItem], api_key: str) -> List[MenuItem]:
    """1件ずつ不要部分削除を行い、結果をMenuItemのリストで返す"""
    llm = get_llm(api_key)
    # chain = cleanup_prompt | llm | output_parser # 旧実装
    # UsageMetadataを取得するために chain を分割実行する
    
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
            
            # 手動でChainを実行してMetadataを抜く
            formatted_prompt = cleanup_prompt.format_prompt(original_text=json.dumps(input_text, ensure_ascii=False))
            response = llm.invoke(formatted_prompt)
            
            # ログ記録
            if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
                usage = response.response_metadata["token_usage"]
                prompt_tokens = usage.get("prompt_tokens", 0) or usage.get("total_tokens", 0) # Fallback if needed
                completion_tokens = usage.get("completion_tokens", 0)
                # Gemini 2.5 Flashは response_metadata の構造が少し違う場合があるが、
                # langchain-google-genai では通常 'token_usage': {'prompt_tokens': X, 'completion_tokens': Y, 'total_tokens': Z}
                log_api_usage("cleanup_ja", llm.model, prompt_tokens, completion_tokens)
            
            parsed_output = output_parser.parse(response.content)
            
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

def translate_japanese_to_english(menu_items: List[MenuItem], api_key: str, persona: str = "標準 (丁寧)") -> List[MenuItem]:
    """日本語のMenuItemリストを英語に翻訳し、結果をMenuItemのリストで返す"""
    llm = get_llm(api_key)
    
    # 英語翻訳用プロンプトにもペルソナ適用
    ja_to_en_template_persona = """
    外国人観光客向けに、以下の日本語メニューを自然な英語に翻訳してください。
    
    {persona_instruction}
    
    {format_instructions}
    
    【日本語】
    {cleaned_japanese_text}
    
    【英語訳】
    """
    
    ja_to_en_prompt_persona = PromptTemplate(
        input_variables=["cleaned_japanese_text", "persona_instruction"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
        template=ja_to_en_template_persona
    )

    # chain = ja_to_en_prompt_persona | llm | output_parser
    
    results = []
    progress_text = "🔤 英語翻訳"
    my_bar = st.progress(0, text=progress_text)
    total_items = len(menu_items)
    
    persona_instruction = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["標準 (丁寧)"])

    for i, menu_item in enumerate(menu_items, 1):
        try:
            input_text = {
                "menu_title": menu_item.menu_title,
                "menu_content": menu_item.menu_content
            }
            
            formatted_prompt = ja_to_en_prompt_persona.format_prompt(
                cleaned_japanese_text=json.dumps(input_text, ensure_ascii=False),
                persona_instruction=persona_instruction
            )
            response = llm.invoke(formatted_prompt)

            # ログ記録
            if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
                usage = response.response_metadata["token_usage"]
                log_api_usage("trans_en", llm.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

            parsed_output = output_parser.parse(response.content)
            
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

async def translate_english_to_many_async(menu_items: List[MenuItem], target_languages: Dict[str, List[MenuItem]], api_key: str, persona: str = "標準 (丁寧)") -> Dict[str, List[MenuItem]]:
    """英語から指定言語への翻訳を非同期で並列実行 (S1-04 Transcreation Engine)"""
    llm = get_llm(api_key)
    
    # --- S1-04 Transcreation Prompt Template ---
    transcreation_template = """
    [ROLE]
    You are a transcreation copywriter for restaurant menus.
    Your voice MUST match the Persona below.

    [PERSONA]
    - Language: {target_language}
    - Speaker: {persona_role}
    - Tone: {persona_tone}
    - Forbidden: {persona_forbidden}

    [INPUT]
    - Item name (JP): {name_ja}
    - Item description (JP): {desc_ja}
    - Context: {persona}

    [OUTPUT RULES]
    1) Title format: "{Localized name}" (Keep it native script only unless specified)
    2) Body: ~18 seconds silent reading (3-beat structure: Texture/Ratio -> How to Eat -> Pairing).
    3) No medical/health claims. No “guarantee”. No unverifiable origin claims.
    4) Be specific without inventing facts. If unknown, phrase as suggestion, not assertion.
    5) JSON Output ONLY.

    [DELIVER]
    Return JSON:
    {{
      "name": "...",
      "description": "...",
      "pairing": "..."
    }}
    """
    
    transcreation_prompt = PromptTemplate(
        input_variables=["target_language", "persona_role", "persona_tone", "persona_forbidden", "name_ja", "desc_ja", "persona"],
        template=transcreation_template
    )

    from .personas import PERSONA_DEFINITIONS, DEFAULT_QC_RULES
    from .models import MenuItem

    async def verify_quality(original_input: dict, generated_output: dict, lang: str) -> Tuple[bool, str]:
        """S1-06 QC Audit"""
        qc_prompt = f"""
        Act as a Quality Control Auditor for restaurant menu translations.
        
        [Rules]
        {DEFAULT_QC_RULES}
        
        [Source (JP)]
        Name: {original_input['menu_title']}
        Desc: {original_input['menu_content']}
        
        [Generated ({lang})]
        Name: {generated_output.get('name', 'N/A')}
        Desc: {generated_output.get('description', 'N/A')}
        Pairing: {generated_output.get('pairing', 'N/A')}
        
        Evaluate PASS or FAIL. If FAIL, provide brief reason.
        Format: "PASS" or "FAIL: [Reason]"
        """
        try:
            res = await llm.ainvoke(qc_prompt)
            content = res.content.strip()
            
            # Log QC Cost
            if hasattr(res, "response_metadata") and "token_usage" in res.response_metadata:
                usage = res.response_metadata["token_usage"]
                log_api_cost(f"QC_{lang}", llm.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

            if content.upper().startswith("PASS"):
                return True, ""
            return False, content
        except Exception as e:
            print(f"QC Error: {e}")
            return True, "" # Fail open

    async def translate_with_retry(input_dict: dict, lang: str, max_retries: int = 1) -> dict:
        # Get Persona Data (S1-03)
        persona_def = PERSONA_DEFINITIONS.get(lang, {
            "role": "Professional Translator",
            "tone": "Polite, accurate.",
            "forbidden": "Mistranslations",
            "keywords": []
        })

        for attempt in range(max_retries):
            # 1. Generate
            formatted_prompt = transcreation_prompt.format_prompt(
                target_language=lang,
                persona_role=persona_def["role"],
                persona_tone=persona_def["tone"],
                persona_forbidden=persona_def["forbidden"],
                name_ja=input_dict["menu_title"],
                desc_ja=input_dict["menu_content"],
                persona=persona # Extra context
            )
            
            try:
                response = await llm.ainvoke(formatted_prompt)
                
                # Log Gen Cost
                if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
                    usage = response.response_metadata["token_usage"]
                    log_api_cost(f"trans_{lang}", llm.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

                # Parse JSON
                parsed = output_parser.parse(response.content)
                
                # Normalize keys just in case
                if "menu_title" in parsed and "name" not in parsed:
                    parsed["name"] = parsed["menu_title"]
                if "menu_content" in parsed and "description" not in parsed:
                    parsed["description"] = parsed["menu_content"]
                
                # 2. Quality Control (QC)
                is_pass, reason = await verify_quality(input_dict, parsed, lang)
                if is_pass:
                    return parsed
                else:
                    # Retry logic could be improved by injecting reason, but implies simple retry for now
                    continue 

            except Exception as e:
                if attempt == max_retries - 1:
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