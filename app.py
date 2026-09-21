import base64
from collections import defaultdict
import hashlib
import io
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

os.makedirs(IMAGE_DIR, exist_ok=True)

st.set_page_config(
    page_title="LOL 内战胜率统计 (千问版)",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🏆 英雄联盟内战胜率统计看板 (通义千问版)")

# ---------------- 核心：玩家名字强力清洗与合并映射 ----------------
NAME_FIX_MAP = {
    "千秋种我一粟卿": "千秋种我一栗卿",
}


def clean_player_name(raw_name: str) -> str:
  if not raw_name:
    return ""

  # 1. 统一全角井号及字符替换
  name = raw_name.replace("＃", "#").replace("一粟卿", "一栗卿")

  # 2. 彻底清除名字中意外混入的所有空格、换行及空白字符
  name = "".join(name.split())

  # 3. 针对形近字/隐形字符的强行归一化合并
  if "千秋" in name and "52652" in name:
    return "千秋种我一栗卿#52652"

  for wrong, right in NAME_FIX_MAP.items():
    if wrong in name:
      name = name.replace(wrong, right)

  return name.strip()


def calculate_md5(data: bytes) -> str:
  return hashlib.md5(data).hexdigest()


# ---------------- 1. 数据持久化与维护 ----------------
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
        os.remove(img_path)
    overwrite_all_records(records)
    return True
  return False


def reset_all_records():
  if os.path.exists(DATA_FILE):
    os.remove(DATA_FILE)
  if os.path.exists(IMAGE_DIR):
    for f in os.listdir(IMAGE_DIR):
      file_path = os.path.join(IMAGE_DIR, f)
      if os.path.isfile(file_path):
        os.remove(file_path)


# ---------------- 2. 通义千问多模态识图引擎 ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
  client = OpenAI(
      api_key=key,
      base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  )
  b64_img = base64.b64encode(image_bytes).decode("utf-8")

  prompt = """这是手机端【掌上英雄联盟 App】或客户端的对局结算战绩截图。
请精准识别整局胜负（上方/下方队伍，或蓝方/红方），以及所有玩家的游戏ID和对应的击杀/死亡/助攻 (K/D/A)。
无需识别英雄。请务必仔细辨别玩家名字中的'栗'与'粟'等形近字。

严格输出纯 JSON 对象，格式如下：
{
  "winning_team": "BLUE" 或 "RED",
  "players": [
    {
      "player_name": "玩家游戏ID",
      "team": "BLUE" 或 "RED",
      "kills": 0,
      "deaths": 0,
      "assists": 0,
      "is_winner": true 或 false
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

      return json.loads(content)
    except Exception as e:
      if attempt < max_retries - 1:
        time.sleep((attempt + 1) * 2)
        continue
      raise e


# ---------------- 3. 侧边栏与控制台 ----------------
with st.sidebar:
  st.title("⚙️ 控制面板")
  default_key = (
      st.secrets.get("DASHSCOPE_API_KEY", "")
      if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets
      else ""
  )
  api_key = st.text_input(
      "通义千问 API Key (DashScope)",
      value=default_key,
      type="password",
      help="以 sk- 开头的阿里云百炼密钥",
  )

  st.markdown("---")
  current_records = load_all_records()
  st.metric("总计收录对局", f"{len(current_records)} 局")

  # 导出备份
  if current_records:
    json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 导出战绩备份 (JSON)",
        data=json_data,
        file_name="lol_match_backup.json",
        mime="application/json",
        help="建议定期备份到本地，防止云端重启",
    )

  # 导入恢复
  with st.expander("📥 导入战绩备份"):
    backup_file = st.file_uploader("选择备份文件", type=["json"])
    if backup_file is not None:
      try:
        imported_data = json.load(backup_file)
        if isinstance(imported_data, list):
          if st.button("⚡ 确认导入恢复", type="primary"):
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
    if
