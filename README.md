# Network Toolkit

Cross-platform modular network diagnostics toolkit for:

- macOS
- Windows 10+
- Ubuntu-based Linux

No version number is used in the project folder or app title so you can replace/update the folder without changing your workflow. Humanity briefly defeats chaos. Briefly.

---

## Quick Start — macOS

After unzipping, double-click:

```text
launch.command
```

Or from Terminal:

```bash
cd ~/Downloads/network-toolkit
./launch.command
```

### Recommended First-Time Setup

```bash
cd ~/Downloads/network-toolkit
./install.sh
./launch.sh
```

---

## Quick Start — Linux / Ubuntu

```bash
cd ~/Downloads/network-toolkit
chmod +x install.sh launch.sh
./install.sh
./launch.sh
```

---

## Quick Start — Windows 10+

Open PowerShell or Windows Terminal in the project folder:

```powershell
install.bat
launch.bat
```

For best results on Windows, run PowerShell or Windows Terminal as Administrator.

---

# Launcher Menu

```text
1) Start Network Toolkit
2) Start Network Toolkit (Administrator Mode)
3) Install/Update Dependencies
4) Rebuild Virtual Environment
5) Exit
```

---

# Install Scripts

## macOS / Linux

Use:

```bash
./install.sh
```

The installer will:

- Check for Python 3
- Create `.venv`
- Install Python requirements
- Install/update pip, setuptools, and wheel
- Fix executable permissions
- On macOS, install Homebrew packages if Homebrew is available
- On Ubuntu/Linux, install apt packages
- Enable `lldpd` on Linux when available

## Windows

Use:

```powershell
install.bat
```

The installer will:

- Check for Python
- Warn if Git is missing
- Create `.venv`
- Install Python requirements
- Upgrade pip, setuptools, and wheel
- Suggest Nmap/Npcap/Wireshark

---

# Manual Setup Instructions

## macOS Manual Setup

### 1. Install Apple Command Line Tools

```bash
xcode-select --install
```

### 2. Install Homebrew

Homebrew is optional but strongly recommended:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. Install Required / Recommended Packages

```bash
brew install python git nmap lldpd iperf3 arp-scan speedtest-cli
```

### 4. Create the Python Virtual Environment

```bash
cd ~/Downloads/network-toolkit
python3 -m venv .venv
```

### 5. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### 6. Install Python Requirements

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 7. Launch

```bash
python main.py
```

Or:

```bash
./launch.sh
```

### 8. Admin Mode

```bash
sudo .venv/bin/python main.py
```

---

## Windows 10+ Manual Setup

### 1. Install Python

Download Python 3 from:

```text
https://www.python.org/downloads/windows/
```

During installation, check:

```text
Add python.exe to PATH
```

Yes, the tiny checkbox matters. Because apparently software installers enjoy scavenger hunts.

### 2. Install Git

Download Git for Windows:

```text
https://git-scm.com/download/win
```

### 3. Optional Network Tools

Install:

```text
Nmap + Npcap:
https://nmap.org/download.html

Wireshark:
https://www.wireshark.org/
```

### 4. Open Terminal

Open PowerShell or Windows Terminal. For best results, right-click and choose:

```text
Run as administrator
```

### 5. Create Virtual Environment

```powershell
cd $env:USERPROFILE\Downloads\network-toolkit
python -m venv .venv
```

### 6. Install Python Requirements

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.venv\Scripts\pip.exe install -r requirements.txt
```

### 7. Launch

```powershell
.venv\Scripts\python.exe main.py
```

Or:

```powershell
launch.bat
```

---

## Ubuntu / Debian-Based Linux Manual Setup

### 1. Install Required Packages

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

### 2. Enable LLDP

```bash
sudo systemctl enable --now lldpd
```

### 3. Create Virtual Environment

```bash
cd ~/Downloads/network-toolkit
python3 -m venv .venv
```

If this fails:

```bash
sudo apt install python3-venv
```

Because Linux likes making you earn conveniences with tiny missing packages. Charming.

### 4. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 5. Install Python Requirements

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 6. Launch

```bash
python main.py
```

Or:

```bash
./launch.sh
```

### 7. Admin Mode

```bash
sudo .venv/bin/python main.py
```

---



## Windows install.bat troubleshooting

If you see:

```text
The system cannot find the path specified.
```

during pip or requirements installation, the virtual environment did not build correctly or `.venv\Scripts\python.exe` is missing.

The installer now checks this and stops instead of pretending everything is fine, because apparently batch files learned honesty late in life.

Try:

```powershell
rmdir /s /q .venv
install.bat
```

Also confirm Python works:

```powershell
py -3 --version
python --version
```

If both fail, reinstall Python from python.org and check:

```text
Add python.exe to PATH
```


# Fixing Common Missing Package Problems

## `speedtest-cli: command not found`

The toolkit installs the Python package automatically:

```bash
pip install speedtest-cli
```

On macOS with Homebrew:

```bash
brew install speedtest-cli
```

On Ubuntu:

```bash
sudo apt install speedtest-cli
```

If the shell command still fails, run:

```bash
./install.sh
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

Windows does not include a built-in `lldpctl` equivalent. Use Wireshark/Npcap or vendor tools.

---

# Permissions / Setup Help

Inside the toolkit, choose:

```text
Permissions / Setup Help
```

This shows platform-specific instructions for:

- macOS Location Services
- macOS Terminal/iTerm/VS Code permissions
- Windows Administrator Mode
- Windows Nmap/Npcap suggestions
- Ubuntu package installation
- Linux LLDP service setup
- Wi-Fi scanning permissions

---

# macOS SSID/BSSID Permissions

Newer macOS versions may redact SSID and BSSID as location-sensitive data.

Go to:

```text
System Settings → Privacy & Security → Location Services
```

Then:

1. Enable Location Services globally.
2. Enable Location Services for the terminal app you use:
   - Terminal
   - iTerm2
   - VS Code
3. Quit and reopen the terminal app.
4. Run the toolkit again.
5. Try Administrator Mode if needed.

If macOS itself returns `<redacted>`, the toolkit cannot reveal the value until macOS permissions allow it.

---

# Current Features

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
- Latency/jitter monitor
- JSON/CSV/HTML report exports
- Settings menu
- Clean exit handling
- Restart in Administrator Mode
- Permissions / Setup Help

---

# Notes

Switch and port info is collected from local LLDP/CDP-style neighbor discovery when supported. This does not require SNMP.

PoE info usually cannot be read from a basic USB-C Ethernet adapter directly. It normally comes from LLDP power negotiation or from the switch.
