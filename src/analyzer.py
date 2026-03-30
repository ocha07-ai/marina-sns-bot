"""
analyzer.py - 過去の投稿パフォーマンスを分析し、次回投稿のインサイトを生成する
PDCAサイクルの「Check → Act」フェーズ
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from metrics import load_logs_with_metrics
from collections import defaultdict

THEME_NAMES = {0: "星座占い", 1: "タロット", 2: "誕生月占い"}


def _score(metrics: dict) -> float:
    """エンゲージメントスコアを計算（いいね・RT・返信を重み付け）"""
    return (
        metrics.get("likes", 0) * 3
        + metrics.get("retweets", 0) * 5
        + metrics.get("replies", 0) * 2
        + metrics.get("impressions", 0) * 0.005
    )


def analyze(session: str, platform: str, lookback: int = 20) -> str:
    """
    過去の投稿を分析してインサイト文字列を返す。
    メトリクス取得失敗・データ不足時は空文字を返す（投稿は続行）。

    Args:
        session:  "morning" / "evening"
        platform: "x" / "threads"
        lookback: 分析対象の最新N件

    Returns:
        生成プロンプトに挿入するインサイトテキスト（なければ空文字）
    """
    try:
        all_records = load_logs_with_metrics()
    except Exception as e:
        print(f"[PDCA] メトリクス取得スキップ: {e}")
        return ""

    # フィルタ: 対象セッション・プラットフォーム・メトリクスあり・テキストあり
    records = [
        r for r in all_records
        if r["platform"] == platform
        and r["session"] == session
        and r.get("metrics")
        and r.get("text")
    ][-lookback:]

    if len(records) < 3:
        print(f"[PDCA] 分析データ不足（{len(records)}件）。インサイトなしで生成します。")
        return ""

    # スコア付け
    for r in records:
        r["_score"] = _score(r["metrics"])

    sorted_records = sorted(records, key=lambda r: r["_score"], reverse=True)
    top = sorted_records[:3]
    bottom = sorted_records[-2:] if len(sorted_records) >= 6 else []

    # ジャンル別集計（主に夜投稿）
    genre_scores: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.get("genre"):
            genre_scores[r["genre"]].append(r["_score"])

    # テーマタイプ別集計（朝投稿）
    theme_scores: dict[int, list[float]] = defaultdict(list)
    for r in records:
        if r.get("theme_type") is not None:
            theme_scores[int(r["theme_type"])].append(r["_score"])

    # ── インサイト構築 ──────────────────────────────────────
    lines = [
        "【PDCAフィードバック（過去投稿の分析結果）】",
        "以下のデータを参考に、より高いエンゲージメントが期待できる投稿を生成してください。",
        "",
    ]

    # ジャンル傾向
    if genre_scores:
        ranked = sorted(
            genre_scores.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True,
        )
        best_genre, best_s = ranked[0]
        avg = sum(best_s) / len(best_s)
        lines.append(f"▼ 最も反応が良いジャンル: 【{best_genre}】（平均スコア {avg:.1f}）→ このジャンルの強みを活かす表現を")
        if len(ranked) > 1:
            worst_genre, worst_s = ranked[-1]
            worst_avg = sum(worst_s) / len(worst_s)
            lines.append(f"▼ 反応が薄いジャンル: 【{worst_genre}】（平均スコア {worst_avg:.1f}）→ 切り口や感情描写を工夫する")

    # テーマタイプ傾向（朝）
    if theme_scores:
        ranked_t = sorted(
            theme_scores.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True,
        )
        best_type, best_ts = ranked_t[0]
        avg_t = sum(best_ts) / len(best_ts)
        lines.append(f"▼ 最も反応が良い朝テーマ形式: 【{THEME_NAMES.get(best_type, best_type)}】（平均スコア {avg_t:.1f}）")

    # 高反応投稿例
    lines.append("")
    lines.append("▼ 高エンゲージメント投稿（書き方・表現を参考にすること）:")
    for r in top[:2]:
        preview = r["text"][:60].replace("\n", " ")
        m = r["metrics"]
        lines.append(f"  「{preview}…」")
        lines.append(f"  → いいね:{m.get('likes',0)}  RT:{m.get('retweets',0)}  返信:{m.get('replies',0)}")

    # 低反応投稿例
    if bottom:
        lines.append("")
        lines.append("▼ 反応が低かった投稿（このパターン・表現は避けること）:")
        for r in bottom[:1]:
            preview = r["text"][:60].replace("\n", " ")
            lines.append(f"  「{preview}…」")

    # サマリ
    avg_score = sum(r["_score"] for r in records) / len(records)
    lines.append("")
    lines.append(f"▼ 直近{len(records)}件の平均エンゲージメントスコア: {avg_score:.1f}")

    return "\n".join(lines)
