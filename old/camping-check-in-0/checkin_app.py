import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Firebase config ---
firebase_config = {
  "apiKey": "AIzaSyBIGqUOP10WP_LJdZoDKD1X728JI2oyNSw",
  "authDomain": "camping-check-in.firebaseapp.com",
  "databaseURL": "",
  "projectId": "camping-check-in",
  "storageBucket": "camping-check-in.firebasestorage.app",
  "messagingSenderId": "761291493383",
  "appId": "1:761291493383:web:daa749d9b6adfde39a5aa2",
  "measurementId": "G-K8L78XZ6BL"
};

EMAIL_ADDRESS = "basics.314159@gmail.com"
EMAIL_PASSWORD = "nwwjjluglsbumvtq"

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# --- Firestore init (only once) ---
if not firebase_admin._apps:
    cred = credentials.Certificate("credentials/camping-check-in-firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Google Sheets setup ---
def append_to_sheet(data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/camping-check-in-sheets-key.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Camping Checkins").sheet1
    sheet.append_row(data)

# --- Email sending ---
def send_email(to_email, checkin_data):
    msg = MIMEText(
        f"New Check-In:\nName: {checkin_data['name']}\nGuests: {checkin_data['numGuests']}\nDate: {checkin_data['checkInDate']}"
    )
    msg["Subject"] = "New Guest Check-In"
    msg["From"] = "basics.314159@gmail.com"
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# --- Auth ---
st.title("🏕️ Camping Check-In App")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    auth_mode = st.radio("Login or Register", ["Login", "Register"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Submit"):
        try:
            if auth_mode == "Register":
                user = auth.create_user_with_email_and_password(email, password)
                st.success("Registered successfully. Please log in")
            else:
                user = auth.sign_in_with_email_and_password(email, password)
                st.success("Logged in.")
                st.session_state.user = user
                st.rerun()                     # force re-run after Login
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

# --- Logged in view ---
st.success(f"Welcome, {st.session_state.user['email']}")
user_id = st.session_state.user["localId"]

st.header("📋 Guest Check-In Form")

with st.form("checkin_form"):
    name = st.text_input("Full Name")
    id_number = st.text_input("ID / Passport Number")
    check_in_date = st.date_input("Check-in Date")
    num_guests = st.number_input("Number of Guests", min_value=1, step=1)
    vehicle_plate = st.text_input("Vehicle Plate (optional)")
    submit = st.form_submit_button("Check In")

if submit:
    data = {
        "userId": user_id,
        "name": name,
        "idNumber": id_number,
        "checkInDate": check_in_date.strftime("%Y-%m-%d"),
        "numGuests": int(num_guests),
        "vehiclePlate": vehicle_plate,
        "timestamp": datetime.now().isoformat(),
    }
    db.collection("checkins").add(data)
    try:
        #> Send email to the user
        send_email(st.session_state.user['email'], data)
        # #> send email to the police and/or other address
        # ...
        # append_to_sheet(list(data.values()))
        # send_email("police@example.com", data)  # change to real address
        # st.success("Check-in successful and logged.")
    except Exception as e:
        st.warning(f"Check-in saved, but email/Google Sheet failed: {e}")

# --- Personal dashboard ---
st.header("📂 My Check-Ins")
docs = db.collection("checkins").where("userId", "==", user_id).stream()
for doc in docs:
    item = doc.to_dict()
    st.write(f"- {item['checkInDate']}: {item['name']} ({item['numGuests']} guests)")

# Logout button
if st.button("Logout"):
    st.session_state.user = None
    st.rerun()

