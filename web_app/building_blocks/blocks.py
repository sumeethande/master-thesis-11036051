# This module contains the blocks which display the various app sections/elements
# It also contains functions supporting these app sections/elements

import streamlit as st
from typing import Callable
from .core import start_extraction
from .utils import get_file_names, download_extracted_file

def render_upload_section(on_change_callable:Callable) -> None:

    """
    Renders the File uploader Widget

    `on_change_callable`: Callback function for the on_change parameter of the file_uploader Widget
    """

    # File uploader widget
    st.file_uploader(
        label="Upload your PDF File/s. (Maximum file upload: 5 PDF files)",
        type="pdf",
        accept_multiple_files=True,
        key="uploaded_files",
        on_change=on_change_callable,
        help="If more than five PDF files are uploaded, although they appear here in the upload widget, they will not be added.",
        disabled=len(st.session_state["files"]) >= 5
    )

def render_file_cards(data_object:str, container_key_prefix:str, button_label:str, button_key_prefix:str, button_callback:Callable) -> None:
    
    '''
    `data_object` `(str)`: Name of the session state object which holds the files.

    `container_key_prefix` `(str)`: Prefix string to add to each key of the file card container.

    `button_label` `(str)`: Label to display on every button of the file card.

    `button_key_prefix` `(str)`: Prefix string to add to each key of the Button.

    `button_callback` `(Callable)`: Callback function which should be triggered when the each button of the file card is pressed.
    '''

    if data_object in st.session_state:
        for file_obj in st.session_state[data_object]:
            card_container = st.container(border=True, key=f"{container_key_prefix}_container_{file_obj.name if data_object == "files" else file_obj["name"]}")
            with card_container:
                name_col, button_col = st.columns([0.8, 0.2], gap="small", vertical_alignment="center")
                with name_col:
                    st.write(f"{file_obj.name.replace(".pdf", "") if data_object == "files" else file_obj["name"].replace("pdf", "")}")
                
                with button_col:
                    st.button(
                        label=button_label,
                        key=f"{button_key_prefix}_{file_obj.name if data_object == "files" else file_obj["name"]}",
                        type="primary",
                        use_container_width=True,
                        on_click=lambda x=file_obj : button_callback(x)
                    )

def render_extract_section() -> None:
    
    # Access session state
    if "files" in st.session_state and len(st.session_state["files"]):
        for file_obj in st.session_state["files"]:
            card_container = st.container(border=True, key=f"extract_container_{file_obj.name}")
            with card_container:
                name_col, input_col, toggle_col = st.columns([0.5, 0.3, 0.2], gap="small", vertical_alignment="center")
                with name_col:
                    st.write(f"{file_obj.name.replace(".pdf", "")}")
                with input_col:
                    st.number_input(
                        label="Enter Page No.", 
                        label_visibility="collapsed", 
                        key=f"module_page_{file_obj.name}",
                        value=None,
                        step=1
                    )
                with toggle_col:
                    st.toggle(
                        label="Select",
                        key=f"select_{file_obj.name}"
                    )
        
        file_names = get_file_names("files")

        selected_files_toggle_values = []
        selected_files_number_values = []
        validation_list = []
        files_for_extraction = []

        for file_name in file_names:
            selected_files_toggle_values.append(st.session_state[f"select_{file_name}"])
            selected_files_number_values.append(st.session_state[f"module_page_{file_name}"])
            if st.session_state[f"select_{file_name}"] and st.session_state[f"module_page_{file_name}"] is not None:
                files_for_extraction.append(file_name)

        # Validation check if the user has selected the toggle and also given page number
        for operand_one, operande_two in zip(selected_files_toggle_values, selected_files_number_values):
            # Toggle selected and page no. entered (Button enabled)
            if operand_one and operande_two:
                validation_list.append(True)
            # Toggle selected but page no. not entered (Button disabled)
            if operand_one and not operande_two:
                validation_list.append(False)
            # Toggle not selected but page no. entered (Button disabled)
            if not operand_one and operande_two:
                validation_list.append(False)

        # If nothing selected, button must be disabled
        if not validation_list:
            validation_list.append(False)
        
        if all(validation_list):

            extraction = st.button(
                "Extract", 
                key="extract_button_enabled", 
                help="Click to start extraction process",
                type="primary"
            )

            if extraction:
                start_extraction(files_for_extraction)

        else:
            st.button(
                "Extract",
                key="extract_button_disabled",
                help="Click to start the extraction process",
                type="secondary",
                disabled=True
            )

def render_download_section() -> None:
    if "extracted_files" in st.session_state:
        for file_obj in st.session_state["extracted_files"]:
            card_container = st.container(border=True, key=f"download_container_{file_obj["name"]}")
            with card_container:
                name_col, button_col = st.columns([0.8, 0.2], gap="small", vertical_alignment="center")
                with name_col:
                    st.write(f"{file_obj["name"].replace(".pdf", "")}")
                
                with button_col:
                    download_extracted_file(file_obj)