# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 jhonatanmizu — released under the GNU GPL v3 or later.

"""Donation targets — single source of truth for the gratitude moment.

The PIX key is intentionally NOT committed to the repository. Set the
``VINCI_CONVERT_PIX_KEY`` environment variable (locally, in CI, or during
packaging) once your key exists; the CLI and GUI will pick it up.
"""

from __future__ import annotations

import os

SPONSORS_URL = "https://github.com/sponsors/jhonatanmizu"
REPO_URL = "https://github.com/jhonatanmizu/vinci-convert"

PIX_KEY = os.environ.get("VINCI_CONVERT_PIX_KEY", "")


def has_pix() -> bool:
    """True when a PIX key is available to show the user."""
    return bool(PIX_KEY)