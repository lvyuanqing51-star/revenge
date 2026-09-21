import base64
from collections import defaultdict
import difflib
import hashlib
from io import BytesIO
from itertools import combinations
import json
import os
import re
import time
from openai import OpenAI
import pandas as pd
from PIL import Image
import streamlit as st

DATA_FILE = "records.json"
CONFIG_FILE = "config.json"
TARGET_QIANQIU = "千秋种我一栗卿#52652"

st.set_page_config(page_title="峡谷内战控制台", page_icon="⚔️", layout="wide")

# ---------------- 全局海克斯科技暗黑电竞 CSS ----------------
st.markdown(
    """
    <style>
    /* 全局背景：深邃暗夜星空 */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d1927 0%, #070a0e 100%) !important;
        color: #cdbe91 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* 顶部标题：鎏金渐变 */
    h1 {
        background: linear-gradient(90deg, #c8aa6e 0%, #f0e6d2 50%, #c8aa6e 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        text-shadow: 0 0 25px rgba(200, 170, 110, 0.3) !important;
    }
    h2, h3 {
        color: #f0e6d2 !important;
        letter-spacing: 1px;
    }

    /* 语音作战室三大发光按钮 */
    div[data-testid="stLinkButton"] a {
        border-radius: 8px !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }
    div[data-testid="stLinkButton"] a:hover {
        transform: translateY(-2px);
    }
    /* 大厅主语音：暗金微光 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, rgba(50, 40, 20, 0.9), rgba(200, 170, 110, 0.35)) !important;
        border-color: #c8aa6e !important;
        box-shadow: 0 0 15px rgba(200, 170, 110, 0.25) !important;
        color: #f0e6d2 !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a:hover {
        box-shadow: 0 0 25px rgba(200, 170, 110, 0.5) !important;
    }
    /* 蓝方作战室：海克斯霓虹蓝 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, rgba(10, 45, 80, 0.9), rgba(0, 150, 255, 0.4)) !important;
        border-color: #0ac8b9 !important;
        box-shadow: 0 0 15px rgba(10, 200, 185, 0.3) !important;
        color: #e0f7fa !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a:hover {
        box-shadow: 0 0 25px rgba(10, 200, 185, 0.6) !important;
    }
    /* 红方作战室：暗红熔岩光 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, rgba(80, 15, 25, 0.9), rgba(230, 50, 70, 0.4)) !important;
        border-color: #e84057 !important;
        box-shadow: 0 0 15px rgba(232, 64, 87, 0.3) !important;
        color: #ffebee !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a:hover {
        box-shadow: 0 0 25px rgba(232, 64, 87, 0.6) !important;
    }

    /* 指标卡片：海克斯毛玻璃暗金面板 */
    div[data-testid="stMetric"] {
        background: rgba(13, 22, 33, 0.75) !important;
        border: 1px solid rgba(200, 170, 110, 0.3) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6) !important;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        border-color: rgba(200, 170, 110, 0.8) !important;
        box-shadow: 0 6px 25px rgba(200, 170, 110, 0.25) !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.82rem !important;
        color: #a09b8c !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] > div {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        color: #f0e6d2 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* 上传框与侧边栏深色适配 */
    div[data-testid="stFileUploader"] {
        background: rgba(13, 22, 33, 0.5) !important;
        border-radius: 8px !important;
        border: 1px dashed rgba(200, 170, 110, 0.4) !important;
        padding: 10px !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #06090d !important;
        border-right: 1px solid rgba(200, 170, 110, 0.15) !important;
    }

    /* 自定义纯血电竞暗黑表格容器 */
    .hextech-table-container {
        width: 100%;
        overflow-x: auto;
        border: 1px solid rgba(200, 170, 110, 0.35);
        border-radius: 10px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.8);
        background: rgba(11, 18, 26, 0.95);
        margin-top: 10px;
        margin-bottom: 25px;
    }
    .hextech-table {
        width: 100%;
        border-collapse: collapse;
        color: #f0e6d2;
        font-size: 0.95rem;
        text-align: center;
    }
    .hextech-table th {
        background: linear-gradient(180deg, rgba(30, 45, 60, 0.95), rgba(15, 25, 35, 0.98));
        color: #c8aa6e;
        font-weight: 700;
        letter-spacing: 0.5px;
        padding: 14px 10px;
        border-bottom: 2px solid rgba(200, 170, 110, 0.4);
    }
    .hextech-table td {
        padding: 12px 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        transition: background 0.2s;
    }
    .hextech-table tr:hover td {
        background: rgba(200, 170, 110, 0.15) !important;
    }
    .hextech-table tr:nth-child(even) {
        background: rgba(18, 28, 40, 0.45);
    }
    .hextech-badge-win {
        color: #0ac8b9;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(10, 200, 185, 0.3);
    }
    .hextech-badge-loss {
        color: #e84057;
        font-weight: 700;
    }
    .hextech-player-name {
        text-align: left;
        padding-left: 18px !important;
        font-weight: 600;
        color: #e1e7eb;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------- 0. 配置与图片压缩 ----------------
def load_config():
  if os.path.exists(CONFIG_FILE):
    try:
      with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {
      "main_voice": "https://kook.top/",
      "blue_voice": "https://kook.top/",
      "red_voice": "https://kook.top/",
  }


def save_config(cfg):
  with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)


def compress_image_to_b64(img_bytes, max_w=720):
  try:
    img = Image.open(BytesIO(img_bytes))
    if img.mode != "RGB":
      img = img.convert("RGB")
    w, h = img.size
    if w > max_w:
      new_h = int(h * (max_w / float(w)))
      img = img.resize((max_w, new_h), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
  except Exception:
    try:
      return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
      return ""


# ---------------- 1. 名字清洗与归一 ----------------
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
  raw = resp.choices[0].message.content.strip()
  match = re.search(r"\{.*\}", raw, re.DOTALL)
  clean_str = match.group(0) if match else raw
  return json.loads(clean_str)


def short_name(full_name):
  if not full_name:
    return "未知"
  return full_name.split("#")[0]


# ---------------- 侧边栏（管理 + 对局图文核对） ----------------
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

  # 逐局图文核对
  if records:
    st.markdown("---")
    st.subheader("🔍 对局图文核对")
    game_options = [
        f"第 {i + 1} 局 ({r.get('winning_team', '未知')}方胜)"
        for i, r in enumerate(records)
    ]
    selected_idx = st.selectbox(
        "选择要核对的场次",
        range(len(records)),
        format_func=lambda i: game_options[i],
    )

    curr_record = records[selected_idx]

    thumb_b64 = curr_record.get("image_thumb", "")
    if thumb_b64:
      st.image(
          f"data:image/jpeg;base64,{thumb_b64}",
          caption=f"第 {selected_idx + 1} 局原始结算图",
          use_container_width=True,
      )
    else:
      st.caption("ℹ️ 此历史记录无缓存截图。")

    p_rows = []
    for p in curr_record.get("players", []):
      p_rows.append({
          "阵营": p.get("team", ""),
          "玩家ID": short_name(p.get("player_name", "")),
          "K/D/A": (
              f"{p.get('kills', 0)}/{p.get('deaths', 0)}/{p.get('assists', 0)}"
          ),
          "胜负": "胜" if p.get("is_winner") else "负",
      })
    if p_rows:
      st.dataframe(pd.DataFrame(p_rows), hide_index=True)

    if st.button("🗑️ 删除本局错误战绩", key=f"del_game_{selected_idx}"):
      records.pop(selected_idx)
      save_records(records)
      st.success("已删除该局记录！")
      time.sleep(0.5)
      st.rerun()

  # 语音房设置
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
    if uploaded_backup is not None:
      try:
        imported_data = json.load(uploaded_backup)
        if isinstance(imported_data, list):
          if st.button("⚡ 确认导入并恢复", type="primary"):
            save_records(imported_data)
            st.success("战绩已恢复！")
            time.sleep(0.8)
            st.rerun()
        else:
          st.error("文件格式不正确，必须是 JSON 列表！")
      except Exception as err:
        st.error(f"读取文件失败: {err}")

  st.markdown("---")
  admin_pwd = (
      st.secrets.get("ADMIN_PASSWORD", "666888")
      if hasattr(st, "secrets") and "ADMIN_PASSWORD" in st.secrets
      else "666888"
  )
  pwd = st.text_input("管理密码", type="password")
  if pwd:
    input_hash = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
    target_hash = hashlib.sha256(admin_pwd.encode("utf-8")).hexdigest()
    if input_hash == target_hash:
      st.success("🔓 管理员身份已验证")
      if records and st.button("🗑️ 删除最近一局"):
        records.pop()
        save_records(records)
        st.rerun()
      if st.button("💣 清空所有对局"):
        save_records([])
        st.rerun()
    else:
      st.error("❌ 密码错误")

# ---------------- 主界面 1：标题与连麦作战室直达 ----------------
st.title("⚔️ 峡谷内战控制台")

cfg = load_config()
c1, c2, c3 = st.columns(3)
with c1:
  st.link_button(
      "🎙️ 进入大厅语音",
      cfg.get("main_voice", "https://kook.top/"),
      use_container_width=True,
  )
with c2:
  st.link_button(
      "🔵 进蓝方作战室",
      cfg.get("blue_voice", "https://kook.top/"),
      use_container_width=True,
  )
with c3:
  st.link_button(
      "🔴 进红方作战室",
      cfg.get("red_voice", "https://kook.top/"),
      use_container_width=True,
  )

st.write("")

# ---------------- 主界面 2：战绩上传窗口 ----------------
with st.form("upload_box", clear_on_submit=False):
  files = st.file_uploader(
      "选择或拖拽战绩截图",
      type=["png", "jpg", "jpeg"],
      accept_multiple_files=True,
  )
  submit_btn = st.form_submit_button("🚀 开始录入战绩", type="primary")

if submit_btn:
  if not files:
    st.warning("⚠️ 请先选择或拖入战绩截图！")
  elif not key:
    st.warning("⚠️ 请在左侧侧边栏填入 DashScope API Key！")
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
          result["image_thumb"] = compress_image_to_b64(img_data)

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

# ---------------- 主界面 3：趣味头衔、双人羁绊与胜率榜 ----------------
records = load_records()

if not records:
  st.info(
      "💡 暂无对局数据。请在上方上传战绩截图；若之前导出过备份，可在左侧侧边栏导入恢复。"
  )
else:
  all_raw = []
  for r in records:
    for p in r.get("players", []):
      raw_pname = p.get("player_name", "")
      if raw_pname:
        all_raw.append(raw_pname)

  name_mapping = build_canonical_name_map(list(set(all_raw)))

  def get_final_name(pname):
    strict_name = clean_player_name_strict(pname)
    fname = name_mapping.get(pname, strict_name)
    if strict_name == TARGET_QIANQIU or "千秋" in fname:
      return TARGET_QIANQIU
    return fname

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

  synergy_stats = defaultdict(lambda: {"同队场次": 0, "胜场": 0, "负场": 0})

  for r in records:
    blue_team = []
    red_team = []

    for p in r.get("players", []):
      raw_pname = p.get("player_name", "")
      if not raw_pname:
        continue
      fname = get_final_name(raw_pname)

      stats[fname]["总场次"] += 1
      is_win = bool(p.get("is_winner"))
      if is_win:
        stats[fname]["胜场"] += 1
      else:
        stats[fname]["负场"] += 1
      stats[fname]["击杀"] += p.get("kills", 0)
      stats[fname]["死亡"] += p.get("deaths", 0)
      stats[fname]["助攻"] += p.get("assists", 0)

      team_side = str(p.get("team", "")).upper()
      if team_side == "BLUE":
        blue_team.append((fname, is_win))
      elif team_side == "RED":
        red_team.append((fname, is_win))

    for t in [blue_team, red_team]:
      team_members = list({item[0]: item[1] for item in t}.items())
      if len(team_members) >= 2:
        for (p1, win1), (p2, _) in combinations(team_members, 2):
          pair_key = tuple(sorted([p1, p2]))
          synergy_stats[pair_key]["同队场次"] += 1
          if win1:
            synergy_stats[pair_key]["胜场"] += 1
          else:
            synergy_stats[pair_key]["负场"] += 1

  df = pd.DataFrame.from_dict(stats, orient="index")

  if not df.empty:
    df["胜率_num"] = (df["胜场"] / df["总场次"] * 100).round(1)
    df["KD"] = (df["击杀"] / df["死亡"].replace(0, 1)).round(2)
    df["KDA_num"] = (
        (df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)
    ).round(2)

    # 1. 单人趣味头衔
    kda_candidates = df[df["总场次"] >= 2]
    if kda_candidates.empty:
      kda_candidates = df

    top_kda_name = kda_candidates.sort_values(
        by="KDA_num", ascending=False
    ).index[0]
    top_kill_name = df.sort_values(by="击杀", ascending=False).index[0]
    top_death_name = df.sort_values(by="死亡", ascending=False).index[0]
    top_assist_name = df.sort_values(by="助攻", ascending=False).index[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
      st.metric(
          label="💀 峡谷死神 (KDA王)",
          value=short_name(top_kda_name),
          delta=f"KDA {df.loc[top_kda_name, 'KDA_num']}",
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

    # 2. 双人羁绊
    if synergy_stats:
      syn_list = []
      for (p1, p2), v in synergy_stats.items():
        t_games = v["同队场次"]
        w_games = v["胜场"]
        l_games = v["负场"]
        wr = w_games / t_games if t_games > 0 else 0
        syn_list.append({
            "pair_name": f"{short_name(p1)} & {short_name(p2)}",
            "games": t_games,
            "wins": w_games,
            "losses": l_games,
            "win_rate": wr,
        })

      syn_df = pd.DataFrame(syn_list)
      if not syn_df.empty:
        syn_candidates = syn_df[syn_df["games"] >= 2]
        if syn_candidates.empty:
          syn_candidates = syn_df

        best_pair = syn_candidates.sort_values(
            by=["win_rate", "games"], ascending=[False, False]
        ).iloc[0]
        worst_pair = syn_candidates.sort_values(
            by=["win_rate", "games"], ascending=[True, False]
        ).iloc[0]

        st.write("")
        col_syn1, col_syn2 = st.columns(2)
        with col_syn1:
          st.metric(
              label="🏆 黄金搭档 (同队胜率最高)",
              value=best_pair["pair_name"],
              delta=(
                  f"{best_pair['wins']}胜{best_pair['losses']}负"
                  f" ({round(best_pair['win_rate'] * 100, 1)}%)"
              ),
          )
        with col_syn2:
          st.metric(
              label="💥 难兄难弟 (同队翻车最多)",
              value=worst_pair["pair_name"],
              delta=(
                  f"{worst_pair['wins']}胜{worst_pair['losses']}负"
                  f" ({round(worst_pair['win_rate'] * 100, 1)}%)"
              ),
              delta_color="inverse",
          )

    st.markdown("---")
    st.subheader("📊 胜率总榜")

    # 排序
    df = df.sort_values(
        by=["胜率_num", "总场次", "KDA_num"],
        ascending=[False, False, False],
    )

    # 紧凑拼接无缩进 HTML，确保绝不触发 Markdown 代码块解析
    table_rows = []
    for player_id, row in df.iterrows():
      wr_val = row["胜率_num"]
      wr_badge = (
          f"<span class='hextech-badge-win'>{wr_val}%</span>"
          if wr_val >= 50
          else f"<span class='hextech-badge-loss'>{wr_val}%</span>"
      )
      kd_str = f"{row['KD']:.2f}"
      kda_str = f"{row['KDA_num']:.2f}"
      p_name = short_name(player_id)

      row_html = (
          "<tr>"
          f"<td class='hextech-player-name'>{p_name}</td>"
          f"<td>{row['总场次']}</td>"
          f"<td>{row['胜场']}</td>"
          f"<td>{row['负场']}</td>"
          f"<td>{wr_badge}</td>"
          f"<td style='color:#0ac8b9;font-weight:600;'>{kd_str}</td>"
          f"<td style='color:#c8aa6e;font-weight:700;'>{kda_str}</td>"
          f"<td>{row['击杀']}</td>"
          f"<td>{row['死亡']}</td>"
          f"<td>{row['助攻']}</td>"
          "</tr>"
      )
      table_rows.append(row_html)

    custom_table_html = (
        '<div class="hextech-table-container">'
        '<table class="hextech-table">'
        "<thead><tr>"
        '<th style="text-align:left;padding-left:18px;">玩家</th>'
        "<th>总场次</th><th>胜场</th><th>负场</th><th>胜率</th>"
        "<th>KD比</th><th>KDA</th><th>击杀</th><th>死亡</th><th>助攻</th>"
        "</tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody>"
        "</table></div>"
    )

    st.markdown(custom_table_html, unsafe_allow_html=True)
