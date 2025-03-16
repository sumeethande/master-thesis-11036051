import os
import json
# Mapping Dictionary of Labels

label_map = {
    "MODULE_NAME": ["Modulname", "Lehrveranstaltung", "Teilmodulname", "Module description", "Module Name", "Module titel"],
    "MODULE_NR": ["Modul Nr.", "Modulkürzel", "Teilmodulkürzel", "Module code", "Module", "Identifier"],
    "MODULE_TYPE": ["Art", "Mode", "Module level"],
    "MODULE_CREDITS": ["Leistungspunkte", "ECTS credit points", "ECTS Credits"],
    "MODULE_SEMESTER": ["Semester", "Where in the curriculum", "Recommended\nSemester (Study\nstart winter)", "Recommended\nSemester (Study\nstart summer)"],
    "MODULE_HOURS": ["Arbeitsaufwand", "Arbeitsaufwand und Credit Points", "Workload", "Contact time (WSH)", "Total hours (h)", "Contact hours (h)"],
    "MODULE_SELF_STUDY_HOURS": ["Selbststudium", "Self-study hours (h)"],
    "MODULE_DURATION": ["Moduldauer", "Dauer, zeitliche Gliederung und Häufigkeit des Angebots", "Duration", "Duration (Semester)"],
    "MODULE_SEM_TYPE": ["Angebotsturnus", "Repetition in the academic\nyear", "Cycle (Semester)"],
    "MODULE_LANGUAGE": ["Sprache", "Lehrsprache", "Language"],
    "MODULE_MANAGER": ["Modulverantwortliche Person", "Modulverantwortliche(r)", "Teilmodulverantwortliche(r)", "Lecturer responsible for the\nmodule", "Person in Charge", "Module coordinator"],
    "MODULE_CONTENT": ["Lerninhalt", "Inhalt", "Contents", "Content"],
    "MODULE_OUTCOMES": ["Qualifikationsziele / Lernergebnisse", "Ziele", "Learning objectives /\ncompetences", "Learning Targets", "Learning Objectives/\nLearning Outcomes"],
    "MODULE_PREREQUISITES": ["Empfohlene Voraussetzungen für die Teilnahme", "Notwendige Kenntnisse", "Empfohlene Kenntnisse", "Recommended requirements", "Prerequisites", "(Study-Specific)\nPrerequisites", "(recommended)\nRequirements"],
    "MODULE_TEACH_LEARN_METHODS": ["Lehr- und Lernformen"],
    "MODULE_EXAM_FORMAT": ["Prüfungsform", "Prüfungsform, Prüfungsdauer und Prüfungsvoraussetzung", "Examinations", "Examination", "Examination duration (min)"],
    "MODULE_PASSING_CRETERIA": ["BestehenderModulabschlussprüfung", "Voraussetzung für die Vergabe von Leistungspunkten", "Requirements according to\nthe Examination Regulations", "Further Required\nQualifications", "Requirements for\nExamination", "Examination Terms"],
    "MODULE_GRADING": ["Benotung", "Assessment"],
    "MODULE_DEGREE_PROGRAM": ["Verwendbarkeit des Moduls", "Studiengangsniveau", "Applicability of the module", "Program"],
    "MODULE_GRADE_IMPROVEMENT": ["Notenverbesserung nach §25 (2)"],
    "MODULE_LITERATURE": ["Literatur", "Literature", "References"],
    "COURSE_NAME": ["Kursname", "Title"],
    "COURSE_NR": ["Kurs-Nr."],
    "MODULE_INSTRUCTOR": ["Dozent/in", "Weitere Lehrende", "Lecturer", "Instructors"],
    "COURSE_TEACHING_FORM": ["Lehrform", "Type"],
    "COURSE_SWS": ["SWS"],
    "MODULE_FACULTY": ["Faculty responsible for the\nmodule"],
    "MODULE_SCHOOL": ["Institute responsible for the\nmodule"]
}

