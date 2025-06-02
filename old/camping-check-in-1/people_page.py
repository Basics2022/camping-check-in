import streamlit as st
from person_manager import save_person, db
from datetime import datetime
from io import BytesIO

def people_page(user):
    st.title("👤 People Associated With Your Place")

    # Load existing people
    people_ref = db.collection("people").where("userId", "==", user["localId"])
    people = list(people_ref.stream())

    # Table
    st.subheader("People List")
    for doc in people:
        person = doc.to_dict()
        st.markdown(f"**{person['name']} {person['surname']}**")
        st.text(f"DOB: {person['dob']}, ID: {person['id_code']}")
        st.markdown(f"[📄 ID Document]({person.get('id_doc_url', '')})")
        st.markdown(f"Status: {'🕒 Pending' if person.get('update_pending') else '✅ Approved'}")
        st.markdown("---")

    # Add / Edit Form
    st.subheader("➕ Add or Update a Person")

    with st.form("person_form", clear_on_submit=True):
        name = st.text_input("First Name")
        surname = st.text_input("Last Name")
        dob = st.date_input("Date of Birth")
        id_code = st.text_input("Document Code")
        id_pdf = st.file_uploader("Upload ID Document (.pdf)", type=["pdf"])
        submit = st.form_submit_button("Save")

        if submit:
            if not name or not surname or not id_code:
                st.error("Name, surname, and ID code are required.")
            else:
                person_data = {
                    "name": name,
                    "surname": surname,
                    "dob": str(dob),
                    "id_code": id_code,
                    "userId": user["localId"]
                }
                file_like = BytesIO(id_pdf.read()) if id_pdf else None
                save_person(person_data, file_like)
                st.success("Person saved successfully. Updates will be reviewed by admin.")
                st.rerun()

