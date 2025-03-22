# This module is the heart of the app. All ML magic comes from here.

import streamlit as st
import time
from .utils import get_file_names
from model_handler.inferencing import *
from model_handler.postprocessing import *

# Function which runs the main extraction process
def start_extraction(files_for_extraction:list):
    
    files = []

    with st.status("Getting files...") as status:
        
        # Get file objects of selected files
        for file_name in files_for_extraction:
            for file_object in st.session_state["files"]:
                if file_name == file_object.name:
                    files.append(file_object)

        # Start extraction process one by one
        for file_obj in files:
            status.update(label=f"Extracting from {file_obj.name}", state="running", expanded=True)

            me = ModelInteractor(file_obj, st.session_state[f"module_page_{file_object.name}"])

            # Extract text from PDF file
            text_object = me.extract_text_from_pdf()

            status.update(label=f"Predicting tokens for {file_obj.name}", state="running", expanded=True)

            # Make predictions
            results = me.make_predictions(text_object)

            status.update(label=f"Doing Post-processing for {file_obj.name}", state="running", expanded=True)

            # Post-process the predictions
            pp = PostProcess(results)

            # Merge subwords and assign text-labels to label IDs
            pp.join_subwords_and_labels()

            # Grouping words with their labels
            extracted_file = pp.group_words_to_labels()

            st.session_state["extracted_files"].append(extracted_file)
        
        status.update(label="Complete", state="complete", expanded=False)

