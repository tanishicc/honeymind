import json
import warnings
import uuid
from datetime import datetime
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.utils import logging as hf_logging

BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ADAPTER_DIR = "honeymind/models/honeymind-tinyllama-lora-v6"
LOG_DIR = Path("logs")
hf_logging.set_verbosity_error()
warnings.filterwarnings("ignore")


TASK_MAP = {
    "whoami": "identity",
    "id": "identity",
    "hostname": "identity",
    "pwd": "working_directory",
    "ls": "directory_listing",
    "ls -la": "directory_listing",
    "ll": "directory_listing",
    "cat .env": "read_env_file",
    "cat config.php": "read_config_file",
    "cat /etc/os-release": "system_info",
    "uname -a": "system_info",
    "uname -r": "system_info",
    "uptime": "system_info",
    "df -h": "system_info",
    "find / -name '*.env' 2>/dev/null": "find_files",
    "find / -name '*.sql' 2>/dev/null": "find_files",
    'grep -R "DB_PASSWORD" . 2>/dev/null': "grep_credentials",
    'grep -R "password" . 2>/dev/null': "grep_credentials",
    "ps aux": "process_enum",
    "ss -tulpn": "network_enum",
    "netstat -tulpn": "network_enum",
    "sudo -l": "sudo_policy",
    "crontab -l": "persistence",
    "cat ~/.ssh/authorized_keys": "persistence",
}


class HoneyMindEngine:
    def __init__(self):
        self.device = "cpu"
        self.hostname = "prod-web-01"
        self.cwd = "/var/www/html"
        self.history = []
        self.session_id = str(uuid.uuid4())

        LOG_DIR.mkdir(exist_ok=True)

        print("Loading HoneyMind tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR)

        print("Loading HoneyMind base model...")
        base = AutoModelForCausalLM.from_pretrained(BASE_MODEL)

        print("Loading HoneyMind LoRA adapter...")
        self.model = PeftModel.from_pretrained(base, ADAPTER_DIR)
        self.model.to(self.device)
        self.model.eval()

    def classify_task(self, command):
        return TASK_MAP.get(command.strip(), "unknown")

    def build_prompt(self, command):
        task = self.classify_task(command)

        return f"""<TASK>
{task}
</TASK>
<CTX>
hostname={self.hostname}
os=Ubuntu 20.04.6 LTS
kernel=5.4.0-148-generic
stack=nginx/php/mysql
web_root=/var/www/html
database=mysql
user=root
cwd={self.cwd}
known_files=.env, config.php, index.php, admin, uploads
services=ssh, nginx, mysql
</CTX>
<CMD>
{command}
</CMD>
<OUT>
"""

    def clean_output(self, text):
        if "</OUT>" in text:
            text = text.split("</OUT>")[0]

        text = text.replace("\\n", "\n").strip()

        # Remove noisy generation warning fragments if they ever appear.
        text = text.replace("[transformers]", "").strip()

        return text

    def generate_response(self, command):
        command = command.strip()

        safe_overrides = {
            "pwd": self.cwd,
            "wd": "bash: wd: command not found",
        }

        if command in safe_overrides:
            response = safe_overrides[command]
            self.history.append({"command": command, "output": response})
            self.log_interaction(command, response)
            return response

        if command.startswith("cd "):
            target = command.split(" ", 1)[1]
            self.cwd = target
            response = ""
            self.log_interaction(command, response)
            return response

        prompt = self.build_prompt(command)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=80,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True)
        response = self.clean_output(decoded.split("<OUT>")[-1])

        self.history.append({"command": command, "output": response})
        self.log_interaction(command, response)

        return response

    def log_interaction(self, command, response):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "hostname": self.hostname,
            "cwd": self.cwd,
            "command": command,
            "response": response,
            "response_length": len(response),
        }

        log_file = LOG_DIR / "honeymind_sessions.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")