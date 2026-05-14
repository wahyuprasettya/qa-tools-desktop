# QA tools

QA tools is a modern PySide6 desktop application for turning raw text copied from ChatGPT into clean Excel or CSV tables.

## Features

- Paste raw ChatGPT output, markdown tables, TSV, CSV, semicolon tables, spaced text, or key-value text.
- Detect, normalize, and clean headers, rows, whitespace, duplicate columns, and empty rows or columns.
- Preview and edit data in a fast Qt table model backed by pandas.
- Export `.xlsx` with bold headers, frozen top row, filters, zebra striping, wrapped text, alignment, and auto column widths.
- Export `.csv`.
- Persist settings, export history, and the last pasted session locally.
- Dark UI by default with optional light theme, custom title bar, sidebar, drag and drop, toasts, and keyboard shortcuts.
- Built-in QSS themes, so Python 3.12+ installs do not depend on older theme packages with restrictive Python version pins.

## Architecture

The application separates UI from business logic:

- `app/core`: constants, paths, exceptions, logging.
- `app/services`: parser, exporter, history, settings, session, themes, file manager.
- `app/models`: Qt table model for pandas dataframes.
- `app/widgets`: reusable window chrome, sidebar, and toast components.
- `app/ui`: screens and main window composition.
- `app/assets/styles`: QSS themes.

Parsing and exporting run through Qt workers so the UI stays responsive while large tables are processed.

## Run Locally

On Linux, install the Qt xcb runtime dependency first:

```bash
# Debian/Ubuntu
sudo apt install libxcb-cursor0

# Fedora
sudo dnf install xcb-util-cursor

# Arch
sudo pacman -S xcb-util-cursor
```

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
```

On Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
```

If your system does not have a `python3.12` command, use the Python 3.12+ launcher available on your machine, such as `python`, `py -3.12`, or a full interpreter path.

### Linux Qt xcb Error

If Qt prints this error:

```text
Could not load the Qt platform plugin "xcb" in "" even though it was found.
```

install the xcb cursor package for your distribution, then run the app again. On Debian and Ubuntu the package is:

```bash
sudo apt install libxcb-cursor0
```

If you are on Wayland and still hit xcb issues, try:

```bash
QT_QPA_PLATFORM=wayland python -m app.main
```

## Keyboard Shortcuts

- `Ctrl+N`: open Paste screen
- `Ctrl+R`: detect table
- `Ctrl+E`: open Export screen
- `Ctrl+,`: open Settings

## Example Input

Use `examples/chatgpt_markdown_table.txt`:

```text
| Product | Region | Q1 Revenue | Notes |
|---|---:|---:|---|
| Atlas CRM | North America | 184000 | Strong renewal motion |
```

## Packaging

Install dependencies, then build with PyInstaller:

```bash
pyinstaller packaging/tableforge.spec --noconfirm
```

The bundled application is created under `dist/QA tools`.

Linux notes:

```bash
sudo apt install python3.12 python3.12-venv libxcb-cursor0
pyinstaller packaging/tableforge.spec --noconfirm
```

Windows notes:

```powershell
python -m pip install -r requirements.txt
pyinstaller packaging\tableforge.spec --noconfirm
```

macOS can be built from the same spec on a macOS host. Add signing/notarization in your release pipeline if distributing publicly.
