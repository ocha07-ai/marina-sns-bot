"""
image_generator.py - タロットカード画像に投稿テキストをオーバーレイして投稿用画像を生成する
"""
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

BASE_DIR      = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR    = os.path.join(BASE_DIR, "assets", "tarot")
OUTPUT_DIR    = os.path.join(BASE_DIR, "output", "images")

CANVAS_W = 1080
CANVAS_H = 1920

# カード名 → ファイル名ベース
TAROT_FILE_MAP = {
    "愚者":      "00_fool",
    "魔術師":    "01_magician",
    "女教皇":    "02_high_priestess",
    "女帝":      "03_empress",
    "皇帝":      "04_emperor",
    "法王":      "05_hierophant",
    "恋人":      "06_lovers",
    "戦車":      "07_chariot",
    "力":        "08_strength",
    "隠者":      "09_hermit",
    "運命の輪":  "10_wheel",
    "正義":      "11_justice",
    "吊された男": "12_hanged_man",
    "死神":      "13_death",
    "節制":      "14_temperance",
    "悪魔":      "15_devil",
    "塔":        "16_tower",
    "星":        "17_star",
    "月":        "18_moon",
    "太陽":      "19_sun",
    "審判":      "20_judgement",
    "世界":      "21_world",
}

# テキストカラー
COLOR_GOLD     = (212, 175, 55)
COLOR_TEXT     = (240, 235, 255)
COLOR_BG       = (15, 10, 30)
COLOR_BG_END   = (25, 15, 55)


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """日本語フォントを取得（Windows / Linux 両対応）"""
    candidates = [
        # Linux (GitHub Actions / Ubuntu)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # Windows
        "C:/Windows/Fonts/YuGothB.ttc",
        "C:/Windows/Fonts/meiryob.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size, index=0)
    return ImageFont.load_default()


def _find_card_image(card_name: str) -> str | None:
    """カード名からファイルパスを探す（PNG/JPG対応）"""
    file_base = TAROT_FILE_MAP.get(card_name)
    if not file_base:
        return None
    for ext in (".png", ".jpg", ".jpeg"):
        path = os.path.join(ASSETS_DIR, f"{file_base}{ext}")
        if os.path.exists(path):
            return path
    return None


def _remove_emoji(text: str) -> str:
    """画像レンダリング用に絵文字を除去する（フォント非対応のため）。
    日本語テキスト（漢字・ひらがな・カタカナ）は除去しない。
    """
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def _wrap_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """日本語テキストを指定幅で折り返す"""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            test = current + char
            w = draw.textlength(test, font=font)
            if w > max_width and current:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def _draw_gradient_bg(draw: ImageDraw.Draw, y_start: int):
    """テキストエリアのグラデーション背景を描画"""
    height = CANVAS_H - y_start
    for i, y in enumerate(range(y_start, CANVAS_H)):
        t = i / height
        r = int(COLOR_BG[0] + t * (COLOR_BG_END[0] - COLOR_BG[0]))
        g = int(COLOR_BG[1] + t * (COLOR_BG_END[1] - COLOR_BG[1]))
        b = int(COLOR_BG[2] + t * (COLOR_BG_END[2] - COLOR_BG[2]))
        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b))


def generate_tarot_image(card_name: str, text: str) -> str | None:
    """
    タロットカード画像にテキストをオーバーレイした投稿用画像を生成する。
    カード画像が未準備の場合は None を返す（テキスト投稿にフォールバック）。

    レイアウト:
        カード画像をキャンバス全体に拡大表示し、
        下部 50% に暗いグラデーションオーバーレイを重ねてテキストを配置する。

    Args:
        card_name: タロットカード名（日本語）
        text:      投稿テキスト（ハッシュタグ含む）

    Returns:
        生成した画像のパス。生成不可の場合は None
    """
    card_path = _find_card_image(card_name)
    if not card_path:
        print(f"[画像] カード画像未準備: {card_name} → テキストのみ投稿")
        return None

    # ── カード画像をキャンバス全体に拡大（中央クロップ）────
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), COLOR_BG)
    card_img = Image.open(card_path).convert("RGB")
    cw, ch = card_img.size

    # キャンバスを埋めるように拡大（はみ出た部分はクロップ）
    ratio = max(CANVAS_W / cw, CANVAS_H / ch)
    fill_w, fill_h = int(cw * ratio), int(ch * ratio)
    card_img = card_img.resize((fill_w, fill_h), Image.LANCZOS)

    x_off = (fill_w - CANVAS_W) // 2
    y_off = (fill_h - CANVAS_H) // 2
    card_img = card_img.crop((x_off, y_off, x_off + CANVAS_W, y_off + CANVAS_H))
    canvas.paste(card_img, (0, 0))

    # ── 下部グラデーションオーバーレイ（RGBA合成）──────────
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    overlay_start = int(CANVAS_H * 0.38)   # 上38%はカードを見せる
    for i, y in enumerate(range(overlay_start, CANVAS_H)):
        t = i / (CANVAS_H - overlay_start)
        alpha = int(220 * min(t * 1.6, 1.0))   # 徐々に不透明に
        r = int(COLOR_BG[0] * (0.6 + 0.4 * t))
        g = int(COLOR_BG[1] * (0.6 + 0.4 * t))
        b = int(COLOR_BG[2] + t * (COLOR_BG_END[2] - COLOR_BG[2]))
        ov_draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, alpha))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # ── テキストエリアの基準Y座標 ───────────────────────────
    text_y = int(CANVAS_H * 0.52)
    pad    = 70

    # ゴールドの区切り線
    draw.line([(pad, text_y), (CANVAS_W - pad, text_y)], fill=COLOR_GOLD, width=2)

    # ── カード名（ゴールド）─────────────────────────────────
    font_title = _get_font(76)
    card_label = f"◆  {card_name}  ◆"
    w = draw.textlength(card_label, font=font_title)
    draw.text(((CANVAS_W - w) // 2, text_y + 24), card_label, font=font_title, fill=COLOR_GOLD)

    # ── 本文（ハッシュタグ・絵文字を除外）──────────────────
    body   = _remove_emoji(text.split("#")[0].strip())
    font_body = _get_font(46)
    lines  = _wrap_text(draw, body, font_body, CANVAS_W - pad * 2)

    y_cur  = text_y + 130
    line_h = 68
    for line in lines:
        if y_cur + line_h > CANVAS_H - 110:
            break
        draw.text((pad, y_cur), line, font=font_body, fill=COLOR_TEXT)
        y_cur += line_h

    # ── マリナブランディング（下部中央）────────────────────
    font_brand = _get_font(38)
    brand = "◆  恋愛霊視・マリナ  ◆"
    bw = draw.textlength(brand, font=font_brand)
    draw.text(((CANVAS_W - bw) // 2, CANVAS_H - 85), brand, font=font_brand, fill=COLOR_GOLD)

    # ── 保存 ────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"tarot_{card_name}_{ts}.png")
    canvas.save(path, "PNG")
    print(f"[画像] 生成完了: {path}")
    return path
