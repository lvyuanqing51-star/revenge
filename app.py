import base64
from collections import defaultdict
import difflib
import hashlib
import io
from itertools import combinations
import json
import os
import time
import zipfile
from openai import OpenAI
import pandas as pd
from PIL import Image
import streamlit as st

DATA_FILE = "records.json"
IMAGE_DIR = "saved_images"

try:
  os.makedirs(IMAGE_DIR, exist_ok=True)
except Exception:
  pass

st.set_page_config(
    page_title="LOL 内战战绩与羁绊统计",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏆 英雄联盟内战战绩与羁绊看板")

# ---------------- 核心：玩家名字纠错与模糊匹配 ----------------
KNOWN_PLAYERS = [
    "千秋种我一栗卿",
]

NAME_FIX_MAP = {
    "千秋种我一粟卿": "千秋种我一栗卿",
    "千秋种我一卵卿": "千秋种我一栗卿",
    "千秋种我一桑卿": "千秋种我一栗卿",
    "千秋种我一梁卿": "千秋种我一栗卿",
}


def clean_player_name(raw_name: str) -> str:
  name = str(raw_name).strip()

  # 1. 强特征前缀拦截（只要是以 "千秋种我" 开头，无论中间被认成什么，直接归一）
  if name.startswith("千秋种我") and (name.endswith("卿") or len(name) >= 6):
    return "千秋种我一栗卿"

  # 2. 字形字典映射
  for wrong, right in NAME_FIX_MAP.items():
    if wrong in name:
      name = name.replace(wrong, right)

  # 3. 常见局部别字直接纠正
  name = name.replace("一粟卿", "一栗卿").replace("一卵卿", "一栗卿")

  # 4. 白名单相似度模糊匹配兜底
  matches = difflib.get_close_matches(name, KNOWN_PLAYERS, n=1, cutoff=0.7)
  if matches:
    return matches[0]

  return name


def calculate_md5(data: bytes) -> str:
  return hashlib.md5(data).hexdigest()


# ---------------- 1. 数据持久化与备份 ----------------
def load_all_records():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
      return []
  return []


def save_record(new_record):
  records = load_all_records()
  records.append(new_record)
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)


def overwrite_all_records(records_list):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(records_list, f, ensure_ascii=False, indent=2)


def delete_record_by_index(target_index: int):
  records = load_all_records()
  if 0 <= target_index < len(records):
    removed = records.pop(target_index)
    img_filename = removed.get("image_file")
    if img_filename:
      img_path = os.path.join(IMAGE_DIR, img_filename)
      if os.path.exists(img_path):
        try:
          os.remove(img_path)
        except Exception:
          pass
    overwrite_all_records(records)
    return True
  return False


def reset_all_records():
  if os.path.exists(DATA_FILE):
    try:
      os.remove(DATA_FILE)
    except Exception:
      pass
  if os.path.exists(IMAGE_DIR):
    for f in os.listdir(IMAGE_DIR):
      file_path = os.path.join(IMAGE_DIR, f)
      if os.path.isfile(file_path):
        try:
          os.remove(file_path)
        except Exception:
          pass


def sanitize_database():
  records = load_all_records()
  modified = False
  for r in records:
    for p in r.get("players", []):
      old_name = p.get("player_name", "")
      fixed_name = clean_player_name(old_name)
      if old_name != fixed_name:
        p["player_name"] = fixed_name
        modified = True
  if modified:
    overwrite_all_records(records)
  return modified


