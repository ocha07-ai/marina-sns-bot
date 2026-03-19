@echo off
:: ========================================
:: テスト実行 - 実際には投稿せずに内容を確認
:: ダブルクリックで実行できます
:: ========================================

SET BOT_DIR=%~dp0..

echo === 朝の投稿テスト ===
python "%BOT_DIR%\src\main.py" --session morning --test

echo.
echo === 夜の投稿テスト ===
python "%BOT_DIR%\src\main.py" --session evening --test

echo.
pause
