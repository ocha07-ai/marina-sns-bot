@echo off
:: ========================================
:: マリナ SNS自動投稿 - タスクスケジューラ登録
:: このファイルを右クリック→「管理者として実行」してください
:: ========================================

SET BOT_DIR=%~dp0..
SET PYTHON=python

echo マリナ SNS自動投稿ツール - スケジューラを登録します...
echo.

:: 朝7時に投稿
schtasks /create /tn "Marina_Morning" ^
  /tr "\"%PYTHON%\" \"%BOT_DIR%\src\main.py\" --session morning" ^
  /sc DAILY /st 07:00 /f

:: 夜21時に投稿
schtasks /create /tn "Marina_Evening" ^
  /tr "\"%PYTHON%\" \"%BOT_DIR%\src\main.py\" --session evening" ^
  /sc DAILY /st 21:00 /f

echo.
echo ✅ 登録完了！毎日 07:00 と 21:00 に自動投稿されます。
echo.
pause
