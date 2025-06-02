import streamlit as st
from person_manager import db, save_checkin

def checkin_page(user):
    st.title("📝 New Guest Check-In")

    user_id = user["localId"]

    # Fetch people linked to user
    people_ref = db.collection("people").where("userId", "==", user_id)
    people_docs = people_ref.stream()
    people_list = [(doc.id, f"{p['name']} {p['surname']}") for doc in people_docs if (p := doc.to_dict())]

    if not people_list:
        st.warning("You must register people before check-in.")
        return

    with st.form("checkin_form"):
        selected_ids = st.multiselect("Select Guests", options=[pid for pid, _ in people_list],
                                      format_func=lambda x: dict(people_list)[x])
        checkin_date = st.date_input("Check-In Date")
        checkout_date = st.date_input("Check-Out Date")
        num_guests = st.number_input("Number of Guests", min_value=1, step=1, value=1)
        vehicle_plate = st.text_input("Vehicle Plate (optional)")

        submitted = st.form_submit_button("Submit Check-In")

        if submitted:
            if not selected_ids:
                st.error("Please select at least one guest.")
            else:
                save_checkin(user_id, selected_ids, str(checkin_date), str(checkout_date), num_guests, vehicle_plate)
                st.success("✅ Check-in recorded successfully.")

