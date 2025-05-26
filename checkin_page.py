import streamlit as st
from person_manager import db, save_checkin

import pandas as pd
from firebase_admin import firestore
from datetime import datetime

import json
import smtplib
from email.mime.text import MIMEText


#> Read smtp parameters from .streamlit/secrets.toml
smtp_params = json.loads(st.secrets["email"]['smtp_params']) 
smtp_server = smtp_params['smtp_server']
smtp_port   = smtp_params['smtp_port']
smtp_user   = smtp_params['smtp_user']
smtp_pswd   = smtp_params['smtp_password']


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
            "People": ", ".join(data.get("peopleIds", [])),
            "checkInDate": data.get("checkInDate"),
            "checkOutDate": data.get("checkOutDate"),
            # "Place": data.get("place_id", "")
        })

    if checkin_data:
        df = pd.DataFrame(checkin_data)
        df = df.sort_values(by="Date", ascending=False)
        st.subheader("🕓 Latest Check-ins")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent check-ins found.")


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
    st.title("📝 Check-In")

    user_id = user["localId"]

    # Fetch people linked to user
    st.subheader("➕ New Check-in")
    people_ref = db.collection("people").where("user_id.localId", "==", user_id)
    people_docs = people_ref.stream()
    people_list = [(doc.id, f"{p['name']} {p['surname']}") for doc in people_docs if (p := doc.to_dict())]

    if not people_list:
        st.warning("You must register people before check-in.")
        return

    with st.form("checkin_form"):
        selected_ids = st.multiselect(
                "Select Guests", 
                options=[pid for pid, _ in people_list],
                default=[pid for pid, _ in people_list],
                format_func=lambda x: dict(people_list)[x])
        checkin_date = st.date_input("Check-In Date")
        checkout_date = st.date_input("Check-Out Date")
        num_guests = st.number_input(
                "Number of Guests", min_value=0, step=1, value=1)
        vehicle_plate = st.text_input("Vehicle Plate (optional)")

        submitted = st.form_submit_button("Submit Check-In")

        if submitted:
            if not selected_ids:
                st.error("Please select at least one guest.")
            else:
                save_checkin(user_id, selected_ids, str(checkin_date), str(checkout_date), num_guests, vehicle_plate)
                st.success("✅ Check-in recorded successfully.")

                #> Send emails: confirmation, police, tourism agency,...
                people_names = [ p[1] for p in people_list if p[0] in selected_ids ]
                confirmation_data = {'people': people_names, 'numGuests': num_guests, 'checkInDate': str(checkin_date), 'checkOutDate': str(checkout_date)}
                send_email_confirmation(st.session_state.user['email'], confirmation_data)

    #> Show recent check-ins
    show_latest_checkins(user_id)

