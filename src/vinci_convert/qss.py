"""Catppuccin Mocha palette for the PySide6 GUI.

These mirror the hex values in theme.py (Rich terminal theme) so the
desktop app and the CLI share one visual identity.
"""

# ── Catppuccin Mocha ──────────────────────────────────────────────
BASE = "#1E1E2E"
MANTLE = "#181825"
CRUST = "#11111B"

TEXT = "#CDD6F4"
SUBTEXT1 = "#BAC2DE"
SUBTEXT0 = "#A6ADC8"
OVERLAY0 = "#6C7086"

SURFACE0 = "#313244"
SURFACE1 = "#45475A"
SURFACE2 = "#585B70"

ROSEWATER = "#F5E0DC"
FLAMINGO = "#F2CDCD"
PINK = "#F5C2E7"
MAUVE = "#CBA6F7"
RED = "#F38BA8"
MAROON = "#EBA0AC"
PEACH = "#FAB387"
YELLOW = "#F9E2AF"
GREEN = "#A6E3A1"
TEAL = "#94E2D5"
SKY = "#89DCEB"
SAPPHIRE = "#74C7EC"
BLUE = "#89B4FA"
LAVENDER = "#B4BEFE"


# ── QSS stylesheet ────────────────────────────────────────────────
# Reproduces the sam5F canvas mockup: dark base, mantle panels, mauve
# accent for the primary action, surface0 for secondary buttons.
QSS = f"""
QWidget {{
    background-color: {BASE};
    color: {TEXT};
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
    font-size: 13px;
}}

/* ── Title bar ─────────────────────────────────────────────── */
QFrame#TitleBar {{
    background-color: {MANTLE};
    border: none;
}}
QLabel#TitleText {{
    color: {OVERLAY0};
    font-size: 13px;
}}

/* ── Body ──────────────────────────────────────────────────── */
QFrame#Body {{
    background-color: {BASE};
}}

/* ── Header ────────────────────────────────────────────────── */
QLabel#AppIcon {{
    font-size: 28px;
}}
QLabel#AppName {{
    color: {MAUVE};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#AppTagline {{
    color: {SUBTEXT0};
    font-size: 12px;
}}

/* ── Mode toggle ───────────────────────────────────────────── */
QPushButton#ModeSingle,
QPushButton#ModeDir {{
    background-color: {SURFACE0};
    border: 1px solid {SURFACE2};
    border-radius: 8px;
    padding: 10px 16px;
    color: {SUBTEXT0};
    text-align: left;
}}
QPushButton#ModeSingle:checked,
QPushButton#ModeDir:checked {{
    background-color: {SURFACE1};
    border: 2px solid {MAUVE};
    color: {TEXT};
    font-weight: 600;
}}
QPushButton#ModeSingle:hover,
QPushButton#ModeDir:hover {{
    border: 1px solid {SURFACE2};
}}

/* ── Info panel ────────────────────────────────────────────── */
QFrame#InfoPanel {{
    background-color: {MANTLE};
    border: 1px solid {SURFACE0};
    border-radius: 10px;
}}
QLabel#InfoLabel {{
    color: {OVERLAY0};
}}
QLabel#InputValue  {{ color: {BLUE}; }}
QLabel#OutputValue {{ color: {GREEN}; }}
QLabel#CodecValue  {{ color: {PEACH}; }}
QLabel#PixfmtValue {{ color: {YELLOW}; }}
QLabel#AudioValue  {{ color: {TEAL}; }}

/* ── Browse row ─────────────────────────────────────────────── */
QLineEdit#PathInput {{
    background-color: {SURFACE0};
    border: 1px solid {SURFACE1};
    border-radius: 6px;
    padding: 10px 12px;
    color: {TEXT};
    selection-background-color: {MAUVE};
}}
QLineEdit#PathInput:focus {{
    border: 1px solid {MAUVE};
}}
QPushButton#BrowseBtn {{
    background-color: {SURFACE1};
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    color: {TEXT};
}}
QPushButton#BrowseBtn:hover {{
    background-color: {SURFACE2};
}}

/* ── Progress ───────────────────────────────────────────────── */
QLabel#ProgressStatus {{ color: {TEXT}; }}
QLabel#ProgressPercent {{
    color: {MAUVE};
    font-weight: 700;
}}
QProgressBar#ProgressBar {{
    background-color: {SURFACE0};
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar#ProgressBar::chunk {{
    background-color: {MAUVE};
    border-radius: 5px;
}}
QLabel#StatLabel {{ color: {OVERLAY0}; font-size: 11px; }}
QLabel#StatValue  {{ color: {SUBTEXT1}; font-size: 14px; font-weight: 600; }}

/* ── Action buttons ─────────────────────────────────────────── */
QPushButton#ConvertBtn {{
    background-color: {MAUVE};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: {BASE};
    font-weight: 600;
}}
QPushButton#ConvertBtn:hover   {{ background-color: {LAVENDER}; }}
QPushButton#ConvertBtn:disabled{{ background-color: {SURFACE1}; color: {OVERLAY0}; }}

QPushButton#ExportBtn {{
    background-color: {SURFACE0};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: {TEXT};
    font-weight: 600;
}}
QPushButton#ExportBtn:hover    {{ background-color: {SURFACE1}; }}
QPushButton#ExportBtn:disabled {{ color: {OVERLAY0}; }}

QPushButton#CleanBtn {{
    background-color: {SURFACE0};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: {RED};
    font-weight: 600;
}}
QPushButton#CleanBtn:hover     {{ background-color: {SURFACE1}; }}

QPushButton#QuitBtn {{
    background-color: {SURFACE0};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: {SUBTEXT0};
    font-weight: 600;
}}
QPushButton#QuitBtn:hover      {{ background-color: {SURFACE1}; }}

/* ── Log panel ──────────────────────────────────────────────── */
QPlainTextEdit#LogPanel {{
    background-color: {CRUST};
    border: 1px solid {SURFACE0};
    border-radius: 8px;
    color: {SUBTEXT1};
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    padding: 8px;
}}
"""
