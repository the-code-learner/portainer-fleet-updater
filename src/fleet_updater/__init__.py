"""Portainer Fleet Updater."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

try:
    __version__ = (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
except OSError:
    __version__ = "0.0.0"
