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
import analyzer
import image_generator
import poster_x
import poster_threads


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

        # ── PDCA: Check ──────────────────────────────────────
        # 過去投稿のメトリクスを取得・分析してインサイトを生成
        print("[PDCA 1/3] 過去投稿を分析中...")
        insights = analyzer.analyze(session, platform)
        if insights:
            print("[PDCA 2/3] インサイト適用 → 生成プロンプトに反映します")
        else:
            print("[PDCA 2/3] インサイトなし（初回 or データ不足）→ 通常生成")

        # ── PDCA: Do ─────────────────────────────────────────
        # インサイトを注入してコンテンツ生成
        print("[PDCA 3/3] コンテンツ生成中...")
        text, meta = generator.generate(session, platform, insights=insights)
        print(f"\n生成テキスト:\n{text}\n")

        # ── 画像生成（タロットテーマの朝投稿のみ）────────────
        image_path = None
        if meta.get("theme_type") == 1 and meta.get("card"):
            image_path = image_generator.generate_tarot_image(meta["card"], text)

        if test_mode:
            if insights:
                print("── 適用インサイト ──")
                print(insights)
                print()
            if image_path:
                print(f"[画像] {image_path}")
            print("（テストモード: 実際には投稿しません）\n")
            continue

        # ── PDCA: Act（投稿 + ログ記録） ──────────────────────
        # メタ情報（genre/theme_type）も保存し、次サイクルの分析に活かす
        if platform == "x":
            poster_x.post(text, session, meta=meta, image_path=image_path)
        elif platform == "threads":
            poster_threads.post(text, session, meta=meta)  # Threadsはテキストのみ

        # ── 画像クリーンアップ ────────────────────────────────
        settings = load_settings()
        if image_path and settings.get("image", {}).get("cleanup_after_post", True):
            try:
                os.remove(image_path)
            except OSError:
                pass


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
