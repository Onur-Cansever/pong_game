@echo off
rem ============================================================
rem  Windows'ta tek dosyalik EXE uret (istege bagli)
rem  Gerekli: pip install pyinstaller
rem  Sonuc: dist\Pong\  carpisinda  Pong.exe  (cift tıklanir)
rem ============================================================
title Pong EXE build
pip install pyinstaller
pyinstaller --onefile --noconsole --name Pong --hidden-import brain ^
    --add-data "pong.html;." --add-data "terminator_music.webm;." server.py
echo.
echo TAMAM: dist\Pong.exe
echo   Dosyayi baslat.bat klasorune veya herhangi bir yere koyup cift tikla.
echo   (Sunucu 0.0.0.0:8077 acilir, tarayici otomatik acilir)
pause
