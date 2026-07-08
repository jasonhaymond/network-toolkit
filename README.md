# Network Toolkit Python v3.6

Cross-platform modular network diagnostics toolkit for:

- macOS
- Windows 10+
- Ubuntu-based Linux

## Quick Start — macOS

### Easiest Method

After unzipping, double-click:

```text
launch.command
```

Or from Terminal:

```bash
cd ~/Downloads/network-toolkit-python-v3.6
./launch.command
```

`launch.command` automatically fixes `launch.sh` permissions after ZIP extraction and then starts the launcher.

### Terminal Method

If you prefer Terminal:

```bash
cd ~/Downloads/network-toolkit-python-v3.6
./launch.sh
```

If macOS still says it is not executable:

```bash
chmod +x launch.command launch.sh
./launch.command
```

## Quick Start — Linux / Ubuntu

```bash
cd ~/Downloads/network-toolkit-python-v3.6
chmod +x launch.sh
./launch.sh
```

## Quick Start — Windows 10+

Open PowerShell or Windows Terminal in the project folder:

```powershell
launch.bat
```

For best results on Windows, run PowerShell or Windows Terminal as Administrator.

## Launcher Menu

```text
1) Start Network Toolkit
2) Start Network Toolkit (Administrator Mode)
3) Install/Update Dependencies
4) Rebuild Virtual Environment
5) Exit
```

## New in v3.6

- Added `launch.command` for macOS.
- `launch.command` automatically runs `chmod +x launch.sh`.
- Packaged `launch.sh` and `launch.command` with executable permissions.
- Keeps the single main launcher workflow.
- Keeps Windows `launch.bat`.

## Permissions / Setup Help

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

## macOS SSID/BSSID Permissions

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

The toolkit uses:

1. CoreWLAN through PyObjC
2. `system_profiler`
3. `networksetup`
4. preferred Wi-Fi networks
5. legacy `airport` if available
6. `wdutil` diagnostics

If macOS itself returns `<redacted>`, the toolkit cannot reveal the value until macOS permissions allow it.

## Windows 10+ Notes

Recommended optional tools:

- Python 3
- Nmap
- Npcap
- Windows Terminal

Useful built-in collectors:

```powershell
netsh wlan show interfaces
netsh wlan show networks mode=bssid
Get-NetAdapter
Get-NetIPConfiguration
```

For best results, run as Administrator.

## Ubuntu/Linux Notes

Recommended packages:

```bash
sudo apt update
sudo apt install nmap lldpd wireless-tools iw net-tools iproute2 dnsutils iperf3 tcpdump network-manager
sudo systemctl enable --now lldpd
```

For privileged tests:

```bash
sudo .venv/bin/python main.py
```

## Optional Tools

### macOS

```bash
brew install nmap lldpd speedtest-cli iperf3 arp-scan
```

### Windows

Install:

- Nmap
- Npcap
- Wireshark, optional

### Ubuntu/Linux

```bash
sudo apt install nmap lldpd iperf3 tcpdump dnsutils
```

## Current Features

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

## Notes

Switch and port info is collected from local LLDP/CDP-style neighbor discovery when supported. This does not require SNMP.

PoE info usually cannot be read from a basic USB-C Ethernet adapter directly. It normally comes from LLDP power negotiation or from the switch.
