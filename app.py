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

# 自定义紧凑字号样式，彻底解决 st.metric 名字超大被省略截断的问题
st.markdown(
    """
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
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
    content = content.split("```")[1]
    if content.startswith("json"):
      content = content[4:]
  return json.loads(content.strip())


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
    if uploaded_backup is not None:
      try:
        imported_data = json.load(uploaded_backup)
        if isinstance(imported_data, list):
          if st.button("⚡ 确认导入并覆盖", type="primary"):
            save_records(imported_data)
            st.success("恢复成功！正在刷新...")
            time.sleep(0.8)
            st.rerun()
        else:
          st.error("备份文件格式不符合要求！")
      except Exception as err:
        st.error(f"读取备份失败: {err}")

  st.markdown("---")
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
          for p in result.get("players", []):
            p["player_name"] = clean_player_name_strict(
                p.get("player_name", "")
            )
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

# ---------------- 主界面 3：趣味头衔与胜率榜单 ----------------
records = load_records()
if not records:
  st.info("💡 暂无战绩数据，请在上方上传截图。")
else:
  all_raw = []
  for r in records:
    for p in r.get("players", []):
      raw_pname = p.get("player_name", "")
      if raw_pname:
        all_raw.append(raw_pname)

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
      raw_pname = p.get("player_name", "")
      if not raw_pname:
        continue

      strict_name = clean_player_name_strict(raw_pname)
      final_name = name_mapping.get(raw_pname, strict_name)

      if strict_name == TARGET_QIANQIU or "千秋" in final_name:
        final_name = TARGET_QIANQIU

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
  df["KDA_num"] = (
      (df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)
  ).round(2)
  df["KDA"] = df["KDA_num"].astype(str)

  # ---------- 趣味头衔计算 ----------
  kda_candidates = df[df["总场次"] >= 2]
  if kda_candidates.empty:
    kda_candidates = df

  top_kda_name = kda_candidates.sort_values(
      by="KDA_num", ascending=False
  ).index[0]
  top_kill_name = df.sort_values(by="击杀", ascending=False).index[0]
  top_death_name = df.sort_values(by="死亡", ascending=False).index[0]
  top_assist_name = df.sort_values(by="助攻", ascending=False).index[0]

  def short_name(full_name):
    # 去除井号及后缀数字，只留纯游戏昵称
    return full_name.split("#")[0]

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        label="💀 峡谷死神 (KDA王)",
        value=short_name(top_kda_name),
        delta=f"KDA {df.loc[top_kda_name, 'KDA']}",
    )
  with col2:
    st.metric(
        label="🩸 人头收割机 (击杀王)",
        value=short_name(top_kill_name),
        delta=f"{df.loc[top_kill_name, '击杀']} 杀",
    )
  with col3:
    st.metric(
        label="🥔 慈善赌王 (白给王)",
        value=short_name(top_death_name),
        delta=f"{df.loc[top_death_name, '死亡']} 阵亡",
        delta_color="inverse",
    )
  with col4:
    st.metric(
        label="🤝 金牌工具人 (助攻王)",
        value=short_name(top_assist_name),
        delta=f"{df.loc[top_assist_name, '助攻']} 助攻",
    )

  st.markdown("---")
  st.subheader("胜率榜单")

  df["sort_key"] = df["胜场"] / df["总场次"]
  df = (
      df.sort_values(
          by=["sort_key", "总场次", "KDA_num"], ascending=[False, False, False]
      )
      .drop(columns=["sort_key", "KDA_num"])
  )

  st.dataframe(df, use_container_width=True)
