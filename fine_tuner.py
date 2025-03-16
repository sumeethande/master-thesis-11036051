import torch
import evaluate
import numpy as np
from datasets import Dataset
from torch.optim import AdamW
from huggingface_hub import login
from sklearn.metrics import f1_score
from dataset_creator.utilities import load_final_jsonl_dataset
from transformers import (
    Trainer,
    AutoTokenizer,
    get_scheduler,
    TrainingArguments,
    EarlyStoppingCallback,
    AutoModelForTokenClassification
)

class FineTuner:

    """
    This is a supporting class which prepares dataset, calculates
    class weights tensor, loads model and tokenizer.

    Must be used along with the Trainer API in combination
    """

    def __init__(self, final_dataset_path:str):
        self.final_dataset_path = final_dataset_path

        # Load dataset as instance variable
        print("----- LOADING DATA FROM JSONL FILE -----")
        self.data = load_final_jsonl_dataset(self.final_dataset_path)

    def prepare_dataset(self) -> list:
        """
        Prepares the JSONL dataset. Converts it into transformers supported Dataset format.
        
        Returns a list as follows:

        `[train_set, val_set, test_set]`
        """

        # Convert the dataset into Hugging Face's Dataset format
        dataset = Dataset.from_list(self.data)

        # Remove columns not need for fine-tuning (keep only "input_ids", "attention_mask", "labels")
        columns_to_keep = ["input_ids", "attention_mask", "labels"]
        dataset = dataset.remove_columns([col for col in dataset.column_names if col not in columns_to_keep])

        # Split dataset into 80% training, 10% validation, 10% testing
        dataset = dataset.train_test_split(test_size=0.2, seed=42)
        train_val = dataset["train"].train_test_split(test_size=0.125, seed=42)

        # Final splits
        train_dataset = train_val["train"]
        val_dataset = train_val["test"]
        test_dataset = dataset["test"]

        return [train_dataset, val_dataset, test_dataset]

    def load_model(self, model_name) -> list:
        """
        Loads the model of provided `model_name`

        Also loads tokenizer for the model

        returns `[model, tokenizer]`
        """

        # Load model checkpoint from transformers
        # Count unique labels
        num_labels = len(set(label for sample in self.data for label in sample["labels"]))
        print(f"NUMBER OF LABELS: {num_labels}")

        # Load pre-trained model for token classification
        model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=num_labels)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        return [model, tokenizer]
    
    def calculate_class_weights(self):
        """
        Calculates the class weights tensor for the classes of the dataset

        This tensor will be used later for creating our own Loss function
        """

        # Calulcate total number of unique labels
        num_labels = len(set(label for sample in self.data for label in sample["labels"]))

        # Collect label counts (excluding "O" which is ignored during training)
        label_counts = {}
        for sample in self.data:
            for label in sample["labels"]:
                if label != -100:  # Ignore O-tag
                    label_counts[label] = label_counts.get(label, 0) + 1

        # Compute inverse frequency weights
        total_labels = sum(label_counts.values())
        num_classes = len(label_counts)

        class_weights = {
            label: total_labels / (num_classes * count) for label, count in label_counts.items()
        }

        # Normalize weights
        max_weight = max(class_weights.values())
        class_weights = {label: weight / max_weight for label, weight in class_weights.items()}

        # Convert to PyTorch tensor
        class_weights_tensor = torch.zeros(num_labels, dtype=torch.float)  # Initialize with zeros
        for label, weight in class_weights.items():
            class_weights_tensor[label] = weight  # Assign weight

        # Move to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        class_weights_tensor = class_weights_tensor.to(device)

        return class_weights_tensor


if __name__ == "__main__":

    # Use FineTuner to load, prepare dataset and model
    ft = FineTuner(f"D:\master-thesis-dataset\stage_three_dataset\final_dataset.jsonl")

    # Prepare the dataset
    training_set, validation_set, testing_set = ft.prepare_dataset()

    # Load model and tokenizer
    model, tokenizer = ft.load_model(model_name="bert-base-multilingual-cased")

    # Calculate class weights for custom Loss function
    class_weights_tensor = ft.calculate_class_weights()

    # Create a function to compute the evaluation metrics
    accuracy_metric = evaluate.load("accuracy")

    def compute_metrics(pred):
        predictions, labels = pred
        predictions = np.argmax(predictions, axis=2)

        # Flatten the predictions and labels
        true_labels = [label for batch in labels for label in batch if label != -100]
        pred_labels = [pred for batch, label_batch in zip(predictions, labels) for pred, label in zip(batch, label_batch) if label != -100]

        accuracy = accuracy_metric.compute(predictions=pred_labels, references=true_labels)["accuracy"]
        f1 = f1_score(true_labels, pred_labels, average="weighted")

        return {"accuracy": accuracy, "f1": f1}
    
    # Override the Trainer with a custom weighted loss function
    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False):
            labels = inputs.get("labels")
            outputs = model(**inputs)
            logits = outputs.get("logits")

            # Apply weighted CrossEntropyLoss
            loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights_tensor, ignore_index=-100)
            loss = loss_fn(logits.view(-1, logits.shape[-1]), labels.view(-1))

            return (loss, outputs) if return_outputs else loss

    # Define the training arugments using TrainingArguments
    training_args = TrainingArguments(
        output_dir="./bert-base-multilingual-cased-fine-tuned",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        num_train_epochs=5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        logging_dir="./logs",
        logging_steps=10,
        load_best_model_at_end=True,
        push_to_hub=True,
        gradient_accumulation_steps=2
    )

    # Define Optimizer to use
    optimizer = AdamW(model.parameters(), lr=7e-5, weight_decay=0.02)

    # Define Learning rate scheduler to use
    num_training_steps = (len(training_set) // training_args.per_device_train_batch_size) * training_args.num_train_epochs
    
    lr_scheduler = get_scheduler(
        name="linear",
        optimizer=optimizer,
        num_warmup_steps=int(0.1 * num_training_steps),
        num_training_steps=num_training_steps
    )

    # Make use of the earlier defined custom Trainer
    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=training_set,
        eval_dataset=validation_set,
        compute_metrics=compute_metrics,
        optimizers=(optimizer, lr_scheduler),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    # Start the fine-tuning process
    trainer.train()

    # Evaluate the model on test test
    test_results = trainer.evaluate(testing_set)
    print("Test Results:", test_results)

    # Save the tokenizer and model locally and on hugging face hub
    tokenizer.save_pretrained(training_args.output_dir)
    hf_username = "sumeet-hande"
    login()
    trainer.push_to_hub(f"{hf_username}/bert-base-multilingual-cased-fine-tuned")