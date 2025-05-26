import streamlit as st
from firebase_admin import auth
import pyrebase
from people_page import people_page
from checkin_page import checkin_page  # if you separate that page too

from firebase_config import firebase_config, EMAIL_ADDRESS, EMAIL_PASSWORD

#> Initialize app with Firebase configuration
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

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

def dashboard():
    st.sidebar.title("Menu")
    choice = st.sidebar.radio("Go to", ["👤 People", "📝 Check-in", "🔓 Logout"])

    if choice == "👤 People":
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

