import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# Relative path to this file
ROOT = Path(__file__).parent

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def render_mario_ui(
    api_base: str,
    demo_session_id: str,
    default_plan: int = 39,
    preview_preset: str = "friendly_nations",
    height: int = 900
):
    """
    Renders the Mario UI component by injecting CSS/JS into the shell HTML.
    """
    # 1. Read Shell
    shell = read_file(ROOT / "mario_shell.html")

    # 2. Read CSS (Concatenate)
    css_files = ["mario_base.css", "mario_card.css", "mario_buttons.css", "mario_toast.css"]
    css_content = "\n".join([read_file(ROOT / "css" / f) for f in css_files])

    # 3. Read JS (Concatenate)
    # Order matters: State -> API -> Render -> Events -> Boot
    js_files = ["mario_state.js", "mario_api.js", "mario_render.js", "mario_events.js", "mario_boot.js"]
    js_content = "\n".join([read_file(ROOT / "js" / f) for f in js_files])

    # 4. Config Injection
    config = {
        "apiBase": api_base,
        "demoSessionId": demo_session_id,
        "defaultPlan": default_plan,
        "previewPreset": preview_preset
    }
    
    # 5. Inject into Shell
    # We inject styles into head and script at bottom
    # Note: We simply append <style> and <script> tags for simplicity
    
    final_html = f"""
    <!doctype html>
    <html lang="ja">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
        <style>
          {css_content}
        </style>
      </head>
      <body>
        {shell}
        
        <script>
          window.__TONOSAMA__ = {json.dumps(config, ensure_ascii=False)};
        </script>
        <script>
          {js_content}
        </script>
      </body>
    </html>
    """

    # 6. Render
    components.html(final_html, height=height, scrolling=True)
