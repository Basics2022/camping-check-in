
from firebase_admin import firestore

db = firestore.client()

def update_checkin(checkin_id, updated_fields):
    """  """
    # debug ---
    # st.write(f"in update_checkin(), checkin_id: {checkin_id}")
    # st.write(f"in update_checkin(), updated_fields: {updated_fields}")
    doc_ref = db.collection("checkins").document(checkin_id)
    doc_ref.update(updated_fields)

