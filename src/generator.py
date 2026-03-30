"""
generator.py - Claude API を使ってSNS投稿コンテンツを生成する
"""
import os
import yaml
import random
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()

WEEKDAYS = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# 曜日別ジャンル固定（夜投稿で使用）
WEEKDAY_GENRE = {
    0: "恋愛霊視",   # 月
    1: "タロット",   # 火
    2: "魂の繋がり", # 水
    3: "恋愛霊視",   # 木
    4: "タロット",   # 金
    5: "魂の繋がり", # 土
    6: "魂の繋がり", # 日
}

# 12星座
ZODIAC_SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]

# 星座と誕生月の対応
ZODIAC_WITH_MONTH = [
    ("牡羊座", "3月・4月生まれ"),
    ("牡牛座", "4月・5月生まれ"),
    ("双子座", "5月・6月生まれ"),
    ("蟹座",   "6月・7月生まれ"),
    ("獅子座", "7月・8月生まれ"),
    ("乙女座", "8月・9月生まれ"),
    ("天秤座", "9月・10月生まれ"),
    ("蠍座",   "10月・11月生まれ"),
    ("射手座", "11月・12月生まれ"),
    ("山羊座", "12月・1月生まれ"),
    ("水瓶座", "1月・2月生まれ"),
    ("魚座",   "2月・3月生まれ"),
]

# タロットカード一覧
TAROT_CARDS = [
    "愚者", "魔術師", "女教皇", "女帝", "皇帝", "法王",
    "恋人", "戦車", "力", "隠者", "運命の輪", "正義",
    "吊された男", "死神", "節制", "悪魔", "塔", "星",
    "月", "太陽", "審判", "世界",
]


def get_morning_theme() -> dict:
    """日付ベースで朝テーマを決定する。
    朝投稿は常にタロットカード形式で統一（画像付き投稿のため）。
    22枚の大アルカナを日付でローテーション。
    """
    day_of_year = datetime.now().timetuple().tm_yday
    card = TAROT_CARDS[day_of_year % len(TAROT_CARDS)]
    theme = f"今日のタロット〜{card}〜"
    extra = (
        f"今日のカードは「{card}」です。\n"
        f"書き出しは「今日のカードは{card}」で始めてください。\n"
        f"このカードが今日の恋愛・復縁・婚活に伝えるメッセージを、\n"
        f"「{card}が出たあなたへ」という語りかけの形で書いてください。\n"
        f"カードの意味を難しくなく、恋愛の具体的な場面に落とし込んで。"
    )
    return {"theme": theme, "extra": extra, "theme_type": 1, "card": card}


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


def generate(session: str, platform: str, insights: str = "") -> tuple[str, dict]:
    """
    コンテンツを生成して返す

    Args:
        session:  "morning" または "evening"
        platform: "x" または "threads"
        insights: PDCAアナライザーが生成したインサイトテキスト（任意）

    Returns:
        (生成された投稿テキスト, メタ情報dict)
        メタ情報: {"genre": str, "theme_type": int|None}
    """
    settings, prompts = load_config()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    genre = get_genre()
    weekday = WEEKDAYS[datetime.now().weekday()]
    morning = get_morning_theme()

    # プロンプトテンプレートに変数を埋め込む
    user_prompt = prompts[session][platform].format(
        weekday=weekday,
        genre=genre,
        morning_theme=morning["theme"],
        morning_extra=morning["extra"],
        coconala_url=settings["profile"]["coconala_url"],
    )

    # PDCAインサイトをプロンプト末尾に追加
    if insights:
        user_prompt = user_prompt + "\n\n" + insights

    response = client.messages.create(
        model=settings["claude"]["model"],
        max_tokens=settings["claude"]["max_tokens"],
        system=prompts["system"],
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = response.content[0].text.strip()

    # メタ情報（ロギング・次サイクルの分析・画像生成用）
    meta = {
        "genre":      genre if session == "evening" else "",
        "theme_type": morning["theme_type"] if session == "morning" else None,
        "card":       morning.get("card") if session == "morning" else None,
    }

    return text, meta


if __name__ == "__main__":
    # テスト用: python src/generator.py
    print("=== 朝 / X ===")
    text, meta = generate("morning", "x")
    print(text)
    print(f"[meta] {meta}")
    print()
    print("=== 夜 / X ===")
    text, meta = generate("evening", "x")
    print(text)
    print(f"[meta] {meta}")
