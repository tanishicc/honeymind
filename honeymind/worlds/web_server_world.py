import random
from dataclasses import dataclass, field


@dataclass
class FakeServerWorld:
    hostname: str
    os: str
    kernel: str
    stack: str
    web_root: str
    database: str
    user: str = "root"
    cwd: str = "/root"
    filesystem: dict = field(default_factory=dict)
    file_contents: dict = field(default_factory=dict)
    services: list = field(default_factory=list)
    known_files: set = field(default_factory=set)


def generate_web_server_world(seed=None):
    rng = random.Random(seed)

    profiles = [
        {
            "hostname": "prod-web-01",
            "stack": "nginx/php/mysql",
            "web_root": "/var/www/html",
            "database": "mysql",
            "app_files": ["index.php", "config.php", ".env", "admin", "uploads"],
            "config_file": "config.php",
        },
        {
            "hostname": "wordpress-prod",
            "stack": "apache/php/mariadb",
            "web_root": "/var/www/html",
            "database": "mariadb",
            "app_files": ["index.php", "wp-config.php", ".env", "wp-admin", "wp-content"],
            "config_file": "wp-config.php",
        },
        {
            "hostname": "api-gateway-02",
            "stack": "nodejs/express/mongodb",
            "web_root": "/opt/app",
            "database": "mongodb",
            "app_files": ["server.js", "package.json", ".env", "routes", "controllers", "node_modules"],
            "config_file": "server.js",
        },
        {
            "hostname": "client-portal-01",
            "stack": "nginx/nodejs/postgresql",
            "web_root": "/srv/client-portal",
            "database": "postgresql",
            "app_files": ["app.js", "package.json", ".env", "public", "src", "logs"],
            "config_file": "app.js",
        },
    ]

    profile = rng.choice(profiles)

    hostname = profile["hostname"]
    stack = profile["stack"]
    web_root = profile["web_root"]
    database = profile["database"]
    app_files = profile["app_files"]
    config_file = profile["config_file"]

    db_password = rng.choice([
        "Spring2023_backup!",
        "ProdWeb2024!",
        "webapp_backup_2022",
        "ClientPortal@123",
    ])

    filesystem = {
        "/root": [".bashrc", ".bash_history", ".ssh", "backup", "deploy"],
        web_root: app_files,
        "/etc": ["passwd", "shadow", "ssh"],
        "/var/log": ["auth.log", "syslog"],
        "/backup": ["db_backup.sql", "site_backup.tar.gz", "old.env"],
    }

    if "nginx" in stack:
        filesystem["/etc"].append("nginx")
        filesystem["/var/log"].append("nginx")

    if "apache" in stack:
        filesystem["/etc"].append("apache2")
        filesystem["/var/log"].append("apache2")

    file_contents = {
        f"{web_root}/.env": (
            "APP_ENV=production\n"
            "APP_DEBUG=false\n"
            "DB_HOST=127.0.0.1\n"
            f"DB_DATABASE={hostname.replace('-', '_')}\n"
            "DB_USERNAME=webuser\n"
            f"DB_PASSWORD={db_password}"
        ),
        "/backup/old.env": (
            "DB_HOST=localhost\n"
            "DB_USER=backup_admin\n"
            "DB_PASS=backup_2022_old!"
        ),
        "/etc/passwd": (
            "root:x:0:0:root:/root:/bin/bash\n"
            "ubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\n"
            "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin"
        ),
    }

    if config_file in ["config.php", "wp-config.php"]:
        file_contents[f"{web_root}/{config_file}"] = (
            "<?php\n"
            "define('DB_HOST', 'localhost');\n"
            "define('DB_USER', 'webuser');\n"
            f"define('DB_PASSWORD', '{db_password}');\n"
            f"define('DB_NAME', '{hostname.replace('-', '_')}');\n"
            "?>"
        )

    if config_file in ["server.js", "app.js"]:
        file_contents[f"{web_root}/{config_file}"] = (
            "const express = require('express');\n"
            "const app = express();\n"
            "require('dotenv').config();\n"
            "app.get('/health', (req, res) => res.send('ok'));\n"
            "app.listen(process.env.PORT || 3000);"
        )

    services = ["ssh"]

    if "nginx" in stack:
        services.append("nginx")
    if "apache" in stack:
        services.append("apache2")
    if "mysql" in stack:
        services.append("mysql")
    if "mariadb" in stack:
        services.append("mariadb")
    if "mongodb" in stack:
        services.append("mongodb")
    if "postgresql" in stack:
        services.append("postgresql")
    if "nodejs" in stack:
        services.append("node")

    return FakeServerWorld(
        hostname=hostname,
        os="Ubuntu 20.04.6 LTS",
        kernel="5.4.0-148-generic",
        stack=stack,
        web_root=web_root,
        database=database,
        filesystem=filesystem,
        file_contents=file_contents,
        services=services,
        known_files=set(filesystem["/root"]),
    )