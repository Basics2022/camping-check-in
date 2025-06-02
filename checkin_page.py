import streamlit as st
from person_manager import db, save_checkin, get_people_gs, save_checkin_gs
from checkin_manager import update_checkin

import pandas as pd
from firebase_admin import firestore
from datetime import datetime

import json
import smtplib
from email.mime.text import MIMEText

from google.oauth2.service_account import Credentials
import gspread

#> Connect to GSpreadsheet on the Drive
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
gs_creds_info = json.loads(st.secrets["google-sheets"]["credentials_json"])
creds = Credentials.from_service_account_info(gs_creds_info, scopes=scope)
client = gspread.authorize(creds)

sh_ci_old    = client.open("CampingPeople").worksheet("CheckIns")
sh_ci        = client.open("CampingDB").worksheet("CheckIns")


#> Read smtp parameters from .streamlit/secrets.toml
smtp_params = json.loads(st.secrets["email"]['smtp_params']) 
smtp_server = smtp_params['smtp_server']
smtp_port   = smtp_params['smtp_port']
smtp_user   = smtp_params['smtp_user']
smtp_pswd   = smtp_params['smtp_password']


db = firestore.client()

def show_latest_checkins_gs(user_id):
    """  """
    #> Piazzola hardcoded here **todo** make it "global"
    resids_list = get_people_gs(user_id,)
    pz = resids_list[0]['Piazzola']

    #> Get checkins of the user
    rows = sh_ci.get_all_records()
    checkin_data = [row for row in rows if row['Piazzola'] == pz ] 

    #> Show details of the latest N checkins
    st.subheader("🕓 Latest Check-ins")
    if checkin_data:
        df = pd.DataFrame(checkin_data)

        cols_to_remove = ['checkin_id', 'userId', 'Piazzola', 'numGuests', 'peopleIds', 'guestsIds' ]
        cols = [col for col in df.columns if col not in cols_to_remove ]
        df = df[cols].sort_values(by="checkInDate", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent check-in found.")


def show_latest_checkins(user_id):
    """ 
    Show a table collecting the latest checkins at the end of the page
    """
    db = firestore.client()
    checkins_ref = db.collection("checkins").where("userId", "==", user_id)
    docs = checkins_ref.stream()

    checkin_data = []
    for doc in docs:
        data = doc.to_dict()
        checkin_data.append({
            "Date": data.get("timestamp", ""), # [:16].replace("T", " "),
            "Status": data.get("status"),
            "People": ", ".join(data.get("peopleIds", [])),
            "checkInDate": data.get("checkInDate"),
            "checkOutDate": data.get("checkOutDate"),
            # "Place": data.get("place_id", "")
        })

    st.subheader("🕓 Latest Check-ins")
    if checkin_data:
        df = pd.DataFrame(checkin_data)
        df = df.sort_values(by="Date", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent check-in found.")


def send_email_confirmation(to_email, checkin_data):
    """  """
    # 0. basic plain text version
    msg = MIMEText(f"Check-in confirmation:\nDate-In: {checkin_data['checkInDate']}\nDate-Out: {checkin_data['checkOutDate']}\nPeople: {checkin_data['people']}\nGuests: {checkin_data['numGuests']}")
    # # 1. html formatting
    # html = """\
    # <html>
    #   <body>
    #     <p>
    #       <b>Check-In Confirmation</b><br>
    #     </p>
    #   </body>
    # </html>
    # """

    msg["Subject"] = f"Camping Monte Rosa. Check-In {checkin_data['checkInDate']}-{checkin_data['checkOutDate']}"
    msg["From"] = smtp_user
    msg["To"] = to_email

    print()
    print("Debug, in send_email_confirmation()")
    print("msg: \n", msg)
    print()

    with smtplib.SMTP_SSL(smtp_server, 465) as server:
        server.login(smtp_user, smtp_pswd)
        server.send_message(msg)



def send_email_police(to_email, checkin_data):
    """  """


def send_email_tourism(to_email, checkin_data):
    """  """


def checkin_page(user):
    """
    Check-in page, layout and some functionalities
    - check-in form
    - show latest checkins

    **todo**: clean the implementation, keeping layout and functions apart

    """
    #> Check-In page -------------------------------------------------
    st.title("📝 Check-In")

    user_id = user.copy()

    #> Add new check-in ----------------------------------------------
    st.subheader("➕ New Check-in")
    # #> read from Firebase db
    # people_ref = db.collection("people").where("user_id.localId", "==", user_id)
    # people_docs = people_ref.stream()
    # people_list = [(doc.id, f"{p['name']} {p['surname']}") for doc in people_docs if (p := doc.to_dict())]

    #> Get people list from GSpreadsheet, both from residentials and guests
    resids_list = get_people_gs(user_id,)
    guests_list = get_people_gs(user_id, people_type="guests")

    people_list = resids_list + guests_list

    # pz, somehow "harcoded" here. Need to take it as a global
    # parameter of the user. **todo** move outside
    pz = people_list[0]['Piazzola']
    # st.write(f"In checkin page, pz: {pz}")

    st.write(f"people_list:\n{people_list}")

    if not people_list:
        st.warning("You must register people before check-in.")
        return

    with st.form("checkin_form"):
        people_names = st.multiselect(
                "People", 
                options = [ p['Nome']+' '+p['Cognome'] for p in resids_list],
                default = [ p['Nome']+' '+p['Cognome'] for p in resids_list],
        )
        guests_names = st.multiselect(
                "Guests", 
                options = [ p['Nome']+' '+p['Cognome'] for p in guests_list],
                default = [ p['Nome']+' '+p['Cognome'] for p in guests_list],
        )
        checkin_date = st.date_input("Check-In Date")
        checkout_date = st.date_input("Check-Out Date")
        num_guests = 0
        # num_guests = st.number_input(
        #         "Number of Guests", min_value=0, step=1, value=0)
        message = st.text_input("Message")

        submitted = st.form_submit_button("Submit Check-In")

        resids_name_to_id = { p['Nome'] + ' ' + p['Cognome']: str(p['Id']) for p in resids_list }
        guests_name_to_id = { p['Nome'] + ' ' + p['Cognome']: str(p['Id']) for p in guests_list }

        people_ids = [ resids_name_to_id[name] for name in people_names if name in resids_name_to_id ]
        guests_ids = [ guests_name_to_id[name] for name in guests_names if name in guests_name_to_id ]

        # Wrong! Preserving resids_list order
        # people_ids = [ str(p['Id']) for p in resids_list if p['Nome']+' '+p['Cognome'] in people_names ]
        # guests_ids = [ str(p['Id']) for p in guests_list if p['Nome']+' '+p['Cognome'] in guests_names ]

        # st.write(f"people_ids: {people_ids}")
        # st.write(f"guests_ids: {guests_ids}")

        # # people_ids = ', '.join(people_ids)
        # # guests_ids = ', '.join(guests_ids)

        # st.write(f"people_ids: {people_ids}")
        # st.write(f"guests_ids: {guests_ids}")

        if submitted:
            if not people_names:
                st.error("Please select at least one person.")
            else:
                save_checkin_gs(user_id, pz,
                        people_names, people_ids, 
                        guests_names, guests_ids, 
                        str(checkin_date), str(checkout_date), num_guests, message, status="pending"
                )
                # save_checkin(user_id, selected_ids, str(checkin_date), str(checkout_date), num_guests, message, status="pending")
                st.success("✅ Check-in recorded successfully.")

                #> Send emails: confirmation, police, tourism agency...
                # moved to admin_page. Email sent after a check-in is
                # accepted
                # people_names = [ p[1] for p in people_list if p[0] in selected_ids ]
                # confirmation_data = {'people': people_names, 'numGuests': num_guests, 'checkInDate': str(checkin_date), 'checkOutDate': str(checkout_date)}
                # send_email_confirmation(st.session_state.user['email'], confirmation_data)

    #> Show recent check-ins -----------------------------------------
    show_latest_checkins_gs(user_id)

