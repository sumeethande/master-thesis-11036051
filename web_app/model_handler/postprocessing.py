
class PostProcess:

    def __init__(self, results:dict):
        self.results = results
        self.mod_predictions = {}
        self.mod_predictions["name"] = self.results["name"]
        self.mod_predictions["predictions"] = []

    
        self.label_id_map = {
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
    
    def _get_label_name(self, label_id:int) -> str:

        for key, value in self.label_id_map.items():
            if value == label_id:
                return key.split("-")[1]
    
    def join_subwords_and_labels(self):

        # Loop over the "contents" of the results dictionary
        for pred_obj in self.results["content"]:

            # ONLY GO FORWARD IF pred_obj["predictions"] is non-empty
            if pred_obj["predictions"]:
                pred_sublist = {}
                pred_sublist["chunk_page_no"] = pred_obj["chunk_page_no"]
                pred_sublist["chunk_predictions"] = []

                for i, pred_set in enumerate(pred_obj["predictions"]):
                    # Check is_overlapped to decide whether to skip first 50 pred_sets
                    if pred_obj["is_overlapped"]:
                        if i < 50:
                            continue

                    # print(f"CHUNK PAGE NO:{pred_sublist["chunk_page_no"]}, {i}, {pred_set}")
                    # Current element is not the last element
                    if i != len(pred_obj["predictions"]) - 1:
                        # Check if token is [UNK] and next token is not subword containing ##
                        if pred_set[0] == "[UNK]" and "##" not in pred_obj["predictions"][i+1][0]:
                            # Skip the current [UNK] token
                            continue

                        # Complete tokens
                        if not pred_set[0].startswith("##"):
                            # Append token set to sublist
                            pred_sublist["chunk_predictions"].append((pred_set[0], self._get_label_name(pred_set[1]), pred_set[2]))
                        
                        # Subword tokens
                        if pred_set[0].startswith("##"):

                            # ---------- SPECIAL EDGE CASE FOR SUBWORD TOKEN ----------
                            # This means the sublist is empty and yet token encoutered is a subword
                            if not pred_sublist["chunk_predictions"]:
                                # Access the previous chunk's last element
                                prev_token, prev_label, prev_conf  = self.mod_predictions["predictions"][-1]["chunk_predictions"][-1]
                                new_word, new_label, new_conf = "", "", 0

                                # Current Confidence less than prev. token's confidence
                                if prev_conf > pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = prev_label
                                    new_conf = prev_conf
                                
                                # Current Confidence greater than prev. token's confidence
                                if prev_conf < pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = self._get_label_name(pred_set[1])
                                    new_conf = pred_set[2]

                                # Remove last element from last chunk's sublist and update it with new token
                                del self.mod_predictions["predictions"][-1]["chunk_predictions"][-1]
                                self.mod_predictions["predictions"][-1]["chunk_predictions"].append((new_word, new_label, new_conf))

                            # ---------- Normal Subword token case ----------
                            else:
                                # Get label and confidence of previous token
                                prev_token, prev_label_id, prev_conf = pred_sublist["chunk_predictions"][-1]
                                new_word, new_label, new_conf = "", "", 0

                                # Current Confidence less than prev. token's confidence
                                if prev_conf > pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = prev_label_id
                                    new_conf = prev_conf
                                
                                # Current Confidence greater than prev. token's confidence
                                if prev_conf < pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = self._get_label_name(pred_set[1])
                                    new_conf = pred_set[2]

                                # Remove last token from sublist and update it with new token
                                del pred_sublist["chunk_predictions"][-1]
                                pred_sublist["chunk_predictions"].append((new_word, new_label, new_conf))
                    
                    # Dealing with the last element of the chunk
                    else:
                        # Check if last token is [UNK]
                        if pred_set[0] == "[UNK]":
                            # Skip the current [UNK] token
                            continue

                        # Complete tokens
                        if not pred_set[0].startswith("##"):
                            # Append token set to sublist
                            pred_sublist["chunk_predictions"].append((pred_set[0], self._get_label_name(pred_set[1]), pred_set[2]))

                        # Last token is subword
                        if pred_set[0].startswith("##"):     
                            
                            # ---------- SPECIAL EDGE CASE FOR SUBWORD TOKEN ----------
                            # This means the sublist is empty and yet token encoutered is a subword
                            if not pred_sublist["chunk_predictions"]:
                                # Access the previous chunk's last element
                                prev_token, prev_label, prev_conf  = self.mod_predictions["predictions"][-1]["chunk_predictions"][-1]
                                new_word, new_label, new_conf = "", "", 0

                                # Current Confidence less than prev. token's confidence
                                if prev_conf > pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = prev_label
                                    new_conf = prev_conf
                                
                                # Current Confidence greater than prev. token's confidence
                                if prev_conf < pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = self._get_label_name(pred_set[1])
                                    new_conf = pred_set[2]

                                # Remove last element from last chunk's sublist and update it with new token
                                del self.mod_predictions["predictions"][-1]["chunk_predictions"][-1]
                                self.mod_predictions["predictions"][-1]["chunk_predictions"].append((new_word, new_label, new_conf))

                            # ---------- Normal Subword token case ----------
                            else:
                                # Get label and confidence of previous token
                                prev_token, prev_label_id, prev_conf = pred_sublist["chunk_predictions"][-1]
                                new_word, new_label, new_conf = "", "", 0

                                # Current Confidence less than prev. token's confidence
                                if prev_conf > pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = prev_label_id
                                    new_conf = prev_conf
                                
                                # Current Confidence greater than prev. token's confidence
                                if prev_conf < pred_set[2]:
                                    new_word = prev_token + pred_set[0].split("##")[1]
                                    new_label = self._get_label_name(pred_set[1])
                                    new_conf = pred_set[2]

                                # Remove last token from sublist and update it with new token
                                del pred_sublist["chunk_predictions"][-1]
                                pred_sublist["chunk_predictions"].append((new_word, new_label, new_conf))
                        
                # Append one page's predictions to the main list
                # print(pred_sublist)
                self.mod_predictions["predictions"].append(pred_sublist)

    def group_words_to_labels(self) -> dict:
        
        extracted_file = {}
        extracted_file["name"] = self.mod_predictions["name"]
        extracted_file["extractions"] = []
        special_chars = [".", ":", ",", ";"]

        # Loop over mod_predictions["predictions"]
        for pred_obj in self.mod_predictions["predictions"]:
            chunk = {}
            chunk["pdf_page_no"] = pred_obj["chunk_page_no"]
            chunk["extracted_text"] = {}

            for pred_set in pred_obj["chunk_predictions"]:
                if pred_set[0] in special_chars:
                    # Check if label already exists in dictionary
                    if pred_set[1] not in chunk["extracted_text"]:
                        chunk["extracted_text"][pred_set[1]] = pred_set[0]
                    else:
                        chunk["extracted_text"][pred_set[1]] = chunk["extracted_text"][pred_set[1]] + pred_set[0]
                else:
                    if pred_set[1] not in chunk["extracted_text"]:
                        chunk["extracted_text"][pred_set[1]] = pred_set[0]
                    else:
                        chunk["extracted_text"][pred_set[1]] = chunk["extracted_text"][pred_set[1]] + " " + pred_set[0]

            extracted_file["extractions"].append(chunk)

        return extracted_file