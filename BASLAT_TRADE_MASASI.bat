@echo off
title Antigravity Trade Masasi - 7/24 Kesintisiz Hizmet
color 0A
chcp 65001 >nul
echo ===================================================================
echo   Antigravity Finans Karar Destek Masasi - 7/24 Canli Servis
echo   Web Sunucusu (localhost:8080) ve Cloudflare Tuneli Baslatiliyor...
echo ===================================================================
cd /d "C:\Users\user\Desktop\GitHub Project\Finance Project"
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" "core\supervisor.py"
pause
