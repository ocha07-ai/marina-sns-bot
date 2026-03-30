"""
poster_threads.py - Threads に投稿するモジュール
"""
import os
import base64
import requests
from dotenv import load_dotenv
from logger import log
from token_manager import ensure_valid_token

load_dotenv()

GRAPH_URL = "https://graph.threads.net/v1.0"


def _upload_to_imgbb(image_path: str) -> str | None:
    """
    imgbb に画像をアップロードして公開URLを返す。
    IMGBB_API_KEY が未設定の場合は None を返す。
    """
    api_key = os.environ.get("IMGBB_API_KEY", "")
    if not api_key:
        return None
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": api_key, "image": encoded},
        )
        if r.ok:
            return r.json()["data"]["url"]
        print(f"[Threads imgbb失敗] {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[Threads imgbb例外] {e}")
    return None


def post(text: str, session: str, meta: dict = None, image_path: str = None) -> bool:
    """
    Threadsにテキスト（＋画像）を投稿する

    Args:
        text:       投稿するテキスト
        session:    "morning" または "evening"
        meta:       PDCAメタ情報 {"genre": str, "theme_type": int|None, "card": str|None}
        image_path: 添付画像のパス（任意）。IMGBB_API_KEY が設定されている場合のみ有効。

    Returns:
        成功したら True
    """
    meta = meta or {}

    # トークンの有効期限確認・自動更新
    if not ensure_valid_token():
        log("threads", session, "error", error="トークンが無効です。手動で再取得してください。")
        return False

    try:
        user_id = os.environ["THREADS_USER_ID"]
        token   = os.environ["THREADS_ACCESS_TOKEN"]

        # 画像URLの取得（imgbbにアップロード）
        image_url = None
        if image_path:
            image_url = _upload_to_imgbb(image_path)
            if not image_url:
                print("[Threads] 画像URLなし → テキストのみ投稿")

        # Step 1: メディアコンテナ作成
        container_data = {"access_token": token, "text": text}
        if image_url:
            container_data["media_type"] = "IMAGE"
            container_data["image_url"]  = image_url
        else:
            container_data["media_type"] = "TEXT"

        r1 = requests.post(
            f"{GRAPH_URL}/{user_id}/threads",
            data=container_data,
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

        log("threads", session, "success", post_id=post_id, text=text,
            genre=meta.get("genre", ""), theme_type=meta.get("theme_type"))

        return True

    except Exception as e:
        log("threads", session, "error", error=str(e))
        return False
