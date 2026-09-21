import base64
from collections import defaultdict
import hashlib
import json
import os
import re
import time
from openai import OpenAI
import pandas as pd
import streamlit as st

DATA_FILE = "records.json"
ALIAS_FILE = "name_aliases.json"  # 专门存放合并映射规则

st.set_page_config(page_title="内战", page_icon="⚔️", layout="wide")


# ---------------- 1. 别名映射与清洗 ----------------
def load_aliases():
  """读取别名映射字典 { 识别错的别名: 正确的标准名字 }"""
  if os.path.exists(ALIAS_FILE):
    try:
      with open(ALIAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def save_aliases(aliases):
  with open(ALIAS_FILE, "w", encoding="utf-8") as f:
    json.dump(aliases, f, ensure_ascii=False, indent=2)


def clean_name(name):
  if not name:
    return ""

  # 1. 过滤空格、长破折号与全角符号
  s = str(name).strip()
  s = re.sub(r"[\s\u200b\ufeff\u3000]+", "", s)
  s = s.replace("＃", "#").replace("—", "-").replace("一粟卿", "一栗卿")

  # 2. 默认规则：千秋系列无条件锁死
  if "千秋" in s:
    return "千秋种我一栗卿#52652"

  # 3. 动态别名池替换
  aliases = load_aliases()
  # 优先全词匹配
  if s in aliases:
    return aliases[s]

  return s


def get_md5(data):
  return hashlib.md5(data).hexdigest()


# ---------------- 2. 数据读写 ----------------
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
      "不要识别英雄。仔细识别完整游戏ID（含#后缀）。\n"
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
    content = content.split("```")[1]
    if content.startswith("json"):
      content = content[4:]
  return json.loads(content.strip())


# ---------------- 侧边栏：配置与名字合并修正 ----------------
with st.sidebar:
  st.header("⚙️ 设置与维护")
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
  st.caption(f"已录入对局: {len(records)} 局")

  # --- 核心功能：玩家名字可视化合并工具 ---
  with st.expander("🔗 修正重复玩家（合并名字）"):
    st.write("把误识别的分裂名字合并为一个：")
    # 获取目前数据库里出现过的全部原始名字
    raw_names = set()
    for r in records:
      for p in r.get("players", []):
        raw_names.add(p.get("player_name", "").strip())
    raw_names = sorted([n for n in raw_names if n])

    if raw_names:
      source_name = st.selectbox("选择【识别错的名字】(被合并):", raw_names)
      target_name = st.selectbox(
          "合并到【正确的标准名字】:", raw_names, index=0
      )

      if st.button("⚡ 确认合并这两个人"):
        if source_name != target_name:
          # 1. 记录进持久化别名表
          aliases = load_aliases()
          aliases[source_name] = target_name
          save_aliases(aliases)

          # 2. 批量将历史对局中的该名字全部替换为标准名字
          for r in records:
            for p in r.get("players", []):
              if p.get("player_name", "").strip() == source_name:
                p["player_name"] = target_name
          save_records(records)

          st.success(f"已成功将【{source_name}】合并至【{target_name}】！")
          time.sleep(0.8)
          st.rerun()
        else:
          st.warning("两个名字不能相同！")

  pwd = st.text_input("管理密码", type="password")
  if pwd == "666888":
    if records and st.button("🗑️ 删除最近一局"):
      records.pop()
      save_records(records)
      st.rerun()
    if st.button("💣 清空所有对局"):
      save_records([])
      st.rerun()

# ---------------- 主界面 1：一行大字“内战” ----------------
st.title("内战")

# ---------------- 主界面 2：战绩上传窗口 ----------------
with st.form("upload_form", clear_on_submit=False):
  files = st.file_uploader(
      "上传掌盟战绩截图",
      type=["png", "jpg", "jpeg"],
      accept_multiple_files=True,
      label_visibility="collapsed",
  )
  submit_btn = st.form_submit_button("🚀 开始录入战绩", type="primary")

if submit_btn:
  if not files:
    st.warning("⚠️ 请先选择或拖入战绩截图！")
  elif not key:
    st.warning("⚠️ 请在左侧输入 DashScope API Key！")
  else:
    records = load_records()
    seen_hashes = {r.get("md5") for r in records if "md5" in r}
    added = 0

    bar = st.progress(0)
    status_box = st.empty()

    for idx, file in enumerate(files):
      status_box.info(f"⏳ 正在分析第 {idx + 1}/{len(files)} 张: {file.name}")
      img_data = file.read()
      h = get_md5(img_data)

      if h in seen_hashes:
        st.warning(f"⚠️ {file.name} 已录入过，已自动跳过。")
      else:
        try:
          result = analyze_image(img_data, key)
          result["md5"] = h
          # 保存前用清洗规则（含别名规则）规整
          for p in result.get("players", []):
            p["player_name"] = clean_name(p.get("player_name", ""))
          records.append(result)
          seen_hashes.add(h)
          added += 1
          save_records(records)
        except Exception as e:
          st.error(f"❌ {file.name} 录入失败: {e}")

      bar.progress((idx + 1) / len(files))

    status_box.empty()
    if added > 0:
      st.success(f"🎉 成功录入 {added} 局战绩！")
      time.sleep(0.8)
      st.rerun()

st.markdown("---")

# ---------------- 主界面 3：胜率榜单 ----------------
st.subheader("胜率榜单")

records = load_records()
if not records:
  st.info("💡 暂无战绩数据，请在上方上传截图。")
else:
  stats = defaultdict(
      lambda: {
          "总场次": 0,
          "胜场": 0,
          "负场": 0,
          "击杀": 0,
          "死亡": 0,
          "助攻": 0,
      }
  )

  for r in records:
    for p in r.get("players", []):
      name = clean_name(p.get("player_name", ""))
      if not name:
        continue
      stats[name]["总场次"] += 1
      if p.get("is_winner"):
        stats[name]["胜场"] += 1
      else:
        stats[name]["负场"] += 1
      stats[name]["击杀"] += p.get("kills", 0)
      stats[name]["死亡"] += p.get("deaths", 0)
      stats[name]["助攻"] += p.get("assists", 0)

  df = pd.DataFrame.from_dict(stats, orient="index")
  df["胜率"] = (df["胜场"] / df["总场次"] * 100).round(1).astype(str) + "%"
  df["KDA"] = (
      (df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)
  ).round(2)
  df["sort_key"] = df["胜场"] / df["总场次"]
  df = df.sort_values(
      by=["sort_key", "总场次", "KDA"], ascending=[False, False, False]
  ).drop(columns=["sort_key"])

  st.dataframe(df, use_container_width=True)
