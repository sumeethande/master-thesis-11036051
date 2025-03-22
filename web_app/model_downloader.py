from transformers import AutoTokenizer, AutoModelForTokenClassification

model = AutoModelForTokenClassification.from_pretrained("sumeet-hande/bert-base-multilingual-cased-v4")
tokenizer = AutoTokenizer.from_pretrained("sumeet-hande/bert-base-multilingual-cased-v4")

model.save_pretrained("./model")
tokenizer.save_pretrained("./model")