#!/usr/bin/env bash
# ============================================================
#  BEAT THE AI - Pong  (Windows) — bu LINUX makineden .exe uret
#  (cross-derleme: wine icinde Python Windows kurulumu + PyInstaller)
#
#  Ciktı: dist-windows/Pong.exe   (Windows'ta cift tiklanir)
#
#  Gerekli (ilk kurulumda kendisi kurar):
#    - wine  (Gentoo: sudo emerge --ask wine)
#    - internet (python.org'dan ~25 MB indirir, sonra onceki calisma
#      onbellek olur: WINEPREFIX_PONG calismasi kalmadir)
#
#  Kullanım:
#    ./build-windows.sh
#
#  Icinde yaptiklari (her biri bir kez, sonralari atlanir):
#    1. wine prefix'i olusturur (~/.wine-pong; silinirse yenisi kurulur)
#    2. python.org'dan Windows Python 3.11.9'i wine icine kurar
#    3. pip ile pyinstaller'i wine icine kurar
#    4. PyInstaller'i wine'da calistirir -> dist-windows/Pong.exe
# ============================================================
set -e
cd "$(dirname "$0")"

PYTHON_VER="3.11.9"
WINEPREFIX_PONG="${WINEPREFIX_PONG:-$HOME/.wine-pong}"
WIN_PY="$WINEPREFIX_PONG/drive_c/Python311/python.exe"
OUT_DIR="dist-windows"

if ! command -v wine >/dev/null 2>&1; then
    echo "HATA: wine bulunamadi. Gentoo icin:  sudo emerge --ask wine"
    exit 1
fi

export WINEPREFIX="$WINEPREFIX_PONG"
export WINEARCH=win64
export WINEDEBUG=-all
export WINEDLLOVERRIDES="mscoree,mshtml="

# ---- 1. wine prefix ----
if [ ! -d "$WINEPREFIX_PONG/drive_c" ]; then
    echo ">> wine prefix olusturuluyor: $WINEPREFIX_PONG (ilk calismanda ~1-2 dk)"
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
echo ">> Wine icindeki Python: $($WIN_PY --version)"

# ---- 3. PyInstaller (bir kez) ----
if ! wine "$WIN_PY" -c "import PyInstaller" 2>/dev/null; then
    echo ">> wine icine PyInstaller kuruluyor..."
    wine "$WIN_PY" -m pip install --quiet pyinstaller
fi

# ---- 4. derleme ----
echo ">> PyInstaller ile Windows EXE derleniyor (~1 dk)..."
wine "$WIN_PY" -m PyInstaller --onefile --noconsole --name Pong \
    --hidden-import brain \
    --add-data "pong.html;." --add-data "terminator_music.webm;." \
    --distpath "$OUT_DIR" --workpath build-windows --specpath . \
    server.py

echo ""
echo "TAMAM: $OUT_DIR/Pong.exe"
echo "  Arkadasina gonder:  zip pong-windows.zip $OUT_DIR/Pong.exe"
echo "  Windows'ta cift tiklanir: sunucu acilir, tarayici http://localhost:8077/"
echo "  AI hafizasi Pong.exe yanina ai_memory.json olarak yazilir."
echo ""
echo "Not: Bu exe YALNIZCA Windows x86_64 icindir (64-bit Windows)."
echo "     Linux binary'si icin: ./build.sh"
