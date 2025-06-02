import firebase_admin
from firebase_admin import credentials, firestore, storage
# from google.oauth2 import service_account
# from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import uuid
import os

# --- Firebase Initialization ---
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": "camping-check-in.firebasestorage.app",
    })

db = firestore.client()
bucket = storage.bucket()

# --- Google Sheets Initialization ---
# scope = ["https://www.googleapis.com/auth/spreadsheets"]
# credentials = Credentials.from_service_account_file("google_sheets_credentials.json", scopes=scope)
# gc = gspread.authorize(credentials)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("CampingPeople").worksheet("People")  # Ensure this sheet/tab exists


# --- Upload PDF to Firebase Storage ---
def upload_pdf(user_id, file, filename):
    blob = bucket.blob(f"people_docs/{user_id}/{filename}")
    blob.upload_from_file(file, content_type="application/pdf")
    blob.make_public()
    return blob.public_url


# --- Add or Update Person ---
def save_person(data, file=None):
    person_id = data.get("id") or str(uuid.uuid4())
    is_new = "id" not in data

    doc_ref = db.collection("people").document(person_id)

    if file:
        pdf_url = upload_pdf(data["userId"], file, f"{person_id}.pdf")
        data["id_doc_url"] = pdf_url

    data["updated_at"] = datetime.utcnow()
    if is_new:
        data["created_at"] = data["updated_at"]

    data["update_pending"] = not is_new  # Edits are flagged

    doc_ref.set(data)

    # Google Sheets Sync
    row = [
        person_id, data["userId"], data["name"], data["surname"],
        data["dob"], data["id_code"], data.get("id_doc_url", ""),
        str(data["updated_at"]), "Pending" if data["update_pending"] else "Approved"
    ]
    if is_new:
        sheet.append_row(row)
    else:
        # Find and update existing row
        records = sheet.get_all_records()
        for i, r in enumerate(records):
            if r["person_id"] == person_id:
                sheet.update(f"A{i+2}:I{i+2}", [row])
                break

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

