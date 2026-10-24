#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

VENV_DIR="${VENV_DIR:-/opt/venv}"
REQ_FILE="$ROOT/requirements.txt"
REQ_HASH="$(sha256sum "$REQ_FILE" | awk '{print $1}')"
REQ_MARKER="$VENV_DIR/.pfu-requirements.sha256"

if [ ! -x "$VENV_DIR/bin/python" ] || [ ! -f "$REQ_MARKER" ] || [ "$(cat "$REQ_MARKER" 2>/dev/null || true)" != "$REQ_HASH" ]; then
    echo "Preparing Python environment..."
    mkdir -p "$VENV_DIR"
    find "$VENV_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
    python -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --disable-pip-version-check --no-cache-dir -r "$REQ_FILE"
    printf '%s\n' "$REQ_HASH" > "$REQ_MARKER"
fi

export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$VENV_DIR/bin/python" -m fleet_updater.runtime
