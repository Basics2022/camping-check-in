"""

"""

import streamlit as st
from person_manager import get_people, save_person, delete_person, update_person, get_people_gs, save_guest
import datetime
import pandas as pd

gender_options = {
    "M: male": "M",
    "F: female": "F",
    "O: non binary/other": "O",
    "N: prefer not to say": "N",
}


def people_page(user_id):
    #> People page ---------------------------------------------------
    st.title("👥 People")

    #> People list ---------------------------------------------------
    st.subheader("📋 Your People")

    #> Get people from spreadsheet (so far, then db?)
    # people = get_people(user_id)
    people = get_people_gs(user_id)
    df = pd.DataFrame(people)
    pz = df['Piazzola'].iloc[0]

    #> Show list of residentialpeople
    if not df.empty:
        #> Remove some keys: id, Piazzola
        cols_to_remove = ['Id', 'Piazzola']
        cols = [col for col in df.columns if col not in cols_to_remove ]
        edited_df = st.data_editor(df[cols], num_rows="dynamic", use_container_width=True, key="people_editor")
    else:
        st.info("No people added yet.")

    #> Guest list ----------------------------------------------------
    st.subheader("📋 Your Guests")
    guests = get_people_gs(user_id, people_type="guests")
    df_guest = pd.DataFrame(guests)

    if not df_guest.empty:
        edited_df = st.data_editor(df_guest[cols], num_rows="dynamic", use_container_width=True, key="guest_list")
    else:
        st.info("No guest added yet.")

    #> Add guest -----------------------------------------------------
    st.subheader("➕ Add a New Guest")
    with st.form("add_person_form"):
        surname = st.text_input("Surname")
        name = st.text_input("Name")
        dob = st.date_input(
                "Date of Birth",
                min_value=datetime.date(1920, 1, 1),
                max_value=datetime.date.today()
        )
        pob = st.text_input("Place of Birth - City")
        provob = st.text_input("Prov. - Foreign Country Code")
        # id_code = st.text_input("ID Doc Code")
        nationality = st.text_input("Nationality. E.g. I:italiana")
        gender_option = st.selectbox("Gender", list(gender_options.keys()))
        gender = gender_options[gender_option]
        residence = st.text_input("Address. E.g. via Roma, 15, Torino")
        doc_type = st.text_input("Document type. CI: carta d'identità, P: patente,...")
        doc_num = st.text_input("Document number")
        # place_id = st.text_input("Place")
        # file = st.file_uploader("Upload ID PDF", type=["pdf"])
        submitted = st.form_submit_button("Add")

        guest_params = {
            'id': 0, 'pz': 29, # df['Piazzola'],
            'surname': surname, 'name': name, 'dob': dob, 'pob': pob,
            'provob': provob, 'nationality': nationality,
            'gender': gender, 'residence': residence, 
            'doc_type': doc_type, 'doc_num': doc_num,
            'doc_expiring': '', 'doc_place': ''
        }
        # # debug ---
        # st.write(f"guest_params.values(): {guest_params.values()}")
        # st.write(f"type(guest_params['dob']): {type(guest_params['dob'])}")
        # st.write(f"type(guest_params['dob'].isoformat()): {type(guest_params['dob'].isoformat())}, {guest_params['dob'].isoformat()}")

        if submitted:
            save_guest(guest_params)
            # save_person(user_id, name, surname, str(dob), id_code, file, place_id)
            st.success("Guest added.")
            st.rerun()

