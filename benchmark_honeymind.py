import json
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

MODELS = {
    "masked": "honeymind/models/honeymind-tinyllama-lora-masked-v1/checkpoint-400",
    "v5": "honeymind/models/honeymind-tinyllama-lora-v5-task",
    "v6": "honeymind/models/honeymind-tinyllama-lora-v6",
    "v7": "honeymind/models/honeymind-tinyllama-lora-v7-targeted",
    "v8": "honeymind/models/honeymind-tinyllama-lora-v8-repair",
    "v9": "honeymind/models/honeymind-tinyllama-lora-v9-replay",
}

TASK_MAP = {
    "whoami": "identity",
    "id": "identity",
    "hostname": "identity",
    "pwd": "working_directory",
    "ls -la": "directory_listing",
    "cat .env": "read_env_file",
    "cat config.php": "read_config_file",
    "cat /etc/os-release": "system_info",
    "uname -r": "system_info",
    "uptime": "system_info",
    "df -h": "system_info",
    "find / -name '*.env' 2>/dev/null": "find_files",
    "find / -name '*.sql' 2>/dev/null": "find_files",
    "grep -R \"DB_PASSWORD\" . 2>/dev/null": "grep_credentials",
    "grep -R \"password\" . 2>/dev/null": "grep_credentials",
    "ps aux": "process_enum",
    "ss -tulpn": "network_enum",
    "sudo -l": "sudo_policy",
    "crontab -l": "persistence",
    "cat ~/.ssh/authorized_keys": "persistence",
}

def build_prompt(cmd):
    task = TASK_MAP.get(cmd, "unknown")
    return f"""<TASK>
{task}
</TASK>
<CTX>
hostname=prod-web-01
os=Ubuntu 20.04.6 LTS
kernel=5.4.0-148-generic
stack=nginx/php/mysql
web_root=/var/www/html
database=mysql
user=root
cwd=/var/www/html
known_files=.env, config.php, index.php, admin, uploads
services=ssh, nginx, mysql
</CTX>
<CMD>
{cmd}
</CMD>
<OUT>
"""

def clean(text):
    if "</OUT>" in text:
        text = text.split("</OUT>")[0]
    return text.replace("\\n", "\n").strip()

def generate(model, tokenizer, cmd, device):
    prompt = build_prompt(cmd)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=False,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )
    decoded = tokenizer.decode(output[0], skip_special_tokens=True)
    return clean(decoded.split("<OUT>")[-1])

def main():
    model_key = sys.argv[1] if len(sys.argv) > 1 else "v6"
    adapter = MODELS[model_key]

    with open("benchmark_commands.json") as f:
        tests = json.load(f)

    device = "cpu"

    tokenizer = AutoTokenizer.from_pretrained(adapter)
    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    model = PeftModel.from_pretrained(base, adapter).to(device)
    model.eval()

    passed = 0

    print(f"Benchmarking model: {model_key}")
    print("=" * 80)

    for test in tests:
        cmd = test["cmd"]
        expected = test["contains"]
        output = generate(model, tokenizer, cmd, device)

        ok = any(token.lower() in output.lower() for token in expected)
        passed += int(ok)

        print(f"\n[{ 'PASS' if ok else 'FAIL' }] {cmd}")
        print("Expected one of:", expected)
        print("Output:")
        print(output[:500])

    print("\n" + "=" * 80)
    print(f"Score: {passed}/{len(tests)} = {passed / len(tests) * 100:.1f}%")

if __name__ == "__main__":
    main()