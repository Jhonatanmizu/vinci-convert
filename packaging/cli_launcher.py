"""PyInstaller entry script for the vinci-convert CLI.

Kept outside the package so the spec files have a plain script to point at
(the package modules use relative imports and can't be run as scripts).
"""

from vinci_convert.cli import app

if __name__ == "__main__":
    app()
