"""
generator.py - Claude API を使ってSNS投稿コンテンツを生成する
"""
import os
import yaml
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()

WEEKDAYS = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# 曜日別ジャンル固定（prompts.yamlのコメントと対応）
WEEKDAY_GENRE = {
    0: "恋愛霊視",   # 月
    1: "タロット",   # 火
    2: "魂の繋がり", # 水
    3: "恋愛霊視",   # 木
    4: "タロット",   # 金
    5: "魂の繋がり", # 土
    6: "魂の繋がり", # 日（週のまとめ）
}


def load_config():
    base = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(base, "config", "settings.yaml"), encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    with open(os.path.join(base, "config", "prompts.yaml"), encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    return settings, prompts


def get_genre() -> str:
    """曜日に基づいてジャンルを返す"""
    return WEEKDAY_GENRE[datetime.now().weekday()]


def generate(session: str, platform: str) -> str:
    """
    コンテンツを生成して返す

    Args:
        session: "morning" または "evening"
        platform: "x" または "threads"

    Returns:
        生成された投稿テキスト
    """
    settings, prompts = load_config()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    genre = get_genre()
    weekday = WEEKDAYS[datetime.now().weekday()]

    # プロンプトテンプレートに変数を埋め込む
    user_prompt = prompts[session][platform].format(
        weekday=weekday,
        genre=genre,
        coconala_url=settings["profile"]["coconala_url"],
    )

    response = client.messages.create(
        model=settings["claude"]["model"],
        max_tokens=settings["claude"]["max_tokens"],
        system=prompts["system"],
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()


if __name__ == "__main__":
    # テスト用: python src/generator.py
    print("=== 朝 / X ===")
    print(generate("morning", "x"))
    print()
    print("=== 夜 / X ===")
    print(generate("evening", "x"))
