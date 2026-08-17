"""Catppuccin Mocha palette — used for Rich/Typer terminal styling."""

from rich.color import Color as RichColor
from rich.console import Console
from rich.theme import Theme

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

# ── Rich theme mapping ────────────────────────────────────────────
THEME = Theme(
    {
        "app.title": f"bold {MAUVE}",
        "app.subtitle": f"{SUBTEXT0}",
        "info.label": f"{OVERLAY0}",
        "info.input": f"{BLUE}",
        "info.output": f"{GREEN}",
        "info.codec": f"{PEACH}",
        "info.pixfmt": f"{YELLOW}",
        "info.audio": f"{TEAL}",
        "status.success": f"bold {GREEN}",
        "status.warning": f"bold {YELLOW}",
        "status.error": f"bold {RED}",
        "status.info": f"{SKY}",
        "progress.elapsed": f"{SUBTEXT1}",
        "progress.eta": f"{SUBTEXT1}",
        "progress.size": f"{SUBTEXT1}",
        "btn.primary": f"bold {TEXT} on {MAUVE}",
        "btn.secondary": f"{TEXT} on {SURFACE0}",
        "btn.danger": f"{RED} on {SURFACE0}",
        "dim": f"{OVERLAY0}",
    }
)

console = Console(theme=THEME)
