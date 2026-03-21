@echo off
SET BOT_DIR=%~dp0..
SET PYTHON=python

schtasks /create /tn "Marina_Morning" ^
  /tr "\"%PYTHON%\" \"%BOT_DIR%\src\main.py\" --session morning --platform x" ^
  /sc DAILY /st 08:47 /f

schtasks /create /tn "Marina_Evening" ^
  /tr "\"%PYTHON%\" \"%BOT_DIR%\src\main.py\" --session evening --platform x" ^
  /sc DAILY /st 19:00 /f

echo Done. Scheduled 08:47 and 19:00 daily.
pause
