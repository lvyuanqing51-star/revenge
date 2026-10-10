import os
import json
import hashlib
import time
import base64
import difflib
import re
import random
import math
import urllib.request
from io import BytesIO
from itertools import combinations
from collections import defaultdict
import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI

DATA_FILE = "records.json"
CONFIG_FILE = "config.json"
TARGET_QIANQIU = "千秋种我一栗卿#52652"

st.set_page_config(
    page_title="海克斯内战",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- 专业级·黑金与醇厚酒红视觉系统 ----------------
st.markdown("""
<style>
:root, [data-theme="light"], .stApp { --primary-color: #881337 !important; }
.stApp {
    background: radial-gradient(circle at 10% 20%, #fff1f2 0%, #fff5f5 45%, #fed7aa 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
}
.app-header-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(254, 242, 242, 0.92) 100%);
    backdrop-filter: blur(14px); border: 1.5px solid #fecdd3; border-left: 6px solid #881337;
    border-radius: 16px; padding: 16px 26px; margin-bottom: 22px;
    box-shadow: 0 6px 24px rgba(114, 9, 44, 0.08);
}
.header-title {
    font-size: 1.70rem; font-weight: 900;
    background: linear-gradient(90deg, #881337 0%, #b91c1c 45%, #d97706 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px;
}
div[data-testid="stLinkButton"] a {
    border-radius: 14px !important; font-weight: 800 !important; font-size: 0.96rem !important;
    padding: 12px 18px !important; transition: all 0.28s ease !important; text-align: center;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #1e1b18 0%, #292524 50%, #1c1917 100%) !important;
    border: 2px solid #d97706 !important; color: #fef08a !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #0c1e33 0%, #1e293b 50%, #0f172a 100%) !important;
    border: 2px solid #38bdf8 !important; color: #e0f2fe !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #380718 0%, #4c0519 50%, #1f040d 100%) !important;
    border: 2px solid #f43f5e !important; color: #ffe4e6 !important;
}
div[data-baseweb="tab-list"] {
    gap: 12px !important; background: transparent !important;
    border-bottom: 2.5px solid #fecdd3 !important; margin-bottom: 22px !important;
}
div[data-baseweb="tab"] {
    background: #ffffff !important; border: 1.5px solid #fbcfe8 !important; border-bottom: none !important;
    border-radius: 12px 12px 0 0 !important; color: #881337 !important; font-weight: 800 !important;
    font-size: 1.06rem !important; padding: 11px 22px !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%) !important;
    color: #72092c !important; border-top: 3.5px solid #72092c !important;
}
.card-panel {
    background: #ffffff; border: 1.2px solid #fecdd3; border-radius: 14px;
    padding: 20px 24px; margin-bottom: 18px; box-shadow: 0 4px 16px rgba(114, 9, 44, 0.06);
}
.panel-header-title {
    font-size: 1.15rem; font-weight: 800; color: #72092c; margin-bottom: 14px;
    border-left: 4px solid #72092c; padding-left: 10px;
}
.metric-stat-box {
    background: #ffffff; border: 1.2px solid #fecdd3; border-radius: 14px;
    padding: 16px 18px; box-shadow: 0 3px 10px rgba(114, 9, 44, 0.05);
}
.metric-title { font-size: 0.85rem; font-weight: 700; color: #881337; margin-bottom: 4px; }
.metric-val-main { font-size: 1.45rem; font-weight: 900; color: #1e293b; }
.metric-badge {
    font-size: 0.80rem; font-weight: 800; padding: 3px 9px; border-radius: 6px;
    display: inline-block; margin-top: 5px;
}
.badge-pink { background: #ffe4e6; color: #9f1239; }
.badge-gold { background: #fef9c3; color: #b45309; }
.badge-blue { background: #e0f2fe; color: #0369a1; }
.badge-gray { background: #f1f5f9; color: #64748b; }
.badge-burgundy { background: #fce7f3; color: #72092c; border: 1px solid #f472b6
