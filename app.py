import base64
from collections import defaultdict
import difflib
import hashlib
import json
import os
import re
import time
from openai import OpenAI
import pandas as pd
import streamlit as st

DATA_FILE = "records.json"
st.set_page_config(page_title="内战", page_icon="⚔️", layout="wide")


# ---------------- 自动名字强力归一与聚类 ----------------
def normalize_name_skeleton(name: str) -> str:
  """骨架化名字：去空格、统一番号、去除常见混淆标点（丶、顿号、横杠等）"""
  if not name:
    return ""
  s = str(name).strip()
  # 去除所有不可见空白
  s = re.sub(r"[\s\u200b\ufeff\u3000]+", "", s)
  # 统一全角井号
  s = s.replace("＃", "#")
  # 统一横杠类
  s = s.replace("—", "-").replace("–", "-")
  # 统一各种'点'和'顿号'为无，解决 大原丶 与 大原、 的分裂
  s = s.replace("丶", "").replace("、", "").replace(",", "")
  # 统一千秋字形
  s = s.replace("一粟卿", "一栗卿")
  return s


def build_canonical_name_map(all_raw_names: list) -> dict:
  """根据所有出现的原始名字，自动聚类合并相似度超 85% 或骨架相同的名字"""
  mapping = {}
  unique_clusters = []  # 存放标准名称

  for raw in all_raw_names:
    if not raw:
      continue
    skel = normalize_name_skeleton(raw)

    # 优先强规则：千秋系列
    if "千秋" in raw:
      mapping[raw] = "千秋种我一栗卿#52652"
      continue

    # 检查是否与已有聚类高度相似
    matched_target = None
    for cluster in unique_clusters:
      cluster_skel = normalize_name_skeleton(cluster)
      # 骨架完全一致（如 大原丶娜娜子#64291 和 大原、娜娜子#64291）
      if skel == cluster_skel:
        matched_target = cluster
        break
      # 或者相似度大于 88%
      ratio = difflib.SequenceMatcher(None, skel, cluster_skel).ratio()
      if ratio >= 0.88:
        matched_target = cluster
        break

    if matched_target:
      mapping[raw] = matched_target
    else:
      unique_clusters.append(raw)
      mapping[raw] = raw

  return mapping


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
    content = content.split("```")[1]
    if content.startswith("json"):
      content = content[4:]
  return json.loads(content.strip())


# ---------------- 侧边栏 ----------------
with st.sidebar:
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

# ---------------- 主界面 3：胜率榜单（自动模糊聚合） ----------------
st.subheader("胜率榜单")

records = load_records()
if not records:
  st.info("💡 暂无战绩数据，请在上方上传截图。")
else:
  # 1. 先收集库中所有出现的全部原始玩家名
  all_raw = []
  for r in records:
    for p in r.get("players", []):
      pname = p.get("player_name", "").strip()
      if pname:
        all_raw.append(pname)

  # 2. 自动生成聚类映射字典（彻底合并微小标点差异如 丶 与 、）
  name_mapping = build_canonical_name_map(list(set(all_raw)))

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
      raw_pname = p.get("player_name", "").strip()
      if not raw_pname:
        continue
      # 使用自动聚类后的统一名字
      final_name = name_mapping.get(raw_pname, raw_pname)

      stats[final_name]["总场次"] += 1
      if p.get("is_winner"):
        stats[final_name]["胜场"] += 1
      else:
        stats[final_name]["负场"] += 1
      stats[final_name]["击杀"] += p.get("kills", 0)
      stats[final_name]["死亡"] += p.get("deaths", 0)
      stats[final_name]["助攻"] += p.get("assists", 0)

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
