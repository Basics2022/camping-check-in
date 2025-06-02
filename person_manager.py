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
scope = [
    "https://spreadsheets.google.com/feeds", 
    "https://www.googleapis.com/auth/drive", 
    "https://www.googleapis.com/auth/spreadsheets"
]
gs_creds_info = json.loads(st.secrets["google-sheets"]["credentials_json"])
creds = Credentials.from_service_account_info(gs_creds_info, scopes=scope)
client = gspread.authorize(creds)

# print('debug -------------------- ')
# print(gs_creds_info['client_email'])
# print(creds.scopes)
# print('debug -------------------- ')

sheet = client.open("CampingPeople").worksheet("People")  # Ensure this sheet/tab exists

sh           = client.open("CampingDB").worksheet("StanzialiContratti")
sh_ppl       = client.open("CampingDB").worksheet("StanzialiPersone")
sh_ppl_guest = client.open("CampingDB").worksheet("OspitiPersone")

# --- Upload PDF to Firebase Storage ---
def upload_pdf(user_id, file, filename):
    blob = bucket.blob(f"people_docs/{user_id}/{filename}")
    blob.upload_from_file(file, content_type="application/pdf")
    blob.make_public()
    return blob.public_url


# --- Add or Update Person ---
def get_people(user_id):
    """ Get people from Firebase db """
    docs = db.collection("people").where("user_id.localId", "==", user_id['localId']).stream()
    people = []
    for doc in docs:
        person = doc.to_dict()
        person["id"] = doc.id
        people.append(person)
    return people

def get_people_gs(user_id, people_type="people"):
    """ Get people from Google spreadsheet """
    # st.write(f"In get_people_gs, user_id: {user_id}")

    #> StanzialiContatti: from user.email to pz = Piazzola
    rows = sh.get_all_records()
    filtered = [row for row in rows if row['user_id'] == user_id['localId']]

    # **todo**: check that filtered is a 1-element list
    pz = filtered[0]['Piazzola']
    #> StanzialiPersone: get people where Piazzola == pz
    if ( people_type == 'guests' ):
        ppl_list = [row for row in sh_ppl_guest.get_all_records() if row['Piazzola'] == pz]
    else:
        ppl_list = [row for row in sh_ppl.get_all_records() if row['Piazzola'] == pz]

    # debug ---
    # st.write(f"user_id['localId']: {user_id['localId']}")
    # st.write(f"filtered:\n {filtered}")
    # st.write(f"ppl_list:\n {ppl_list}")

    return ppl_list


def save_guest(guest_params):
    """  """
    guest_params['dob'] = guest_params['dob'].isoformat()
    sh_ppl_guest.append_row(list(guest_params.values()))


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
    # **todo**

def update_person(user_id, person_id, updated_fields):
    doc_ref = db.collection("people").document(person_id)
    doc_ref.update(updated_fields)
    # Optional: log update to sheet as an update log
    # **todo**

def save_checkin_gs(user_id, pz, people_names, people_ids, guests_names, guests_ids, checkin_date, checkout_date, num_guests, vehicle_plate="", status="pending"):
    checkin_data = {
        "userId": user_id,
        "peopleNames": people_names,
        "peopleIds"  : people_ids,
        "guestsName" : guests_names,
        "guestsIds"  : guests_ids,
        "checkInDate": checkin_date,
        "checkOutDate": checkout_date,
        "numGuests": num_guests,
        "vehiclePlate": vehicle_plate,
        "timestamp": datetime.utcnow(),
        "status": status
    }

    # Append to Google Sheet
    row = [
        "", user_id['localId'], pz,
        ", ".join(people_names),
        ", ".join(people_ids), 
        ", ".join(guests_names),
        ", ".join(guests_ids), 
        checkin_date, checkout_date, num_guests, vehicle_plate,
        str(datetime.utcnow()), status
    ]

    sheet = client.open("CampingDB").worksheet("CheckIns")  # tab must exist
    sheet.append_row(row)


def save_checkin(user_id, people_ids, checkin_date, checkout_date, num_guests, vehicle_plate="", status="pending"):
    checkin_data = {
        "userId": user_id,
        "peopleIds": people_ids,
        "checkInDate": checkin_date,
        "checkOutDate": checkout_date,
        "numGuests": num_guests,
        "vehiclePlate": vehicle_plate,
        "timestamp": datetime.utcnow(),
        "status": status
    }

    # doc_ref = db.collection("checkins").document()
    # doc_ref.set(checkin_data)

    # Append to Google Sheet
    row = [
        "", user_id['localId'], ", ".join(people_ids), checkin_date, 
        checkout_date, num_guests, vehicle_plate,
        str(datetime.utcnow()), status
    ]
    # row = [
    #     str(doc_ref.id), user_id, ", ".join(people_ids), checkin_date, 
    #     checkout_date, num_guests, vehicle_plate,
    #     str(datetime.utcnow()), status
    # ]

    sheet = client.open("CampingPeople").worksheet("CheckIns")  # tab must exist
    sheet.append_row(row)

