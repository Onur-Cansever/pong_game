@echo off
rem ============================================================
rem  Windows'ta tek dosyalik EXE uret (istege bagli)
rem  Gerekli: pip install pyinstaller
rem  Sonuc: dist\Pong\  carpisinda  Pong.exe  (cift tıklanir)
rem ============================================================
title Pong EXE build
pip install pyinstaller
pyinstaller --onefile --noconsole --name Pong --add-data "pong.html;." --add-data "terminator_music.webm;." server.py
echo.
echo TAMAM: dist\Pong\Pong.exe  (veya dist\Pong.exe --onefile oldugundan)
pause
