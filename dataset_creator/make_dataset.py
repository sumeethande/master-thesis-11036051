from .utilities import *
from transformers import AutoTokenizer
import time
import torch

class MakeDataset:
    def __init__(self, model_name:str, label_mapper:dict, label_id_mapper:dict, json_dataset_path:str, final_dataset_save_path:str):
        self.model_name = model_name
        self.label_mapper = label_mapper
        self.label_id_mapper = label_id_mapper
        self.json_dataset_path = json_dataset_path
        self.final_dataset_save_path = final_dataset_save_path

        # Load the Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Load dataset
        self.json_dataset = load_json_dataset(self.json_dataset_path)

        # Initialize empty final dataset
        self.final_dataset = []
    
    def _get_standard_label(self, label:str):
        for std_label, variations in self.label_mapper.items():
            if label in variations:
                return std_label
    
    def _get_standard_label_id(self, std_label_input:str):
        for std_label, id in self.label_id_mapper.items():
            if std_label_input == std_label:
                return id

    def _create_label_ids(self, text_labels:str):
        ids = []
        for text_label in text_labels:
            id = self._get_standard_label_id(text_label)
            ids.append(id)
        return ids

    def _add_special_tokens(self, training_sample:dict):

        cls_token = self.tokenizer.cls_token
        cls_token_id = self.tokenizer.cls_token_id

        sep_token = self.tokenizer.sep_token
        sep_token_id = self.tokenizer.sep_token_id

        # Insert CLS token at the beginning
        training_sample["input_ids"].insert(0, cls_token_id)
        training_sample["labels"].insert(0, -100)  # CLS should not be used in loss
        training_sample["attention_mask"].insert(0, 1)  # CLS should be attended to
        training_sample["tokens"].insert(0, cls_token)  # Add to tokens for reference
        training_sample["text_labels"].insert(0, "O")  # Assign "O" label

        # Append SEP token at the end
        training_sample["input_ids"].append(sep_token_id)
        training_sample["labels"].append(-100)  # SEP should not be used in loss
        training_sample["attention_mask"].append(1)  # SEP should be attended to
        training_sample["tokens"].append(sep_token)  # Add to tokens for reference
        training_sample["text_labels"].append("O")  # Assign "O" label

        return training_sample

    def _add_padding(self, training_sample:dict, chunk_size:int=512):
        # Ensure each chunk is of size 512
        pad_length = chunk_size - len(training_sample["input_ids"])
        if pad_length > 0:
            pad_id = self.tokenizer.pad_token_id
            pad_token = self.tokenizer.pad_token
            training_sample["input_ids"] += [pad_id] * pad_length
            training_sample["tokens"] += [pad_token] * pad_length
            training_sample["labels"] += [-100] * pad_length
            training_sample["text_labels"] += ["O"] * pad_length
            training_sample["attention_mask"] += [0] * pad_length
        
        return training_sample

    def _make_chunks(self, training_sample:dict, chunk_size:int=512, stride:int=128):

        chunks = []

        input_ids = training_sample["input_ids"]
        tokens = training_sample["tokens"]
        labels = training_sample["labels"]
        text_labels = training_sample["text_labels"]
        attention_mask = training_sample["attention_mask"]
        text_lang = training_sample["text_lang"]
        
        chunks = []
        for i in range(0, len(input_ids), chunk_size - 2 - stride):
            chunk = {
                "input_ids": input_ids[i : i + chunk_size - 2],
                "tokens": tokens[i : i + chunk_size - 2],
                "labels": labels[i : i + chunk_size - 2],
                "text_labels": text_labels[i : i + chunk_size - 2],
                "attention_mask": attention_mask[i : i + chunk_size - 2],
                "text_lang": text_lang
            }

            # Ensure first label is a B- tag if it's an I- tag
            if len(chunk["text_labels"]) > 0 and chunk["text_labels"][0].startswith("I-"):
                # Update text label
                chunk["text_labels"][0] = "B-" + chunk["text_labels"][0][2:]

                # Update label ID
                # print(chunk["tokens"])
                # print(chunk["text_labels"])
                # print(chunk["labels"])
                chunk["labels"][0] = chunk["labels"][0] - 1
            
            # Add special tokens
            chunk = self._add_special_tokens(chunk)

            chunks.append(chunk)
        
        print("\n")
        print(f"----- MADE {len(chunks)} CHUNKS OF THE ORIGINAL TRAINING SAMPLE -----")
        for i, chunk in enumerate(chunks):
            print(f"----- CHUNK {i} STATS: -----")
            print(f"INPUT IDS: {len(chunk["input_ids"])}")
            print(f"TOKENS: {len(chunk["tokens"])}")
            print(f"LABELS: {len(chunk["labels"])}")
            print(f"TEXT_LABLES: {len(chunk["text_labels"])}")
            print(f"ATTENTION_MASK: {len(chunk["attention_mask"])}")
            print(f"TEXT_LANG: {chunk["text_lang"]}")
    
        return chunks

    def _tokenize_and_label_module(self, module:dict) -> dict:

        # Initialize empty training sample
        training_sample = {
            "input_ids": [],
            "tokens": [],
            "labels": [],
            "text_labels": [],
            "attention_mask": []
        }

        # Add module's text lang
        training_sample["text_lang"] = module["TEXT_LANG"]

        # Loop through module's key-value pairs and tokenize them
        for key, value in module["MODULE_DETAILS"].items():
            if key != "SUB_MODULE_DETAILS":
                std_label = self._get_standard_label(key)
                if std_label:
                    text = key + " " + value
                    tokenized_text = self.tokenizer(text, is_split_into_words=False, add_special_tokens=False)
                    text_labels = [f"B-{std_label}"] + [f"I-{std_label}"] * (len(tokenized_text["input_ids"]) - 1)
                    labels = self._create_label_ids(text_labels)

                    training_sample["input_ids"].extend(tokenized_text["input_ids"])
                    training_sample["tokens"].extend(tokenized_text.tokens())
                    training_sample["labels"].extend(labels)
                    training_sample["text_labels"].extend(text_labels)
                    training_sample["attention_mask"].extend(tokenized_text["attention_mask"])
            
            if key == "SUB_MODULE_DETAILS" and len(module["MODULE_DETAILS"]["SUB_MODULE_DETAILS"]) != 0:
                for course in value:
                    for course_key, course_value in course.items():
                        std_label = self._get_standard_label(course_key)
                        if std_label:
                            text = course_key + " " + course_value
                            tokenized_text = self.tokenizer(text, is_split_into_words=False, add_special_tokens=False)
                            text_labels = [f"B-{std_label}"] + [f"I-{std_label}"] * (len(tokenized_text["input_ids"]) - 1)
                            labels = self._create_label_ids(text_labels)

                            training_sample["input_ids"].extend(tokenized_text["input_ids"])
                            training_sample["tokens"].extend(tokenized_text.tokens())
                            training_sample["labels"].extend(labels)
                            training_sample["text_labels"].extend(text_labels)
                            training_sample["attention_mask"].extend(tokenized_text["attention_mask"])
        
        print("----- INITIAL TRAINING SAMPLE STATS: -----")
        print(f"INPUT IDS: {len(training_sample["input_ids"])}")
        print(f"TOKENS: {len(training_sample["tokens"])}")
        print(f"LABELS: {len(training_sample["labels"])}")
        print(f"TEXT_LABLES: {len(training_sample["text_labels"])}")
        print(f"ATTENTION_MASK: {len(training_sample["attention_mask"])}")
        print(f"TEXT_LANG: {training_sample["text_lang"]}")
        
        time.sleep(0.1)

        return training_sample
    
    def _finalize_training_sample(self, training_sample:dict):

        # STEP 1: Check len(training_sample["input_ids"]) Based on whether it exceeds 512 or not
        # call the chunking function and chunk the sample into chunks & adding special tokens
        if len(training_sample["input_ids"]) > 512:
            chunks = self._make_chunks(training_sample)
            for chunk in chunks:
                if len(chunk["input_ids"]) == 512:
                    self.final_dataset.append(chunk)
                if len(chunk["input_ids"]) < 512:
                    chunk = self._add_padding(chunk)
                    self.final_dataset.append(chunk)

        # STEP 2: Add padding for chunks to make them size 512 tokens
        if len(training_sample["input_ids"]) < 512:
            self.final_dataset.append(self._add_padding(self._add_special_tokens(training_sample)))

        # STEP 3: Append finalized chunks/training samples to self.final_dataset
        if len(training_sample["input_ids"]) == 512:

            # Slice off last two tokens from the sample
            training_sample["input_ids"] = training_sample["input_ids"][:-2]
            training_sample["tokens"] = training_sample["tokens"][:-2]
            training_sample["labels"] = training_sample["labels"][:-2]
            training_sample["text_labels"] = training_sample["text_labels"][:-2]
            training_sample["attention_mask"] = training_sample["attention_mask"][:-2]

            # Add special tokens
            training_sample = self._add_special_tokens(training_sample)

            # Recheck
            if len(training_sample["input_ids"]) == 512:
                self.final_dataset.append(training_sample)

    def make_and_save_final_dataset(self):

        print(f"FOUND {len(self.json_dataset)} MODULES...")

        # Loop over all modules
        for i, module in enumerate(self.json_dataset):

            print(f"<---------- PREPROCESSING MODULE {i} ---------->")

            training_sample = self._tokenize_and_label_module(module)

            self._finalize_training_sample(training_sample)
        
        # DISPLAY FINAL STATS:
        print(f"----- FINAL DATASET CONTAINS {len(self.final_dataset)} SAMPLES -----")
        
        en_count = 0
        de_count = 0

        for sample in self.final_dataset:
            if sample["text_lang"] == "EN":
                en_count += 1
            if sample["text_lang"] == "DE":
                de_count += 1
        
        print(f"------ NO. OF EN SAMPLES: {en_count} ------")
        print(f"------ NO. OF DE SAMPLES: {de_count} ------")

        print(f"----- SAVING DATASET AT {self.final_dataset_save_path} -----")
        # Save the dataset as JSONL
        with open(self.final_dataset_save_path, "w", encoding="utf-8") as dataset_file:
            for entry in self.final_dataset:
                dataset_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
