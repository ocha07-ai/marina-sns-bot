"""
main.py - SNS自動投稿ツール エントリーポイント

使い方:
  python src/main.py --session morning
  python src/main.py --session evening
  python src/main.py --session morning --platform x   # X のみ投稿
  python src/main.py --test                           # 投稿せずに生成内容を確認
"""
import argparse
import os
import sys
import yaml
from dotenv import load_dotenv

# src フォルダを import パスに追加
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

import generator
import poster_x


def load_settings():
    base = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(base, "config", "settings.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(session: str, platform_filter: str = "all", test_mode: bool = False):
    settings = load_settings()
    platforms = settings["platforms"]

    targets = []

    # X
    if (platform_filter in ("all", "x")
            and platforms["x"]["enabled"]
            and platforms["x"][session]):
        targets.append("x")

    # Threads（有効化後に使用）
    if (platform_filter in ("all", "threads")
            and platforms["threads"]["enabled"]
            and platforms["threads"][session]):
        targets.append("threads")

    if not targets:
        print(f"⚠️  {session} に投稿対象のプラットフォームがありません。settings.yaml を確認してください。")
        return

    print(f"\n🔮 マリナ SNS自動投稿ツール")
    print(f"   セッション: {session} | 対象: {', '.join(targets)}\n")

    for platform in targets:
        print(f"--- {platform.upper()} ---")

        # コンテンツ生成
        text = generator.generate(session, platform)
        print(f"生成テキスト:\n{text}\n")

        if test_mode:
            print("（テストモード: 実際には投稿しません）\n")
            continue

        # 投稿実行
        if platform == "x":
            poster_x.post(text, session)


def main():
    parser = argparse.ArgumentParser(description="マリナ SNS自動投稿ツール")
    parser.add_argument(
        "--session",
        choices=["morning", "evening"],
        default="morning",
        help="朝投稿: morning / 夜投稿: evening",
    )
    parser.add_argument(
        "--platform",
        default="all",
        help="特定のプラットフォームのみ投稿 (x / threads / all)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード: コンテンツを生成して表示するだけ（実際には投稿しない）",
    )
    args = parser.parse_args()
    run(args.session, args.platform, args.test)


if __name__ == "__main__":
    main()
