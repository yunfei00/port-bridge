# PortBridge

A lightweight cross-platform tool for TCP port forwarding, USB/VISA-to-TCP bridging, and reverse TCP tunneling.

## Current baseline

This repository was extracted from `yunfei00/instrument-automation-platform`.

Implemented now:
- TCP -> TCP raw byte forwarding
- USB/VISA -> TCP SCPI bridge
- Single-client exclusive sessions
- Connection test (`*IDN?`)
- VISA resource discovery
- RX/TX statistics and connection duration
- Modern PySide6 GUI
- Legacy Tkinter GUI for older Windows instrument PCs

Planned:
- Reverse TCP tunnel
- Headless CLI for Windows/Linux
- Serial/TCP adapters

## Run

```bash
python -m pip install -e ".[gui,visa]"
python -m port_bridge
```

Legacy Tkinter UI:

```bash
python -m port_bridge.legacy
```

## Notes

The VISA bridge is a SCPI message bridge, not USB-over-IP. TCP requests are newline-framed; query responses use raw VISA reads so binary IEEE 488.2 blocks can be returned unchanged.
