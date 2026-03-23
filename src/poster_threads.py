"""
poster_threads.py - Threads に投稿するモジュール
"""
import os
import requests
from dotenv import load_dotenv
from logger import log

load_dotenv()

GRAPH_URL = "https://graph.threads.net/v1.0"


def post(text: str, session: str) -> bool:
    """
    Threadsにテキストを投稿する

    Args:
        text:    投稿するテキスト
        session: "morning" または "evening"

    Returns:
        成功したら True
    """
    try:
        user_id = os.environ["THREADS_USER_ID"]
        token   = os.environ["THREADS_ACCESS_TOKEN"]

        # Step 1: メディアコンテナ作成
        r1 = requests.post(
            f"{GRAPH_URL}/{user_id}/threads",
            data={
                "media_type": "TEXT",
                "text": text,
                "access_token": token,
            },
        )
        if not r1.ok:
            raise Exception(f"{r1.status_code}: {r1.text}")
        creation_id = r1.json()["id"]

        # Step 2: 公開
        r2 = requests.post(
            f"{GRAPH_URL}/{user_id}/threads_publish",
            data={
                "creation_id": creation_id,
                "access_token": token,
            },
        )
        r2.raise_for_status()
        post_id = str(r2.json()["id"])

        # CTAをリプライで追加
        cta_text = "🔮 彼の気持ち・本音・ご縁の流れ…\nタロット×霊視で個別に視ます。\nご予約・詳細はこちら👇\nhttps://coconala.com/users/5372174"
        r3 = requests.post(
            f"{GRAPH_URL}/{user_id}/threads",
            data={
                "media_type": "TEXT",
                "text": cta_text,
                "reply_to_id": post_id,
                "access_token": token,
            },
        )
        if r3.ok:
            cta_creation_id = r3.json()["id"]
            r4 = requests.post(
                f"{GRAPH_URL}/{user_id}/threads_publish",
                data={
                    "creation_id": cta_creation_id,
                    "access_token": token,
                },
            )
            if not r4.ok:
                print(f"[THREADS CTA publish error] {r4.status_code}: {r4.text}")
        else:
            print(f"[THREADS CTA container error] {r3.status_code}: {r3.text}")

        log("threads", session, "success", post_id=post_id, text=text)
        return True

    except Exception as e:
        log("threads", session, "error", error=str(e))
        return False
