#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "main.py" ] || [ ! -f "src/langchain_utils.py" ]; then
  echo "[NG] repo root ではありません。main.py があるディレクトリで実行してください。"
  exit 1
fi

python3 - <<'PY'
from pathlib import Path
import re

p = Path("src/langchain_utils.py")
txt = p.read_text(encoding="utf-8")

m = re.search(r"(?m)^#\s*スキーマの定義\s*$", txt)
if not m:
    raise SystemExit("[NG] src/langchain_utils.py に「# スキーマの定義」が見つかりません。")

tail = txt[m.start():]

head_lines = [
"from __future__ import annotations",
"",
"from typing import List, Dict, Tuple, Any",
"import asyncio",
"import json",
"import re",
"from langchain_core.prompts import PromptTemplate",
"from langchain_google_genai import ChatGoogleGenerativeAI",
"import streamlit as st",
"",
"from .models import MenuItem",
"",
"# LangChain v1系で output_parsers の場所が割れるので、ここは classic に固定して安定化",
"from langchain_classic.output_parsers import StructuredOutputParser, ResponseSchema",
"",
"",
]

head = "\n".join(head_lines) + "\n"
p.write_text(head + tail, encoding="utf-8")
print("[OK] rewrote header:", p)
PY

# ローカルで即死チェック（ここで行番号が出る）
python3 -m py_compile src/langchain_utils.py

git add src/langchain_utils.py
git commit -m "Fix: langchain_utils header indentation + use langchain_classic parsers" || true
git push
echo "[DONE] pushed."