label_id_map = {
    "O": 0,
    "B-MODULE_NAME": 1,
    "I-MODULE_NAME": 2,
    "B-MODULE_NR": 3,
    "I-MODULE_NR": 4,
    "B-MODULE_TYPE": 5,
    "I-MODULE_TYPE": 6,
    "B-MODULE_CREDITS": 7,
    "I-MODULE_CREDITS": 8,
    "B-MODULE_SEMESTER": 9,
    "I-MODULE_SEMESTER": 10,
    "B-MODULE_HOURS": 11,
    "I-MODULE_HOURS": 12,
    "B-MODULE_SELF_STUDY_HOURS": 13,
    "I-MODULE_SELF_STUDY_HOURS": 14,
    "B-MODULE_DURATION": 15,
    "I-MODULE_DURATION": 16,
    "B-MODULE_SEM_TYPE": 17,
    "I-MODULE_SEM_TYPE": 18,
    "B-MODULE_LANGUAGE": 19,
    "I-MODULE_LANGUAGE": 20,
    "B-MODULE_MANAGER": 21,
    "I-MODULE_MANAGER": 22,
    "B-MODULE_CONTENT": 23,
    "I-MODULE_CONTENT": 24,
    "B-MODULE_OUTCOMES": 25,
    "I-MODULE_OUTCOMES": 26,
    "B-MODULE_PREREQUISITES": 27,
    "I-MODULE_PREREQUISITES": 28,
    "B-MODULE_TEACH_LEARN_METHODS": 29,
    "I-MODULE_TEACH_LEARN_METHODS": 30,
    "B-MODULE_EXAM_FORMAT": 31,
    "I-MODULE_EXAM_FORMAT": 32,
    "B-MODULE_PASSING_CRETERIA": 33,
    "I-MODULE_PASSING_CRETERIA": 34,
    "B-MODULE_GRADING": 35,
    "I-MODULE_GRADING": 36,
    "B-MODULE_DEGREE_PROGRAM": 37,
    "I-MODULE_DEGREE_PROGRAM": 38,
    "B-MODULE_GRADE_IMPROVEMENT": 39,
    "I-MODULE_GRADE_IMPROVEMENT": 40,
    "B-MODULE_LITERATURE": 41,
    "I-MODULE_LITERATURE": 42,
    "B-COURSE_NAME": 43,
    "I-COURSE_NAME": 44,
    "B-COURSE_NR": 45,
    "I-COURSE_NR": 46,
    "B-MODULE_INSTRUCTOR": 47,
    "I-MODULE_INSTRUCTOR": 48,
    "B-COURSE_TEACHING_FORM": 49,
    "I-COURSE_TEACHING_FORM": 50,
    "B-COURSE_SWS": 51,
    "I-COURSE_SWS": 52,
    "B-MODULE_FACULTY": 53,
    "I-MODULE_FACULTY": 54,
    "B-MODULE_SCHOOL": 55,
    "I-MODULE_SCHOOL": 56
}

def get_label_map() -> dict:
    """
    Returns the Label map dictionary
    """
    return label_map

def get_label_id_map() -> dict:
    """
    Returns the Label ID Map dictionary
    """
    return label_id_map


def clean_list(list_to_clean:list) -> list:        
    """
    Removes `None` and white space elements from list and returns the clean list.
    """
    return [item for item in list_to_clean if item is not None and item != "" and len(item) > 1]

def flatten_2d_list(list_to_flatten:list) -> list:
    """
    Flattens a list of lists (2D) to a single list of elements
    """
    return [string for sublist in list_to_flatten for string in sublist]

def remove_none_from_lol(lol_to_clean:list) -> list:

    """
    Removes `None` from the list and returns the clean list
    """
    return [[item for item in sublist if item is not None] for sublist in lol_to_clean]

def load_json_dataset(file_path:str) -> list | None:

    """
    Takes a JSON file path as input and returns list of JSON objects.
    """

    if os.path.isfile(file_path):
        if ".json" in file_path:
            with open(file_path, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)

            return json_data
        else:
            print("Given file path does not point to a JSON File.")
            return None
    else:
        print("File path does not point to a file.")
        return None

def save_json_dataset(dataset:list, file_path:str) -> None:

    """
    Take a list of JSON objects as input and stores it in a JSON file at the give path.

    Path must be complete and end with .json
    """

    if ".json" in file_path:
        # Check if file already exists, append data to it
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as json_file:
                old_json_data = json.load(json_file)
            
            new_json_data = old_json_data.extend(dataset)

            with open(file_path, "w", encoding="utf-8") as new_json_file:
                json.dump(new_json_data, new_json_file, ensure_ascii=False, indent=4)
        # Create new file and add data to it
        else:
            with open(file_path, "w", encoding="utf-8") as new_json_file:
                json.dump(dataset, new_json_file, ensure_ascii=False, indent=4)
    else:
        print("The given path does not contain proper .json file extension")

def load_final_jsonl_dataset(file_path:str) -> list:
    dataset = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            dataset.append(json.loads(line))
    
    return dataset