import firebase_admin
import json

import streamlit as st
from firebase_admin import credentials, firestore, storage
# from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import uuid
import os

# FIREBASE_SERVICE_ACCOUNT_JSON  = '.credentials/camping-check-in-firebase-key.json'   # 'firebase_service_account.json'
# GOOGLE_SHEETS_CREDENTIALS_JSON = '.credentials/camping-check-in-sheets-key.json'     # 'google_sheets_credentials.json'

service_account_info = json.loads(st.secrets["firebase-key"]["service_account_key"])

# --- Firebase Initialization ---
if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_info) # FIREBASE_SERVICE_ACCOUNT_JSON)
    firebase_admin.initialize_app(cred, {
        "storageBucket": "camping-check-in.firebasestorage.app",
    })

db = firestore.client()
bucket = storage.bucket()

# --- Google Sheets Initialization ---
# #> old
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
# creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS_JSON, scope)
# #> new
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
gs_creds_info = json.loads(st.secrets["google-sheets"]["credentials_json"])
creds = Credentials.from_service_account_info(gs_creds_info, scopes=scope)
client = gspread.authorize(creds)

# print('debug -------------------- ')
# print(gs_creds_info['client_email'])
# print(creds.scopes)
# print('debug -------------------- ')

sheet = client.open("CampingPeople").worksheet("People")  # Ensure this sheet/tab exists


# --- Upload PDF to Firebase Storage ---
def upload_pdf(user_id, file, filename):
    blob = bucket.blob(f"people_docs/{user_id}/{filename}")
    blob.upload_from_file(file, content_type="application/pdf")
    blob.make_public()
    return blob.public_url


# --- Add or Update Person ---
def get_people(user_id):
    docs = db.collection("people").where("user_id.localId", "==", user_id['localId']).stream()
    people = []
    for doc in docs:
        person = doc.to_dict()
        person["id"] = doc.id
        people.append(person)
    return people

def save_person(user_id, name, surname, dob, id_code, file, place_id):

    doc_id = str(uuid.uuid4())
    file_url = ""

    if file:
        blob = bucket.blob(f"id_docs/{doc_id}.pdf")
        blob.upload_from_file(file, content_type="application/pdf")
        file_url = blob.public_url

    person_data = {
        "user_id": user_id,
        "name": name,
        "surname": surname,
        "dob": dob,
        "id_code": id_code,
        "place_id": place_id,
        "file_url": file_url,
        "timestamp": datetime.now().isoformat()
    }

    db.collection("people").document(doc_id).set(person_data)

    sheet.append_row([user_id['localId'], name, surname, dob, id_code, place_id, file_url, person_data["timestamp"]])

def delete_person(user_id, person_id):
    db.collection("people").document(person_id).delete()
    # Optional: no Google Sheets delete unless syncing

def update_person(user_id, person_id, updated_fields):
    doc_ref = db.collection("people").document(person_id)
    doc_ref.update(updated_fields)
    # Optional: log update to sheet as an update log

def save_checkin(user_id, people_ids, checkin_date, checkout_date, num_guests, vehicle_plate=""):
    checkin_data = {
        "userId": user_id,
        "peopleIds": people_ids,
        "checkInDate": checkin_date,
        "checkOutDate": checkout_date,
        "numGuests": num_guests,
        "vehiclePlate": vehicle_plate,
        "timestamp": datetime.utcnow(),
    }

    doc_ref = db.collection("checkins").document()
    doc_ref.set(checkin_data)

    # Append to Google Sheet
    row = [
        str(doc_ref.id), user_id, ", ".join(people_ids), checkin_date, 
        checkout_date, num_guests, vehicle_plate,
        str(datetime.utcnow())
    ]
    sheet = client.open("CampingPeople").worksheet("CheckIns")  # tab must exist
    sheet.append_row(row)

