#!/usr/bin/env bash
# ============================================================
#  BEAT THE AI - Pong — LINUX build
#  Cikti:  releases/Pong-linux-x86_64  (tek dosya, calistirilabilir)
#
#  Kullanim:   ./build-linux.sh
#  Gerekli:    python3 + internet (ilk calistirmada venv + PyInstaller kurulur)
#  Not:        Bu binary YALNIZCA Linux x86_64 icin.
#              Windows icin:  ./build-windows.sh
# ============================================================
set -e
cd "$(dirname "$0")"

# ---- venv (PyInstaller'i ana Python'a dokunmadan kur) ----
VENV=".build-venv"
if [ ! -x "$VENV/bin/python" ]; then
    echo ">> venv olusturuluyor: $VENV"
    python3 -m venv "$VENV"
fi
PY="$VENV/bin/python"

if ! "$PY" -c "import PyInstaller" 2>/dev/null; then
    echo ">> PyInstaller kuruluyor..."
    "$PY" -m pip install --quiet pyinstaller
fi

# ---- cikti dizini ----
rm -rf releases
mkdir -p releases

# ---- derle ----
echo ">> PyInstaller ile Linux binary derleniyor (~30 sn)..."
"$PY" -m PyInstaller --onefile --name Pong \
    --hidden-import brain \
    --add-data "pong.html:." --add-data "terminator_music.webm:." \
    --distpath build-linux/dist --workpath build-linux --specpath . \
    server.py

OUT="releases/Pong-linux-x86_64"
mv build-linux/dist/Pong "$OUT"
chmod +x "$OUT"

echo ""
echo "TAMAM: $OUT ($(du -h "$OUT" | cut -f1))"
echo "  Calistirma:  ./$OUT          (tarayici acilir)"
echo "  Port:       ./$OUT --port 9000"
echo "  Gonderim:    zip pong-linux.zip $OUT"
echo ""
echo "Not: Bu binary YALNIZCA Linux x86_64 icin derlendi."
