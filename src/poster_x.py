"""
poster_x.py - X (Twitter) に投稿するモジュール
"""
import os
import tweepy
from dotenv import load_dotenv
from logger import log

load_dotenv()


def _upload_media(image_path: str) -> str | None:
    """v1.1 APIで画像をアップロードしてmedia_idを返す"""
    try:
        auth = tweepy.OAuth1UserHandler(
            os.environ["X_API_KEY"],
            os.environ["X_API_SECRET"],
            os.environ["X_ACCESS_TOKEN"],
            os.environ["X_ACCESS_SECRET"],
        )
        api_v1 = tweepy.API(auth)
        media = api_v1.media_upload(filename=image_path)
        return str(media.media_id)
    except Exception as e:
        print(f"[X 画像アップロード失敗] {e} → テキストのみ投稿")
        return None


def post(text: str, session: str, meta: dict = None, image_path: str = None) -> bool:
    """
    Xにテキスト（＋画像）を投稿する

    Args:
        text:       投稿するテキスト
        session:    "morning" または "evening"
        meta:       PDCAメタ情報 {"genre": str, "theme_type": int|None, "card": str|None}
        image_path: 添付画像のパス（任意）

    Returns:
        成功したら True
    """
    meta = meta or {}
    try:
        client = tweepy.Client(
            consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_SECRET"],
        )

        # 画像アップロード
        media_ids = None
        if image_path:
            media_id = _upload_media(image_path)
            if media_id:
                media_ids = [media_id]

        response = client.create_tweet(text=text, media_ids=media_ids)
        post_id = str(response.data["id"])

        log("x", session, "success", post_id=post_id, text=text,
            genre=meta.get("genre", ""), theme_type=meta.get("theme_type"))

        # CTAをツリーで追加（失敗してもメイン投稿は成功扱い）
        try:
            cta_text = "🔮 彼の気持ち・本音・ご縁の流れ…\nタロット×霊視で個別に視ます。\nご予約・詳細はこちら👇\nhttps://coconala.com/users/5372174"
            client.create_tweet(text=cta_text, in_reply_to_tweet_id=post_id)
        except Exception as cta_err:
            print(f"[X CTA error] {cta_err}")

        return True

    except Exception as e:
        log("x", session, "error", error=str(e))
        return False
