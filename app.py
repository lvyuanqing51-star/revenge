import base64
from collections import defaultdict
import hashlib
import json
import os
import time
from openai import OpenAI
import pandas as pd
import streamlit as st

DATA_FILE = "records.json"
st.set_page_config(page_title="LOL胜率榜", layout="wide")
st.title("🏆 英雄联盟内战胜率看板")

# 终极归一化规则：只要带"千秋"，直接锁死为同一个字符串
UNIFIED_QIANQIU = "千秋种我一栗卿#52652"


def clean_name(name):
  if not name:
    return ""
  s = str(name).strip().replace(" ", "").replace("＃", "#")
  if "千秋" in s:
    return UNIFIED_QIANQIU
  return s


def get_md5(data):
  return hashlib.md5(data).hexdigest()


def load_records():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
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
  )
  b64 = base64.b64encode(img_bytes).decode("utf-8")
  prompt = (
      "识别这张英雄联盟对局截图。"
      "提取胜负队伍(BLUE或RED)，以及每位玩家的ID和KDA。"
      "不要识别英雄。"
      '输出JSON格式: {"winning_team": "BLUE", "players": [{"player_name":'
      ' "ID", "team": "BLUE", "kills": 0, "deaths": 0, "assists": 0,'
      ' "is_winner": true}]}'
  )

  resp = client.chat.completions.create(
      model="qwen-vl-max",
      messages=[{
          "role": "user",
          "content": [
              {"type": "text", "text": prompt},
              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
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


# 侧边栏
with st.sidebar:
  st.header("设置")
  default_key = st.secrets.get("DASHSCOPE_API_KEY", "") if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets else ""
  key = st.text_input("DashScope API Key", value=default_key, type="password")

  records = load_records()
  st.write(f"当前对局数: {len(records)}")

  if st.button("🔄 立即强制合并千秋"):
    for r in records:
      for p in r.get("players", []):
        p["player_name"] = clean_name(p.get("player_name", ""))
    save_records(records)
    st.success("已完成清洗合并！")
    time.sleep(0.5)
    st.rerun()

  pwd = st.text_input("管理密码", type="password")
  if pwd == "666888":
    if records and st.button("🗑️ 删除最近一局"):
      records.pop()
      save_records(records)
      st.rerun()
    if st.button("💣 清空所有对局"):
      save_records([])
      st.rerun()

# 主界面上传
files = st.file_uploader("上传战绩截图", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
if files and st.button("开始录入", type="primary"):
  if not key:
    st.warning("请先填写 API Key！")
  else:
    records = load_records()
    seen_hashes = {r.get("md5") for r in records if "md5" in r}
    added = 0

    bar = st.progress(0)
    for i, file in enumerate(files):
      data = file.read()
      h = get_md5(data)
      if h not in seen_hashes:
        try:
          res = analyze_image(data, key)
          res["md5"] = h
          for p in res.get("players", []):
            p["player_name"] = clean_name(p.get("player_name", ""))
          records.append(res)
          seen_hashes.add(h)
          added += 1
        except Exception as e:
          st.error(f"{file.name} 失败: {e}")
      bar.progress((i + 1) / len(files))

    save_records(records)
    st.success(f"成功新增 {added} 局战绩！")
    time.sleep(0.8)
    st.rerun()

# 胜率榜展示
records = load_records()
if not records:
  st.info("暂无战绩数据，请上传截图。")
else:
  stats = defaultdict(lambda: {"总场次": 0, "胜场": 0, "负场": 0, "击杀": 0, "死亡": 0, "助攻": 0})
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
  df["KDA"] = ((df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)).round(2)
  df["sort_key"] = df["胜场"] / df["总场次"]
  df = df.sort_values(by=["sort_key", "总场次", "KDA"], ascending=[False, False, False]).drop(columns=["sort_key"])

  st.dataframe(df, use_container_width=True)
