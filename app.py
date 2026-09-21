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
      "main_voice": "[https://kook.top/](https://kook.top/)",
      "blue_voice": "[https://kook.top/](https://kook.top/)",
      "red_voice": "[https://kook.top/](https://kook.top/)",
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


def clean_json_text(text: str) -> str:
  t = text.strip()
  # 安全去除 markdown 代码块标记，防止因为反引号在复制时折行断裂
  match = re.search(r"\{.*\}", t, re.DOTALL)
  if match:
    return match.group(0)
  return t


def analyze_image(img_bytes, api_key):
  client = OpenAI(
      api_key=api_key,
      base_url="[https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)",
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
  raw_content = resp.choices[0].message.content
  parsed_content = clean_json_text(raw_content)
  return json.loads(parsed_content)


def short_name(full_name):
  return full_name.split("#")[0]


# ---------------- 侧边栏 ----------------
with st.sidebar:
  st.header("⚙️ 系统管理")
  default_key = (
      st.secrets.get("DASHSCOPE_API_KEY", "")
      if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets
      else ""
  )
  key = st.text_input(
      "DashScope API Key",
      value=default_key,
      type="password",
      help="sk- 开头的密钥",
  )

  records = load_records()
  st.metric("总计收录对局", f"{len(records)} 局")

  with st.expander("🎙️ 配置内战语音房链接"):
    cfg = load_config()
    new_main = st.text_input("大厅主语音链接", value=cfg.get("main_voice", ""))
    new_blue = st.text_input("🔵 蓝方专属语音链接", value=cfg.get("blue_voice", ""))
    new_red = st.text_input("🔴 红方专属语音链接", value=cfg.get("red_voice", ""))
    if st.button("💾 保存语音房链接"):
      save_config(
          {"main_voice": new_main, "blue_voice": new_blue, "red_voice": new_red}
      )
      st.success("配置已保存！")
      time.sleep(0.5)
      st.rerun()

  st.markdown("---")
  st.subheader("📦 数据备份与恢复")

  if records:
    json_bytes = json.dumps(records, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    st.download_button(
        label="💾 导出战绩备份 (JSON)",
        data=json_bytes,
        file_name="lol_records_backup.json",
        mime="application/json",
        help="点击下载备份文件到本地",
    )

  with st.expander("📥 导入恢复历史数据"):
    uploaded_backup = st.file_uploader(
        "选择已备份的 JSON 文件",
        type=["json"],
        key="backup_uploader",
    )
