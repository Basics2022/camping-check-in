import streamlit as st
import json
import pyrebase
from people_page import people_page
from checkin_page import checkin_page  # if you separate that page too
from admin_page import admin_page

#> App initialization
firebase_config = json.loads(st.secrets["firebase"]['firebase_config'])
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

#> Admin
admin_info = json.loads(st.secrets["admin"]["admin_params"])

# --- Page Routing ---
def login():
    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.success("Logged in.")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# --- Dashboard ---
def dashboard():
    st.sidebar.title("Menu")
    if ( st.session_state.user['email'] in admin_info['emails'] ):
        choice = st.sidebar.radio("Go to", ["Admin", "👤 People", "📝 Check-in", "🔓 Logout"])
    else:
        choice = st.sidebar.radio("Go to", ["👤 People", "📝 Check-in", "🔓 Logout"])

    if choice == "Admin":
        admin_page(st.session_state.user)
    elif choice == "👤 People":
        people_page(st.session_state.user)
    elif choice == "📝 Check-in":
        checkin_page(st.session_state.user)
    elif choice == "🔓 Logout":
        del st.session_state.user
        st.rerun()

# --- Main App ---
def main():
    st.set_page_config(page_title="Camping Check-In", layout="centered")
    if "user" not in st.session_state:
        login()
    else:
        dashboard()

if __name__ == "__main__":
    main()

