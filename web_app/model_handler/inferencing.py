import torch
import pymupdf
from transformers import AutoTokenizer, AutoModelForTokenClassification
import io

class ModelInteractor:

    def __init__(self, pdf_file_object, module_start_page:int):
        self.pdf_file_object = pdf_file_object
        self.module_start_page = module_start_page

    def _split_into_chunks(self, tokenizer, zipped_contents):

        chunks = []
        max_length = 510
        overlap = 50

        for page_no, text in zipped_contents:
            tokens = tokenizer(text, add_special_tokens=False)["input_ids"]
            token_length = len(tokens)

            # If the text is already short, add it as a single chunk
            if token_length <= max_length:
                chunks.append([False, page_no, tokens])
            else:
                start = 0
                while start < token_length:
                    # Ensure the last chunk is not out of bounds
                    end = min(start + max_length, token_length)
                    chunk = tokens[start:end]
                    
                    # Check if it is first chunk
                    if start == 0 and len(chunk) == 510:
                        chunks.append([False, page_no, chunk])
                    # For other chunks
                    else:
                        chunks.append([True, page_no, chunk])

                    # Stop if we've reached the last token
                    if end == token_length:
                        break

                    # Slide window forward
                    start += max_length - overlap

                # Ensure last chunk has overlap only if it is too small
                if len(chunks) > 1:
                    last_chunk_len = len(chunks[-1][2])
                    if last_chunk_len < overlap:
                        # Second-last chunk
                        prev_chunk = chunks[-2][2]
                        chunks[-1][2] = prev_chunk[-overlap:] + chunks[-1][2]
                        # Change overlap flag to True
                        chunks[-1][0] = True

        return chunks

    def _add_special_tokens(self, tokenizer, chunks):

        cls_token_id = tokenizer.cls_token_id
        sep_token_id = tokenizer.sep_token_id

        input_ids = []
        chunk_pages = []
        chunk_overlaps = []

        for chunk_set in chunks:
            sample = chunk_set[2]
            sample.insert(0, cls_token_id)
            sample.append(sep_token_id)
            input_ids.append(sample)
            chunk_pages.append(chunk_set[1])
            chunk_overlaps.append(chunk_set[0])
        
        # Adding padding
        max_length = max(len(chunk) for chunk in input_ids)
        input_ids_padded = [chunk + [tokenizer.pad_token_id] * (max_length - len(chunk)) for chunk in input_ids]

        # Create attention_mask
        attention_mask = [[1] * len(chunk) + [0] * (max_length - len(chunk)) for chunk in input_ids]

        return (input_ids_padded, attention_mask, chunk_pages, chunk_overlaps)

    def extract_text_from_pdf(self):

        pdf_text = {}
        pdf_text["name"] = self.pdf_file_object.name
        pdf_text["content"] = []

        file_bytes = self.pdf_file_object.getvalue()

        pdf_doc = pymupdf.open("pdf", io.BytesIO(file_bytes))

        for page_number, page in enumerate(pdf_doc):
            if page_number < self.module_start_page - 1:
                continue
            else:
                text = page.get_text().replace("\n", " ")
                text = " ".join(text.split())
                pdf_text["content"].append(
                    {
                        page_number+1:text
                    }
                )

        return pdf_text
    
    def make_predictions(self, pdf_text:dict):

        results = {}
        results["name"] = pdf_text["name"]
        results["content"] = []

        # Load the model
        model = AutoModelForTokenClassification.from_pretrained("./model")
        tokenizer = AutoTokenizer.from_pretrained("./model")

        # Move model to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)


        # Zip the contents to preserve page and text order
        page_numbers = []
        contents = []
        for text_object in pdf_text["content"]:
            for key, value in text_object.items():
                page_numbers.append(key)
                contents.append(value)
        zipped_contents = zip(page_numbers, contents)

        # Make chunks
        chunks = self._split_into_chunks(tokenizer, zipped_contents)

        # Add special tokens
        input_ids_padded, attention_mask, chunk_pages, chunk_overlaps = self._add_special_tokens(tokenizer, chunks)

        # Converting input and mask to tensors
        input_ids_padded = torch.tensor(input_ids_padded).to(device)
        attention_mask = torch.tensor(attention_mask).to(device)

        # Getting model predictions in one batch
        with torch.no_grad():
            outputs = model(input_ids_padded, attention_mask=attention_mask)
        
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=2)
        confidence_scores, predictions = torch.max(probabilities, dim=2)

        # Align everything togther
        # Iterate over each chunk
        for i in range(len(input_ids_padded)):
            # Convert token IDs to text tokens
            tokenized_words = tokenizer.convert_ids_to_tokens(input_ids_padded[i])
            
            result = {}
            result["chunk_page_no"] = chunk_pages[i]
            result["is_overlapped"] = chunk_overlaps[i]
            result["predictions"] = []
            for word, tag, confidence in zip(tokenized_words, predictions[i].cpu().numpy(), confidence_scores[i].cpu().numpy()):
                if word not in ["[CLS]", "[SEP]", "[PAD]"]:  # Ignore special tokens
                    result["predictions"].append((word, tag, confidence))
    
            results["content"].append(result)
    
        return results