# ---------------- 2. 通义千问 Qwen-VL 视觉文字识别 ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
  client = OpenAI(
      api_key=key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
  )
  b64_img = base64.b64encode(image_bytes).decode("utf-8")

  prompt = """这是手机端【掌上英雄联盟 App】或客户端的对局结算截图。
请精准识别整局胜负（蓝方/红方，或上方/下方队伍），以及所有选手的ID和击杀/死亡/助攻(K/D/A)。
请勿识别英雄。

【特别提醒选手名字识别】：
常驻选手包含“千秋种我一栗卿”，请务必注意是“栗（板栗的栗）”，切勿错认成“粟”或“卵”。

严格输出纯 JSON 对象，格式必须如下：
{
  "winning_team": "BLUE",
  "players": [
    {
      "player_name": "玩家游戏ID",
      "team": "BLUE",
      "kills": 0,
      "deaths": 0,
      "assists": 0,
      "is_winner": true
    }
  ]
}
"""

  for attempt in range(max_retries):
    try:
      response = client.chat.completions.create(
          model="qwen-vl-max",
          messages=[{
              "role": "user",
              "content": [
                  {"type": "text", "text": prompt},
                  {
                      "type": "image_url",
                      "image_url": {
                          "url": f"data:image/jpeg;base64,{b64_img}"
                      },
                  },
              ],
          }],
          response_format={"type": "json_object"},
          temperature=0.1,
      )
      content = response.choices[0].message.content.strip()

      if content.startswith("```json"):
        content = content[7:]
      elif content.startswith("```"):
        content = content[3:]
      if content.endswith("```"):
        content = content[:-3]
      content = content.strip()

      data = json.loads(content)

      for p in data.get("players", []):
        p["player_name"] = clean_player_name(p.get("player_name", ""))
        p["kills"] = int(p.get("kills", 0))
        p["deaths"] = int(p.get("deaths", 0))
        p["assists"] = int(p.get("assists", 0))
        p["is_winner"] = bool(p.get("is_winner", False))

      return data
    except Exception as e:
      if attempt < max_retries - 1:
        time.sleep((attempt + 1) * 2)
        continue
      raise e


# ---------------- 3. 侧边栏与管理功能 ----------------
with st.sidebar:
  st.title("⚙️ 控制面板")
  default_key = ""
  try:
    if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets:
      default_key = st.secrets["DASHSCOPE_API_KEY"]
  except Exception:
    pass

  api_key = st.text_input(
      "通义千问 API Key (DashScope)",
      value=default_key,
      type="password",
      help="在阿里云百炼控制台获取的 sk- 开头密钥",
  )

  st.markdown("---")
  current_records = load_all_records()
  st.metric("总计收录对局", f"{len(current_records)} 局")

  if current_records:
    json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 导出战绩备份 (JSON)",
        data=json_data,
        file_name="lol_match_backup.json",
        mime="application/json",
        help="建议定期备份",
    )

  with st.expander("📥 导入战绩备份"):
    backup_file = st.file_uploader(
        "选择备份文件", type=["json"], key="backup_uploader"
    )
    if backup_file is not None:
      try:
        imported_data = json.load(backup_file)
        if isinstance(imported_data, list):
          if st.button("⚡ 确认导入恢复", type="primary", key="btn_restore"):
            overwrite_all_records(imported_data)
            st.success("恢复成功！")
            time.sleep(1)
            st.rerun()
      except Exception as err:
        st.error(f"读取失败: {err}")

  st.markdown("---")
  with st.expander("🔒 管理员功能"):
    admin_pwd = st.text_input(
        "输入管理员密码", type="password", key="admin_pwd_input"
    )
    admin_target_pwd = "666888"
    try:
      if hasattr(st, "secrets") and "ADMIN_PWD" in st.secrets:
        admin_target_pwd = st.secrets["ADMIN_PWD"]
    except Exception:
      pass

    if admin_pwd == admin_target_pwd:
      if st.button("🧹 一键清洗历史别字(粟/卵等)", key="btn_sanitize"):
        if sanitize_database():
          st.toast("已成功修复历史数据中的所有错别字！", icon="✨")
          time.sleep(0.8)
          st.rerun()
        else:
          st.info("数据很健康，未发现需要清洗的别字。")

      if current_records:
        if st.button("⏪ 撤回最近的一局", key="btn_undo"):
          delete_record_by_index(len(current_records) - 1)
          st.toast("已撤回最新对局！", icon="🗑️")
          time
