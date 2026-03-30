"""
logger.py - 投稿履歴をJSONLファイルに記録する
"""
import json
import os
from datetime import datetime


LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "post_log.jsonl")


def log(platform: str, session: str, status: str, post_id: str = "", error: str = "", text: str = "",
        genre: str = "", theme_type=None):
    """
    投稿結果をログファイルに追記する

    Args:
        platform:   "x" / "threads" / "tiktok"
        session:    "morning" / "evening"
        status:     "success" / "error"
        post_id:    投稿成功時のID
        error:      エラー時のメッセージ
        genre:      夜投稿のジャンル（恋愛霊視/タロット/魂の繋がり）
        theme_type: 朝投稿のテーマ種別（0=星座占い, 1=タロット, 2=誕生月占い）
    """
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "platform": platform,
        "session": session,
        "status": status,
        "post_id": post_id,
        "error": error,
        "text": text,
        "genre": genre,
        "theme_type": theme_type,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # コンソールにも表示
    icon = "✅" if status == "success" else "❌"
    print(f"{icon} [{platform.upper()}] {session} - {status}"
          + (f" | ID: {post_id}" if post_id else "")
          + (f" | ERR: {error}" if error else ""))
