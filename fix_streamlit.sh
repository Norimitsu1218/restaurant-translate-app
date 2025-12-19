#!/usr/bin/env bash
set -euo pipefail

# repo root check
if [ ! -f "main.py" ] || [ ! -d "src" ]; then
  echo "[NG] repo root ではありません。main.py があるディレクトリで実行してください。"
  echo "     例) cd ~/projects/restaurant-translate-app"
  exit 1
fi

echo "[1/2] Patch src/st_auth.py (logout_button key arg)"
python3 - <<'PY'
from pathlib import Path
import re

p = Path("src/st_auth.py")
txt = p.read_text(encoding="utf-8")

# logout_button(key="logout_btn") などを logout_button() に
txt2 = re.sub(r'logout_button\([^)]*key\s*=\s*["\']logout_btn["\'][^)]*\)', "logout_button()", txt)

# それでも変わらない場合は、logout_button(…) 行を互換呼び出しにする（保険）
if txt2 == txt:
    txt2 = re.sub(
        r'(?m)^\s*logout_button\((.*)\)\s*$',
        'try:\n    logout_button()\nexcept TypeError:\n    logout_button(\\1)',
        txt,
    )

p.write_text(txt2, encoding="utf-8")
print("[OK] patched:", p)
PY

echo "[2/2] Patch src/langchain_utils.py (StructuredOutputParser import)"
python3 - <<'PY'
from pathlib import Path
import re

p = Path("src/langchain_utils.py")
txt = p.read_text(encoding="utf-8")

# 旧: from langchain.output_parsers import ...
# 新: langchain_classic を優先（ログ上 langchain-classic==1.0.0 が入っているため）
txt2 = re.sub(
    r'(?m)^\s*from\s+langchain\.output_parsers\s+import\s+StructuredOutputParser,\s*ResponseSchema\s*$',
    'from langchain_classic.output_parsers import StructuredOutputParser, ResponseSchema',
    txt
)

# それでも変わらないなら、冒頭付近の import を強制差し替え（安全側）
if txt2 == txt:
    # 「StructuredOutputParser, ResponseSchema」を含む行を全部 classic へ寄せる
    txt2 = re.sub(
        r'(?m)^\s*from\s+langchain(?:_core)?(?:\.output_parsers(?:\.\w+)?)?\s+import\s+StructuredOutputParser,\s*ResponseSchema.*$',
        'from langchain_classic.output_parsers import StructuredOutputParser, ResponseSchema',
        txt,
    )

p.write_text(txt2, encoding="utf-8")
print("[OK] patched:", p)
PY

git add src/st_auth.py src/langchain_utils.py
git commit -m "Fix: logout_button arg + use langchain_classic output parsers" || true
git push
echo "[DONE] pushed."
