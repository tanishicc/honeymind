from honeymind.models.honeymind_engine import HoneyMindEngine

BANNER = r"""
 _   _                        __  __ _           _
| | | | ___  _ __   ___ _   _|  \/  (_)_ __   __| |
| |_| |/ _ \| '_ \ / _ \ | | | |\/| | | '_ \ / _` |
|  _  | (_) | | | |  __/ |_| | |  | | | | | | (_| |
|_| |_|\___/|_| |_|\___|\__, |_|  |_|_|_| |_|\__,_|
                         |___/

HoneyMind AI Deception Honeypot
Ubuntu 20.04.6 LTS
"""

PROMPT_USER = "root@prod-web-01"


def main():
    print(BANNER)

    engine = HoneyMindEngine()

    while True:
        try:
            cmd = input(f"{PROMPT_USER}:{engine.cwd}# ").strip()

            if not cmd:
                continue

            if cmd in ["exit", "quit"]:
                print("logout")
                break

            if cmd == "clear":
                print("\033c", end="")
                continue

            if cmd == "history":
                for i, item in enumerate(engine.history, 1):
                    print(f"{i}  {item['command']}")
                continue

            output = engine.generate_response(cmd)

            if output:
                print(output)

        except KeyboardInterrupt:
            print("\nlogout")
            break


if __name__ == "__main__":
    main()
