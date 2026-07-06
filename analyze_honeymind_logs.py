import json
from collections import Counter, defaultdict
from pathlib import Path

LOG_FILE = Path("logs/honeymind_sessions.jsonl")

CATEGORIES = {
    "reconnaissance": [
        "whoami", "id", "hostname", "pwd", "ls", "uname", "df", "free",
        "ps", "ss", "netstat", "ifconfig", "ip a", "cat /etc/os-release"
    ],
    "credential_access": [
        ".env", "config.php", "wp-config.php", "DB_PASSWORD", "password",
        "SECRET", "authorized_keys", "id_rsa", "shadow"
    ],
    "persistence": [
        "crontab", "authorized_keys", "ssh-rsa", "systemctl enable",
        "nohup", "history -c", "unset HISTFILE"
    ],
    "malware_staging": [
        "curl", "wget", "chmod +x", "./bot.sh", "payload", "bot.sh",
        "tar -czf", "base64", "scp"
    ],
    "defense_evasion": [
        "rm -f", "auth.log", "bash_history", "kill -9", "auditd"
    ],
}


def classify_command(command):
    command_lower = command.lower()
    matches = []

    for category, indicators in CATEGORIES.items():
        for indicator in indicators:
            if indicator.lower() in command_lower:
                matches.append(category)
                break

    return matches or ["unknown"]


def risk_score(categories, command_count):
    score = 0

    weights = {
        "reconnaissance": 1,
        "credential_access": 3,
        "persistence": 4,
        "malware_staging": 5,
        "defense_evasion": 5,
        "unknown": 1,
    }

    for category, count in categories.items():
        score += weights.get(category, 1) * count

    score += min(command_count, 20)

    if score >= 35:
        return "high", score
    if score >= 15:
        return "medium", score
    return "low", score


def main():
    if not LOG_FILE.exists():
        print("No HoneyMind logs found yet.")
        return

    sessions = defaultdict(list)

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            event = json.loads(line)
            session_id = event.get("session_id", "legacy-session")
            sessions[session_id].append(event)

    print("HoneyMind Session Analysis")
    print("=" * 80)
    print(f"Total sessions: {len(sessions)}")
    print()

    for session_id, events in sessions.items():
        commands = [e["command"] for e in events]
        category_counts = Counter()

        for cmd in commands:
            for cat in classify_command(cmd):
                category_counts[cat] += 1

        risk, score = risk_score(category_counts, len(commands))

        print(f"Session: {session_id}")
        print(f"Commands: {len(commands)}")
        print(f"Risk: {risk.upper()} ({score})")
        print("Categories:", dict(category_counts))
        print("Command timeline:")

        for i, cmd in enumerate(commands, 1):
            cats = ",".join(classify_command(cmd))
            print(f"  {i:02d}. [{cats}] {cmd}")

        print("-" * 80)


if __name__ == "__main__":
    main()
