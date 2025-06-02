import streamlit as st
from person_manager import get_people, save_person, delete_person, update_person
import pandas as pd

def people_page(user_id):
    st.title("👥 People")

    people = get_people(user_id)
    df = pd.DataFrame(people)

    if not df.empty:
        st.subheader("📋 Your People")
        df["Edit"] = False
        df["Delete"] = False
        df = df[["name", "surname", "dob", "id_code", "place_id", "Edit", "Delete"]]  # Display order

        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="people_editor")

        for index, row in edited_df.iterrows():
            if row["Delete"]:
                delete_person(user_id, people[index]["id"])
                st.success(f"Deleted {row['name']} {row['surname']}")
                st.rerun()

        for index, row in edited_df.iterrows():
            if row["Edit"]:
                with st.form(f"edit_form_{people[index]['id']}"):
                    name = st.text_input("Name", value=row["name"])
                    surname = st.text_input("Surname", value=row["surname"])
                    dob = st.date_input("Date of Birth", value=pd.to_datetime(row["dob"]))
                    id_code = st.text_input("ID Doc Code", value=row["id_code"])
                    place_id = st.text_input("Place", value=row.get("place_id", ""))
                    submitted = st.form_submit_button("Save")
                    if submitted:
                        update_person(user_id, people[index]["id"], {
                            "name": name,
                            "surname": surname,
                            "dob": str(dob),
                            "id_code": id_code,
                            "place_id": place_id
                        })
                        st.success("Updated successfully.")
                        st.rerun()
    else:
        st.info("No people added yet.")

    st.subheader("➕ Add a New Person")
    with st.form("add_person_form"):
        name = st.text_input("Name")
        surname = st.text_input("Surname")
        dob = st.date_input("Date of Birth")
        id_code = st.text_input("ID Doc Code")
        place_id = st.text_input("Place")
        file = st.file_uploader("Upload ID PDF", type=["pdf"])
        submitted = st.form_submit_button("Add")

        if submitted:
            save_person(user_id, name, surname, str(dob), id_code, file, place_id)
            st.success("Person added.")
            st.rerun()

