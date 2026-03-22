"""
researcher.py - ターゲットアカウントのリサーチ
ハッシュタグ検索で投稿アカウントを抽出する
"""
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

SEARCH_QUERIES = [
    "#恋愛占い -is:retweet lang:ja",
    "#復縁 -is:retweet lang:ja",
    "#婚活 -is:retweet lang:ja",
    "#タロット -is:retweet lang:ja",
]


def research_accounts(max_per_query: int = 10) -> list[dict]:
    """
    ターゲットハッシュタグから投稿アカウントを抽出する

    Returns:
        [{name, url, tag, note, last_action}, ...]
    """
    # 検索はBearer Token（App-only）で実行
    client = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])

    own_id = None

    found = {}
    errors = []

    for query in SEARCH_QUERIES:
        try:
            resp = client.search_recent_tweets(
                query=query,
                max_results=max_per_query,
                expansions=["author_id"],
                user_fields=["username", "name"],
            )
            if not resp.data:
                continue
            users = {u.id: u for u in (resp.includes.get("users") or [])}
            for tweet in resp.data:
                user = users.get(tweet.author_id)
                if user and user.id != own_id and user.id not in found:
                    tag = query.split()[0]  # ハッシュタグ部分
                    found[user.id] = {
                        "name": user.name,
                        "url": f"https://x.com/{user.username}",
                        "tag": "いいね",
                        "note": f"{tag} で発見",
                        "last_action": "",
                    }
        except Exception as e:
            errors.append(str(e))

    return list(found.values()), errors
