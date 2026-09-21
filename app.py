import base64
import io
import json
import os
import re
import time
from openai import OpenAI
import pandas as pd
from PIL import Image
import streamlit as st

DATA_FILE = "records.json"
IMAGE_DIR = "saved_images"

os.makedirs(IMAGE_DIR, exist_ok=True)

st.set_page_config(
    page_title="LOL 内战战绩看板",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🎮 英雄联盟对局结算智能统计看板 (DeepSeek 版)")

# ---------------- 核心：玩家名字防呆与纠错映射 ----------------
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


# ---------------- 1. 持久化存储与备份恢复函数 ----------------
def load_all_records():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return []
  return []


def save_record(new_record):
  records = load_all_records()
  records.append(new_record)
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)


def overwrite_all_records(records_list):
  """导入备份时一键覆写恢复"""
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(records_list, f, ensure_ascii=False, indent=2)


def reset_all_records():
  if os.path.exists(DATA_FILE):
    os.remove(DATA_FILE)
  if os.path.exists(IMAGE_DIR):
    for f in os.listdir(IMAGE_DIR):
      file_path = os.path.join(IMAGE_DIR, f)
      if os.path.isfile(file_path):
        os.remove(file_path)


# ---------------- 2. DeepSeek API 识图核心 ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
  client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
  b64_img = base64.b64encode(image_bytes).decode("utf-8")

  prompt = """这是一张英雄联盟战绩结算界面截图。
请精准识别整局胜负（蓝方/红方）以及所有玩家的对局数据。
请直接输出纯 JSON 对象，不要输出任何额外的 markdown 标记或解释文字。格式如下：
{
  "winning_team": "BLUE" 或 "RED",
  "players": [
    {
      "player_name": "玩家游戏ID",
      "champion": "所选英雄",
      "team": "BLUE" 或 "RED",
      "kills": 0,
      "deaths": 0,
      "assists": 0,
      "is_winner": true 或 false
    }
  ]
}
注意：请仔细区分"栗"与"粟"等形近字。
"""

  for attempt in range(max_retries):
    try:
      response = client.chat.completions.create(
          model="deepseek-flash",  # 调用 DeepSeek 官方支持视觉的多模态模型
          messages=[{
              "role": "user",
              "content": [
                  {"type": "text", "text": prompt},
                  {
                      "type": "image_url",
                      "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                  },
              ],
          }],
          response_format={"type": "json_object"},
          temperature=0.1,
      )

      content = response.choices[0].message.content.strip()
      content = re.sub(r"^```json\s*", "", content)
      content = re.sub(r"\s*```$", "", content)
      return json.loads(content)

    except Exception as e:
      if attempt < max_retries - 1:
        time.sleep((attempt + 1) * 2)
        continue
      raise e


# ---------------- 3. 侧边栏配置（含导入与备份） ----------------
with st.sidebar:
  st.header("⚙️ 核心设置")
  default_key = (
      st.secrets.get("DEEPSEEK_API_KEY", "")
      if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets
      else ""
  )
  api_key = st.text_input(
      "DeepSeek API Key",
      value=default_key,
      type="password",
      help="以 sk- 开头的 DeepSeek 密钥",
  )

  st.markdown("---")
  st.header("📂 历史数据管理")
  current_records = load_all_records()
  saved_images = [
      f
      for f in os.listdir(IMAGE_DIR)
      if f.lower().endswith((".png", ".jpg", ".jpeg"))
  ]

  st.metric("已累计对局", f"{len(current_records)} 局")
  st.metric("已归档截图", f"{len(saved_images)} 张")

  # 1. 导出备份
  if current_records:
    json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 导出战绩备份 (JSON)",
        data=json_data,
        file_name="lol_match_backup.json",
        mime="application/json",
        help="建议定期下载备份到本地，防止云端容器休眠重启导致数据重置",
    )

  # 2. 导入恢复备份功能
  with st.expander("📥 导入战绩备份（数据恢复）"):
    backup_file = st.file_uploader(
        "上传之前下载的 JSON 备份文件", type=["json"], key="backup_uploader"
    )
    if backup_file is not None:
      try:
        imported_data = json.load(backup_file)
        if isinstance(imported_data, list):
          if st.button("⚡ 确认恢复该备份数据", type="primary"):
            overwrite_all_records(imported_data)
            st.success(f"成功恢复 {len(imported_data)} 局历史数据！")
            time.sleep(1)
            st.rerun()
        else:
          st.error("文件格式不正确，内容必须是对局列表")
      except Exception as err:
        st.error(f"读取备份文件失败: {err}")

  st.markdown("---")
  # 3. 管理员安全清空（密码 666888）
  with st.expander("🔒 管理员功能（危险操作）"):
    admin_pwd = st.text_input(
        "输入管理密码",
        type="password",
        key="admin_pwd",
        help="防止他人误清空数据",
    )
    if admin_pwd == "666888":
      if st.button("🗑️ 确认清空所有数据与原图", type="primary"):
        reset_all_records()
        st.toast("已清空所有历史数据和截图！", icon="🧹")
        st.rerun()
    elif admin_pwd:
      st.error("密码错误，无法清空")


