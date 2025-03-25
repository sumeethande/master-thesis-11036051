import streamlit as st
from building_blocks import beautify

# Page Settings
st.set_page_config(
    page_title="InformaIQ",
    page_icon="💡",
    layout="centered"
)

beautify.sticky_bar()
beautify.page_link_center()

file_to_view = None

# Get requrested file for viewing
if "requested_file_for_viewing" in st.session_state:
    requested_file_name = st.session_state["requested_file_for_viewing"]
    for file_obj in st.session_state["extracted_files"]:
        if file_obj["name"] == requested_file_name:
            file_to_view = file_obj
            del st.session_state["requested_file_for_viewing"]
    
if file_to_view:
    st.write(f"You are now viewing the extracted data from :red[{file_to_view["name"]}]")
    st.write(file_to_view["extractions"])
else:
    st.markdown("⚠️ Requested File cannot be found anymore. If has been removed, you will need to re-upload and extract the file.")

st.page_link(page="app_views/app.py", label="Back to app", icon="🔙")