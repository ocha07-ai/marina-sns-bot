"""
metrics.py - 投稿のパフォーマンス指標を取得する
"""
import os
import json
import requests
import tweepy
from dotenv import load_dotenv

load_dotenv()

LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "post_log.jsonl")


def fetch_x_metrics(post_ids: list[str]) -> dict:
    """X APIから複数投稿のメトリクスを取得"""
    if not post_ids:
        return {}
    try:
        client = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])
        resp = client.get_tweets(
            ids=post_ids,
            tweet_fields=["public_metrics", "created_at"],
        )
        result = {}
        if resp.data:
            for tweet in resp.data:
                m = tweet.public_metrics
                result[str(tweet.id)] = {
                    "impressions": m.get("impression_count", 0),
                    "likes":       m.get("like_count", 0),
                    "retweets":    m.get("retweet_count", 0),
                    "replies":     m.get("reply_count", 0),
                }
        return result
    except Exception as e:
        return {}


def fetch_threads_metrics(post_ids: list[str]) -> dict:
    """Threads APIから複数投稿のメトリクスを取得"""
    if not post_ids:
        return {}
    token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    result = {}
    for pid in post_ids:
        try:
            r = requests.get(
                f"https://graph.threads.net/v1.0/{pid}/insights",
                params={
                    "metric": "views,likes,replies,reposts,quotes",
                    "access_token": token,
                },
            )
            if r.ok:
                data = {d["name"]: d["values"][0]["value"] for d in r.json().get("data", [])}
                result[pid] = {
                    "impressions": data.get("views", 0),
                    "likes":       data.get("likes", 0),
                    "retweets":    data.get("reposts", 0),
                    "replies":     data.get("replies", 0),
                }
        except Exception:
            pass
    return result


def load_logs_with_metrics() -> list[dict]:
    """ログを読み込みメトリクスを付与して返す"""
    if not os.path.exists(LOG_PATH):
        return []

    records = []
    x_ids = []
    threads_ids = []

    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line.strip())
            if r["status"] == "success" and r["post_id"]:
                records.append(r)
                if r["platform"] == "x":
                    x_ids.append(r["post_id"])
                elif r["platform"] == "threads":
                    threads_ids.append(r["post_id"])

    # メトリクス取得
    x_metrics = fetch_x_metrics(x_ids)
    threads_metrics = fetch_threads_metrics(threads_ids)

    for r in records:
        pid = r["post_id"]
        if r["platform"] == "x":
            r["metrics"] = x_metrics.get(pid, {})
        elif r["platform"] == "threads":
            r["metrics"] = threads_metrics.get(pid, {})

    return records
