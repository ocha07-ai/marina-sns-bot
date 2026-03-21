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
    """日付ベースで朝テーマをローテーション（毎日変わる）"""
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday

    # 12日サイクルで星座をローテーション
    zodiac, month_label = ZODIAC_WITH_MONTH[day_of_year % 12]

    # テーマは3種類をローテーション
    theme_type = day_of_year % 3

    if theme_type == 0:
        # 星座占い（直接語りかけ）
        theme = f"今日の星座占い〜{zodiac}のあなたへ〜"
        extra = (
            f"今日は{zodiac}（{month_label}）の方への恋愛メッセージです。\n"
            f"書き出しは「{zodiac}のあなたへ」または「{month_label}のあなたへ」で始めてください。\n"
            f"その星座の性質（例：蟹座なら感情豊か・直感的など）を踏まえた、\n"
            f"今日の恋愛・人間関係への具体的なメッセージを書いてください。\n"
            f"他の星座の人も「これ私のことかも」と感じるよう、感情描写を丁寧に。"
        )
    elif theme_type == 1:
        # タロットカード（具体的なカード名）
        card = TAROT_CARDS[day_of_year % len(TAROT_CARDS)]
        theme = f"今日のタロット〜{card}〜"
        extra = (
            f"今日のカードは「{card}」です。\n"
            f"書き出しは「今日のカードは{card}」で始めてください。\n"
            f"このカードが今日の恋愛・復縁・婚活に伝えるメッセージを、\n"
            f"「{card}が出たあなたへ」という語りかけの形で書いてください。\n"
            f"カードの意味を難しくなく、恋愛の具体的な場面に落とし込んで。"
        )
    else:
        # 誕生月占い
        theme = f"今日の誕生月占い〜{month_label}のあなたへ〜"
        extra = (
            f"今日は{month_label}の方への恋愛メッセージです。\n"
            f"書き出しは「{month_label}のあなたへ」で始めてください。\n"
            f"その月生まれの人が持つ特性・恋愛傾向を踏まえた、\n"
            f"今日実践できる具体的なアドバイスまたは気づきを届けてください。\n"
            f"読んだ人が「なんで私のことわかるの？」と感じるくらい具体的に。"
        )

    return {"theme": theme, "extra": extra}


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
    morning = get_morning_theme()

    # プロンプトテンプレートに変数を埋め込む
    user_prompt = prompts[session][platform].format(
        weekday=weekday,
        genre=genre,
        morning_theme=morning["theme"],
        morning_extra=morning["extra"],
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
