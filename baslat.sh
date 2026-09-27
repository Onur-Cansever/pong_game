#!/usr/bin/env bash
# ============================================================
#  BEAT THE AI - Pong  (Linux)
#  Gerekli: Python 3.8+  (python3 komutu)
# ============================================================
set -e
cd "$(dirname "$0")"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
    echo "HATA: python3 bulunamadi."
    echo "  Gentoo : sudo emerge --ask python"
    echo "  Debian : sudo apt install python3"
    echo "  Fedora : sudo dnf install python3"
    exit 1
fi

PORT="${1:-8077}"
echo "Pong calisiyor: http://localhost:${PORT}  (Ctrl+C ile durdur)"
"$PY" server.py --port "$PORT"
