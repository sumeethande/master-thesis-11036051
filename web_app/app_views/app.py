import streamlit as st
import time
from typing import Callable
from building_blocks import beautify, blocks, utils

# Page Settings
st.set_page_config(
    page_title="InformaIQ",
    page_icon="💡",
    layout="centered"
)

# Check if files exist in session state
if "files" not in st.session_state:
    st.session_state["files"] = []

if "extracted_files" not in st.session_state:
    st.session_state["extracted_files"] = []

beautify.custom_header()

st.subheader("Using InformatIQ you can extract all important content from a PDF.", divider="orange")

main_container = st.container(key="main_container")

beautify.sticky_bar()
beautify.center_button_group()

with main_container:
    if "main_activity_selector" in st.session_state:
        utils.load_widget_value("main_activity_selector")
    menubar_segment = st.segmented_control(
        label="Select an activity",
        options=["Upload", "Manage", "Extract", "View", "Download"],
        key="_main_activity_selector",
        label_visibility="collapsed",
        on_change=utils.store_widget_value,
        args=["main_activity_selector"]
    )

    if not menubar_segment:
        note = '''
        **Manage**: See all uploaded PDF Files. Processed files after extraction appear here as well. You can remove files if not required from this tab.

        **Upload:** Upload the PDF Files for extraction in this tab.

        **Extract:** Start the extraction process of important information from the selected PDF's in this tab.

        **View:** Here you can view the extracted information in a tabular format.

        **Download:** Extracted files can be downloaded in CSV format from this tab.
        '''
        st.info(note, icon="ℹ️")
    
    if menubar_segment == "Upload":
        blocks.render_upload_section(utils.sync_uploaded_files)
    
    if menubar_segment == "Manage":

        st.write("Uploaded PDF Files appear here. You can remove them using the Remove button.")

        blocks.render_file_cards("files", "manage", "Remove", "delete", utils.delete_file)
    
    if menubar_segment == "Extract":

        st.write('''
        Select the PDF files by clicking the toggle button.
        For Each selected file, **write the Page no. where the modules begin in the PDF**.
        After selecting the files, click on Extract to start the process.
        ''')

        blocks.render_extract_section()
    
    if menubar_segment == "View":

        st.write("Extracted files will appear here. You can view the extracted data for each file.")

        blocks.render_file_cards("extracted_files", "view", "View", "view", utils.view_extracted_file)

        # Switch Page requested
        if st.session_state.get("switch_page", False):
            st.session_state["switch_page"] = False
            st.switch_page("app_views/view_page.py")

    if menubar_segment == "Download":

        st.write("You can download the Extracted text in the form of JSON files. Just click on the download button of the file you want to dowload.")
        
        blocks.render_download_section()