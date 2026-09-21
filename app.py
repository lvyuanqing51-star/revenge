import base64
from collections import defaultdict
import difflib
import hashlib
from itertools import combinations
import json
import os
import re
import time
from openai import OpenAI
import pandas as pd
import streamlit as st

DATA_FILE = "records.json"
CONFIG_FILE = "config.json"
st.set_page_config(page_title="内战", page_icon="⚔️", layout="wide")

# 自定义紧凑字号样式
st.markdown(
    """
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 1.12rem !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

TARGET_QIANQIU = "千秋种我一栗卿#52652"


# ---------------- 0. 语音房配置管理 ----------------
def load_config():
  if os.path.exists(CONFIG_FILE):
    try:
      with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {
      "main_voice": "https://kook.top/",  # 默认主频道
      "blue_voice": "https://kook.top/",  # 默认蓝方语音
      "red_voice": "https://kook.top/",  # 默认红方语音
  }


def save_config(cfg):
  with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---------------- 自动名字强力归一与聚类 ----------------
def clean_player_name_strict(name: str) -> str:
  if not name:
    return ""

  s = re.sub(r"[\s\u200b\ufeff\u3000\r\n\t]+", "", str(name))
  s = s.replace("＃", "#").replace("—", "-").replace("–", "-")

  if (
      ("千秋" in s)
      or ("52652" in s)
      or ("一栗卿" in s)
      or ("一粟卿" in s)
      or ("栗卿" in s)
      or ("粟卿" in s)
  ):
    return TARGET_QIANQIU

  s = s.replace("丶", "").replace("、", "").replace(",", "")
  return s


def build_canonical_name_map(all_raw_names: list) -> dict:
  mapping = {}
  unique_clusters = []

  for raw in all_raw_names:
    cleaned = clean_player_name_strict(raw)
    if not cleaned:
      continue

    if cleaned == TARGET_QIANQIU:
      mapping[raw] = TARGET_QIANQIU
      continue

    matched_target = None
    for cluster in unique_clusters:
      if cleaned == cluster:
        matched_target = cluster
        break
      ratio = difflib.SequenceMatcher(None, cleaned, cluster).ratio()
      if ratio >= 0.88:
        matched_target = cluster
        break

    if matched_target:
      mapping[raw] = matched_target
    else:
      unique_clusters.append(cleaned)
      mapping[raw] = cleaned

  return mapping


def get_md5(data):
  return hashlib.md5(data).hexdigest()


def load_records():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
      return []
  return []


def save_records(records):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)


def analyze_image(img_bytes, api_key):
  client = OpenAI(
      api_key=api_key,
      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
      timeout=40.0,
  )
  b64 = base64.b64encode(img_bytes).decode("utf-8")

  prompt = (
      "这是英雄联盟掌盟战绩结算截图。\n"
      "请识别整局胜负（BLUE或RED），以及全部10位玩家的游戏ID与KDA数值。\n"
      "不要识别英雄。\n"
      "请严格输出合法JSON：\n"
      '{"winning_team": "BLUE", "players": [{"player_name": "ID", "team":'
      ' "BLUE", "kills": 0, "deaths": 0, "assists": 0, "is_winner": true}]}'
  )

  resp = client.chat.completions.create(
      model="qwen-vl-max",
      messages=[{
          "role": "user",
          "content": [
              {"type": "text", "text": prompt},
              {
                  "type": "image_url",
                  "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
              },
          ],
      }],
      response_format={"type": "json_object"},
      temperature=0.1,
  )
  content = resp.choices[0].message.content.strip()
  if content.startswith("```"):
    content = content.split("
