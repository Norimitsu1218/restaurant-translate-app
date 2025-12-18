from streamlit_supabase_auth import login_form, logout_button
import os
import dotenv
import streamlit as st
from supabase import Client, create_client

def supabase_auth_widget() -> str:
    # .envファイルの読み込み
    dotenv.load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Supabaseクライアントの作成
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    session = login_form(
        url=SUPABASE_URL,
        apiKey=SUPABASE_KEY,
        providers=[],
    )
    # 未ログインの場合は処理を終了
    if not session:
        st.stop()
    else:
        user_email = session['user']['email']
        user_id = session['user']['id']
        access_token = session['access_token']
        refresh_token = session['refresh_token']
        st.sidebar.write(f"ようこそ {user_email}")
        logout_button(key="logout_btn")