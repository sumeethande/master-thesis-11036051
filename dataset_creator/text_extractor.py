import pymupdf
import time
import json
import os
from .utilities import *
from collections import OrderedDict

class TextExtractor:

    '''
    ### Class with methods to extract texts from various university handbooks.
    
    #### args: 
    
    `json_dataset_path`: `(str)`
    
    Provide a path to save the extracted JSON objects into a JSON file. All JSON objects 
    
    will be stored at this path regardless of the university module handbook.
    '''

    def __init__(self, json_dataset_path:str):
        self.json_dataset_path = json_dataset_path

    # Method to save extracted text into JSON file (To be used internally only)
    def _save_to_json_file(self, json_list:list, dataset_json_path:str) -> None:

        # If JSON already exists, append to it, else create new JSON file
        if os.path.isfile(dataset_json_path) and ".json" in dataset_json_path:
            with open(dataset_json_path, "r", encoding="utf-8") as existing_json_file:
                existing_json_content = json.load(existing_json_file)

            extended_json_content = existing_json_content + json_list

            with open(dataset_json_path, "w", encoding="utf-8") as extended_json_file:
                json.dump(extended_json_content, extended_json_file, ensure_ascii=False, indent=4)

            print(f"Saved JSON file to {dataset_json_path}")
        else:
            if ".json" in dataset_json_path:
                with open(dataset_json_path, "w", encoding="utf-8") as new_json_file:
                    json.dump(json_list, new_json_file, ensure_ascii=False, indent=4)

                print(f"Saved JSON file to {dataset_json_path}")
            else:
                print(f"Provided path for variable dataset_json_path {dataset_json_path} does not point to a JSON file.")
                default_json_path = r"C:\extracted_text.json"
                print(f"Saving data to default path {default_json_path}")
                with open(default_json_path, "w", encoding="utf-8") as default_json_file:
                    json.dump(json_list, default_json_file, ensure_ascii=False, indent=4)

    # Helper Method to split list of lists based on first element of sublist (To be used internally only)
    def _split_list_of_lists(self, lol:list, keyword:str):
        for i, sublist in enumerate(lol):
            if sublist and sublist[0] == keyword:
                return lol[:i], lol[i:]
        # If keyword not found, return the entire list as the first part
        return lol, []  

    # Method to extract text from TU Darmstadt module Handbooks
    def extract_tud_de(self, path_to_pdf:str) -> None:

        '''
        Extracts module data into JSON objects from TU darmstadt module handbooks
        '''

        # Tags (exclusive to TU Darmstadt module handbooks. May change with different module handbook design)
        tags = [
            "Modulname",
            "Modul Nr.",
            "Leistungspunkte",
            "Arbeitsaufwand",
            "Selbststudium",
            "Moduldauer",
            "Angebotsturnus",
            "Sprache",
            "Modulverantwortliche Person",
            "Lerninhalt",
            "Qualifikationsziele / Lernergebnisse",
            "Empfohlene Voraussetzungen für die Teilnahme",
            "Prüfungsform",
            "Voraussetzung für die Vergabe von Leistungspunkten",
            "Benotung",
            "Verwendbarkeit des Moduls",
            "Notenverbesserung nach §25 (2)",
            "Literatur"
        ]

        special_tags = ["Kurs-Nr.", "Kursname", "Dozent/in", "Lehrform", "SWS"]
        num_list = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

        pdf_doc = pymupdf.open(path_to_pdf)
        dataset_json_path = self.json_dataset_path

        json_list = []
        json_obj = OrderedDict()
        json_obj["UNIVERSITY"] = "Technical University Darmstadt"
        json_obj["TEXT_LANG"] = "DE"
        json_obj["MODULE_DETAILS"] = OrderedDict()
        json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []

        print(f"Total pages: {len(pdf_doc)}")

        for page in pdf_doc:

            print(f"Extracting text from {page}", end="\r", flush=True)
            tabs = page.find_tables()

            for table in tabs.tables:
                extracted_lol = table.extract()

                # Split LOL into Non-numbered, Numbered elements and (Enthaltene Kurse) LOL's
                part_one, part_two = self._split_list_of_lists(extracted_lol, "Enthaltene Kurse")

                if part_one:
                    if "Modulname" in part_one[0][0] and len(json_obj["MODULE_DETAILS"]) != 0:
                        json_list.append(json_obj)
                        json_obj = OrderedDict()
                        json_obj["UNIVERSITY"] = "Technical University Darmstadt"
                        json_obj["TEXT_LANG"] = "DE"
                        json_obj["MODULE_DETAILS"] = OrderedDict()
                        json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []
                else:
                    if "Modulename" in part_two[0][0] and len(json_obj["MODULE_DETAILS"]) != 0:
                        json_list.append(json_obj)
                        json_obj = OrderedDict()
                        json_obj["UNIVERSITY"] = "Technical University Darmstadt"
                        json_obj["TEXT_LANG"] = "DE"
                        json_obj["MODULE_DETAILS"] = OrderedDict()
                        json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []

                if part_one:
                    # Remove None from LOL
                    part_one = remove_none_from_lol(part_one)
                    
                    # Check length of part_one. If it is 12, do normal extraction
                    if len(part_one) == 12:
                        flat_part_one = flatten_2d_list(part_one)
                        for i, str_item in enumerate(flat_part_one):
                            if str_item in num_list:
                                continue

                            if "\n" in str_item:
                                tag, tag_content = str_item.split("\n", 1)
                                json_obj["MODULE_DETAILS"][tag] = tag_content
                            else:
                                json_obj["MODULE_DETAILS"][str_item] = ""
            
                    # part_one length is not 12
                    else:
                        # First make sure part_one does not contain any of the special tags
                        # if not any(special_tag in part_one[0] for special_tag in special_tags):
                        if not any(special_tag in string_item for special_tag in special_tags for string_item in part_one[0]):
                            # Check if first element of first sublist of part_one is ""
                            # If it is "", it means that the content belongs to previous tag
                            if part_one[0][0] == "":
                                # Deal with first sublist as it's content belongs to previous tag
                                previous_list = part_one.pop(0)
                                text = previous_list[1]
                                last_key, last_val = list(json_obj["MODULE_DETAILS"].items())[-1]
                                updated_last_val = last_val + text
                                json_obj["MODULE_DETAILS"][last_key] = updated_last_val

                            flat_part_one = flatten_2d_list(part_one)
                            for i, str_item in enumerate(flat_part_one):

                                if str_item in num_list:
                                    continue

                                if "\n" in str_item:
                                    tag, tag_content = str_item.split("\n", 1)
                                    json_obj["MODULE_DETAILS"][tag] = tag_content
                                else:
                                    json_obj["MODULE_DETAILS"][str_item] = ""

                        # Special case where part_one contains special_tags
                        else:
                            flat_part_one = flatten_2d_list(part_one)
                            # Identify how many Enthaltene Kurse are there.
                            # Each Enthaltene Kurse takes 2 sublists.
                            if len(part_one) % 2 == 0:
                                course = {}
                                for str_item in flat_part_one:
                                    if str_item == "" or str_item == " ":
                                        continue

                                    if "\n" in str_item:
                                        tag, tag_content = str_item.split("\n", 1)
                                        if tag in special_tags:
                                            special_tags.remove(tag)
                                            course[tag] = tag_content
                                    else:
                                        if str_item in special_tags:
                                            special_tags.remove(str_item)
                                            course[str_item] = ""
                                    
                                    if len(special_tags) == 0:
                                        json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"].append(course)
                                        course = {}
                                        special_tags = ["Kurs-Nr.", "Kursname", "Dozent/in", "Lehrform", "SWS"]
        
                # Extract the "Included Courses" part (Enthaltene Kurse)
                if part_two:
                    part_two = part_two[1:]
                    if part_two:
                        part_two = remove_none_from_lol(part_two)
                        flat_part_two = flatten_2d_list(part_two)
                        # Identify how many Enthaltene Kurse are there.
                        # Each Enthaltene Kurse takes 2 sublists.
                        if len(part_two) % 2 == 0:
                            course = {}
                            for str_item in flat_part_two:
                                if str_item == "" or str_item == " ":
                                    continue

                                if "\n" in str_item:
                                    tag, tag_content = str_item.split("\n", 1)
                                    if tag in special_tags:
                                        special_tags.remove(tag)
                                        course[tag] = tag_content
                                else:
                                    if str_item in special_tags:
                                        special_tags.remove(str_item)
                                        course[str_item] = ""
                                
                                if len(special_tags) == 0:
                                    json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"].append(course)
                                    course = {}
                                    special_tags = ["Kurs-Nr.", "Kursname", "Dozent/in", "Lehrform", "SWS"]

                

        print("Extraction complete!")
        time.sleep(0.5)

        self._save_to_json_file(json_list, dataset_json_path)

    # Method to extract text from Hochschule Darmstadt module Handbooks
    def extract_hda_de(self, path_to_pdf:str) -> None:
        '''
        Extracts module data into JSON objects from TU darmstadt module handbooks
        '''

        # Tags (exclusive to Hochschule Darmstadt module handbooks. May change with different module handbook design)
        tags = [
            "Modulname",
            "Modulkürzel",
            "Art",
            "Lehrveranstaltung",
            "Semester",
            "Modulverantwortliche(r)",
            "Weitere Lehrende",
            "Studiengangsniveau",
            "Lehrsprache",
            "Inhalt",
            "Ziele",
            "Lehr- und Lernformen",
            "Arbeitsaufwand und Credit Points",
            "Prüfungsform, Prüfungsdauer und Prüfungsvoraussetzung",
            "Notwendige Kenntnisse",
            "Empfohlene Kenntnisse",
            "Dauer, zeitliche Gliederung und Häufigkeit des Angebots",
            "Verwendbarkeit des Moduls",
            "Literatur"
        ]

        pdf_doc = pymupdf.open(path_to_pdf)
        dataset_json_path = self.json_dataset_path

        print(f"Total pages: {len(pdf_doc)}")

        json_list = []
        json_obj = OrderedDict()
        json_obj["UNIVERSITY"] = "Hochschule Darmstadt"
        json_obj["TEXT_LANG"] = "DE"
        json_obj["MODULE_DETAILS"] = OrderedDict()
        
        # Looping over each page in the PDF
        for page in pdf_doc:
            print(f"Extracting text from {page}", end="\r", flush=True)
            tabs = page.find_tables()

            # Looping over each table on the page
            for table in tabs.tables:
                extracted_lol = table.extract()

                # Looping over each list in List of lists extracted from one table
                for str_list in extracted_lol:
                    number = str_list[0]
                    text = str_list[1]

                    # Check for last point of the module
                    if number == "11":
                        if "\n" in text:
                            tag, tag_content = text.split("\n", 1)
                            json_obj["MODULE_DETAILS"][tag] = tag_content
                            json_list.append(json_obj)

                            # Clear json_obj and reinitialize
                            json_obj = OrderedDict()
                            json_obj["UNIVERSITY"] = "Hochschule Darmstadt"
                            json_obj["TEXT_LANG"] = "DE"
                            json_obj["MODULE_DETAILS"] = OrderedDict()

                    if number == "":
                        # Incomplete data does not belong to 11 Literatur tag
                        if len(json_obj["MODULE_DETAILS"]) != 0:
                            last_key, last_val = list(json_obj["MODULE_DETAILS"].items())[-1]
                            updated_last_val = last_val + text
                            json_obj["MODULE_DETAILS"][last_key] = updated_last_val
                        # Incomplete data belongs to 11 Literatur tag
                        else:
                            previous_obj = json_list.pop()
                            previous_obj["MODULE_DETAILS"]["Literatur"] = previous_obj["MODULE_DETAILS"]["Literatur"] + text
                            json_list.append(previous_obj)

                    else:
                        if "\n" in text:
                            tag, tag_content = text.split("\n", 1)
                            json_obj["MODULE_DETAILS"][tag] = tag_content

        print("Extraction complete!")
        time.sleep(0.5)

        self._save_to_json_file(json_list, dataset_json_path)

    # Method to extract text from University of Bonn module Handbooks
    def extract_uni_bonn(self, path_to_pdf:str, handbook_text_lang:str) -> None:
        '''
        Extracts module data into JSON objects from TU darmstadt module handbooks

        Pass either `"EN"` or `"DE"` in `handbook_text_lang` parameter.
        '''

        if handbook_text_lang == "EN":
            
            pdf_doc = pymupdf.open(path_to_pdf)
            dataset_json_path = self.json_dataset_path

            tags_en_one = [
                "Module",
                "Credit Points",
                "Workload",
                "Duration",
                "Offered",
                "Person in Charge",
                "Instructors",
                "Learning Targets",
                "Contents",
                "Prerequisites",
                "Further Required\nQualifications",
                "Examination",
                "Requirements for\nExamination",
                "More Information"

            ]

            tags_en_two = [
                "Usability",
                "Program",
                "Mode",
                "Semester",
                "Courses",
                "Type, Topic",
                "h/week",
                "Workload (hours)",
                "CP"
            ]

            json_list = []
            json_obj = {}
            json_obj["UNIVERSITY"] = "University of Bonn"
            json_obj["TEXT_LANG"] = "EN"
            json_obj["MODULE_DETAILS"] = {}

            # Loop through each page of PDF
            for page in pdf_doc:
                
                print(f"Extracting text from {page}", end="\r", flush=True)
                tabs = page.find_tables()

                for table in tabs.tables:
                    extracted_lol = table.extract()

                    # Remove None's from LOL
                    clean_lol = remove_none_from_lol(extracted_lol)

                    tags_en_one_copy = tags_en_one.copy()
                    tags_en_two_copy = tags_en_two.copy()

                    # Loop through each sublist of LOL
                    for sublist_index, sublist in enumerate(clean_lol):
                        if sublist_index == 0:
                            tag, content = sublist[0].split("\n")
                            json_obj["MODULE_DETAILS"][tag] = content

                            json_obj["MODULE_DETAILS"]["Module Name"] = sublist[1]
                        
                        else:
                            if len(sublist) == 2:
                                if sublist[0] in tags_en_one_copy:
                                    tags_en_one_copy.remove(sublist[0])
                                    json_obj["MODULE_DETAILS"][sublist[0]] = sublist[1]
                            
                            if len(sublist) == 4:
                                tags = sublist
                                contents = clean_lol[sublist_index+1]
                                if len(tags) == len(contents):
                                    sub_dict = zip(tags, contents)
                                    json_obj["MODULE_DETAILS"].update(sub_dict)
                    
                    json_list.append(json_obj)

                    json_obj = {}
                    json_obj["UNIVERSITY"] = "University of Bonn"
                    json_obj["TEXT_LANG"] = "EN"
                    json_obj["MODULE_DETAILS"] = {}

            print("Extraction complete!")
            time.sleep(0.5)
            self._save_to_json_file(json_list, dataset_json_path)

        elif handbook_text_lang == "DE":
            None
        else:
            print("Unrecognized Language code passed as parameter!")

    # Method to extract text from University of Kiel module Handbook
    def extract_uni_kiel(self, path_to_pdf:str, handbook_text_lang:str) -> None:
        if handbook_text_lang == "EN":
            pdf_doc = pymupdf.open(path_to_pdf)
            
            dataset_json_path = self.json_dataset_path

            json_list = []
            json_obj = OrderedDict()
            json_obj["UNIVERSITY"] = "University of Kiel"
            json_obj["TEXT_LANG"] = "EN"
            json_obj["MODULE_DETAILS"] = OrderedDict()
            json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []

            for page in pdf_doc:

                print(f"Extracting text from {page}", end="\r", flush=True)
                tabs = page.find_tables()

                for table in tabs.tables:
                    
                    # Get LOL
                    extracted_lol = table.extract()

                    # Remove None's
                    clean_lol = remove_none_from_lol(extracted_lol)

                    # Loop over LOL
                    for sublist_index, sublist in enumerate(clean_lol):
                        
                        # New Module
                        if sublist_index == 0 and sublist[0] == "Module description":

                            # Append previous Module's data to list
                            if len(json_obj["MODULE_DETAILS"]) > 1:
                                json_list.append(json_obj)
                                json_obj = OrderedDict()
                                json_obj["UNIVERSITY"] = "University of Kiel"
                                json_obj["TEXT_LANG"] = "EN"
                                json_obj["MODULE_DETAILS"] = OrderedDict()
                                json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []

                            json_obj["MODULE_DETAILS"][sublist[0]] = clean_lol[sublist_index+1][1]

                        elif sublist_index > 0 and clean_lol[0][0] == "Module description":

                            if len(sublist) == 2 and sublist[0] != "":
                                json_obj["MODULE_DETAILS"][sublist[0]] = sublist[1]
                            
                            if sublist[0] == "Courses":
                                sublist.remove("Courses")

                                # DO this only if current sublist is not the last sublist of clean_lol
                                counter_max = len(clean_lol) - 1
                                if sublist_index != counter_max:
                                    course_content_lol = []
                                    counter = sublist_index

                                    while(True):
                                        if counter < counter_max:
                                            counter = counter + 1
                                        else:
                                            break

                                        if len(clean_lol[counter]) == 4:
                                            course_content_lol.append(clean_lol[counter])
                                        else:
                                            break
                                    
                                    for content_list in course_content_lol:
                                        if len(sublist) == len(content_list):
                                            course_obj = dict(zip(sublist, content_list))
                                            json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"].append(course_obj)
                            
                            if sublist[0] == "Examinations" and len(sublist) == 2:
                                json_obj["MODULE_DETAILS"][sublist[0]] = sublist[1]

                                # DO this only if current sublist is not the last sublist of clean_lol
                                counter_max = len(clean_lol) - 1
                                if sublist_index != counter_max:
                                    exam_content_lol = []
                        
                                    counter = sublist_index

                                    exam_labels = clean_lol[counter+1]

                                    exam_labels = ["Examinations " + word for word in exam_labels]
                                    
                                    lol_length = len(clean_lol[counter+1])

                                    while(True):
                                        if counter < counter_max:
                                            counter = counter + 1
                                        else:
                                            break

                                        if len(clean_lol[counter]) == lol_length:
                                            exam_content_lol.append(clean_lol[counter])
                                        else:
                                            break
                                    
                                    for content_list in exam_content_lol:
                                        if len(exam_labels) == len(content_list):
                                            exam_obj = dict(zip(exam_labels, content_list))
                                            json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"].append(exam_obj)

                        # Continuition of old previous Module
                        else:
                            if sublist[0] == "" and len(sublist) == 2:
                                content = sublist[1]
                                last_key, last_value = list(json_obj["MODULE_DETAILS"].items())[-1]
                                new_value = last_value + " " + content
                                json_obj["MODULE_DETAILS"][last_key] = new_value
                            
                            if sublist[0] != "" and len(sublist) == 2:
                                json_obj["MODULE_DETAILS"][sublist[0]] = sublist[1]
                        
                        # Add last module details to json_list
                        if page.number == len(pdf_doc) - 1:
                            json_list.append(json_obj)

            print("Extraction complete!")
            time.sleep(0.5)
            self._save_to_json_file(json_list, dataset_json_path)

        elif handbook_text_lang == "DE":
            None
        else:
            print("Handbook Text language is not recognized.")

    # Method to extract text from RWTH Aachen University module Handbook
    def extract_rwth_aachen(self, path_to_pdf:str, handbook_text_lang:str) -> None:
        if handbook_text_lang == "EN":

            pdf_doc = pymupdf.open(path_to_pdf)

            dataset_json_path = self.json_dataset_path

            json_list = []
            json_obj = OrderedDict()
            json_obj["UNIVERSITY"] = "RWTH Aachen University"
            json_obj["TEXT_LANG"] = "EN"
            json_obj["MODULE_DETAILS"] = OrderedDict()
            json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []

            for page in pdf_doc:

                print(f"Extracting text from {page}", end="\r", flush=True)
                tabs = page.find_tables()

                if len(tabs.tables) > 0 and page.number > 8:
                    current_module = tabs.tables[0].extract()[0][1]

                    for table_index, table in enumerate(tabs.tables):
                        
                        extracted_lol = table.extract()

                        clean_lol = remove_none_from_lol(extracted_lol)

                        # Table check
                        if table_index == 0 and len(clean_lol) == 1:
                            continue

                        if table_index == 0 and len(clean_lol[1]) == 2:

                            for sublist_index, sublist in enumerate(clean_lol):

                                if sublist_index == 0 and "Computer Science\nBSInf" in sublist[0]:

                                    if "CHECK_TOKEN" not in json_obj["MODULE_DETAILS"]:
                                        json_obj["MODULE_DETAILS"]["CHECK_TOKEN"] = sublist[1]

                                    if json_obj["MODULE_DETAILS"]["CHECK_TOKEN"] != current_module:
                                        json_list.append(json_obj)
                                        json_obj = OrderedDict()
                                        json_obj["UNIVERSITY"] = "RWTH Aachen University"
                                        json_obj["TEXT_LANG"] = "EN"
                                        json_obj["MODULE_DETAILS"] = OrderedDict()
                                        json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"] = []
                                    
                                    if "CHECK_TOKEN" not in json_obj["MODULE_DETAILS"]:
                                        json_obj["MODULE_DETAILS"]["CHECK_TOKEN"] = sublist[1]

                                # Skip first sublist
                                if sublist_index > 0:
                                    # Handle normal key-value pairs where sublist len is 2
                                    if len(sublist) == 2 and sublist[0] != "":
                                        json_obj["MODULE_DETAILS"][sublist[0]] = sublist[1]
                                    
                                    if len(sublist) == 2 and sublist[0] == "":
                                        content = sublist[1]
                                        last_key, last_value = list(json_obj["MODULE_DETAILS"].items())[-1]
                                        new_value = last_value + " " + content
                                        json_obj["MODULE_DETAILS"][last_key] = new_value
                        
                        # Table with Exam node details
                        elif table_index == 0 and len(clean_lol[0][0]) == 5:
                            tags_list = clean_lol[0]
                            contents_list = clean_lol[1:]

                            for sublist in contents_list:
                                course_obj = dict(zip(tags_list, sublist))
                                json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"].append(course_obj)

                        
                        # Table with Offer node details
                        else:
                            tags_list = clean_lol[0]
                            contents_list = clean_lol[1:]

                            for sublist in contents_list:
                                course_obj = dict(zip(tags_list, sublist))
                                json_obj["MODULE_DETAILS"]["SUB_MODULE_DETAILS"].append(course_obj)
                        
                        # Add last module details to json_list
                        if page.number == len(pdf_doc) - 1:
                            json_list.append(json_obj)

            print("Extraction complete!")
            time.sleep(0.5)
            self._save_to_json_file(json_list, dataset_json_path)

        elif handbook_text_lang == "DE":
            None
        else:
            print("Handbook language not recognized.")