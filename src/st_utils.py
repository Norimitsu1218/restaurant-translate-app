import streamlit as st

# サイドバーでログイン
def login():
    supabase = st.session_state["supabase"]
    user_name = st.text_input("ユーザ名", value="")
    password = st.text_input("パスワード", value="", type="password")

    if st.button("🚪 ログイン"):
        if user_name and password:
            dummy_email = f"{user_name}@dummy.mail"
            try:
                # ログイン処理
                result = supabase.auth.sign_in_with_password({
                    "email": dummy_email,
                    "password": password
                })
                print("ログインに成功")
                st.success("ログインに成功しました！")
                st.session_state["is_login"] = True
                st.session_state["session"] = result.session
                st.rerun()
            except Exception as e:
                st.error(f"ログインに失敗しました: {e}")
                st.session_state["is_login"] = False
                st.session_state["session"] = None

def logout():
    if st.button("🚙 ログアウト"):
        st.session_state["is_login"] = False
        st.session_state["session"] = None
        st.rerun()

def get_gemini_api_key():
    """
    supabaseからgemini_api_keyを取得する
    """
    supabase = st.session_state["supabase"]
    try:
        # app_data テーブルから gemini_api_key を取得
        response = supabase.table("app_data").select("gemini_api_key").eq("id", 1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("gemini_api_key", "")
        else:
            return ""
    except Exception as e:
        st.error(f"APIキーの取得中にエラーが発生しました: {e}")
        return ""

def set_gemini_api_key(new_key:str):
    """
    supabaseにgemini_api_keyを設定する
    """
    supabase = st.session_state["supabase"]
    try:
        supabase.table("app_data").update({"gemini_api_key": new_key}).eq("id", 1).execute()
        st.success("Gemini APIキーを更新しました")
    except Exception as e:
        st.error(f"Gemini APIキーの更新中にエラーが発生しました: {e}")