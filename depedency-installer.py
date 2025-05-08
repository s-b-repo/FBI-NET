#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil
import tarfile
import zipfile
import tempfile
import re
from urllib.parse import urlparse

def download_file(url, dest_path):
    print(f"[~] Downloading from {url}")
    if shutil.which("wget"):
        result = subprocess.run(["wget", "-O", dest_path, url])
    elif shutil.which("curl"):
        result = subprocess.run(["curl", "-L", "-o", dest_path, url])
    else:
        import urllib.request
        try:
            with urllib.request.urlopen(url) as r, open(dest_path, "wb") as f:
                f.write(r.read())
            result = 0
        except Exception as e:
            print(f"[!] Python download error: {e}")
            return False
    return result.returncode == 0 if isinstance(result, subprocess.CompletedProcess) else True

def install_pip():
    try:
        subprocess.run(["python3", "-m", "pip", "--version"], check=True, stdout=subprocess.DEVNULL)
        print("[+] pip already installed")
    except subprocess.CalledProcessError:
        print("[~] Installing pip...")
        subprocess.run(["curl", "-sS", "https://bootstrap.pypa.io/get-pip.py", "-o", "/tmp/get-pip.py"])
        subprocess.run(["python3", "/tmp/get-pip.py"])

def install_os_packages():
    print("[~] Installing common Python build dependencies...")
    packages = ["python3-pip", "python3-dev", "build-essential"]
    managers = {
        "apt": ["apt", "update", "&&", "apt", "install", "-y"] + packages,
        "dnf": ["dnf", "install", "-y"] + packages,
        "yum": ["yum", "install", "-y"] + packages,
        "apk": ["apk", "add"] + packages,
        "pacman": ["pacman", "-Sy", "--noconfirm"] + packages,
    }
    for mgr, cmd in managers.items():
        if shutil.which(mgr):
            subprocess.call(" ".join(cmd), shell=True)
            break

def extract_archive(archive_path, extract_to):
    print(f"[~] Extracting {archive_path}")
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        print("[!] Unknown archive type")
        return False
    return True

def parse_requirements_from_py(py_file):
    print(f"[~] Parsing imports from {py_file}")
    reqs = set()
    with open(py_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                mod = re.findall(r'(?:import|from)\s+([\w_]+)', line)
                if mod:
                    reqs.add(mod[0])
    stdlib = {"os", "sys", "re", "subprocess", "shutil", "time", "tempfile", "socket", "random", "threading", "asyncio", "pathlib"}
    third_party = reqs - stdlib
    return list(third_party)

def pip_install(args):
    version_info = sys.version_info
    if version_info.major == 3 and version_info.minor >= 11:
        cmd = ["pip3", "install", "--break-system-packages"] + args
    else:
        cmd = ["pip3", "install", "--user"] + args
    subprocess.run(cmd)

def install_requirements(requirements_path=None, fallback_py=None):
    if requirements_path and os.path.exists(requirements_path):
        print(f"[~] Installing from {requirements_path}")
        pip_install(["-r", requirements_path])
    elif fallback_py:
        inferred = parse_requirements_from_py(fallback_py)
        if inferred:
            print(f"[~] Inferred requirements: {inferred}")
            pip_install(inferred)
        else:
            print("[!] No third-party requirements found.")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <URL-to-zip|tar.gz|.py>")
        sys.exit(1)

    url = sys.argv[1]
    filename = os.path.basename(urlparse(url).path)
    tempdir = tempfile.mkdtemp()
    archive_path = os.path.join(tempdir, filename)

    if not download_file(url, archive_path):
        print("[!] Failed to download the file.")
        sys.exit(1)

    install_os_packages()
    install_pip()

    extract_path = os.path.join(tempdir, "extracted")
    os.makedirs(extract_path, exist_ok=True)

    if filename.endswith((".zip", ".tar.gz", ".tgz")):
        if not extract_archive(archive_path, extract_path):
            print("[!] Failed to extract archive")
            sys.exit(1)
    elif filename.endswith(".py"):
        shutil.copy(archive_path, extract_path)
    else:
        print("[!] Unsupported file type.")
        sys.exit(1)

    req_path = os.path.join(extract_path, "requirements.txt")
    py_files = [f for f in os.listdir(extract_path) if f.endswith(".py")]
    main_py = os.path.join(extract_path, py_files[0]) if py_files else None

    install_requirements(req_path if os.path.exists(req_path) else None, main_py)

    print("[+] Installation complete.")
    print(f"[~] Files extracted to: {extract_path}")

if __name__ == "__main__":
    main()
