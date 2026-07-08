# Network Toolkit

Cross-platform Python network diagnostics toolkit starter.

## Windows

Run:

```powershell
.\launch.bat
```

The startup audit checks external tools and can install supported dependencies automatically using winget.

## macOS/Linux

Run:

```bash
./launch.sh
```

macOS uses Homebrew when available. Linux uses apt when available.

## Notes

- Nmap powers subnet scans, port scans, and fingerprinting.
- LLDP switch/port discovery requires LLDP enabled on the switch and lldpd/lldpctl installed.
- USB-C Ethernet adapters usually cannot directly read PoE voltage or power. PoE info typically comes from LLDP or switch data.
- Some installs may require reopening the terminal so PATH refreshes. Because apparently that is civilization.
