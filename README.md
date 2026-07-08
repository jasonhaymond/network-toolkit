# 🌐 Network Toolkit

> A cross-platform network diagnostics toolkit for people who would rather fix the network than argue with it.  
> Works on **macOS**, **Windows 10+**, and **Ubuntu-based Linux**.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Platforms" src="https://img.shields.io/badge/Platforms-macOS%20%7C%20Windows%20%7C%20Linux-green">
  <img alt="Status" src="https://img.shields.io/badge/Status-Field%20Toolkit-orange">
</p>

---

## ✨ What This Does

Network Toolkit gathers common troubleshooting checks into one menu-driven app:

| Area | What it checks |
|---|---|
| 🖧 Interfaces | IP, MAC, netmask, subnet, useful/all interface views |
| 🌍 Internet | Reachability, DNS, speed test |
| 📶 Wi-Fi | SSID/BSSID where OS permissions allow it, signal, channel, AP scan |
| 🔌 Switching | LLDP switch/port discovery where supported |
| 🧪 Connection Quality | TCP, HTTPS, DNS, ICMP, iPerf3, health score |
| 📄 Reports | JSON, CSV, and formatted HTML reports |
| 🛠 Permissions | Platform-specific setup and permission help |

Because apparently the only thing harder than fixing a network is remembering seventeen different commands across three operating systems.

---

## 🚀 Quick Start

### macOS

After unzipping, double-click:

```text
launch.command
```

Or from Terminal:

```bash
cd ~/Downloads/network-toolkit
./launch.command
```

Recommended first-time setup:

```bash
cd ~/Downloads/network-toolkit
./install.sh
./launch.sh
```

### Linux / Ubuntu

```bash
cd ~/Downloads/network-toolkit
chmod +x install.sh launch.sh
./install.sh
./launch.sh
```

### Windows 10+

Open PowerShell or Windows Terminal in the project folder:

```powershell
install.bat
launch.bat
```

For best results on Windows, run PowerShell or Windows Terminal as Administrator.

---

## 🧭 Launcher Menu

```text
1) Start Network Toolkit
2) Start Network Toolkit (Administrator Mode)
3) Install/Update Dependencies
4) Rebuild Virtual Environment
5) Exit
```

---

## 🗂 Project Layout

```text
network-toolkit/
├── main.py
├── settings.yaml
├── requirements.txt
├── launch.sh
├── launch.command
├── launch.bat
├── install.sh
├── install.bat
├── core/
│   ├── config.py
│   ├── exports.py
│   └── utils.py
├── modules/
│   ├── connection_quality.py
│   ├── dns.py
│   ├── gateway.py
│   ├── interfaces.py
│   ├── internet.py
│   ├── permissions.py
│   ├── scanning.py
│   ├── switch.py
│   └── wifi.py
└── scripts/
    ├── unix/
    └── windows/
```

The root launcher files are intentionally small. The real launch/install logic lives in `scripts/`, because copy-pasting the same bug into four files is not software architecture, it is gardening for gremlins.

---

## 🎛 Main Menu

```text
1) Useful Interface / IP Info
2) All Interface / IP Info
3) Gateway Info
4) DNS Test
5) Internet Reachability
6) Internet Speed Test
7) Wi-Fi Info
8) Wi-Fi AP Scan
9) Advanced Wi-Fi Diagnostics
10) Subnet Scan
11) Switch + Port Info
12) Connection Tests
13) Restart in Administrator Mode
14) Permissions / Setup Help
15) Export Reports
16) Settings

0) Exit
```

All menus use:

```text
0) Exit
```

or:

```text
0) Return
```

There is a blank row above exit/return options because visual spacing is cheaper than confusion. Revolutionary stuff.

---

# 🧪 Connection Tests

The old ICMP-only latency/jitter test has been replaced with a **Connection Tests** submenu.

Why? Because many corporate networks block ICMP ping. The network may be fine, but ping gets tossed into a firewall dungeon.

#



## True DNS Lookup Timing

The DNS connection test now measures actual DNS query time instead of timing the `nslookup` process.

Why this matters:

```text
nslookup timing = process startup + endpoint security + resolver behavior + output parsing + DNS lookup
true DNS timing = DNS query/response time
```

The toolkit now uses:

1. `dnspython` direct query to the configured DNS server
2. system resolver fallback if direct DNS is unavailable

This means the DNS latency result should be much closer to what you expect when manually running a fast lookup, instead of showing an 8-second average because the subprocess wandered through corporate security theater before doing its job.

## DNS Connection Test Fix

The DNS connection-quality test now uses a safer two-step method:

1. System resolver lookup with Python `socket.getaddrinfo()`
2. Optional `nslookup` against the configured DNS server

This avoids false DNS failures on corporate networks where `nslookup` may take longer to start, get inspected by endpoint security, or behave differently when called from a subprocess. Because apparently DNS needed plot twists.

# Connection Tests Submenu

```text
1) Run Auto Quality Test
2) Run All Tests
3) TCP Connect Test
4) HTTPS Request Test
5) DNS Lookup Test
6) ICMP Ping Test
7) iPerf3 Test
8) Show Score Inclusion Settings

0) Return to Main Menu
```

## Methods

| Method | What it measures | Works when ICMP is blocked? |
|---|---:|---:|
| TCP Connect | Time to open a TCP socket | ✅ Usually |
| HTTPS Request | DNS + TCP + TLS + first byte | ✅ Usually |
| DNS Lookup | Resolver latency | ✅ Usually |
| ICMP Ping | Traditional ping | ❌ Often blocked |
| iPerf3 | Throughput/performance to server | ✅ If server exists |

