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
                   page_icon="🏨", layout="wide", initial_sidebar_state="collapsed")

NAVY, SURFACE, LINE = "#0F1B2D", "#16263D", "#24364F"
BRASS, IVORY, MUTED = "#C9A45C", "#F3EEE3", "#8A96A8"
CORAL, SAGE = "#E36F5B", "#6FB58A"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,600;9..144,700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ============================================================ BASE */
* { box-sizing: border-box; }
html, body, [class*="css"], .stMarkdown, .stCaption, label, input, select, button, textarea {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}
h1, h2, h3, h4 { font-family: 'Fraunces', serif !important; font-weight: 600; letter-spacing: -0.02em; }
.block-container { padding-top: 1.5rem; padding-bottom: 4rem; max-width: 1240px; }

/* Custom scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0F1B2D; }
::-webkit-scrollbar-thumb { background: #24364F; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #C9A45C; }

/* ============================================================ BACKGROUND */
.stApp { background: #0F1B2D; overflow-x: hidden; }

/* Layered aurora with depth */
.stApp::before {
    content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
      radial-gradient(ellipse 50% 50% at 15% 25%, rgba(201,164,92,0.12), transparent 60%),
      radial-gradient(ellipse 45% 45% at 85% 20%, rgba(111,181,138,0.08), transparent 60%),
      radial-gradient(ellipse 55% 55% at 65% 90%, rgba(227,111,91,0.08), transparent 60%),
      radial-gradient(ellipse 40% 40% at 30% 75%, rgba(201,164,92,0.06), transparent 60%);
    animation: aurora 22s ease-in-out infinite alternate;
    filter: blur(24px);
}
.stApp::after {
    content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image: 
        linear-gradient(rgba(201,164,92,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(201,164,92,0.02) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse 80% 60% at 50% 40%, black 30%, transparent 100%);
}
@keyframes aurora {
    0%   { transform: translate(0, 0) rotate(0deg) scale(1); }
    33%  { transform: translate(3%, -2%) rotate(2deg) scale(1.04); }
    66%  { transform: translate(-2%, 3%) rotate(-1deg) scale(1.02); }
    100% { transform: translate(-3%, -2%) rotate(1deg) scale(1.03); }
}
.block-container { position: relative; z-index: 1; }

/* ============================================================ HERO */
.hero { padding: 24px 0 36px 0; margin-bottom: 32px; position: relative; }
.hero::after {
    content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, #24364F 20%, #C9A45C 50%, #24364F 80%, transparent);
    animation: lineGrow 1.2s .4s cubic-bezier(.2,.8,.2,1) both;
}
@keyframes lineGrow { from { transform: scaleX(0); } to { transform: scaleX(1); } }

.eyebrow { display: inline-flex; align-items: center; gap: 8px; color: #C9A45C; font-size: 0.82rem;
           font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 18px;
           animation: rise .7s cubic-bezier(.2,.8,.2,1) both; }
.eyebrow::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #C9A45C;
                   box-shadow: 0 0 12px #C9A45C; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .5; transform: scale(.8); } }

.hero h1 { font-size: clamp(2.4rem, 5.5vw, 4.2rem); line-height: 1.02; margin: 0 0 20px 0; color: #F3EEE3;
           font-weight: 600; animation: rise .8s .1s cubic-bezier(.2,.8,.2,1) both; }
.hero h1 .accent { background: linear-gradient(120deg, #C9A45C 0%, #E8CF8A 40%, #C9A45C 100%);
                   background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   background-clip: text; animation: shimmer 4s linear infinite; font-style: italic; font-weight: 400; }
@keyframes shimmer { to { background-position: 200% center; } }
.hero p { font-size: 1.12rem; color: #B7C0CF; max-width: 620px; margin: 0 0 26px 0; line-height: 1.65; font-weight: 300;
          animation: rise .8s .2s cubic-bezier(.2,.8,.2,1) both; }
.pills { display: flex; flex-wrap: wrap; gap: 10px; animation: rise .8s .3s cubic-bezier(.2,.8,.2,1) both; }
@keyframes rise { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }

.pill { display: inline-flex; align-items: baseline; gap: 6px; padding: 10px 18px; border-radius: 999px;
        background: rgba(22,38,61,0.7); border: 1px solid #24364F; color: #B7C0CF; font-size: 0.92rem;
        backdrop-filter: blur(10px); position: relative; overflow: hidden;
        transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, border-color .3s ease; }
.pill::before { content: ""; position: absolute; inset: 0; background: linear-gradient(120deg, transparent, rgba(201,164,92,0.15), transparent);
                transform: translateX(-100%); transition: transform .6s ease; }
.pill:hover { transform: translateY(-4px); border-color: #C9A45C; box-shadow: 0 14px 32px rgba(201,164,92,0.2), 0 0 0 1px rgba(201,164,92,0.3); }
.pill:hover::before { transform: translateX(100%); }
.pill b { color: #F3EEE3; font-weight: 600; font-family: 'Fraunces', serif; font-size: 1.15rem; }

/* ============================================================ TABS */
[data-testid="stTabs"] [role="tablist"], div[role="tablist"] {
    gap: 4px !important; padding: 5px !important; border-radius: 16px !important; border: 1px solid #24364F !important;
    background: rgba(22,38,61,0.6) !important; backdrop-filter: blur(14px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04) !important;
    width: fit-content; margin: 0 0 28px 0 !important;
}
button[role="tab"], [role="tab"] {
    padding: 11px 22px !important; border-radius: 12px !important; color: #8A96A8 !important;
    font-weight: 500 !important; font-size: 0.95rem !important; cursor: pointer; position: relative;
    background: transparent !important; border: none !important;
    transition: all .25s cubic-bezier(.2,.8,.2,1) !important;
}
button[role="tab"]:hover, [role="tab"]:hover {
    color: #F3EEE3 !important; background: rgba(201,164,92,0.08) !important; transform: translateY(-1px);
}
button[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #C9A45C 0%, #DBB86E 100%) !important; color: #0F1B2D !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(201,164,92,0.4), inset 0 1px 0 rgba(255,255,255,0.3) !important;
}
[role="tab"] p, [role="tab"] span, [role="tab"] div { color: inherit !important; margin: 0 !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
[role="tabpanel"] { animation: fadeUp .5s cubic-bezier(.2,.8,.2,1) both; padding-top: 4px; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }

/* ============================================================ CARDS & CONTAINERS */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 24px !important; border: 1px solid #24364F !important;
    background: linear-gradient(160deg, rgba(22,38,61,0.7), rgba(15,27,45,0.5)) !important;
    backdrop-filter: blur(12px); padding: 8px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.03) !important;
}
[data-testid="stMetric"], [data-testid="stExpander"] {
    background: rgba(22,38,61,0.6); border: 1px solid #24364F; border-radius: 18px; padding: 18px 22px;
    backdrop-filter: blur(8px);
    transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, border-color .3s ease;
}
[data-testid="stMetric"]:hover, [data-testid="stExpander"]:hover {
    transform: translateY(-5px); border-color: rgba(201,164,92,0.5);
    box-shadow: 0 20px 48px rgba(0,0,0,0.4), 0 0 0 1px rgba(201,164,92,0.15);
}
[data-testid="stMetricValue"] { font-family: 'Fraunces', serif !important; font-size: 2.1rem; color: #F3EEE3; }
[data-testid="stMetricLabel"] { color: #8A96A8; font-size: 0.85rem; letter-spacing: 0.04em; }
[data-testid="stExpander"] summary { font-weight: 500; color: #F3EEE3; }
[data-testid="stExpander"] summary:hover { color: #C9A45C; }

/* ============================================================ INPUTS */
.stSelectbox label, .stNumberInput label, .stSlider label, .stFileUploader label {
    color: #B7C0CF !important; font-size: 0.86rem !important; font-weight: 500 !important; letter-spacing: 0.01em;
}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, .stNumberInput div[data-baseweb="input"] {
    background: rgba(15,27,45,0.8) !important; border: 1px solid #24364F !important; border-radius: 12px !important;
    transition: all .25s ease !important; min-height: 44px;
}
[data-baseweb="select"] > div:hover, [data-baseweb="input"] > div:hover { border-color: rgba(201,164,92,0.6) !important; background: rgba(15,27,45,1) !important; }
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"] > div:focus-within {
    border-color: #C9A45C !important; box-shadow: 0 0 0 4px rgba(201,164,92,0.15), 0 4px 12px rgba(0,0,0,0.2) !important;
}
[data-baseweb="select"] input, [data-baseweb="input"] input { color: #F3EEE3 !important; }
[data-baseweb="popover"] [data-baseweb="menu"], [role="listbox"] {
    background: #16263D !important; border: 1px solid #24364F !important; border-radius: 12px !important;
    box-shadow: 0 16px 48px rgba(0,0,0,0.5) !important;
}
[role="option"] { transition: background .15s ease; }
[role="option"]:hover { background: rgba(201,164,92,0.12) !important; }
.stNumberInput button { background: transparent !important; border: none !important; color: #8A96A8 !important; transition: color .2s; }
.stNumberInput button:hover { color: #C9A45C !important; background: rgba(201,164,92,0.1) !important; }

.group { color: #C9A45C; font-family: 'Fraunces', serif; font-size: 1.28rem; font-weight: 600; margin: 4px 0 14px 0;
         padding-bottom: 10px; border-bottom: 1px solid #24364F; display: flex; align-items: center; gap: 10px; }
.group::before { content: ""; width: 4px; height: 20px; background: linear-gradient(180deg, #C9A45C, transparent); border-radius: 2px; }

/* Slider */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: #C9A45C !important; border: 3px solid #0F1B2D !important; box-shadow: 0 0 0 2px #C9A45C, 0 4px 12px rgba(201,164,92,0.4) !important;
    width: 22px !important; height: 22px !important; transition: transform .2s ease;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]:hover { transform: scale(1.2); }
[data-testid="stSlider"] [data-baseweb="slider"] > div > div { background: linear-gradient(90deg, #6FB58A, #C9A45C, #E36F5B) !important; }
[data-testid="stSlider"] [data-testid="stTickBar"] { color: #8A96A8; }

/* ============================================================ BUTTONS */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #C9A45C 0%, #E0C27A 50%, #C9A45C 100%);
    background-size: 200% auto; color: #0F1B2D; border: none; border-radius: 16px;
    height: 3.6em; font-size: 1.08rem; font-weight: 600; letter-spacing: 0.02em; position: relative; overflow: hidden;
    transition: transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, background-position .6s ease;
    box-shadow: 0 10px 30px rgba(201,164,92,0.3), inset 0 1px 0 rgba(255,255,255,0.3);
}
.stButton > button[kind="primary"]::after {
    content: ""; position: absolute; inset: 0;
    background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.3) 50%, transparent 70%);
    transform: translateX(-100%); transition: transform .8s ease;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.01); background-position: right center; color: #0F1B2D;
    box-shadow: 0 20px 50px rgba(201,164,92,0.5), inset 0 1px 0 rgba(255,255,255,0.3);
}
.stButton > button[kind="primary"]:hover::after { transform: translateX(100%); }
.stButton > button[kind="primary"]:active { transform: translateY(-1px) scale(.99); }
.stButton > button[kind="primary"] p { color: #0F1B2D !important; font-weight: 600 !important; }

.stDownloadButton > button {
    border-radius: 14px; border: 1px solid #24364F; background: rgba(22,38,61,0.6); color: #F3EEE3;
    transition: all .25s cubic-bezier(.2,.8,.2,1); backdrop-filter: blur(8px);
}
.stDownloadButton > button:hover { transform: translateY(-2px); border-color: #C9A45C; box-shadow: 0 12px 28px rgba(201,164,92,0.25); color: #C9A45C; }
.stDownloadButton > button[kind="primary"] { background: linear-gradient(135deg, #C9A45C, #E0C27A); color: #0F1B2D; border: none; }
.stDownloadButton > button[kind="primary"]:hover { color: #0F1B2D; }

/* ============================================================ VERDICT */
.verdict { border-radius: 22px; padding: 28px 32px; border: 1px solid; position: relative; overflow: hidden;
           animation: verdictIn .7s .2s cubic-bezier(.2,.8,.2,1) both;
           transition: transform .3s ease, box-shadow .3s ease; }
.verdict::before { content: ""; position: absolute; top: -50%; right: -20%; width: 200px; height: 200px; border-radius: 50%;
                   filter: blur(60px); opacity: .4; }
.verdict:hover { transform: translateY(-4px); box-shadow: 0 24px 56px rgba(0,0,0,0.4); }
.verdict .tag { display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 600;
                letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 14px; }
.verdict h2 { margin: 0 0 12px 0; font-size: 1.9rem; line-height: 1.15; position: relative; }
.verdict p  { margin: 0; color: #D6DCE6; line-height: 1.6; font-size: 1rem; position: relative; }
.verdict.bad  { background: linear-gradient(160deg, rgba(46,27,24,0.95), rgba(34,23,26,0.95)); border-color: rgba(227,111,91,0.6); }
.verdict.bad::before { background: #E36F5B; }
.verdict.bad .tag { background: rgba(227,111,91,0.2); color: #F0A08F; }
.verdict.bad h2  { color: #F0A08F; }
.verdict.good { background: linear-gradient(160deg, rgba(21,44,35,0.95), rgba(20,33,30,0.95)); border-color: rgba(111,181,138,0.6); }
.verdict.good::before { background: #6FB58A; }
.verdict.good .tag { background: rgba(111,181,138,0.2); color: #9FD4B2; }
.verdict.good h2 { color: #9FD4B2; }
@keyframes verdictIn { from { opacity: 0; transform: translateY(24px) scale(.97); } to { opacity: 1; transform: none; } }

/* ============================================================ MISC */
[data-testid="stFileUploader"] { border: 2px dashed #24364F; border-radius: 20px; padding: 14px; background: rgba(22,38,61,0.3);
    transition: all .3s ease; }
[data-testid="stFileUploader"]:hover { border-color: #C9A45C; background: rgba(201,164,92,0.05); transform: scale(1.005); }
[data-testid="stFileUploader"] section { background: transparent !important; }
[data-testid="stFileUploader"] button { border-radius: 10px !important; border-color: #24364F !important; transition: all .2s; }
[data-testid="stFileUploader"] button:hover { border-color: #C9A45C !important; color: #C9A45C !important; }
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; border: 1px solid #24364F; }
.stSpinner > div { border-top-color: #C9A45C !important; }
[data-testid="stCaptionContainer"] { color: #8A96A8 !important; }
.stAlert { border-radius: 14px !important; }
hr { border-color: #24364F !important; }

/* ============================================================ CUSTOM COMPONENTS */
.sc-row { display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 16px; margin: 8px 0 20px; }
.sc { background: linear-gradient(160deg, rgba(22,38,61,0.8), rgba(22,38,61,0.5)); border: 1px solid #24364F; border-radius: 20px;
      padding: 22px 24px; animation: rise .6s both; position: relative; overflow: hidden; backdrop-filter: blur(8px);
      transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, border-color .3s ease; }
.sc::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
              background: linear-gradient(90deg, transparent, #C9A45C, transparent); opacity: 0; transition: opacity .3s; }
.sc:hover { transform: translateY(-6px); border-color: rgba(201,164,92,0.5); box-shadow: 0 20px 48px rgba(0,0,0,0.4), 0 0 0 1px rgba(201,164,92,0.2); }
.sc:hover::before { opacity: 1; }
.sv { font-family: 'Fraunces', serif; font-size: 38px; font-weight: 600; color: #F3EEE3; line-height: 1.05; letter-spacing: -0.02em; }
.sl { color: #8A96A8; font-size: 13px; margin-top: 6px; font-weight: 500; letter-spacing: 0.02em; }

.rings { display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 16px; margin: 8px 0 24px; }
.ring { background: linear-gradient(160deg, rgba(22,38,61,0.8), rgba(22,38,61,0.5)); border: 1px solid #24364F; border-radius: 22px;
        padding: 20px 12px 16px; text-align: center; animation: rise .6s both; backdrop-filter: blur(8px);
        transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, border-color .3s ease; }
.ring:hover { transform: translateY(-6px) scale(1.02); border-color: rgba(201,164,92,0.5); box-shadow: 0 20px 48px rgba(0,0,0,0.4); }
.ring svg { width: 124px; height: 124px; }
.rp { animation: ringdraw 1.5s cubic-bezier(.2,.8,.2,1) forwards; filter: drop-shadow(0 0 8px rgba(201,164,92,.6)); }
@keyframes ringdraw { to { stroke-dashoffset: var(--off); } }
.rl { color: #8A96A8; font-size: 13px; margin-top: 8px; font-weight: 500; letter-spacing: 0.02em; }

.flow { position: relative; display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 12px; padding-top: 8px; margin-bottom: 24px; }
.flow::before { content: ""; position: absolute; top: 36px; left: 6%; right: 6%; height: 2px; background: #24364F; }
.flow::after  { content: ""; position: absolute; top: 36px; left: 6%; width: 0; height: 2px; background: linear-gradient(90deg, #C9A45C, #E0C27A);
                animation: draw 1.8s .3s cubic-bezier(.2,.8,.2,1) forwards; box-shadow: 0 0 12px rgba(201,164,92,.8); }
@keyframes draw { to { width: 88%; } }
.step { position: relative; background: linear-gradient(160deg, rgba(22,38,61,0.8), rgba(22,38,61,0.5)); border: 1px solid #24364F;
        border-radius: 18px; padding: 16px 12px; text-align: center; animation: rise .6s both; backdrop-filter: blur(8px);
        transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, border-color .3s ease; }
.step:hover { transform: translateY(-6px); border-color: rgba(201,164,92,0.5); box-shadow: 0 20px 48px rgba(0,0,0,0.4); }
.step.ai { border-color: #C9A45C; background: linear-gradient(160deg, rgba(34,48,74,0.95), rgba(22,38,61,0.9));
           box-shadow: 0 0 0 1px rgba(201,164,92,.3), 0 0 40px rgba(201,164,92,.2); }
.step .n { width: 38px; height: 38px; margin: 0 auto 12px; border-radius: 50%; background: #0F1B2D; border: 2px solid #C9A45C; color: #C9A45C;
           font-family: 'Fraunces', serif; font-weight: 600; font-size: 15px; display: flex; align-items: center; justify-content: center;
           transition: transform .3s ease; }
.step:hover .n { transform: scale(1.1) rotate(5deg); }
.step.ai .n { background: linear-gradient(135deg, #C9A45C, #E0C27A); color: #0F1B2D; box-shadow: 0 4px 16px rgba(201,164,92,0.5); }
.step .t { color: #F3EEE3; font-weight: 600; font-size: 14px; margin-bottom: 6px; }
.step .d { color: #8A96A8; font-size: 12px; line-height: 1.45; }

.ig { display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 16px; margin: 8px 0 20px; }
.ic { background: linear-gradient(160deg, rgba(22,38,61,0.8), rgba(22,38,61,0.5)); border: 1px solid #24364F; border-radius: 20px;
      padding: 22px 24px; animation: rise .6s both; position: relative; overflow: hidden; backdrop-filter: blur(8px);
      transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease, border-color .3s ease; }
.ic::after { content: ""; position: absolute; bottom: -40px; right: -40px; width: 100px; height: 100px; border-radius: 50%;
             background: rgba(201,164,92,0.06); filter: blur(30px); transition: all .4s ease; }
.ic:hover { transform: translateY(-6px); border-color: rgba(201,164,92,0.5); box-shadow: 0 20px 48px rgba(0,0,0,0.4); }
.ic:hover::after { background: rgba(201,164,92,0.15); transform: scale(1.5); }
.it { color: #C9A45C; font-size: 12px; font-weight: 600; margin-bottom: 8px; letter-spacing: 0.1em; text-transform: uppercase; }
.ib { color: #F3EEE3; font-family: 'Fraunces', serif; font-size: 22px; font-weight: 600; line-height: 1.2; margin-bottom: 10px; }
.id { color: #B7C0CF; font-size: 14px; line-height: 1.55; }
.id code { background: rgba(15,27,45,0.9); color: #C9A45C; padding: 2px 8px; border-radius: 6px; font-size: 12.5px; font-family: 'DM Sans', monospace; }

.section-title { font-family: 'Fraunces', serif; font-size: 1.7rem; font-weight: 600; color: #F3EEE3; margin: 0 0 6px 0; }
.section-sub { color: #8A96A8; font-size: 0.98rem; margin: 0 0 22px 0; line-height: 1.55; }

/* ============================================================ RESPONSIVE */
@media (max-width: 768px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }
    .hero { padding: 12px 0 24px 0; margin-bottom: 20px; }
    .hero p { font-size: 1rem; }
    .pill { padding: 8px 14px; font-size: 0.85rem; }
    .pill b { font-size: 1rem; }
    div[role="tablist"] { width: 100% !important; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; border-radius: 14px !important; }
    div[role="tablist"]::-webkit-scrollbar { display: none; }
    button[role="tab"], [role="tab"] { padding: 9px 14px !important; font-size: 0.85rem !important; white-space: nowrap; flex-shrink: 0; }
    .sc-row { grid-template-columns: repeat(2, 1fr); gap: 10px; } .sv { font-size: 26px; } .sc { padding: 16px; }
    .rings { grid-template-columns: repeat(3, 1fr); gap: 10px; } .ring svg { width: 84px; height: 84px; } .ring { padding: 14px 8px 12px; }
    .flow { grid-template-columns: repeat(2, 1fr); } .flow::before, .flow::after { display: none; }
    .ig { grid-template-columns: 1fr; gap: 10px; }
    .verdict { padding: 20px 22px; } .verdict h2 { font-size: 1.5rem; }
    .section-title { font-size: 1.4rem; }
    .stApp::before { animation: none; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px !important; padding: 4px !important; }
}
@media (max-width: 480px) {
    .rings { grid-template-columns: repeat(2, 1fr); }
    .sc-row { grid-template-columns: 1fr 1fr; }
}

/* ============================================================ NO SIDEWAYS SCROLL */
html, body { overflow-x: hidden !important; max-width: 100vw; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container { overflow-x: hidden !important; max-width: 100vw; }
[data-testid="stAppViewContainer"] > section { overflow-x: hidden !important; }
.hero, .sc-row, .rings, .flow, .ig, .verdict, .pills { max-width: 100%; }
iframe, [data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container { max-width: 100% !important; }

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
PLOT_CFG = {"displayModeBar": False, "responsive": True}


def plotly_base(fig, height=300):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=IVORY, size=12), height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        xaxis=dict(gridcolor="rgba(36,54,79,0.5)", zerolinecolor=LINE, showline=False),
        yaxis=dict(gridcolor="rgba(36,54,79,0.5)", zerolinecolor=LINE, showline=False),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BRASS, font=dict(color=IVORY, family="DM Sans")),
        transition=dict(duration=500, easing="cubic-in-out"),
        title_font=dict(family="Fraunces", size=17, color=IVORY),
    )
    return fig


def bar(series, title, color=BRASS, horizontal=False, height=300, fmt=None):
    x, y = (series.values, series.index) if horizontal else (series.index, series.values)
    fig = go.Figure(go.Bar(
        x=x, y=y, orientation="h" if horizontal else "v",
        marker=dict(color=color, line=dict(width=0), cornerradius=6),
        hovertemplate="%{x}<br>%{y}<extra></extra>"))
    fig.update_layout(title=dict(text=title))
    if fmt:
        fig.update_layout(**({"xaxis_tickformat": fmt} if horizontal else {"yaxis_tickformat": fmt}))
    return plotly_base(fig, height)


def predict_one(d):
    row = pd.DataFrame([d])[NUM_FEATURES + CAT_FEATURES]
    return float(model.predict_proba(row)[0, 1])   # the AI decides here


def animated_gauge(prob, threshold):
    """SVG gauge: arc sweeps in, number counts up, threshold needle marked."""
    pct = round(prob * 100, 1)
    color = CORAL if prob >= threshold else SAGE
    html = f"""
    <div style="font-family:'DM Sans',sans-serif;color:{IVORY};text-align:center;padding:8px 0;">
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=DM+Sans:wght@400;500;600&display=swap');
      .arc {{ transition: stroke-dashoffset 1.6s cubic-bezier(.2,.8,.2,1); }}
      .num {{ font-family:'Fraunces',serif; font-size:68px; font-weight:600; line-height:1; letter-spacing:-0.02em;
              text-shadow: 0 0 40px {color}66; }}
      .lab {{ color:{MUTED}; font-size:13px; margin-top:8px; letter-spacing:0.04em; font-weight:500; }}
      .needle {{ transition: transform 1.2s cubic-bezier(.2,.8,.2,1); transform-origin: 150px 150px; }}
    </style>
    <svg viewBox="0 0 300 180" width="100%" style="max-width:380px;overflow:visible">
      <defs>
        <linearGradient id="g" x1="0" x2="1">
          <stop offset="0" stop-color="{SAGE}"/><stop offset="{threshold}" stop-color="{BRASS}"/><stop offset="1" stop-color="{CORAL}"/>
        </linearGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <path d="M30 150 A120 120 0 0 1 270 150" fill="none" stroke="{LINE}" stroke-width="20" stroke-linecap="round" opacity="0.6"/>
      <path id="arc" class="arc" d="M30 150 A120 120 0 0 1 270 150" fill="none" stroke="url(#g)"
            stroke-width="20" stroke-linecap="round" filter="url(#glow)"
            stroke-dasharray="377" stroke-dashoffset="377"/>
      <g id="needle" class="needle" style="transform: rotate(-90deg)">
        <line x1="150" y1="26" x2="150" y2="48" stroke="{IVORY}" stroke-width="3.5" stroke-linecap="round" opacity="0.9"/>
        <circle cx="150" cy="26" r="4" fill="{IVORY}"/>
      </g>
      <text x="30" y="176" fill="{MUTED}" font-size="12" text-anchor="middle" font-family="DM Sans">0%</text>
      <text x="270" y="176" fill="{MUTED}" font-size="12" text-anchor="middle" font-family="DM Sans">100%</text>
    </svg>
    <div class="num" id="num" style="color:{color}">0%</div>
    <div class="lab">PROBABILITY OF CANCELLATION · THRESHOLD {int(threshold*100)}%</div>
    </div>
    <script>
      const target = {pct};
      const arc = document.getElementById('arc');
      const needle = document.getElementById('needle');
      requestAnimationFrame(() => {{
        arc.style.strokeDashoffset = 377 - 377 * target / 100;
        needle.style.transform = 'rotate(' + (-90 + 180 * {threshold}) + 'deg)';
      }});
      const el = document.getElementById('num');
      const t0 = performance.now(), dur = 1600;
      function tick(t) {{
        const k = Math.min(1, (t - t0) / dur);
        const e = 1 - Math.pow(1 - k, 4);
        el.textContent = (target * e).toFixed(1) + '%';
        if (k < 1) requestAnimationFrame(tick);
      }}
      requestAnimationFrame(tick);
    </script>
    """
    components.html(html, height=310)


def stat_cards(items):
    """Hover-floating stat cards. items = [(label, value, suffix, decimals)]"""
    cards = ""
    for i, (lab, v, s, d) in enumerate(items):
        txt = f"{v:,.{d}f}{s}"
        cards += f'<div class="sc" style="animation-delay:{i*0.08}s"><div class="sv">{txt}</div><div class="sl">{lab}</div></div>'
    st.markdown(f'<div class="sc-row" style="--n:{len(items)}">{cards}</div>', unsafe_allow_html=True)


def metric_rings(items):
    """Circular progress rings that draw themselves. items = [(label, value_0_to_1, display_text)]"""
    dash = 2 * 3.14159 * 42
    rings = ""
    for i, (lab, val, disp) in enumerate(items):
        rings += f"""
        <div class="ring" style="animation-delay:{i*0.08}s">
          <svg viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="{LINE}" stroke-width="8" opacity="0.6"/>
            <circle class="rp" cx="50" cy="50" r="42" fill="none" stroke="{BRASS}" stroke-width="8"
                    stroke-linecap="round" stroke-dasharray="{dash:.1f}"
                    style="--off:{dash*(1-val):.1f}; stroke-dashoffset:{dash:.1f}; animation-delay:{0.2+i*0.12}s"
                    transform="rotate(-90 50 50)"/>
            <text x="50" y="57" text-anchor="middle" fill="{IVORY}" font-size="19"
                  font-family="Fraunces, serif" font-weight="600">{disp}</text>
          </svg>
          <div class="rl">{lab}</div>
        </div>"""
    st.markdown(f'<div class="rings" style="--n:{len(items)}">{rings}</div>', unsafe_allow_html=True)


def pipeline_flow(steps, active=None):
    """Step flow with a brass connector that draws across. steps = [(title, detail)]"""
    cells = ""
    for i, (t, d) in enumerate(steps):
        cls = "step ai" if i == active else "step"
        cells += f'<div class="{cls}" style="animation-delay:{i*0.09}s"><div class="n">{i+1}</div><div class="t">{t}</div><div class="d">{d}</div></div>'
    st.markdown(f'<div class="flow" style="--n:{len(steps)}">{cells}</div>', unsafe_allow_html=True)


def info_cards(items, cols=3):
    """Grid of hover-floating cards. items = [(title, big, body)]"""
    cells = "".join(f'<div class="ic" style="animation-delay:{i*0.08}s"><div class="it">{t}</div>'
                    f'<div class="ib">{b}</div><div class="id">{d}</div></div>'
                    for i, (t, b, d) in enumerate(items))
    st.markdown(f'<div class="ig" style="--n:{cols}">{cells}</div>', unsafe_allow_html=True)


def section(title, sub=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


# ============================================================== hero
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">Machine learning · Random Forest · Live model</div>
  <h1>Will this booking<br>be <span class="accent">cancelled?</span></h1>
  <p>A Random Forest trained on {meta['train_rows']:,} real bookings from a city hotel and a resort hotel
     reads 25 details of a reservation and answers with a probability, not just a yes or no.</p>
  <div class="pills">
    <span class="pill"><b>{meta['train_rows']:,}</b> bookings learned from</span>
    <span class="pill"><b>{DM['roc_auc']:.2f}</b> ROC-AUC on unseen data</span>
    <span class="pill"><b>{DM['recall']:.0%}</b> of real cancellations caught</span>
  </div>
</div>
""", unsafe_allow_html=True)

tab_predict, tab_batch, tab_perf, tab_eda, tab_about = st.tabs(
    ["✦  Predict", "▤  Batch", "◔  Performance", "◈  Insights", "◎  About"])

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

        st.write("")
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
                level = "Very high risk" if prob >= 0.7 else "Moderate risk"
                advice = ("Ask for a deposit, or plan to overbook this slot."
                          if prob >= 0.7 else
                          "A confirmation call or reminder email is worth it.")
                st.markdown(f'<div class="verdict bad"><span class="tag">{level}</span>'
                            f'<h2>Likely to be cancelled</h2>'
                            f'<p>The model puts this booking at <b>{prob:.1%}</b>, above your {threshold:.0%} '
                            f'threshold. {advice}</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="verdict good"><span class="tag">Low risk</span>'
                            f'<h2>Likely to be honoured</h2>'
                            f'<p>The model puts this booking at <b>{prob:.1%}</b>, below your {threshold:.0%} '
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
                rows.append({"If instead…": name, "Probability": p2, "Change": (p2 - prob) * 100})
            st.write("")
            st.markdown("**What would change the risk?** The model is re-run with one detail changed.")
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={
                             "Probability": st.column_config.ProgressColumn("Probability", min_value=0, max_value=1, format="%.1f%%"),
                             "Change": st.column_config.NumberColumn("Change (pts)", format="%+.1f"),
                         })

# ============================================================== TAB 2 : batch
with tab_batch:
    sample = load_data()
    top_l, top_r = st.columns([1.4, 1], gap="large")
    with top_l:
        section("Score a whole booking list at once",
                "Drop in a CSV with the same column names as the Kaggle dataset. Every row gets a "
                "cancellation probability, a yes/no flag, and you get the riskiest bookings first.")
        up = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    with top_r:
        info_cards([("Need a file to try?", "Sample of 500 bookings",
                     "Download this, then upload it on the left to see the whole flow.")], cols=1)
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
                hist = go.Figure(go.Histogram(x=probs, nbinsx=40, marker=dict(color=BRASS, line=dict(width=0)), opacity=0.9,
                                              hovertemplate="probability %{x}<br>%{y} bookings<extra></extra>"))
                hist.add_vrect(x0=THRESH, x1=1, fillcolor=CORAL, opacity=0.08, line_width=0)
                hist.add_vline(x=THRESH, line_color=IVORY, line_dash="dash",
                               annotation_text=f"threshold {THRESH}", annotation_font_color=IVORY)
                hist.update_layout(title=dict(text="Where the bookings fall"),
                                   xaxis_title="cancellation probability", yaxis_title="bookings", bargap=0.05)
                st.plotly_chart(plotly_base(hist, 320), use_container_width=True, config=PLOT_CFG)
            with h_r:
                donut = go.Figure(go.Pie(values=[len(out) - n_flag, n_flag], labels=["Likely honoured", "Likely cancelled"],
                                         hole=0.7, marker=dict(colors=[SAGE, CORAL], line=dict(color=NAVY, width=3)),
                                         textinfo="none", sort=False))
                donut.update_layout(title=dict(text="Verdict split"),
                                    showlegend=True, legend=dict(orientation="h", y=-0.1),
                                    annotations=[dict(text=f"{n_flag/len(out):.0%}<br><span style='font-size:12px;color:{MUTED}'>flagged</span>",
                                                      x=0.5, y=0.5, showarrow=False,
                                                      font=dict(family="Fraunces", size=32, color=IVORY))])
                st.plotly_chart(plotly_base(donut, 320), use_container_width=True, config=PLOT_CFG)

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
    section(f"Deployed model: Random Forest, class-balanced, threshold {THRESH}",
            f"Learned from {meta['train_rows']:,} bookings. Every number below is measured on "
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
                               marker=dict(color=imp.values, colorscale=[[0, LINE], [1, BRASS]], line=dict(width=0), cornerradius=6),
                               hovertemplate="%{y}<br>importance %{x:.3f}<extra></extra>"))
        fig.update_layout(title=dict(text="What the model relies on most"), xaxis_title="importance")
        st.plotly_chart(plotly_base(fig, 440), use_container_width=True, config=PLOT_CFG)
    with right:
        if meta.get("comparison"):
            comp = pd.DataFrame(meta["comparison"])
            radar_cols = [c for c in comp.columns if c != "Model"]
            palette = [MUTED, SAGE, BRASS, CORAL]
            radar = go.Figure()
            for i, (_, r) in enumerate(comp.iterrows()):
                radar.add_trace(go.Scatterpolar(r=[r[c] for c in radar_cols] + [r[radar_cols[0]]],
                                                theta=radar_cols + [radar_cols[0]], fill="toself",
                                                name=r["Model"], line=dict(color=palette[i % 4], width=2.5),
                                                opacity=0.75))
            radar.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                           radialaxis=dict(range=[0.4, 1], gridcolor=LINE, color=MUTED, tickfont=dict(size=10)),
                                           angularaxis=dict(gridcolor=LINE, tickfont=dict(size=11))),
                                legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
                                title=dict(text="Models, side by side"))
            st.plotly_chart(plotly_base(radar, 440), use_container_width=True, config=PLOT_CFG)

    if meta.get("comparison"):
        st.markdown("#### Models compared in the notebook (full 245-feature versions)")
        comp = pd.DataFrame(meta["comparison"])
        cfg = {c: st.column_config.ProgressColumn(c, min_value=0, max_value=1, format="%.3f")
               for c in comp.columns if c != "Model"}
        st.dataframe(comp, hide_index=True, use_container_width=True, column_config=cfg)

    st.write("")
    info_cards([
        ("Accuracy", "Right overall", "Share of all predictions that were correct."),
        ("Precision", "Right when it flags", "Of the bookings flagged as cancellations, how many really cancelled."),
        ("Recall", "Catches the real ones", "Of all real cancellations, how many the model found."),
        ("F1 score", "Balance", "The harmonic mean of precision and recall, one number for both."),
        ("ROC-AUC", "Separation power", "How well it ranks cancellers above non-cancellers. 1.0 is perfect, 0.5 is guessing."),
    ], cols=5)

# ============================================================== TAB 4 : EDA
with tab_eda:
    df = load_data()
    if df is None:
        st.info("Place hotel_bookings.csv next to app.py to enable this tab.")
    else:
        section("What the data says before any model is trained")
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
        ], cols=3)
        l, r = st.columns(2, gap="large")
        with l:
            st.plotly_chart(bar(df.groupby("hotel")["is_canceled"].mean(),
                                "Cancellation rate by hotel type", fmt=".0%"),
                            use_container_width=True, config=PLOT_CFG)
            st.plotly_chart(bar(df.groupby("deposit_type")["is_canceled"].mean(),
                                "Cancellation rate by deposit type", fmt=".0%"),
                            use_container_width=True, config=PLOT_CFG)
        with r:
            monthly = df.groupby("arrival_date_month")["is_canceled"].mean().reindex(MONTHS)
            line = go.Figure(go.Scatter(x=monthly.index, y=monthly.values, mode="lines+markers",
                                        line=dict(color=BRASS, width=3, shape="spline"),
                                        marker=dict(size=9, color=NAVY, line=dict(color=BRASS, width=2)),
                                        fill="tozeroy", fillcolor="rgba(201,164,92,0.12)",
                                        hovertemplate="%{x}<br>%{y:.0%}<extra></extra>"))
            line.update_layout(title=dict(text="Cancellation rate across the year"), yaxis_tickformat=".0%")
            st.plotly_chart(plotly_base(line, 300), use_container_width=True, config=PLOT_CFG)
            lt = df[df.lead_time <= 365]
            box = go.Figure()
            for val, name, col in [(0, "Not cancelled", SAGE), (1, "Cancelled", CORAL)]:
                box.add_trace(go.Box(y=lt[lt.is_canceled == val].lead_time, name=name, marker_color=col,
                                     boxmean=True, line=dict(width=2)))
            box.update_layout(title=dict(text="Lead time in days (up to a year)"), showlegend=False)
            st.plotly_chart(plotly_base(box, 300), use_container_width=True, config=PLOT_CFG)

        seg = df.groupby("market_segment")["is_canceled"].agg(["mean", "size"]).sort_values("size", ascending=False)
        bub = go.Figure(go.Scatter(x=seg.index, y=seg["mean"], mode="markers+text",
                                   marker=dict(size=seg["size"] / seg["size"].max() * 70 + 12, color=seg["mean"],
                                               colorscale=[[0, SAGE], [0.5, BRASS], [1, CORAL]], line=dict(color=NAVY, width=2)),
                                   text=[f"{v:.0%}" for v in seg["mean"]], textposition="top center",
                                   textfont=dict(color=IVORY),
                                   hovertemplate="%{x}<br>%{customdata:,} bookings<br>%{y:.0%} cancel<extra></extra>",
                                   customdata=seg["size"]))
        bub.update_layout(title=dict(text="Market segments: bubble size is volume, colour is cancellation rate"),
                          yaxis_tickformat=".0%")
        st.plotly_chart(plotly_base(bub, 340), use_container_width=True, config=PLOT_CFG)

# ============================================================== TAB 5 : about
with tab_about:
    section("How this project works",
            "Seven steps, in the order every machine-learning project follows. The highlighted one is where the AI lives.")
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
    ], cols=3)
    info_cards([
        ("Models compared", "Random Forest vs Logistic Regression",
         "Random Forest won on every metric. Logistic Regression can only draw one straight boundary; a forest of trees captures interactions between features."),
        ("Built with", "Python, scikit-learn, pandas, Plotly, Streamlit",
         "The notebook trains and evaluates; this app loads the exported pipeline and serves predictions."),
        ("Author", "Muhammad Shahmir Khan",
         "Introduction to AI course project. Source code and the full notebook are on GitHub."),
    ], cols=3)