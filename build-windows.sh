#!/usr/bin/env bash
# ============================================================
#  BEAT THE AI - Pong — WINDOWS build (bu LINUX makineden)
#  Yontem:  wine icinde Windows Python + PyInstaller (cross-derleme)
#  Cikti:   releases/Pong-windows-x64.exe
#
#  Kullanim:   ./build-windows.sh
#  Gerekli:    wine (Gentoo: sudo emerge --ask wine) + internet
#              (ilk calistirmada wine prefix + Windows Python kurulur,
#               sonraki calistirmalar ~1 dk: onceki kurulum kalinir)
#  Not:        Bu exe YALNIZCA 64-bit Windows icin.
#              Linux icin:  ./build-linux.sh
# ============================================================
set -e
cd "$(dirname "$0")"

PYTHON_VER="3.11.9"
WINEPREFIX_PONG="${WINEPREFIX_PONG:-$HOME/.wine-pong}"
WIN_PY="$WINEPREFIX_PONG/drive_c/Python311/python.exe"

if ! command -v wine >/dev/null 2>&1; then
    echo "HATA: wine bulunamadi. Gentoo icin:  sudo emerge --ask wine"
    exit 1
fi

export WINEPREFIX="$WINEPREFIX_PONG"
export WINEARCH=win64
export WINEDEBUG=-all
export WINEDLLOVERRIDES="mscoree,mshtml="

# ---- 1. wine prefix (bir kez) ----
if [ ! -d "$WINEPREFIX_PONG/drive_c" ]; then
    echo ">> wine prefix olusturuluyor: $WINEPREFIX_PONG (~1-2 dk)..."
    wineboot -u
fi

# ---- 2. Windows Python (bir kez) ----
if [ ! -f "$WIN_PY" ]; then
    echo ">> Windows Python ${PYTHON_VER} indiriliyor (python.org, ~25 MB)..."
    curl -fsSL -o /tmp/pong-py-${PYTHON_VER}.exe \
        "https://www.python.org/ftp/python/${PYTHON_VER}/python-${PYTHON_VER}-amd64.exe"
    echo ">> wine icine Python kuruluyor (~1-2 dk)..."
    wine /tmp/pong-py-${PYTHON_VER}.exe /quiet \
        InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=0 Include_doc=0
    rm -f /tmp/pong-py-${PYTHON_VER}.exe
fi
echo ">> Wine icindeki Python: $("$WIN_PY" --version)"

# ---- 3. PyInstaller (bir kez) ----
if ! wine "$WIN_PY" -c "import PyInstaller" 2>/dev/null; then
    echo ">> wine icine PyInstaller kuruluyor..."
    wine "$WIN_PY" -m pip install --quiet pyinstaller
fi

# ---- 4. derle ----
rm -rf releases
mkdir -p releases
echo ">> PyInstaller ile Windows EXE derleniyor (~1 dk)..."
wine "$WIN_PY" -m PyInstaller --onefile --noconsole --name Pong \
    --hidden-import brain \
    --add-data "pong.html;." --add-data "terminator_music.webm;." \
    --distpath build-windows/dist --workpath build-windows --specpath . \
    server.py

mv build-windows/dist/Pong.exe releases/Pong-windows-x64.exe

echo ""
echo "TAMAM: releases/Pong-windows-x64.exe ($(du -h releases/Pong-windows-x64.exe | cut -f1))"
echo "  Gonderim:   zip pong-windows.zip releases/Pong-windows-x64.exe"
echo "  Windows'ta cift tiklanir: sunucu acilir, tarayici http://localhost:8077/"
echo "  AI hafizasi Pong.exe yanina ai_memory.json olarak yazilir."
echo ""
echo "Not: Bu exe YALNIZCA 64-bit Windows icin derlendi."
