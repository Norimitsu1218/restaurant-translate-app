from supabase import create_client
import streamlit as st
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Supabaseクライアントの初期化関数
def init_supabase():
    # 1. st.secrets から取得を試みる (Streamlit Cloud用)
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
    except (FileNotFoundError, KeyError):
         # 2. 環境変数から取得を試みる (ローカル開発用)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("Supabaseの認証情報が設定されていません。Streamlit CloudのSecretsまたは.envファイルを確認してください。")
        st.stop()
    
    # Supabaseクライアントを作成
    supabase = create_client(supabase_url, supabase_key)
    return supabase

# Streamlitのセッションステートにクライアントを保存
def get_supabase():
    if 'supabase' not in st.session_state:
        st.session_state.supabase = init_supabase()
    return st.session_state.supabase
