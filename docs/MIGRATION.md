# Migration baseline

Source repository: `yunfei00/instrument-automation-platform`.

The standalone project currently carries the reusable bridge logic without importing the instrument automation platform:

- raw TCP-to-TCP forwarding
- VISA/USBTMC-to-TCP SCPI bridging
- single-client ownership
- connection/discovery helpers
- PySide6 GUI
- protocol tests

The old instrument repository remains unchanged during this first migration so the existing production path is not broken.

## Next migration steps

1. Restore the full legacy Tkinter VISA screen in the standalone package.
2. Move/adapt PyInstaller Windows and FSW-legacy packaging.
3. Add Linux/headless packaging.
4. Add reverse TCP tunneling as a new feature after the extracted baseline is stable.
