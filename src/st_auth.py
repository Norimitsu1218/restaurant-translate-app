from streamlit_supabase_auth import login_form, logout_button
import os
import dotenv
import streamlit as st
from supabase import Client, create_client

def supabase_auth_widget() -> str:
    # .envファイルの読み込み
    dotenv.load_dotenv()
    
    # 1. st.secrets から取得を試みる
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    except (FileNotFoundError, KeyError):
        # 2. 環境変数から取得を試みる
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase認証エラー: Secretsが設定されていません。")
        st.stop()
    
    # Supabaseクライアントの作成
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 認証ウィジェットをサイドバーの上部に配置
    auth_container = st.sidebar.container()
    with auth_container:
        session = login_form(
            url=SUPABASE_URL,
            apiKey=SUPABASE_KEY,
            providers=[],
        )
        # 未ログインの場合は処理を一旦止める
        if not session:
            st.stop()
        
        user_email = session['user']['email']
        st.write(f"ようこそ {user_email}")
        logout_button(url=SUPABASE_URL, apiKey=SUPABASE_KEY, key="logout_btn")