# ---------------- 4. 榜单渲染 ----------------
def render_leaderboard(records):
  if not records:
    st.info("💡 暂无历史对局数据。请在下方上传截图开始统计！")
    return

  player_stats = {}
  for record in records:
    for p in record.get("players", []):
      raw_name = p.get("player_name", "")
      name = clean_player_name(raw_name)

      if not name:
        continue

      if name not in player_stats:
        player_stats[name] = {
            "总场次": 0,
            "胜场": 0,
            "负场": 0,
            "总击杀": 0,
            "总死亡": 0,
            "总助攻": 0,
        }

      player_stats[name]["总场次"] += 1
      if p.get("is_winner"):
        player_stats[name]["胜场"] += 1
      else:
        player_stats[name]["负场"] += 1
      player_stats[name]["总击杀"] += p.get("kills", 0)
      player_stats[name]["总死亡"] += p.get("deaths", 0)
      player_stats[name]["总助攻"] += p.get("assists", 0)

  df = pd.DataFrame.from_dict(player_stats, orient="index")
  df["胜率"] = (df["胜场"] / df["总场次"] * 100).round(1).astype(str) + "%"
  df["K/D"] = (df["总击杀"] / df["总死亡"].replace(0, 1)).round(2)
  df["KDA"] = (
      (df["总击杀"] + df["总助攻"]) / df["总死亡"].replace(0, 1)
  ).round(2)

  df["win_ratio"] = df["胜场"] / df["总场次"]
  df = df.sort_values(by=["win_ratio", "总场次"], ascending=[False, False])
  df = df.drop(columns=["win_ratio"])

  st.subheader(f"🏆 玩家全员胜率榜单（累计收录 {len(records)} 局）")
  st.dataframe(df, use_container_width=True)


# ---------------- 5. 主界面上传与即时刷新 ----------------
uploaded_files = st.file_uploader(
    "📤 上传结算截图（支持单张或批量拖入）",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files:
  if not api_key:
    st.warning("⚠️ 请先在左侧输入你的 DeepSeek API Key！")
  else:
    if st.button("🚀 开始解析并录入", type="primary"):
      success_count = 0
      progress_bar = st.progress(0)
      total = len(uploaded_files)

      for idx, file in enumerate(uploaded_files):
        with st.spinner(f"正在使用 DeepSeek 识别 ({idx + 1}/{total}): {file.name}..."):
          try:
            img_bytes = file.read()
            result = analyze_screenshot(img_bytes, api_key)
            save_record(result)

            save_path = os.path.join(
                IMAGE_DIR, f"{int(time.time())}_{file.name}"
            )
            with open(save_path, "wb") as img_file:
              img_file.write(img_bytes)

            success_count += 1
            time.sleep(0.5)
          except Exception as e:
            st.error(f"❌ 解析 {file.name} 失败: {str(e)}")
        progress_bar.progress((idx + 1) / total)

      if success_count > 0:
        st.success(f"🎉 成功录入 {success_count} 局战绩并归档原图！")
        st.rerun()

st.markdown("---")
render_leaderboard(load_all_records())

# ---------------- 6. 历史截图展示区 ----------------
st.markdown("---")
all_saved_imgs = [
    f
    for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
]
all_saved_imgs.sort(reverse=True)

with st.expander(
    f"🖼️ 查看已上传的历史战绩截图（共 {len(all_saved_imgs)} 张）"
):
  if not all_saved_imgs:
    st.caption("暂无归档截图")
  else:
    cols = st.columns(3)
    for index, img_name in enumerate(all_saved_imgs):
      col = cols[index % 3]
      img_path = os.path.join(IMAGE_DIR, img_name)
      with col:
        st.image(
            img_path,
            caption=img_name.split("_", 1)[-1],
            use_container_width=True,
        )
