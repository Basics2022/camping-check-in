import streamlit as st
from datetime import date
import firebase_admin
from firebase_admin import credentials, firestore, auth as fb_auth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from uuid import uuid4

# --- Firebase Setup ---
if not firebase_admin._apps:
    firebase_cred = credentials.Certificate("credentials/camping-check-in-firebase-key.json")
    firebase_admin.initialize_app(firebase_cred)

db = firestore.client()

# --- Optional Google Sheets Setup ---
use_google_sheets = True
if use_google_sheets:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials/camping-check-in-sheets-key.json", scope)
    gs_client = gspread.authorize(creds)
    sheet = gs_client.open("Camping Checkins").sheet1

# --- Streamlit UI ---
st.title("🏕️ Guest Check-In")

with st.form("checkin_form"):
    name = st.text_input("Full Name")
    id_number = st.text_input("ID / Passport Number")
    check_in_date = st.date_input("Check-In Date", value=date.today())
    num_guests = st.number_input("Number of Guests", min_value=1, value=1)
    vehicle_plate = st.text_input("Vehicle Plate (optional)")

    submitted = st.form_submit_button("Check In")

if submitted:
    user_id = "guest_" + str(uuid4())  # Fake auth for now — you can add real login later

    data = {
        "name": name,
        "idNumber": id_number,
        "checkInDate": str(check_in_date),
        "numGuests": num_guests,
        "vehiclePlate": vehicle_plate,
        "userId": user_id,
        "timestamp": firestore.SERVER_TIMESTAMP,
    }

    # Save to Firebase
    db.collection("checkins").add(data)

    # Save to Google Sheets (optional)
    if use_google_sheets:
        row = [name, id_number, str(check_in_date), num_guests, vehicle_plate, user_id]
        sheet.append_row(row)

    st.success("✅ Check-in submitted!")
