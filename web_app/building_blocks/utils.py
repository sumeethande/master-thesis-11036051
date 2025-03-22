# Helper functions used throughout building_blocks package
import streamlit as st
import json

def store_widget_value(key) -> None:

    """
    Stores the value of the Widget using a key in session state.
    Useful to save widget state during page changes.

    `key`: Session State key of the Widget
    """

    st.session_state[key] = st.session_state["_"+key]

def load_widget_value(key) -> None:

    """
    Loads the values of the Widget from a key stored in session state.

    `key`: Session State key of the Widget

    """

    st.session_state["_"+key] = st.session_state[key]

def get_file_names(var_name) -> list:

    """
    Returns a list of file names from the session state.

    `var_name`: Key from the session state which holds a dictionary of file objects.

    """

    file_names = []
    if var_name in st.session_state:
        if len(st.session_state[var_name]) != 0:
            for file_object in st.session_state[var_name]:
                file_names.append(file_object.name)
    
    return file_names

def sync_uploaded_files() -> None:
    
    """
    Syncs the files uploaded by the user with the key-value pair in the Session State.
    """

    # Get updated list of uploaded files from widget state
    # Check if files is full. At any given point of time, files should have no more than 5 PDF files
    if len(st.session_state["uploaded_files"]) >= 5:
        st.toast("More than 5 files uploaded. Additional files will be ignored...", icon="⚠️")

    difference = 5 - len(st.session_state["files"])
    widget_files = st.session_state["uploaded_files"][:difference]

    # Get file names from files
    file_names = get_file_names("files")

    # First check if file from widget already exists in files
    # If not, then append widget file to files
    for widget_file_object in widget_files:
        if widget_file_object.name in file_names:
            continue
        else:
            st.session_state["files"].append(widget_file_object)
    
    if len(st.session_state["files"]) >= 5 and len(st.session_state["uploaded_files"]) <= 5 and difference != 0:
        st.toast(f"Cannot add all {len(st.session_state["uploaded_files"])} files. Only first {difference} file/s added as per order of file selection.", icon="⚠️") 

def delete_file(file_obj) -> None:

    """
    Deletes the file object from the files key and extracted_files key of session state
    """
    
    st.session_state["files"].remove(file_obj)
    file_name_to_delete = file_obj.name
    for file_obj in st.session_state["extracted_files"]:
        if file_name_to_delete == file_obj["name"]:
            st.session_state["extracted_files"].remove(file_obj)
    st.toast(f"Removed {file_name_to_delete}", icon="❎")

def view_extracted_file(file_obj) -> None:

    """
    Sets the `requested_file_for_viewing` key to file_obj and sets `switch_page` to True
    """
    
    # Put file_obj in session state so that it is available when page changes
    st.session_state["requested_file_for_viewing"] = file_obj["name"]

    # Set Switch Page Flag to True
    st.session_state["switch_page"] = True

def download_extracted_file(file_obj) -> None:
    
    data = json.dumps(file_obj["extractions"], indent=4, ensure_ascii=False)
    file_name = f"{file_obj['name'].replace(".pdf", "")}_extracted.json"

    st.download_button(
        label="JSON",
        icon=":material/download:",
        key=f"download_{file_obj["name"]}",
        data=data,
        file_name=file_name
    )