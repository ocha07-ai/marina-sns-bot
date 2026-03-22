"""
poster_x.py - X (Twitter) に投稿するモジュール
"""
import os
import tweepy
from dotenv import load_dotenv
from logger import log

load_dotenv()


def post(text: str, session: str) -> bool:
    """
    Xにテキストを投稿する

    Args:
        text:    投稿するテキスト
        session: "morning" または "evening"

    Returns:
        成功したら True
    """
    try:
        client = tweepy.Client(
            consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_SECRET"],
        )

        response = client.create_tweet(text=text)
        post_id = str(response.data["id"])

        # CTAをツリーで追加
        cta_text = "🔮 彼の気持ち・本音・ご縁の流れ…\nタロット×霊視で個別に視ます。\nご予約・詳細はこちら👇\nhttps://coconala.com/users/5372174"
        client.create_tweet(text=cta_text, in_reply_to_tweet_id=post_id)

        log("x", session, "success", post_id=post_id)
        return True

    except Exception as e:
        log("x", session, "error", error=str(e))
        return False
