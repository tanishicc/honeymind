def simulate_response(world, command):
    cmd = command.strip()

    simple = {
        "whoami": "root",
        "id": "uid=0(root) gid=0(root) groups=0(root)",
        "hostname": world.hostname,
        "pwd": world.cwd,
        "uname -r": world.kernel,
        "groups": "root",
        "env": "SHELL=/bin/bash\nPWD=/root\nHOME=/root\nUSER=root\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "printenv": "SHELL=/bin/bash\nPWD=/root\nHOME=/root\nUSER=root\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "w": "root     pts/0    203.0.113.42     10:38    1.00s  0.02s  0.00s w",
        "last": "root     pts/0        203.0.113.42     Tue Jun 23 10:38   still logged in",
        "history -c": "",
        "unset HISTFILE": "",
    }


    if cmd == "cat /etc/os-release":
        return "NAME=\"Ubuntu\"\nVERSION=\"20.04.6 LTS (Focal Fossa)\"\nID=ubuntu\nPRETTY_NAME=\"Ubuntu 20.04.6 LTS\""

    if cmd in simple:
        return simple[cmd]

    if cmd == "history":
        return "  1  cd /var/www/html\n  2  nano .env\n  3  mysql -u webuser -p\n  4  systemctl restart nginx\n  5  logout"

    if cmd == "who":
        return "root     pts/0        2026-06-23 10:38 (203.0.113.42)"

    if cmd == "cat package.json":
        return "{\\n  \"name\": \"client-api\",\\n  \"version\": \"1.0.0\",\\n  \"main\": \"app.js\",\\n  \"dependencies\": {\\n    \"express\": \"^4.18.2\",\\n    \"dotenv\": \"^16.0.3\"\\n  }\\n}"


    if cmd == "systemctl list-units --type=service --state=running":
        return "\n".join([f"{s}.service loaded active running {s} service" for s in world.services])

    if cmd.startswith("grep -R"):
        return "\n".join([f"{p}:{line}" for p, c in world.file_contents.items() for line in c.splitlines() if "PASS" in line or "SECRET" in line or "password" in line.lower()])

    if cmd == "base64 /backup/old.env":
        return "REJfSE9TVD1sb2NhbGhvc3QKREJfVVNFUj1iYWNrdXBfYWRtaW4KREJfUEFTUz1iYWNrdXBfMjAyMl9vbGQh"

    if cmd.startswith("curl -F"):
        return "OK"

    if cmd.startswith("scp "):
        return "ssh: connect to host 192.168.1.50 port 22: Connection timed out"

    if cmd == "cat /backup/db_backup.sql":
        return "-- MySQL dump\nCREATE TABLE users (id int, email varchar(255), password varchar(255));"

    if cmd == "find / -perm -4000 -type f 2>/dev/null":
        return "/usr/bin/passwd\n/usr/bin/sudo\n/bin/mount\n/bin/su"

    if cmd == "sudo -l":
        return f"User root may run the following commands on {world.hostname}:\n    (ALL : ALL) ALL"

    if cmd == "ls -la /tmp":
        return "total 16\ndrwxrwxrwt 4 root root 4096 Jun 23 10:24 .\ndrwxr-xr-x 1 root root 4096 Jun 12 10:20 ..\ndrwxr-xr-x 2 root root 4096 Jun 23 10:42 .x"

    if cmd == "cat ~/.ssh/authorized_keys":
        return "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCprodkey deploy@ci-server"

    if cmd == "find / -name '*.sql' 2>/dev/null":
        return "/backup/db_backup.sql"

    if cmd == "find / -name '*.bak' 2>/dev/null":
        return "/backup/site_backup.tar.gz"

    if cmd == "getcap -r / 2>/dev/null":
        return "/usr/bin/python3.8 = cap_setuid+ep"

    if cmd == "cat /etc/sudoers":
        return "root ALL=(ALL:ALL) ALL\n%sudo ALL=(ALL:ALL) ALL"

    if cmd in ["ls ~/.ssh", "ls -la ~/.ssh"]:
        return "authorized_keys\nknown_hosts"

    if cmd.startswith("mkdir -p "):
        return ""

    if "authorized_keys" in cmd and cmd.startswith("echo "):
        return ""

    if "crontab -" in cmd and cmd.startswith("echo "):
        return ""

    if cmd == "ls -la /etc/cron.d":
        return "e2scrub_all\nphp\ncertbot"

    if cmd.startswith("nohup "):
        return "[1] 18422"

    if cmd == "systemctl list-timers":
        return "logrotate.timer loaded active waiting Daily rotation of log files"

    if cmd.startswith("rm -f "):
        return ""

    if cmd.startswith("kill -9 "):
        return "kill: usage: kill [-s sigspec | -n signum] pid"

    if cmd.startswith("tar -czf "):
        return ""

    if cmd.startswith("cd "):
        target = cmd.split(" ", 1)[1]
        if target in world.filesystem:
            world.cwd = target
            world.known_files.update(world.filesystem[target])
            return ""
        return f"bash: cd: {target}: No such file or directory"

    if cmd in ["ls", "ls -la"]:
        files = world.filesystem.get(world.cwd, [])
        return "\n".join(files)

    if cmd.startswith("cat "):
        target = cmd.split(" ", 1)[1]
        path = target if target.startswith("/") else world.cwd + "/" + target
        if path in world.file_contents:
            return world.file_contents[path]
        if target == "/etc/passwd":
            return world.file_contents["/etc/passwd"]
        return f"cat: {target}: No such file or directory"

    if cmd == "uname -a":
        return f"Linux {world.hostname} {world.kernel} #165-Ubuntu SMP x86_64 GNU/Linux"

    if cmd == "cat /etc/os-release":
        return 'NAME="Ubuntu"\nVERSION="20.04.6 LTS (Focal Fossa)"\nID=ubuntu'

    if cmd == "uptime":
        return "10:42:18 up 41 days, 3:17, 1 user, load average: 0.08, 0.05, 0.01"

    if cmd == "df -h":
        return "Filesystem Size Used Avail Use% Mounted on\n/dev/xvda1 30G 18G 11G 63% /"

    if cmd == "free -m":
        return "Mem: 1987 812 344 12 830 982\nSwap: 0 0 0"

    if cmd.startswith("find / -name '*.env'"):
        return "\n".join([p for p in world.file_contents if p.endswith(".env")])

    if cmd.startswith("find / -name '*config*'"):
        return "\n".join([p for p in world.file_contents if "config" in p])

    if cmd in ["ps aux", "netstat -tulpn", "ss -tulpn"]:
        return "root 721 0.0 sshd\nroot 931 0.0 web service\nwww-data 944 0.1 worker"

    if cmd.startswith("systemctl status "):
        service = cmd.split("systemctl status ", 1)[1]
        if service in world.services:
            return f"● {service}.service - {service} service\nActive: active (running)"
        return f"Unit {service}.service could not be found."

    if cmd.startswith("wget ") or cmd.startswith("curl -O "):
        return "HTTP request sent, awaiting response... 200 OK\nSaving file... saved"

    if cmd.startswith("chmod "):
        return ""

    if cmd.startswith("./"):
        return "bash: ./bot.sh: cannot execute binary file: Exec format error"

    if cmd == "crontab -l":
        return "no crontab for root"

    return f"bash: {cmd}: command not found"
