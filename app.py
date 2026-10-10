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
import urllib.error
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

# ---------------- 专业级·黑金与醇厚酒红 (Burgundy & Obsidian Gold) 视觉系统 ----------------
CSS_STYLES = """
<style>
:root, [data-theme="light"], .stApp {
    --primary-color: #881337 !important;
}

.stApp {
    background: radial-gradient(circle at 10% 20%, #fff1f2 0%, #fff5f5 45%, #fed7aa 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.app-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(254, 242, 242, 0.92) 100%);
    backdrop-filter: blur(14px);
    border: 1.5px solid #fecdd3;
    border-left: 6px solid #881337;
    border-radius: 16px;
    padding: 16px 26px;
    margin-bottom: 22px;
    box-shadow: 0 6px 24px rgba(114, 9, 44, 0.08);
}
.header-title {
    font-size: 1.70rem;
    font-weight: 900;
    background: linear-gradient(90deg, #881337 0%, #b91c1c 45%, #d97706 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 10px;
    letter-spacing: 0.5px;
}

div[data-testid="stLinkButton"] a {
    border-radius: 14px !important;
    font-weight: 800 !important;
    font-size: 0.96rem !important;
    padding: 12px 18px !important;
    transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: blur(10px) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
    text-align: center;
}
div[data-testid="stLinkButton"] a:hover {
    transform: translateY(-3px) scale(1.015);
}

div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #1e1b18 0%, #292524 50%, #1c1917 100%) !important;
    border: 2px solid #d97706 !important;
    box-shadow: 0 0 0 1px #78350f, 0 6px 18px rgba(217, 119, 6, 0.45) !important;
    color: #fef08a !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a:hover {
    border-color: #fbbf24 !important;
    box-shadow: 0 0 0 2px #d97706, 0 8px 24px rgba(245, 158, 11, 0.65) !important;
    color: #ffffff !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #0c1e33 0%, #1e293b 50%, #0f172a 100%) !important;
    border: 2px solid #38bdf8 !important;
    box-shadow: 0 0 0 1px #0369a1, 0 6px 18px rgba(56, 189, 248, 0.45) !important;
    color: #e0f2fe !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a:hover {
    border-color: #7dd3fc !important;
    box-shadow: 0 0 0 2px #0284c7, 0 8px 24px rgba(56, 189, 248, 0.65) !important;
    color: #ffffff !important;
}

div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #380718 0%, #4c0519 50%, #1f040d 100%) !important;
    border: 2px solid #f43f5e !important;
    box-shadow: 0 0 0 1px #9f1239, 0 6px 18px rgba(244, 63, 94, 0.45) !important;
    color: #ffe4e6 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a:hover {
    border-color: #fb7185 !important;
    box-shadow: 0 0 0 2px #e11d48, 0 8px 24px rgba(244, 63, 94, 0.65) !important;
    color: #ffffff !important
