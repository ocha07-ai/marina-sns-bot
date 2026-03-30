@echo off
SET BOT_DIR=%~dp0..
SET PYTHON=C:\Users\kou\AppData\Local\Programs\Python\Python314\python.exe

REM 既存タスクを削除してから再作成
schtasks /delete /tn "Marina_Morning" /f 2>nul
schtasks /delete /tn "Marina_Evening" /f 2>nul

REM 朝投稿（8:00）ラッパーバッチ経由で実行（作業ディレクトリを確実に設定）
schtasks /create /tn "Marina_Morning" ^
  /tr "C:\Users\kou\marina-sns-bot\scripts\run_morning.bat" ^
  /sc DAILY /st 08:00 /f ^
  /rl HIGHEST

REM 夜投稿（21:00）ラッパーバッチ経由で実行
schtasks /create /tn "Marina_Evening" ^
  /tr "C:\Users\kou\marina-sns-bot\scripts\run_evening.bat" ^
  /sc DAILY /st 21:00 /f ^
  /rl HIGHEST

REM スリープ後の未実行タスクを起動するよう設定（PowerShell経由）
powershell -Command "& { $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable; Set-ScheduledTask -TaskName 'Marina_Morning' -Settings $s }"
powershell -Command "& { $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable; Set-ScheduledTask -TaskName 'Marina_Evening' -Settings $s }"

echo Done.
echo   朝投稿: 08:00 daily (X + Threads)
echo   夜投稿: 21:00 daily (X + Threads)
echo   ※PCスリープ後に起動したとき、未実行分を自動で実行します
pause
