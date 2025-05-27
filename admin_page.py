"""

"""

import streamlit as st
from firebase_admin import firestore
from checkin_page import update_checkin
import pandas as pd

db = firestore.client()

def admin_page(user):
    st.title("Admin")

    #> Get check-in requests
    st.write("Get check-in requests")
    checkins_ref = db.collection("checkins").where("status", "==", "pending")   # query
    docs = checkins_ref.stream()   # stream generator

    #> Set data to be shown
    checkin_data = []
    for doc in docs:
        data = doc.to_dict()
        checkin_data.append({
            "CheckinId": doc.id,
            "Date": data.get("timestamp", ""), # [:16].replace("T", " "),
            "People": ", ".join(data.get("peopleIds", [])),
            "checkInDate": data.get("checkInDate"),
            "checkOutDate": data.get("checkOutDate"),
            "Status": data.get("status")
        })
        # st.write(data)

    #> Print table as a pd.DataFrame, adding accepted option
    if checkin_data:
        df = pd.DataFrame(checkin_data)
        st.subheader("🕓 Latest Check-in Requests")
        df["Accept"] = False
        df = df[["Date", "Status", "Accept", "People", "checkInDate", "checkOutDate", "CheckinId"]]

        #> Action after accepting:
        # - change status (both df and google)
        # - send emails: confirmation, police, tourism agency
        if not df.empty:
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="checkin_status")
            for index, row in edited_df.iterrows():
                if row["Accept"]:
                    #> Update Firbase db
                    update_checkin(
                        row['CheckinId'],
                        {"status": "accepted"}
                    )
                    #> Update Google sheet
                    # ...

                    #> Print success message to the webpage
                    st.success("Checkin Accepted Successfully!")
                    st.rerun()

    else:
        st.info("No recent check-in request")


    #> List latest accepted check-ins
    st.subheader("✅ Latest Accepted Check-ins")
    acc_checkins_ref = db.collection("checkins").where("status", "==", "accepted")
    acc_docs = acc_checkins_ref.stream()
    
    #> Set data to be shown
    acc_checkin_data = []
    for doc in acc_docs:
        data = doc.to_dict()
        acc_checkin_data.append({
            "CheckinId": doc.id,
            "Date": data.get("timestamp", ""), # [:16].replace("T", " "),
            "People": ", ".join(data.get("peopleIds", [])),
            "checkInDate": data.get("checkInDate"),
            "checkOutDate": data.get("checkOutDate"),
            "Status": data.get("status")
        })
        # st.write(data)

    #> Print table as a pd.DataFrame, adding accepted option
    if acc_checkin_data:
        acc_df = pd.DataFrame(acc_checkin_data)
        acc_df = acc_df.sort_values(by="Date", ascending=False)
        # df["Reject"] = False
        acc_df = acc_df[["Date", "Status", "People", "checkInDate", "checkOutDate", "CheckinId"]]

        #> Action after accepting:
        # - change status (both df and google)
        # - send emails: confirmation, police, tourism agency
        if not acc_df.empty:
            acc_edited_df = st.data_editor(acc_df, num_rows="dynamic", use_container_width=True, key="checkin_accepted")

    else:
        st.info("No recent check-in request")
    
    # todo list
    st.write("todo")
    st.write("- Add option to revert from accepted to pending?")
    st.write("- ...")
