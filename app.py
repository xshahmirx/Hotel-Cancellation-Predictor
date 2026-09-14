import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import joblib
import plotly.graph_objects as go

# ============================================================== setup
st.set_page_config(page_title="Hotel Booking Cancellation Predictor",
                   page_icon="🏨", layout="wide")

NAVY, SURFACE, LINE = "#0F1B2D", "#16263D", "#24364F"
BRASS, IVORY, MUTED = "#C9A45C", "#F3EEE3", "#8A96A8"
CORAL, SAGE = "#E36F5B", "#6FB58A"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=DM+Sans:wght@400;500;600&display=swap');

/* ---------- base ---------- */
html, body, [class*="css"], .stMarkdown, .stCaption, label, input, select, button, textarea {
    font-family: 'DM Sans', sans-serif !important;
}
h1, h2, h3 { font-family: 'Fraunces', serif !important; font-weight: 600; letter-spacing: -0.01em; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1180px; }

/* ---------- living background: slow aurora ---------- */
.stApp { background: #0F1B2D; }
.stApp::before {
    content: ""; position: fixed; inset: -20%; z-index: 0; pointer-events: none;
    background:
      radial-gradient(40% 40% at 20% 20%, rgba(201,164,92,0.14), transparent 70%),
      radial-gradient(35% 35% at 80% 30%, rgba(111,181,138,0.10), transparent 70%),
      radial-gradient(45% 45% at 60% 85%, rgba(227,111,91,0.10), transparent 70%);
    animation: aurora 18s ease-in-out infinite alternate;
    filter: blur(20px);
}
@keyframes aurora {
    0%   { transform: translate(0, 0) rotate(0deg) scale(1); }
    50%  { transform: translate(4%, -3%) rotate(3deg) scale(1.05); }
    100% { transform: translate(-3%, 4%) rotate(-2deg) scale(1.02); }
}
.block-container { position: relative; z-index: 1; }

/* ---------- hero: one orchestrated entrance ---------- */
.hero { padding: 8px 0 26px 0; border-bottom: 1px solid #24364F; margin-bottom: 26px; }
.hero h1 { font-size: 3.2rem; line-height: 1.05; margin: 0 0 14px 0; color: #F3EEE3;
           animation: rise .7s cubic-bezier(.2,.8,.2,1) both; }
.hero p  { font-size: 1.08rem; color: #B7C0CF; max-width: 640px; margin: 0 0 18px 0; line-height: 1.55;
           animation: rise .7s .12s cubic-bezier(.2,.8,.2,1) both; }
.pills { animation: rise .7s .24s cubic-bezier(.2,.8,.2,1) both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

.pill { display: inline-block; padding: 8px 16px; margin: 0 8px 8px 0; border-radius: 999px;
        background: #16263D; border: 1px solid #24364F; color: #F3EEE3; font-size: 0.95rem;
        transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
.pill:hover { transform: translateY(-4px); border-color: #C9A45C;
              box-shadow: 0 12px 28px rgba(201,164,92,0.18); }
.pill b { color: #C9A45C; font-weight: 600; font-family: 'Fraunces', serif; font-size: 1.1rem; }

/* ---------- tabs: segmented control (no .stTabs prefix, works on any version) ---------- */
[data-testid="stTabs"] [role="tablist"], div[role="tablist"] {
    gap: 6px !important; padding: 6px !important; border-radius: 999px !important; border: 1px solid #24364F !important;
    background: rgba(22,38,61,0.75) !important; backdrop-filter: blur(8px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.25) !important; width: fit-content; margin: 4px 0 22px 0 !important;
}
button[role="tab"], [role="tab"] {
    padding: 10px 22px !important; border-radius: 999px !important; color: #B7C0CF !important;
    font-weight: 500 !important; font-size: 0.98rem !important; cursor: pointer;
    background: transparent !important; border: 1px solid transparent !important;
    transition: transform .22s cubic-bezier(.2,.8,.2,1), background .22s ease, color .22s ease,
                box-shadow .22s ease, border-color .22s ease !important;
    will-change: transform;
}
button[role="tab"]:hover, [role="tab"]:hover {
    color: #F3EEE3 !important; background: rgba(201,164,92,0.14) !important;
    border-color: rgba(201,164,92,0.55) !important;
    transform: translateY(-3px) scale(1.04) !important;
    box-shadow: 0 10px 26px rgba(0,0,0,0.35), 0 0 18px rgba(201,164,92,0.25) !important;
}
button[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] {
    background: linear-gradient(120deg, #C9A45C, #E0C27A) !important; color: #0F1B2D !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 24px rgba(201,164,92,0.45), inset 0 1px 0 rgba(255,255,255,0.35) !important;
}
button[role="tab"][aria-selected="true"]:hover, [role="tab"][aria-selected="true"]:hover {
    transform: translateY(-2px) scale(1.03) !important;
    box-shadow: 0 14px 32px rgba(201,164,92,0.6) !important;
}
[role="tab"] p, [role="tab"] span, [role="tab"] div { color: inherit !important; margin: 0 !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
[role="tabpanel"] { animation: rise .45s cubic-bezier(.2,.8,.2,1) both; padding-top: 4px; }

/* ---------- cards that float on hover ---------- */
[data-testid="stMetric"], [data-testid="stExpander"], .card {
    background: #16263D; border: 1px solid #24364F; border-radius: 16px; padding: 16px 20px;
    transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s ease, border-color .28s ease;
}
[data-testid="stMetric"]:hover, [data-testid="stExpander"]:hover, .card:hover {
    transform: translateY(-6px); border-color: rgba(201,164,92,0.6);
    box-shadow: 0 18px 40px rgba(0,0,0,0.35), 0 0 0 1px rgba(201,164,92,0.15);
}
[data-testid="stMetricValue"] { font-family: 'Fraunces', serif !important; font-size: 2rem; color: #F3EEE3; }
[data-testid="stMetricLabel"] { color: #8A96A8; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px !important; border-color: #24364F !important;
    background: rgba(22,38,61,0.55); backdrop-filter: blur(6px); }

/* ---------- inputs ---------- */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, .stNumberInput div[data-baseweb="input"] {
    background: #0F1B2D !important; border-color: #24364F !important; border-radius: 10px !important;
    transition: border-color .2s ease, box-shadow .2s ease; }
[data-baseweb="select"] > div:hover, [data-baseweb="input"] > div:hover { border-color: #C9A45C !important; }
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"] > div:focus-within {
    border-color: #C9A45C !important; box-shadow: 0 0 0 3px rgba(201,164,92,0.2) !important; }
.group { color: #C9A45C; font-family: 'Fraunces', serif; font-size: 1.2rem; margin: 6px 0 4px 0; }

/* ---------- the button ---------- */
.stButton > button[kind="primary"] {
    background: linear-gradient(120deg, #C9A45C 0%, #E0C27A 50%, #C9A45C 100%);
    background-size: 200% auto; color: #0F1B2D; border: none; border-radius: 14px;
    height: 3.3em; font-size: 1.08rem; font-weight: 600; letter-spacing: 0.01em;
    transition: transform .2s ease, box-shadow .25s ease, background-position .6s ease;
    box-shadow: 0 8px 24px rgba(201,164,92,0.25);
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.01); background-position: right center; color: #0F1B2D;
    box-shadow: 0 16px 40px rgba(201,164,92,0.45);
}
.stButton > button[kind="primary"]:active { transform: translateY(0) scale(.99); }
.stDownloadButton > button { border-radius: 12px; transition: transform .2s ease, box-shadow .2s ease; }
.stDownloadButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(201,164,92,0.3); }

/* ---------- verdict ---------- */
.verdict { border-radius: 18px; padding: 24px 28px; border: 1px solid; animation: rise .5s .15s both;
           transition: transform .28s ease, box-shadow .28s ease; }
.verdict:hover { transform: translateY(-4px); box-shadow: 0 18px 40px rgba(0,0,0,0.35); }
.verdict h2 { margin: 0 0 8px 0; font-size: 1.75rem; }
.verdict p  { margin: 0; color: #D6DCE6; line-height: 1.55; }
.verdict.bad  { background: linear-gradient(160deg, #2E1B18, #22171A); border-color: #E36F5B; }
.verdict.good { background: linear-gradient(160deg, #152C23, #14211E); border-color: #6FB58A; }
.verdict.bad h2  { color: #F0A08F; }
.verdict.good h2 { color: #9FD4B2; }

/* ---------- misc ---------- */
[data-testid="stFileUploader"] { border: 1px dashed #24364F; border-radius: 16px; padding: 10px;
    transition: border-color .2s ease, background .2s ease; }
[data-testid="stFileUploader"]:hover { border-color: #C9A45C; background: rgba(201,164,92,0.05); }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
.footer { color: #8A96A8; font-size: 0.9rem; border-top: 1px solid #24364F; padding-top: 14px; margin-top: 30px; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
""", unsafe_allow_html=True)

BASE = Path(__file__).parent


@st.cache_resource
def load_model():
    return joblib.load(BASE / "model.joblib")


@st.cache_data
def load_metrics():
    with open(BASE / "metrics.json") as f:
        return json.load(f)


@st.cache_data
def load_data():
    p = BASE / "hotel_bookings.csv"
    return pd.read_csv(p) if p.exists() else None


model = load_model()
meta = load_metrics()
THRESH = meta["threshold"]
TOP_COUNTRIES = meta["top_countries"]
NUM_FEATURES = meta["num_features"]
CAT_FEATURES = meta["cat_features"]
DM = meta["deployment_metrics"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def plotly_base(fig, height=300):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=IVORY), height=height,
        margin=dict(l=10, r=10, t=36, b=10),
        xaxis=dict(gridcolor=LINE, zerolinecolor=LINE),
        yaxis=dict(gridcolor=LINE, zerolinecolor=LINE),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BRASS, font=dict(color=IVORY)),
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    return fig


def bar(series, title, color=BRASS, horizontal=False, height=300, fmt=None):
    x, y = (series.values, series.index) if horizontal else (series.index, series.values)
    fig = go.Figure(go.Bar(
        x=x, y=y, orientation="h" if horizontal else "v",
        marker=dict(color=color, line=dict(width=0)),
        hovertemplate="%{x}<br>%{y}<extra></extra>"))
    fig.update_layout(title=dict(text=title, font=dict(family="Fraunces", size=17)))
    if fmt:
        fig.update_layout(**({"xaxis_tickformat": fmt} if horizontal else {"yaxis_tickformat": fmt}))
    return plotly_base(fig, height)


def predict_one(d):
    row = pd.DataFrame([d])[NUM_FEATURES + CAT_FEATURES]
    return float(model.predict_proba(row)[0, 1])   # the AI decides here


def animated_gauge(prob, threshold):
    """Custom SVG gauge: arc sweeps into place, number counts up, threshold needle marked."""
    pct = round(prob * 100, 1)
    color = CORAL if prob >= threshold else SAGE
    html = f"""
    <div style="font-family:'DM Sans',sans-serif;color:{IVORY};text-align:center;">
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=DM+Sans:wght@400;500&display=swap');
      .arc {{ transition: stroke-dashoffset 1.4s cubic-bezier(.2,.8,.2,1); }}
      .num {{ font-family:'Fraunces',serif; font-size:64px; font-weight:600; line-height:1; }}
      .lab {{ color:{MUTED}; font-size:14px; margin-top:6px; }}
    </style>
    <svg viewBox="0 0 300 180" width="100%" style="max-width:360px;overflow:visible">
      <defs>
        <linearGradient id="g" x1="0" x2="1">
          <stop offset="0" stop-color="{SAGE}"/><stop offset="{threshold}" stop-color="{BRASS}"/><stop offset="1" stop-color="{CORAL}"/>
        </linearGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <path d="M30 150 A120 120 0 0 1 270 150" fill="none" stroke="{LINE}" stroke-width="18" stroke-linecap="round"/>
      <path id="arc" class="arc" d="M30 150 A120 120 0 0 1 270 150" fill="none" stroke="url(#g)"
            stroke-width="18" stroke-linecap="round" filter="url(#glow)"
            stroke-dasharray="377" stroke-dashoffset="377"/>
      <g id="needle" transform="rotate(-90 150 150)">
        <line x1="150" y1="30" x2="150" y2="46" stroke="{IVORY}" stroke-width="3" stroke-linecap="round"/>
      </g>
      <text x="30" y="175" fill="{MUTED}" font-size="12" text-anchor="middle">0%</text>
      <text x="270" y="175" fill="{MUTED}" font-size="12" text-anchor="middle">100%</text>
    </svg>
    <div class="num" id="num" style="color:{color}">0%</div>
    <div class="lab">probability of cancellation · threshold {int(threshold*100)}%</div>
    </div>
    <script>
      const target = {pct};
      const arc = document.getElementById('arc');
      const needle = document.getElementById('needle');
      requestAnimationFrame(() => {{
        arc.style.strokeDashoffset = 377 - 377 * target / 100;
        needle.setAttribute('transform', 'rotate(' + (-90 + 180 * {threshold}) + ' 150 150)');
      }});
      const el = document.getElementById('num');
      const t0 = performance.now(), dur = 1400;
      function tick(t) {{
        const k = Math.min(1, (t - t0) / dur);
        const e = 1 - Math.pow(1 - k, 3);
        el.textContent = (target * e).toFixed(1) + '%';
        if (k < 1) requestAnimationFrame(tick);
      }}
      requestAnimationFrame(tick);
    </script>
    """
    components.html(html, height=300)


def stat_cards(items):
    """Hover-floating stat cards with count-up numbers. items = [(label, value, suffix, decimals)]"""
    cards = "".join(
        f"""<div class="c"><div class="v" data-v="{v}" data-s="{s}" data-d="{d}">0</div><div class="l">{lab}</div></div>"""
        for lab, v, s, d in items)
    html = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=DM+Sans:wght@400;500&display=swap');
      .row {{ display:grid; grid-template-columns: repeat({len(items)}, 1fr); gap:14px; font-family:'DM Sans',sans-serif; }}
      .c {{ background:{SURFACE}; border:1px solid {LINE}; border-radius:16px; padding:18px 20px;
            transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s ease, border-color .28s ease;
            animation: rise .6s both; }}
      .c:nth-child(2) {{ animation-delay:.08s }} .c:nth-child(3) {{ animation-delay:.16s }}
      .c:nth-child(4) {{ animation-delay:.24s }} .c:nth-child(5) {{ animation-delay:.32s }}
      .c:hover {{ transform: translateY(-6px); border-color:{BRASS}; box-shadow: 0 18px 40px rgba(0,0,0,.35), 0 0 0 1px rgba(201,164,92,.2); }}
      .v {{ font-family:'Fraunces',serif; font-size:34px; font-weight:600; color:{IVORY}; }}
      .l {{ color:{MUTED}; font-size:13px; margin-top:4px; }}
      @keyframes rise {{ from {{ opacity:0; transform:translateY(12px) }} to {{ opacity:1; transform:none }} }}
    </style>
    <div class="row">{cards}</div>
    <script>
      document.querySelectorAll('.v').forEach(el => {{
        const target = parseFloat(el.dataset.v), suf = el.dataset.s, dec = parseInt(el.dataset.d);
        const t0 = performance.now(), dur = 1200;
        function tick(t) {{
          const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
          el.textContent = (target * e).toLocaleString(undefined, {{minimumFractionDigits: dec, maximumFractionDigits: dec}}) + suf;
          if (k < 1) requestAnimationFrame(tick);
        }}
        requestAnimationFrame(tick);
      }});
    </script>
    """
    components.html(html, height=120)




def metric_rings(items):
    """Circular progress rings that draw themselves. items = [(label, value_0_to_1, display_text)]"""
    rings = ""
    for i, (lab, val, disp) in enumerate(items):
        dash = 2 * 3.14159 * 42
        rings += f"""
        <div class="ring" style="animation-delay:{i*0.08}s">
          <svg viewBox="0 0 100 100" width="118" height="118">
            <circle cx="50" cy="50" r="42" fill="none" stroke="{LINE}" stroke-width="8"/>
            <circle class="p" cx="50" cy="50" r="42" fill="none" stroke="{BRASS}" stroke-width="8"
                    stroke-linecap="round" stroke-dasharray="{dash:.1f}" stroke-dashoffset="{dash:.1f}"
                    data-off="{dash*(1-val):.1f}" transform="rotate(-90 50 50)"/>
            <text x="50" y="55" text-anchor="middle" fill="{IVORY}" font-size="19"
                  font-family="Fraunces, serif" font-weight="600">{disp}</text>
          </svg>
          <div class="rl">{lab}</div>
        </div>"""
    html = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=DM+Sans:wght@400;500&display=swap');
      .rings {{ display:grid; grid-template-columns: repeat({len(items)},1fr); gap:14px; font-family:'DM Sans',sans-serif; }}
      .ring {{ background:{SURFACE}; border:1px solid {LINE}; border-radius:18px; padding:16px 10px 12px; text-align:center;
               transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s ease, border-color .28s ease;
               animation: rise .6s both; }}
      .ring:hover {{ transform: translateY(-6px); border-color:{BRASS}; box-shadow: 0 18px 40px rgba(0,0,0,.35); }}
      .p {{ transition: stroke-dashoffset 1.3s cubic-bezier(.2,.8,.2,1); filter: drop-shadow(0 0 6px rgba(201,164,92,.5)); }}
      .rl {{ color:{MUTED}; font-size:13px; margin-top:6px; }}
      @keyframes rise {{ from {{ opacity:0; transform:translateY(12px) }} to {{ opacity:1; transform:none }} }}
    </style>
    <div class="rings">{rings}</div>
    <script>
      requestAnimationFrame(() => requestAnimationFrame(() =>
        document.querySelectorAll('.p').forEach(c => c.style.strokeDashoffset = c.dataset.off)));
    </script>
    """
    components.html(html, height=190)


def pipeline_flow(steps, active=None):
    """Horizontal step flow with a brass connector that draws across. steps = [(title, detail)]"""
    cells = ""
    for i, (t, d) in enumerate(steps):
        cls = "step ai" if i == active else "step"
        cells += f"""<div class="{cls}" style="animation-delay:{i*0.09}s">
                       <div class="n">{i+1}</div><div class="t">{t}</div><div class="d">{d}</div></div>"""
    html = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=DM+Sans:wght@400;500&display=swap');
      .flow {{ position:relative; display:grid; grid-template-columns: repeat({len(steps)},1fr); gap:10px; font-family:'DM Sans',sans-serif; padding-top:8px; }}
      .flow::before {{ content:""; position:absolute; top:34px; left:6%; right:6%; height:2px; background:{LINE}; }}
      .flow::after  {{ content:""; position:absolute; top:34px; left:6%; width:0; height:2px; background:{BRASS};
                       animation: draw 1.6s .3s cubic-bezier(.2,.8,.2,1) forwards; box-shadow:0 0 10px rgba(201,164,92,.7); }}
      @keyframes draw {{ to {{ width:88%; }} }}
      .step {{ position:relative; background:{SURFACE}; border:1px solid {LINE}; border-radius:16px; padding:14px 12px 14px; text-align:center;
               transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s ease, border-color .28s ease; animation: rise .6s both; }}
      .step:hover {{ transform: translateY(-6px); border-color:{BRASS}; box-shadow: 0 18px 40px rgba(0,0,0,.35); }}
      .step.ai {{ border-color:{BRASS}; background: linear-gradient(160deg, #22304A, {SURFACE}); box-shadow: 0 0 0 1px rgba(201,164,92,.25), 0 0 30px rgba(201,164,92,.15); }}
      .n {{ width:34px; height:34px; margin:0 auto 10px; border-radius:50%; background:{NAVY}; border:2px solid {BRASS}; color:{BRASS};
            font-family:'Fraunces',serif; font-weight:600; display:flex; align-items:center; justify-content:center; }}
      .step.ai .n {{ background:{BRASS}; color:{NAVY}; }}
      .t {{ color:{IVORY}; font-weight:600; font-size:14px; margin-bottom:4px; }}
      .d {{ color:{MUTED}; font-size:12px; line-height:1.4; }}
      @keyframes rise {{ from {{ opacity:0; transform:translateY(12px) }} to {{ opacity:1; transform:none }} }}
    </style>
    <div class="flow">{cells}</div>
    """
    components.html(html, height=200)


def info_cards(items, cols=3, height=210):
    """Grid of hover-floating cards with a title, a big line and a body. items = [(title, big, body)]"""
    cells = "".join(f"""<div class="ic" style="animation-delay:{i*0.08}s"><div class="it">{t}</div>
                        <div class="ib">{b}</div><div class="id">{d}</div></div>"""
                    for i, (t, b, d) in enumerate(items))
    html = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=DM+Sans:wght@400;500&display=swap');
      .g {{ display:grid; grid-template-columns: repeat({cols},1fr); gap:14px; font-family:'DM Sans',sans-serif; }}
      .ic {{ background:{SURFACE}; border:1px solid {LINE}; border-radius:18px; padding:18px 20px;
             transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s ease, border-color .28s ease; animation: rise .6s both; }}
      .ic:hover {{ transform: translateY(-6px); border-color:{BRASS}; box-shadow: 0 18px 40px rgba(0,0,0,.35); }}
      .it {{ color:{BRASS}; font-size:13px; font-weight:500; margin-bottom:6px; }}
      .ib {{ color:{IVORY}; font-family:'Fraunces',serif; font-size:22px; font-weight:600; line-height:1.15; margin-bottom:8px; }}
      .id {{ color:#B7C0CF; font-size:13.5px; line-height:1.5; }}
      .id code {{ background:{NAVY}; color:{BRASS}; padding:1px 6px; border-radius:6px; font-size:12.5px; }}
      @keyframes rise {{ from {{ opacity:0; transform:translateY(12px) }} to {{ opacity:1; transform:none }} }}
    </style>
    <div class="g">{cells}</div>
    """
    components.html(html, height=height)


# ============================================================== hero
st.markdown(f"""
<div class="hero">
  <h1>Will this booking be cancelled?</h1>
  <p>A Random Forest trained on 87,204 real bookings from a city hotel and a resort hotel
     reads 25 details of a reservation and answers with a probability, not just a yes or no.</p>
  <div class="pills">
    <span class="pill"><b>{meta['train_rows']:,}</b> bookings learned from</span>
    <span class="pill"><b>{DM['roc_auc']:.2f}</b> ROC-AUC on unseen data</span>
    <span class="pill"><b>{DM['recall']:.0%}</b> of real cancellations caught</span>
  </div>
</div>
""", unsafe_allow_html=True)

tab_predict, tab_batch, tab_perf, tab_eda, tab_about = st.tabs(
    ["✦  Predict", "▤  Batch predictions", "◔  Model performance", "◈  Data insights", "◎  About"])

# ============================================================== TAB 1 : predict
with tab_predict:
    with st.container(border=True):
        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            st.markdown('<div class="group">The stay</div>', unsafe_allow_html=True)
            hotel = st.selectbox("Hotel", ["City Hotel", "Resort Hotel"])
            lead_time = st.number_input("Lead time (days before arrival)", 0, 800, 60)
            month = st.selectbox("Arrival month", MONTHS, index=6)
            day = st.number_input("Arrival day of month", 1, 31, 15)
            week = st.number_input("Arrival week number", 1, 53, 28)
            weekend_nights = st.number_input("Weekend nights", 0, 20, 1)
            week_nights = st.number_input("Week nights", 0, 50, 2)
            room = st.selectbox("Reserved room type", list("ABCDEFGHL"))
            meal = st.selectbox("Meal plan", ["BB", "HB", "FB", "SC", "Undefined"])
        with c2:
            st.markdown('<div class="group">The guests</div>', unsafe_allow_html=True)
            adults = st.number_input("Adults", 0, 10, 2)
            children = st.number_input("Children", 0, 10, 0)
            babies = st.number_input("Babies", 0, 10, 0)
            country = st.selectbox("Country", TOP_COUNTRIES + ["Other"])
            customer = st.selectbox("Customer type", ["Transient", "Transient-Party", "Contract", "Group"])
            repeated = st.selectbox("Repeated guest?", ["No", "Yes"])
            prev_cancel = st.number_input("Previous cancellations", 0, 30, 0)
            prev_ok = st.number_input("Previous bookings not cancelled", 0, 100, 0)
        with c3:
            st.markdown('<div class="group">The booking</div>', unsafe_allow_html=True)
            market = st.selectbox("Market segment", ["Online TA", "Offline TA/TO", "Direct", "Groups",
                                                     "Corporate", "Complementary", "Aviation"])
            channel = st.selectbox("Distribution channel", ["TA/TO", "Direct", "Corporate", "GDS"])
            deposit = st.selectbox("Deposit type", ["No Deposit", "Non Refund", "Refundable"])
            adr = st.number_input("Average daily rate (price per night)", 0.0, 1000.0, 100.0, step=5.0)
            changes = st.number_input("Booking changes", 0, 20, 0)
            waiting = st.number_input("Days in waiting list", 0, 400, 0)
            parking = st.number_input("Car parking spaces", 0, 5, 0)
            requests = st.number_input("Special requests", 0, 5, 0)

        threshold = st.slider("Decision threshold: call it a cancellation when probability is at least",
                              0.1, 0.9, float(THRESH), 0.05)
        go_btn = st.button("Predict cancellation risk", type="primary", use_container_width=True)

    if go_btn:
        booking = {
            "lead_time": lead_time, "arrival_date_week_number": week,
            "arrival_date_day_of_month": day, "stays_in_weekend_nights": weekend_nights,
            "stays_in_week_nights": week_nights, "adults": adults, "children": children,
            "babies": babies, "is_repeated_guest": 1 if repeated == "Yes" else 0,
            "previous_cancellations": prev_cancel, "previous_bookings_not_canceled": prev_ok,
            "booking_changes": changes, "days_in_waiting_list": waiting, "adr": adr,
            "required_car_parking_spaces": parking, "total_of_special_requests": requests,
            "hotel": hotel, "arrival_date_month": month, "meal": meal, "country": country,
            "market_segment": market, "distribution_channel": channel,
            "reserved_room_type": room, "deposit_type": deposit, "customer_type": customer,
        }
        with st.spinner("Asking the model…"):
            time.sleep(0.5)
            prob = predict_one(booking)
        will_cancel = prob >= threshold

        st.write("")
        g, v = st.columns([1, 1.25], gap="large")
        with g:
            animated_gauge(prob, threshold)
        with v:
            if will_cancel:
                advice = ("Very high risk. Ask for a deposit, or plan to overbook this slot."
                          if prob >= 0.7 else
                          "Moderate risk. A confirmation call or reminder email is worth it.")
                st.markdown(f'<div class="verdict bad"><h2>Likely to be cancelled</h2>'
                            f'<p>The model puts this booking at {prob:.1%}, above your {threshold:.0%} '
                            f'threshold. {advice}</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="verdict good"><h2>Likely to be honoured</h2>'
                            f'<p>The model puts this booking at {prob:.1%}, below your {threshold:.0%} '
                            f'threshold. No action needed.</p></div>', unsafe_allow_html=True)

            scenarios = {
                "Half the lead time": {**booking, "lead_time": lead_time // 2},
                "One more special request": {**booking, "total_of_special_requests": min(requests + 1, 5)},
                "No deposit required": {**booking, "deposit_type": "No Deposit"},
                "Booked directly (not via agent)": {**booking, "market_segment": "Direct",
                                                    "distribution_channel": "Direct"},
            }
            rows = []
            for name, sc in scenarios.items():
                p2 = predict_one(sc)
                rows.append({"If instead…": name, "Probability": f"{p2:.1%}",
                             "Change": f"{(p2 - prob) * 100:+.1f} pts"})
            st.write("")
            st.markdown("**What would change the risk?** The model is re-run with one detail changed.")
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ============================================================== TAB 2 : batch
with tab_batch:
    sample = load_data()
    top_l, top_r = st.columns([1.4, 1], gap="large")
    with top_l:
        st.markdown("### Score a whole booking list at once")
        st.write("Drop in a CSV with the same column names as the Kaggle dataset. Every row gets a "
                 "cancellation probability, a yes/no flag, and you get the riskiest bookings first.")
        up = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    with top_r:
        info_cards([("Need a file to try?", "Sample of 500 bookings",
                     "Download this, then upload it on the left to see the whole flow.")],
                   cols=1, height=150)
        if sample is not None:
            st.download_button("Download sample CSV", sample.sample(500, random_state=1).to_csv(index=False).encode(),
                               "sample_bookings.csv", "text/csv", use_container_width=True)
        with st.expander("Required columns"):
            st.code(", ".join(NUM_FEATURES + CAT_FEATURES), language="text")

    if up is not None:
        data = pd.read_csv(up)
        missing = [c for c in NUM_FEATURES + CAT_FEATURES if c not in data.columns]
        if missing:
            st.error(f"These columns are missing: {', '.join(missing)}")
        else:
            with st.spinner("Scoring bookings…"):
                time.sleep(0.4)
                X = data[NUM_FEATURES + CAT_FEATURES].copy()
                X["children"] = X["children"].fillna(0)
                X["country"] = X["country"].fillna("Other")
                X["country"] = X["country"].where(X["country"].isin(TOP_COUNTRIES), "Other")
                probs = model.predict_proba(X)[:, 1]
            out = data.copy()
            out["cancel_probability"] = probs.round(3)
            out["predicted_cancel"] = (probs >= THRESH).astype(int)
            n_flag = int(out["predicted_cancel"].sum())
            high = int((probs >= 0.7).sum())

            st.write("")
            stat_cards([("bookings scored", len(out), "", 0),
                        ("flagged as likely cancellations", n_flag, "", 0),
                        ("very high risk (70%+)", high, "", 0),
                        ("flag rate", n_flag / len(out) * 100, "%", 1)])

            h_l, h_r = st.columns([1.3, 1], gap="large")
            with h_l:
                hist = go.Figure(go.Histogram(x=probs, nbinsx=40, marker_color=BRASS, opacity=0.9,
                                              hovertemplate="probability %{x}<br>%{y} bookings<extra></extra>"))
                hist.add_vrect(x0=THRESH, x1=1, fillcolor=CORAL, opacity=0.08, line_width=0)
                hist.add_vline(x=THRESH, line_color=IVORY, line_dash="dash",
                               annotation_text=f"threshold {THRESH}", annotation_font_color=IVORY)
                hist.update_layout(title=dict(text="Where the bookings fall", font=dict(family="Fraunces", size=17)),
                                   xaxis_title="cancellation probability", yaxis_title="bookings", bargap=0.05)
                st.plotly_chart(plotly_base(hist, 320), use_container_width=True, config={"displayModeBar": False})
            with h_r:
                donut = go.Figure(go.Pie(values=[len(out) - n_flag, n_flag], labels=["Likely honoured", "Likely cancelled"],
                                         hole=0.68, marker_colors=[SAGE, CORAL], textinfo="none", sort=False))
                donut.update_layout(title=dict(text="Verdict split", font=dict(family="Fraunces", size=17)),
                                    showlegend=True, legend=dict(orientation="h", y=-0.1),
                                    annotations=[dict(text=f"{n_flag/len(out):.0%}<br><span style='font-size:12px;color:{MUTED}'>flagged</span>",
                                                      x=0.5, y=0.5, showarrow=False,
                                                      font=dict(family="Fraunces", size=30, color=IVORY))])
                st.plotly_chart(plotly_base(donut, 320), use_container_width=True, config={"displayModeBar": False})

            st.markdown("#### Riskiest bookings first")
            show_cols = ["cancel_probability", "predicted_cancel", "hotel", "lead_time", "deposit_type",
                         "market_segment", "adr", "total_of_special_requests", "country"]
            show_cols = [c for c in show_cols if c in out.columns]
            ranked = out.sort_values("cancel_probability", ascending=False)[show_cols].head(200)
            st.dataframe(ranked, use_container_width=True, hide_index=True, height=380,
                         column_config={
                             "cancel_probability": st.column_config.ProgressColumn(
                                 "Cancellation probability", min_value=0, max_value=1, format="%.2f"),
                             "predicted_cancel": st.column_config.CheckboxColumn("Flagged"),
                         })
            st.download_button("Download all predictions (CSV)", out.to_csv(index=False).encode(),
                               "predictions.csv", "text/csv", type="primary", use_container_width=True)

# ============================================================== TAB 3 : performance
with tab_perf:
    st.markdown(f"### Deployed model: Random Forest, class-balanced, threshold {THRESH}")
    st.caption(f"Learned from {meta['train_rows']:,} bookings. Every number below is measured on "
               f"{meta['test_rows']:,} bookings the model never saw during training.")
    metric_rings([("Accuracy", DM["accuracy"], f"{DM['accuracy']:.0%}"),
                  ("Precision", DM["precision"], f"{DM['precision']:.2f}"),
                  ("Recall", DM["recall"], f"{DM['recall']:.2f}"),
                  ("F1 score", DM["f1"], f"{DM['f1']:.2f}"),
                  ("ROC-AUC", DM["roc_auc"], f"{DM['roc_auc']:.2f}")])

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        names = model.named_steps["prep"].get_feature_names_out()
        names = [n.replace("cat__", "").replace("remainder__", "").replace("_", " ") for n in names]
        imp = pd.Series(model.named_steps["rf"].feature_importances_, index=names)
        imp = imp.sort_values(ascending=False).head(12).sort_values()
        fig = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h",
                               marker=dict(color=imp.values, colorscale=[[0, LINE], [1, BRASS]], line=dict(width=0)),
                               hovertemplate="%{y}<br>importance %{x:.3f}<extra></extra>"))
        fig.update_layout(title=dict(text="What the model relies on most", font=dict(family="Fraunces", size=17)),
                          xaxis_title="importance")
        st.plotly_chart(plotly_base(fig, 440), use_container_width=True, config={"displayModeBar": False})
    with right:
        if meta.get("comparison"):
            comp = pd.DataFrame(meta["comparison"])
            radar_cols = [c for c in comp.columns if c != "Model"]
            palette = [MUTED, SAGE, BRASS, CORAL]
            radar = go.Figure()
            for i, (_, r) in enumerate(comp.iterrows()):
                radar.add_trace(go.Scatterpolar(r=[r[c] for c in radar_cols] + [r[radar_cols[0]]],
                                                theta=radar_cols + [radar_cols[0]], fill="toself",
                                                name=r["Model"], line=dict(color=palette[i % 4], width=2),
                                                opacity=0.7))
            radar.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                           radialaxis=dict(range=[0.4, 1], gridcolor=LINE, color=MUTED, tickfont=dict(size=10)),
                                           angularaxis=dict(gridcolor=LINE)),
                                legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
                                title=dict(text="Four models, side by side", font=dict(family="Fraunces", size=17)))
            st.plotly_chart(plotly_base(radar, 440), use_container_width=True, config={"displayModeBar": False})

    if meta.get("comparison"):
        st.markdown("#### Models compared in the notebook (full 245-feature versions)")
        comp = pd.DataFrame(meta["comparison"])
        cfg = {c: st.column_config.ProgressColumn(c, min_value=0, max_value=1, format="%.3f")
               for c in comp.columns if c != "Model"}
        st.dataframe(comp, hide_index=True, use_container_width=True, column_config=cfg)

    info_cards([
        ("Accuracy", "Right overall", "Share of all predictions that were correct."),
        ("Precision", "Right when it flags", "Of the bookings flagged as cancellations, how many really cancelled."),
        ("Recall", "Catches the real ones", "Of all real cancellations, how many the model found."),
        ("F1 score", "Balance", "The harmonic mean of precision and recall, one number for both."),
        ("ROC-AUC", "Separation power", "How well it ranks cancellers above non-cancellers. 1.0 is perfect, 0.5 is guessing."),
    ], cols=5, height=190)

# ============================================================== TAB 4 : EDA
with tab_eda:
    df = load_data()
    if df is None:
        st.info("Place hotel_bookings.csv next to app.py to enable this tab.")
    else:
        st.markdown("### What the data says before any model is trained")
        rate = df["is_canceled"].mean()
        stat_cards([("bookings in dataset", len(df), "", 0),
                    ("overall cancellation rate", rate * 100, "%", 1),
                    ("columns", df.shape[1], "", 0),
                    ("countries", df["country"].nunique(), "", 0)])

        info_cards([
            ("Finding 1", "Longer lead time, more cancellations",
             f"Cancelled bookings were made {df[df.is_canceled==1].lead_time.mean():.0f} days ahead on average, "
             f"versus {df[df.is_canceled==0].lead_time.mean():.0f} for honoured ones."),
            ("Finding 2", "City hotels cancel more",
             f"{df[df.hotel=='City Hotel'].is_canceled.mean():.0%} of city bookings cancel, "
             f"against {df[df.hotel=='Resort Hotel'].is_canceled.mean():.0%} at the resort."),
            ("Finding 3", "Special requests mean commitment",
             f"Guests with no requests cancel {df[df.total_of_special_requests==0].is_canceled.mean():.0%} of the time; "
             f"with two or more, only {df[df.total_of_special_requests>=2].is_canceled.mean():.0%}."),
        ], cols=3, height=175)

        l, r = st.columns(2, gap="large")
        with l:
            st.plotly_chart(bar(df.groupby("hotel")["is_canceled"].mean(),
                                "Cancellation rate by hotel type", fmt=".0%"),
                            use_container_width=True, config={"displayModeBar": False})
            st.plotly_chart(bar(df.groupby("deposit_type")["is_canceled"].mean(),
                                "Cancellation rate by deposit type", fmt=".0%"),
                            use_container_width=True, config={"displayModeBar": False})
        with r:
            monthly = df.groupby("arrival_date_month")["is_canceled"].mean().reindex(MONTHS)
            line = go.Figure(go.Scatter(x=monthly.index, y=monthly.values, mode="lines+markers",
                                        line=dict(color=BRASS, width=3, shape="spline"),
                                        marker=dict(size=8, color=NAVY, line=dict(color=BRASS, width=2)),
                                        fill="tozeroy", fillcolor="rgba(201,164,92,0.12)",
                                        hovertemplate="%{x}<br>%{y:.0%}<extra></extra>"))
            line.update_layout(title=dict(text="Cancellation rate across the year", font=dict(family="Fraunces", size=17)),
                               yaxis_tickformat=".0%")
            st.plotly_chart(plotly_base(line, 300), use_container_width=True, config={"displayModeBar": False})
            lt = df[df.lead_time <= 365]
            box = go.Figure()
            for val, name, col in [(0, "Not cancelled", SAGE), (1, "Cancelled", CORAL)]:
                box.add_trace(go.Box(y=lt[lt.is_canceled == val].lead_time, name=name, marker_color=col,
                                     boxmean=True, line=dict(width=2)))
            box.update_layout(title=dict(text="Lead time in days (up to a year)", font=dict(family="Fraunces", size=17)),
                              showlegend=False)
            st.plotly_chart(plotly_base(box, 300), use_container_width=True, config={"displayModeBar": False})

        seg = df.groupby("market_segment")["is_canceled"].agg(["mean", "size"]).sort_values("size", ascending=False)
        bub = go.Figure(go.Scatter(x=seg.index, y=seg["mean"], mode="markers+text",
                                   marker=dict(size=seg["size"] / seg["size"].max() * 70 + 12, color=seg["mean"],
                                               colorscale=[[0, SAGE], [0.5, BRASS], [1, CORAL]], line=dict(color=NAVY, width=2)),
                                   text=[f"{v:.0%}" for v in seg["mean"]], textposition="top center",
                                   textfont=dict(color=IVORY),
                                   hovertemplate="%{x}<br>%{customdata:,} bookings<br>%{y:.0%} cancel<extra></extra>",
                                   customdata=seg["size"]))
        bub.update_layout(title=dict(text="Market segments: bubble size is volume, colour is cancellation rate",
                                     font=dict(family="Fraunces", size=17)), yaxis_tickformat=".0%")
        st.plotly_chart(plotly_base(bub, 340), use_container_width=True, config={"displayModeBar": False})

# ============================================================== TAB 5 : about
with tab_about:
    st.markdown("### How this project works")
    st.write("Seven steps, in the order every machine-learning project follows. The highlighted one is where the AI lives.")
    pipeline_flow([
        ("Load dataset", "119,390 bookings, 32 columns, read from CSV"),
        ("Clean data", "Missing values, duplicates, zero-guest rows, leaked columns"),
        ("Preprocess", "Feature engineering and one-hot encoding"),
        ("Explore (EDA)", "Charts and correlations to understand the data"),
        ("Split", "80% seen for training, 20% unseen for testing"),
        ("Train model", "Random Forest learns the rules by itself"),
        ("Predict & evaluate", "Accuracy, precision, recall, F1, ROC-AUC on unseen data"),
    ], active=5)

    info_cards([
        ("Where the AI is", "It learns the rules, nobody writes them",
         f"<code>model.fit</code> builds 120 decision trees from {meta['train_rows']:,} past bookings and discovers "
         f"if-then patterns on its own. <code>model.predict_proba</code> applies those patterns to a booking it has never seen."),
        ("The dataset", "Hotel Booking Demand",
         "Published by Antonio, Almeida and Nunes in <i>Data in Brief</i> (2019) and hosted on Kaggle. "
         "Two real Portuguese hotels, 2015 to 2017, personal details removed."),
        ("The decision threshold", f"{THRESH}, not the default 0.5",
         "Chosen by testing thresholds from 0.3 to 0.7 and keeping the one with the best F1 score. "
         "The slider on the Predict tab lets you move it and watch the trade-off."),
    ], cols=3, height=230)

    info_cards([
        ("Models compared", "Random Forest vs Logistic Regression",
         "Random Forest won on every metric. Logistic Regression can only draw one straight boundary; a forest of trees captures interactions between features."),
        ("Built with", "Python, scikit-learn, pandas, Plotly, Streamlit",
         "The notebook trains and evaluates; this app loads the exported pipeline and serves predictions."),
        ("Author", "Muhammad Shahmir Khan",
         "Introduction to AI course project. Source code and the full notebook are on GitHub."),
    ], cols=3, height=210)