## Health Score Exclusions

Some tests may be expected to fail. For example, ICMP is often blocked on corporate networks. You can exclude methods from the health score:

```yaml
connection_quality_score_include_tcp: true
connection_quality_score_include_https: true
connection_quality_score_include_dns: true
connection_quality_score_include_icmp: false
connection_quality_score_include_iperf3: true
```

By default, ICMP is excluded from the health score. Ping can sulk in the corner without ruining the report card.

---

# 📄 Reports

Reports can be exported as:

| Format | Best for |
|---|---|
| JSON | Automation, future dashboards |
| CSV | Spreadsheets and inventories |
| HTML | Human-readable troubleshooting reports |

The HTML report preserves command output in readable `<pre>` blocks instead of stuffing terminal dumps into sad table cells.

---

# 🔧 Install Scripts

## macOS / Linux

```bash
./install.sh
```

The installer will:

- Check for Python 3
- Create `.venv`
- Install Python requirements
- Upgrade pip, setuptools, and wheel
- Fix executable permissions
- Install system packages where supported
- Enable `lldpd` on Linux when available

## Windows

```powershell
install.bat
```

The installer will:

- Detect Python from PATH, `py -3`, common locations, and Intune-style installs
- Offer manual `python.exe` path entry
- Create `.venv`
- Install Python requirements
- Suggest optional Nmap/Npcap/Wireshark tools

---

# 🪟 Windows / Intune Python Notes

If Python was installed through Intune or Company Portal, it may not be available as:

```powershell
python
py -3
```

The Windows installer checks:

- `py -3`
- `python`
- `python3`
- common Program Files locations
- common AppData locations
- limited Program Files and LocalAppData search
- manual `python.exe` path entry

Manual checks:

```powershell
where python
where py
Get-ChildItem "C:\Program Files" -Filter python.exe -Recurse -ErrorAction SilentlyContinue
Get-ChildItem "$env:LOCALAPPDATA" -Filter python.exe -Recurse -ErrorAction SilentlyContinue
```

If Intune installed Python without `venv` or `pip`, ask IT to include:

```text
venv
pip
setuptools
wheel
```

---

# 🍎 macOS SSID/BSSID Permissions

Newer macOS versions may redact SSID and BSSID as location-sensitive data.

Go to:

```text
System Settings → Privacy & Security → Location Services
```

Then:

1. Enable Location Services globally.
2. Enable Location Services for your terminal app:
   - Terminal
   - iTerm2
   - VS Code
3. Quit and reopen the terminal app.
4. Run the toolkit again.
5. Try Administrator Mode if needed.

If macOS itself returns `<redacted>`, the toolkit cannot reveal the value until macOS permissions allow it. The toolkit is helpful, not magical. Tragic, I know.

---

# 🐧 Ubuntu / Debian Setup

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  git \
  nmap \
  lldpd \
  wireless-tools \
  iw \
  net-tools \
  iproute2 \
  dnsutils \
  iperf3 \
  tcpdump \
  network-manager \
  curl \
  unzip
```

Enable LLDP:

```bash
sudo systemctl enable --now lldpd
```

---

# 📦 Optional Tools

| Platform | Tools |
|---|---|
| macOS | `brew install nmap lldpd speedtest-cli iperf3 arp-scan` |
| Windows | Nmap, Npcap, Wireshark |
| Ubuntu | `sudo apt install nmap lldpd iperf3 tcpdump dnsutils` |

---

# 🧠 Troubleshooting Quick Fixes

## `speedtest-cli: command not found`

```bash
pip install speedtest-cli
```

macOS:

```bash
brew install speedtest-cli
```

Ubuntu:

```bash
sudo apt install speedtest-cli
```

## `venv` missing on Ubuntu

```bash
sudo apt install python3-venv
```

## `nmap` missing

macOS:

```bash
brew install nmap
```

Ubuntu:

```bash
sudo apt install nmap
```

Windows:

```text
https://nmap.org/download.html
```

## `lldpctl` missing

macOS:

```bash
brew install lldpd
```

Ubuntu:

```bash
sudo apt install lldpd
sudo systemctl enable --now lldpd
```

Windows does not include a built-in `lldpctl` equivalent. Use Wireshark/Npcap or vendor tools, because Windows looked at LLDP visibility and chose mystery.

---

# 🧾 Current Features

- Useful interface filtering
- All interface view
- Primary/default interface detection
- Dynamic subnet detection
- Gateway info
- DNS testing
- Internet reachability
- Human-readable speed test summary
- Cross-platform Wi-Fi info
- Cross-platform Wi-Fi AP scan where OS permissions allow it
- Advanced Wi-Fi diagnostics
- Location/permission guidance
- Preferred network fallback on macOS
- Human-readable subnet scan
- LLDP switch/port discovery on macOS/Linux
- Windows LLDP guidance
- Connection Tests submenu with TCP/HTTPS/DNS/ICMP/iPerf support
- Health score exclusion settings
- JSON/CSV/HTML report exports
- Better HTML command dump formatting
- Settings menu
- Clean exit handling
- Restart in Administrator Mode
- Permissions / Setup Help

---

# 🧯 Notes

Switch and port info is collected from local LLDP/CDP-style neighbor discovery when supported. This does not require SNMP.

PoE info usually cannot be read from a basic USB-C Ethernet adapter directly. It normally comes from LLDP power negotiation or from the switch.

---

## Final Thought

This toolkit exists because opening five terminals, three system panels, two vendor apps, and one browser tab just to answer “is the network okay?” is apparently what civilization calls progress.
