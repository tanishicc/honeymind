import json
from pathlib import Path

import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

DATA_PATH = Path("data/deception_training_v2.jsonl")
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
OUTPUT_DIR = Path("honeymind/models/honeymind-tinyllama-lora-masked-v1")

MAX_LENGTH = 512


def load_rows():
    rows = []
    with DATA_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return Dataset.from_list(rows)


def split_prompt_answer(text):
    marker = "<OUT>\n"
    if marker not in text:
        return text, ""

    before, after = text.split(marker, 1)
    prompt = before + marker

    if "</OUT>" in after:
        answer = after.split("</OUT>", 1)[0] + "\n</OUT>"
    else:
        answer = after

    return prompt, answer


class OutputOnlyCollator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.pad_id = tokenizer.pad_token_id

    def __call__(self, examples):
        input_ids_batch = []
        attention_masks_batch = []
        labels_batch = []

        for ex in examples:
            text = ex["text"]
            prompt, answer = split_prompt_answer(text)

            prompt_ids = self.tokenizer(prompt, add_special_tokens=False)["input_ids"]
            answer_ids = self.tokenizer(answer, add_special_tokens=False)["input_ids"]

            input_ids = prompt_ids + answer_ids

            if len(input_ids) > MAX_LENGTH:
                overflow = len(input_ids) - MAX_LENGTH
                prompt_ids = prompt_ids[overflow:] if overflow < len(prompt_ids) else []
                input_ids = prompt_ids + answer_ids
                input_ids = input_ids[:MAX_LENGTH]

            labels = [-100] * len(prompt_ids) + input_ids[len(prompt_ids):]
            labels = labels[:len(input_ids)]

            attention_mask = [1] * len(input_ids)

            pad_len = MAX_LENGTH - len(input_ids)
            input_ids += [self.pad_id] * pad_len
            attention_mask += [0] * pad_len
            labels += [-100] * pad_len

            input_ids_batch.append(input_ids)
            attention_masks_batch.append(attention_mask)
            labels_batch.append(labels)

        return {
            "input_ids": torch.tensor(input_ids_batch, dtype=torch.long),
            "attention_mask": torch.tensor(attention_masks_batch, dtype=torch.long),
            "labels": torch.tensor(labels_batch, dtype=torch.long),
        }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading dataset...")
    dataset = load_rows().train_test_split(test_size=0.05, seed=42)

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    print("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    model.config.pad_token_id = tokenizer.eos_token_id

    print("Adding LoRA...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    collator = OutputOnlyCollator(tokenizer)

    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=2,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1e-4,
        logging_steps=25,
        eval_strategy="steps",
        eval_steps=400,
        save_steps=400,
        save_total_limit=2,
        report_to="none",
        fp16=False,
        dataloader_pin_memory=False,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        data_collator=collator,
    )

    print("Starting masked-output LoRA training...")
    trainer.train()

    print("Saving adapter...")
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print(f"Saved masked HoneyMind model to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
