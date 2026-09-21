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
    page_title="LOL 内战胜率统计",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🏆 英雄联盟内战胜率统计看板")

# ---------------- 核心：玩家名字纠错映射 ----------------
NAME_FIX_MAP = {
    "千秋种我一粟卿": "千秋种我一栗卿",
}


def clean_player_name(raw_name: str) -> str:
  name = raw_name.strip()
  name = name.replace("一粟卿", "一栗卿")
  for wrong, right in NAME_FIX_MAP.items():
    if wrong in name:
      name = name.replace(wrong, right)
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


# ---------------- 2. 通义千问 Qwen-VL 视觉文字识别 ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
  # 使用通义千问官方兼容 OpenAI 的 Base URL
  client = OpenAI(
      api_key=key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
  )
  b64_img = base64.b64encode(image_bytes).decode("utf-8")

  prompt = """这是手机端【掌上英雄联盟 App】或客户端的对局结算截图。
请精准识别整局胜负（蓝方/红方，或上方/下方队伍），以及所有选手的ID和击杀/死亡/助攻(K/D/A)。
请勿识别英雄。注意区分'栗'与'粟'等形近字。

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
          model="qwen-vl-max",  # 通义千问视觉大模型主力版本，文字识别极准
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

      # 防御性转换：确保数值字段统一为 int 类型，避免计算时报错
      for p in data.get("players", []):
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
  default_key = (
      st.secrets.get("DASHSCOPE_API_KEY", "")
      if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets
      else ""
  )
  api_key = st.text_input(
      "通义千问 API Key (DashScope)",
      value=default_key,
      type="password",
      help="在阿里云百炼控制台获取的以 sk- 开头的密钥",
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
        help="建议定期备份，防止服务器休眠清空",
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
  # 撤销与删除
  with st.expander("🔒 管理员功能"):
    admin_pwd = st.text_input(
        "输入管理员密码", type="password", key="admin_pwd_input"
    )
    if admin_pwd == "666888":
      if current_records:
        if st.button("⏪ 撤回最近的一局"):
          delete_record_by_index(len(current_records) - 1)
          st.toast("已撤回最新对局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

        corr_options = {i: f"第 {i + 1} 局" for i in range(len(current_records))}
        sel_del_idx = st.selectbox(
            "选择要删除的对局",
            options=list(reversed(list(corr_options.keys()))),
            format_func=lambda x: corr_options[x],
            key="select_del_game",
        )
        if st.button("❌ 确认删除该局"):
          delete_record_by_index(sel_del_idx)
          st.toast("已删除该局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

      if st.button("💣 清空所有历史数据", type="primary"):
        reset
