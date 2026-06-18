import streamlit as st
from utils.db import get_client_registry
from utils.excel_parser import parse_excel

def render():
    st.header("Charges Master Upload")

    registry = get_client_registry()
    if not registry:
        st.warning("No clients registered.")
        return

    client_names = {c['client_name']: c['client_id'] for c in registry}
    selected_client_name = st.selectbox("Select Target Client", list(client_names.keys()))

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Charges Excel", type=["xlsx"])

    if uploaded_file:
        try:
            st.info("Parsing file...")
            charges_df = parse_excel(uploaded_file, sheet_name="Charges")
            st.success("File parsed successfully.")
            
            st.subheader("Preview")
            st.dataframe(charges_df)
            
            if st.button("Confirm & Insert Charges"):
                st.success("Charges inserted successfully into target DB (Mock).")
        except Exception as e:
            st.error(f"Error processing file: {e}")
