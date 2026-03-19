"""
app.py - マリナ SNS自動投稿ツール ダッシュボード
起動: streamlit run app.py
"""
import json, os, sys
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

BASE_DIR      = Path(__file__).parent
LOG_PATH      = BASE_DIR / "logs" / "post_log.jsonl"
SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"

PLATFORM_LABELS = {"x": "X (Twitter)", "threads": "Threads", "tiktok": "TikTok"}
SESSION_LABELS  = {"morning": "朝投稿", "evening": "夜投稿"}
PLATFORM_ICONS  = {"x": "𝕏", "threads": "⊚", "tiktok": "♪"}

# Gentelella カラー
C_SIDEBAR   = "#2A3F54"
C_SIDEBAR_H = "#1F2E3F"
C_BLUE      = "#3498DB"
C_GREEN     = "#26B99A"
C_ORANGE    = "#E9967A"
C_YELLOW    = "#F0AD4E"
C_RED       = "#E74C3C"
C_BG        = "#F7F8FA"
C_WHITE     = "#FFFFFF"
C_BORDER    = "#E6E9ED"
C_TEXT      = "#2C3E50"
C_MUTED     = "#73879C"

st.set_page_config(
    page_title="Marina Bot",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, .stApp {{
    font-family: 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background: {C_BG};
    color: {C_TEXT};
    font-size: 14px;
}}

/* ── サイドバー ── */
section[data-testid="stSidebar"] {{
    background: {C_SIDEBAR} !important;
    width: 230px !important;
    min-width: 230px !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    background: {C_SIDEBAR} !important;
    padding: 0 !important;
}}

/* ── メインエリア ── */
.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* ── トップバー ── */
.topbar {{
    background: {C_WHITE};
    border-bottom: 1px solid {C_BORDER};
    padding: 0 24px;
    height: 57px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.topbar-title {{
    font-size: 1rem;
    font-weight: 700;
    color: {C_TEXT};
    letter-spacing: 0.01em;
}}
.topbar-sub {{
    font-size: 0.8rem;
    color: {C_MUTED};
    margin-top: 1px;
}}
.breadcrumb {{
    font-size: 0.78rem;
    color: {C_MUTED};
    display: flex;
    align-items: center;
    gap: 6px;
}}
.breadcrumb-sep {{ color: #C8D0DA; }}

/* ── コンテンツ ── */
.page-content {{
    padding: 24px;
}}

/* ── 統計タイル ── */
.tile {{
    border-radius: 4px;
    padding: 20px 24px;
    color: #fff;
    position: relative;
    overflow: hidden;
    margin-bottom: 0;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.tile::after {{
    content: '';
    position: absolute;
    right: -12px;
    bottom: -12px;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(255,255,255,0.12);
}}
.tile-blue   {{ background: {C_BLUE}; }}
.tile-green  {{ background: {C_GREEN}; }}
.tile-orange {{ background: {C_ORANGE}; }}
.tile-yellow {{ background: {C_YELLOW}; }}
.tile-red    {{ background: {C_RED}; }}
.tile-label {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    opacity: 0.85;
}}
.tile-value {{
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
}}
.tile-meta {{
    font-size: 0.75rem;
    opacity: 0.8;
    margin-top: 4px;
}}
.tile-icon {{
    position: absolute;
    right: 18px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 3rem;
    opacity: 0.18;
    z-index: 0;
}}

/* ── ホワイトカード ── */
.card {{
    background: {C_WHITE};
    border: 1px solid {C_BORDER};
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.card-header {{
    background: {C_WHITE};
    border-bottom: 1px solid {C_BORDER};
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.card-header-title {{
    font-size: 1rem;
    font-weight: 600;
    color: {C_TEXT};
}}
.card-body {{
    padding: 20px;
}}

/* ── サイドバーメニュー ── */
.sb-header {{
    background: {C_SIDEBAR_H};
    padding: 20px 18px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}
.sb-logo {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.02em;
}}
.sb-logo-sub {{
    font-size: 0.7rem;
    color: rgba(255,255,255,0.45);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.sb-section {{
    padding: 18px 18px 4px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
}}
.sb-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 18px;
    font-size: 0.875rem;
    color: rgba(255,255,255,0.7);
    font-weight: 400;
    transition: all 0.15s;
    cursor: pointer;
    border-left: 3px solid transparent;
    text-decoration: none;
}}
.sb-item:hover {{
    background: rgba(255,255,255,0.07);
    color: #fff;
    border-left-color: {C_BLUE};
}}
.sb-item-active {{
    background: rgba(255,255,255,0.1) !important;
    color: #fff !important;
    border-left-color: {C_BLUE} !important;
    font-weight: 600 !important;
}}
.sb-icon {{ width: 18px; text-align: center; opacity: 0.7; font-size: 1rem; }}
.sb-status {{
    padding: 16px 18px;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin-top: auto;
}}
.sb-status-dot {{
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    vertical-align: middle;
}}

/* ── アクティビティ行 ── */
.activity-item {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid #F0F3F7;
}}
.activity-item:last-child {{ border-bottom: none; }}
.activity-avatar {{
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: #fff;
    flex-shrink: 0;
    font-weight: 700;
}}
.activity-content {{ flex: 1; min-width: 0; }}
.activity-title {{ font-size: 0.875rem; color: {C_TEXT}; font-weight: 600; }}
.activity-sub   {{ font-size: 0.75rem; color: {C_MUTED}; margin-top: 2px; }}
.badge {{
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 3px;
    color: #fff;
    white-space: nowrap;
}}
.badge-success {{ background: {C_GREEN}; }}
.badge-danger  {{ background: {C_RED}; }}

/* ── プログレスバー ── */
.prog-wrap {{ margin-bottom: 16px; }}
.prog-label {{
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: {C_TEXT};
    font-weight: 600;
    margin-bottom: 5px;
}}
.prog-pct {{ color: {C_MUTED}; font-weight: 400; }}
.prog-track {{
    height: 6px;
    background: #E8ECF1;
    border-radius: 3px;
    overflow: hidden;
}}
.prog-bar {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease;
}}

/* ── ボタン ── */
.stButton > button {{
    background: {C_WHITE} !important;
    color: {C_TEXT} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 4px !important;
    font-family: 'Source Sans Pro', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    width: 100%;
    transition: all 0.15s !important;
}}
.stButton > button:hover {{
    background: #EBF0F5 !important;
    border-color: #BDC6D0 !important;
}}
.stButton > button[kind="primary"] {{
    background: {C_BLUE} !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 6px rgba(52,152,219,0.35) !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: #2980B9 !important;
    box-shadow: 0 4px 12px rgba(52,152,219,0.45) !important;
}}

/* テキストエリア */
.stTextArea textarea {{
    background: {C_WHITE} !important;
    color: {C_TEXT} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 4px !important;
    font-family: 'Source Sans Pro', sans-serif !important;
    font-size: 0.9rem !important;
    line-height: 1.65 !important;
    padding: 10px 14px !important;
}}
.stTextArea textarea:focus {{
    border-color: {C_BLUE} !important;
    box-shadow: 0 0 0 3px rgba(52,152,219,0.15) !important;
}}

/* セレクト・入力 */
.stSelectbox > div > div,
.stTextInput > div > div > input {{
    background: {C_WHITE} !important;
    color: {C_TEXT} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 4px !important;
    font-family: 'Source Sans Pro', sans-serif !important;
    font-size: 0.875rem !important;
}}
.stSelectbox label, .stTextInput label {{
    color: {C_TEXT} !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}}

/* タブ */
.stTabs [data-baseweb="tab-list"] {{
    background: {C_WHITE} !important;
    border-bottom: 1px solid {C_BORDER} !important;
    gap: 0 !important;
    padding: 0 20px !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {C_MUTED} !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 12px 20px !important;
    border: none !important;
    background: transparent !important;
    font-family: 'Source Sans Pro', sans-serif !important;
}}
.stTabs [aria-selected="true"] {{
    color: {C_BLUE} !important;
    border-bottom: 2px solid {C_BLUE} !important;
}}

/* データテーブル */
[data-testid="stDataFrame"] {{
    border: 1px solid {C_BORDER} !important;
    border-radius: 4px !important;
    overflow: hidden;
}}
[data-testid="stDataFrame"] th {{
    background: #F7F8FA !important;
    color: {C_MUTED} !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 12px !important;
}}
[data-testid="stDataFrame"] td {{
    color: {C_TEXT} !important;
    font-size: 0.85rem !important;
    padding: 9px 12px !important;
}}

/* チェックボックス */
.stCheckbox label {{
    color: {C_TEXT} !important;
    font-size: 0.875rem !important;
    font-family: 'Source Sans Pro', sans-serif !important;
    font-weight: 400 !important;
}}

/* ラジオ */
.stRadio > div {{ gap: 2px !important; }}
.stRadio label {{
    border-radius: 4px !important;
    padding: 9px 12px !important;
    font-size: 0.875rem !important;
    color: rgba(255,255,255,0.7) !important;
    font-weight: 400 !important;
    transition: all 0.15s !important;
    font-family: 'Source Sans Pro', sans-serif !important;
}}
.stRadio label:hover {{
    background: rgba(255,255,255,0.07) !important;
    color: #fff !important;
}}

/* misc */
hr {{ border-color: {C_BORDER} !important; margin: 20px 0 !important; }}
.stCaption {{ color: {C_MUTED} !important; font-size: 0.75rem !important; }}
[data-testid="stAlert"] {{ border-radius: 4px !important; font-size: 0.875rem !important; }}
[data-testid="stSpinner"] p {{ color: {C_MUTED} !important; }}
[data-testid="stMetricValue"] {{ color: {C_TEXT} !important; font-size: 1.8rem !important; font-weight: 700 !important; }}
[data-testid="stMetricLabel"] {{ color: {C_MUTED} !important; font-size: 0.72rem !important; font-weight: 700 !important; letter-spacing: 0.08em !important; }}
[data-testid="stBarChart"] {{ background: {C_WHITE}; border: 1px solid {C_BORDER}; border-radius: 4px; padding: 16px; }}
</style>
""", unsafe_allow_html=True)


# ── ユーティリティ ─────────────────────────────────────────
@st.cache_data(ttl=5)
def load_settings():
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_settings(data):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    load_settings.clear()

def load_logs():
    if not LOG_PATH.exists():
        return pd.DataFrame(columns=["timestamp","platform","session","status","post_id","error"])
    rows = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            ln = line.strip()
            if ln:
                try: rows.append(json.loads(ln))
                except: pass
    if not rows:
        return pd.DataFrame(columns=["timestamp","platform","session","status","post_id","error"])
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp", ascending=False).reset_index(drop=True)

def today_stats(df):
    if df.empty: return 0, 0
    td = df[df["timestamp"].dt.date == date.today()]
    return len(td[td["status"]=="success"]), len(td[td["status"]=="error"])

def api_ok():
    return bool(os.environ.get("ANTHROPIC_API_KEY","").strip())


# ── サイドバー ─────────────────────────────────────────────
with st.sidebar:
    settings = load_settings()

    st.markdown(f"""
    <div class="sb-header">
        <div class="sb-logo">🔮 Marina Bot</div>
        <div class="sb-logo-sub">SNS 自動投稿ツール</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">メニュー</div>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["ダッシュボード", "投稿管理", "投稿履歴", "設定"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="sb-section">プラットフォーム</div>', unsafe_allow_html=True)

    for p, label in PLATFORM_LABELS.items():
        enabled = settings["platforms"][p]["enabled"]
        dot_color = C_GREEN if enabled else "#555"
        shadow = f"box-shadow:0 0 5px {C_GREEN}99;" if enabled else ""
        status_text = "稼働中" if enabled else "停止中"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:8px 18px;">
            <span style="width:7px;height:7px;border-radius:50%;background:{dot_color};{shadow};display:inline-block;flex-shrink:0;"></span>
            <span style="font-size:0.82rem;color:{'rgba(255,255,255,0.75)' if enabled else 'rgba(255,255,255,0.35)'};flex:1;">{label}</span>
            <span style="font-size:0.65rem;color:{'rgba(255,255,255,0.4)' if enabled else 'rgba(255,255,255,0.2)'};">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # API状態
    api_color = C_GREEN if api_ok() else C_RED
    api_label = "Claude API 接続中" if api_ok() else "Claude API 未設定"
    st.markdown(f"""
    <div style="padding:14px 18px;border-top:1px solid rgba(255,255,255,0.07);">
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="width:8px;height:8px;border-radius:50%;background:{api_color};display:inline-block;"></span>
            <span style="font-size:0.75rem;color:rgba(255,255,255,0.55);">{api_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── ページ: ダッシュボード ────────────────────────────────
if page == "ダッシュボード":
    df = load_logs()
    s_ok, s_err = today_stats(df)
    total = len(df[df["status"]=="success"]) if not df.empty else 0
    settings = load_settings()

    now = datetime.now()
    mh,mm = map(int, settings["schedule"]["morning_time"].split(":"))
    eh,em = map(int, settings["schedule"]["evening_time"].split(":"))
    if now.hour < mh or (now.hour==mh and now.minute<mm):
        next_txt = settings["schedule"]["morning_time"]
        next_lbl = "朝投稿"
    elif now.hour < eh or (now.hour==eh and now.minute<em):
        next_txt = settings["schedule"]["evening_time"]
        next_lbl = "夜投稿"
    else:
        next_txt = settings["schedule"]["morning_time"]
        next_lbl = "明日の朝"

    # トップバー
    st.markdown(f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">ダッシュボード</div>
            <div class="breadcrumb">
                <span>Home</span>
                <span class="breadcrumb-sep">›</span>
                <span style="color:{C_BLUE}">ダッシュボード</span>
            </div>
        </div>
        <div style="font-size:0.78rem;color:{C_MUTED};">{now.strftime("%Y年%m月%d日  %H:%M")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    # 統計タイル
    c1,c2,c3,c4 = st.columns(4)
    tiles = [
        (c1, "tile-blue",   "今日の投稿", str(s_ok),    "成功件数", "📤"),
        (c2, "tile-red",    "エラー",     str(s_err),   "今日のエラー", "⚠️"),
        (c3, "tile-green",  "累計投稿",   str(total),   "全期間合計", "📊"),
        (c4, "tile-yellow", "次回投稿",   next_txt,     next_lbl, "🕐"),
    ]
    for col, cls, label, value, meta, icon in tiles:
        with col:
            st.markdown(f"""
            <div class="tile {cls}">
                <div class="tile-icon">{icon}</div>
                <div>
                    <div class="tile-label">{label}</div>
                    <div class="tile-value">{value}</div>
                    <div class="tile-meta">{meta}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2], gap="medium")

    with col_l:
        st.markdown(f"""
        <div class="card">
            <div class="card-header">
                <span class="card-header-title">最近の投稿アクティビティ</span>
                <span style="font-size:0.75rem;color:{C_MUTED};">直近6件</span>
            </div>
            <div class="card-body" style="padding:0 20px;">
        """, unsafe_allow_html=True)

        if df.empty:
            st.markdown(f'<div style="padding:40px 0;text-align:center;color:{C_MUTED};font-size:0.875rem;">まだ投稿履歴がありません</div>', unsafe_allow_html=True)
        else:
            colors = {"x": C_BLUE, "threads": C_GREEN, "tiktok": C_ORANGE}
            for _, row in df.head(6).iterrows():
                p    = row["platform"]
                icon = PLATFORM_ICONS.get(p, "?")
                col  = colors.get(p, C_BLUE)
                ts   = row["timestamp"].strftime("%m/%d  %H:%M")
                ok   = row["status"] == "success"
                badge_cls = "badge-success" if ok else "badge-danger"
                badge_txt = "成功" if ok else "エラー"
                st.markdown(f"""
                <div class="activity-item">
                    <div class="activity-avatar" style="background:{col};">{icon}</div>
                    <div class="activity-content">
                        <div class="activity-title">{PLATFORM_LABELS.get(p,p)}  ·  {SESSION_LABELS.get(row['session'],row['session'])}</div>
                        <div class="activity-sub">{ts}</div>
                    </div>
                    <span class="badge {badge_cls}">{badge_txt}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    with col_r:
        st.markdown(f"""
        <div class="card">
            <div class="card-header">
                <span class="card-header-title">プラットフォーム別投稿</span>
            </div>
            <div class="card-body">
        """, unsafe_allow_html=True)

        if not df.empty and len(df[df["status"]=="success"]) > 0:
            chart = df[df["status"]=="success"].groupby("platform").size()
            total_chart = chart.sum()
            colors_map = {"x": C_BLUE, "threads": C_GREEN, "tiktok": C_ORANGE}
            for p, cnt in chart.items():
                pct = int(cnt / total_chart * 100)
                col = colors_map.get(p, C_BLUE)
                st.markdown(f"""
                <div class="prog-wrap">
                    <div class="prog-label">
                        <span>{PLATFORM_LABELS.get(p,p)}</span>
                        <span class="prog-pct">{cnt}件  ({pct}%)</span>
                    </div>
                    <div class="prog-track">
                        <div class="prog-bar" style="width:{pct}%;background:{col};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="padding:20px 0;text-align:center;color:{C_MUTED};font-size:0.875rem;">データなし</div>', unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── ページ: 投稿管理 ─────────────────────────────────────
elif page == "投稿管理":
    st.markdown(f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">投稿管理</div>
            <div class="breadcrumb">
                <span>Home</span><span class="breadcrumb-sep">›</span>
                <span style="color:{C_BLUE}">投稿管理</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    if not api_ok():
        st.error(".env ファイルに ANTHROPIC_API_KEY を設定してください。")
        st.stop()

    cl, cr = st.columns([1, 2], gap="medium")

    with cl:
        st.markdown(f"""
        <div class="card">
            <div class="card-header"><span class="card-header-title">投稿設定</span></div>
            <div class="card-body">
        """, unsafe_allow_html=True)

        session  = st.selectbox("セッション", ["morning","evening"], format_func=lambda s: SESSION_LABELS[s])
        platform = st.selectbox("プラットフォーム", ["x","threads"], format_func=lambda p: PLATFORM_LABELS[p])
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("コンテンツを生成", type="primary"):
            with st.spinner("Claudeが生成中…"):
                try:
                    import generator
                    text = generator.generate(session, platform)
                    st.session_state.update({"gen_text":text,"gen_session":session,"gen_platform":platform})
                    st.success("生成完了！")
                except Exception as e:
                    st.error(f"生成エラー: {e}")

        st.markdown("</div></div>", unsafe_allow_html=True)

    with cr:
        st.markdown(f"""
        <div class="card">
            <div class="card-header"><span class="card-header-title">生成コンテンツ</span></div>
            <div class="card-body">
        """, unsafe_allow_html=True)

        if "gen_text" not in st.session_state:
            st.markdown(f"""
            <div style="border:2px dashed {C_BORDER};border-radius:4px;text-align:center;
                        padding:48px 24px;color:{C_MUTED};font-size:0.875rem;">
                左の「コンテンツを生成」を押してください
            </div>
            """, unsafe_allow_html=True)
        else:
            edited = st.text_area("", value=st.session_state["gen_text"], height=180, label_visibility="collapsed")
            limit  = 140 if st.session_state.get("gen_platform")=="x" else 400
            cnt    = len(edited)
            pct    = min(cnt/limit*100, 100)
            bar_c  = C_RED if cnt > limit else C_BLUE
            st.markdown(f"""
            <div style="margin-top:6px;">
                <div style="height:4px;background:#E8ECF1;border-radius:2px;overflow:hidden;">
                    <div style="height:100%;width:{pct:.1f}%;background:{bar_c};transition:width 0.3s;"></div>
                </div>
                <div style="display:flex;justify-content:flex-end;margin-top:4px;">
                    <span style="font-size:0.72rem;color:{bar_c};font-weight:600;">{cnt} / {limit} 文字</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            c1,c2 = st.columns(2)
            with c1:
                if st.button("投稿する", type="primary"):
                    p = st.session_state.get("gen_platform","x")
                    s = st.session_state.get("gen_session","morning")
                    with st.spinner("投稿中…"):
                        try:
                            if p=="x":
                                import poster_x
                                ok = poster_x.post(edited, s)
                            else:
                                st.warning("Threads は準備中です。")
                                ok = False
                            if ok:
                                st.success("投稿しました！")
                                del st.session_state["gen_text"]
                                st.rerun()
                        except Exception as e:
                            st.error(str(e))
            with c2:
                if st.button("リセット"):
                    del st.session_state["gen_text"]
                    st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── ページ: 投稿履歴 ─────────────────────────────────────
elif page == "投稿履歴":
    st.markdown(f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">投稿履歴</div>
            <div class="breadcrumb">
                <span>Home</span><span class="breadcrumb-sep">›</span>
                <span style="color:{C_BLUE}">投稿履歴</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    st.markdown(f'<div class="card"><div class="card-header"><span class="card-header-title">投稿ログ一覧</span></div><div class="card-body">', unsafe_allow_html=True)

    df = load_logs()
    if df.empty:
        st.markdown(f'<div style="text-align:center;padding:40px;color:{C_MUTED};">投稿履歴がありません</div>', unsafe_allow_html=True)
    else:
        c1,c2,c3 = st.columns(3)
        with c1: fp  = st.selectbox("プラットフォーム", ["すべて","x","threads","tiktok"])
        with c2: fs  = st.selectbox("セッション",       ["すべて","morning","evening"])
        with c3: fst = st.selectbox("ステータス",        ["すべて","success","error"])

        fdf = df.copy()
        if fp  != "すべて": fdf = fdf[fdf["platform"]==fp]
        if fs  != "すべて": fdf = fdf[fdf["session"]==fs]
        if fst != "すべて": fdf = fdf[fdf["status"]==fst]

        st.markdown(f'<div style="font-size:0.78rem;color:{C_MUTED};margin:8px 0 14px;font-weight:600;">{len(fdf)} 件</div>', unsafe_allow_html=True)

        disp = fdf[["timestamp","platform","session","status","post_id"]].copy()
        disp["timestamp"] = disp["timestamp"].dt.strftime("%Y/%m/%d  %H:%M")
        disp["platform"]  = disp["platform"].map(PLATFORM_LABELS)
        disp["session"]   = disp["session"].map(SESSION_LABELS)
        disp["status"]    = disp["status"].apply(lambda s: "✓ 成功" if s=="success" else "✕ エラー")
        disp.columns      = ["日時","プラットフォーム","セッション","結果","投稿ID"]
        st.dataframe(disp, use_container_width=True, hide_index=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── ページ: 設定 ─────────────────────────────────────────
elif page == "設定":
    st.markdown(f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">設定</div>
            <div class="breadcrumb">
                <span>Home</span><span class="breadcrumb-sep">›</span>
                <span style="color:{C_BLUE}">設定</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    settings = load_settings()

    tab1, tab2 = st.tabs(["スケジュール & プラットフォーム", "API キー"])

    with tab1:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        cs, cp = st.columns(2, gap="medium")

        with cs:
            st.markdown(f'<div class="card"><div class="card-header"><span class="card-header-title">投稿スケジュール</span></div><div class="card-body">', unsafe_allow_html=True)
            morning_time = st.text_input("朝投稿の時間", value=settings["schedule"]["morning_time"])
            evening_time = st.text_input("夜投稿の時間", value=settings["schedule"]["evening_time"])
            st.markdown("</div></div>", unsafe_allow_html=True)

        with cp:
            st.markdown(f'<div class="card"><div class="card-header"><span class="card-header-title">プラットフォーム管理</span></div><div class="card-body">', unsafe_allow_html=True)
            for p, label in PLATFORM_LABELS.items():
                st.markdown(f'<div style="font-size:0.875rem;color:{C_TEXT};font-weight:600;margin-bottom:6px;">{label}</div>', unsafe_allow_html=True)
                ca,cb,cc = st.columns(3)
                with ca: settings["platforms"][p]["enabled"] = st.checkbox("有効", value=settings["platforms"][p]["enabled"], key=f"{p}_e")
                with cb: settings["platforms"][p]["morning"] = st.checkbox("朝",   value=settings["platforms"][p]["morning"],  key=f"{p}_m")
                with cc: settings["platforms"][p]["evening"] = st.checkbox("夜",   value=settings["platforms"][p]["evening"],  key=f"{p}_n")
                st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)

        if st.button("設定を保存", type="primary"):
            settings["schedule"]["morning_time"] = morning_time
            settings["schedule"]["evening_time"] = evening_time
            save_settings(settings)
            st.success("保存しました")

    with tab2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="card"><div class="card-header"><span class="card-header-title">API キーの状態</span></div><div class="card-body">', unsafe_allow_html=True)
        for env_key, label in {
            "ANTHROPIC_API_KEY": "Claude API",
            "X_API_KEY":         "X (Twitter)",
            "THREADS_ACCESS_TOKEN": "Threads",
            "TIKTOK_ACCESS_TOKEN":  "TikTok",
        }.items():
            val = os.environ.get(env_key,"")
            if val:
                masked = val[:8]+"••••••••"+val[-4:]
                dot_c, txt_c, right = C_GREEN, C_TEXT, f'<span style="font-size:0.75rem;color:{C_MUTED};font-family:monospace;">{masked}</span>'
            else:
                dot_c, txt_c, right = C_RED, C_MUTED, f'<span style="font-size:0.75rem;color:{C_RED};font-weight:600;">.env に未設定</span>'
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid {C_BORDER};">
                <span style="width:8px;height:8px;border-radius:50%;background:{dot_c};display:inline-block;flex-shrink:0;"></span>
                <span style="flex:1;font-size:0.875rem;color:{txt_c};font-weight:600;">{label}</span>
                {right}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
