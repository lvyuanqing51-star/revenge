import base64
import hashlib
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


# 计算文件唯一 MD5 指纹（去重核心）
def calculate_md5(data: bytes) -> str:
  return hashlib.md5(data).hexdigest()


# ---------------- 1. 数据读写与管理函数 ----------------
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
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(records_list, f, ensure_ascii=False, indent=2)


def delete_record_by_index(target_index: int):
  """删除指定索引的一局，同时清理对应的关联图片"""
  records = load_all_records()
  if 0 <= target_index < len(records):
    removed = records.pop(target_index)
    # 尝试同步删除图片文件
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
          model="deepseek-flash",
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


# ---------------- 3. 侧边栏配置与管理控制台 ----------------
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

  # 导出备份
  if current_records:
    json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 导出战绩备份 (JSON)",
        data=json_data,
        file_name="lol_match_backup.json",
        mime="application/json",
        help="定期备份，防止云端重启",
    )

  # 导入备份
  with st.expander("📥 导入战绩备份"):
    backup_file = st.file_uploader(
        "选择 JSON 备份文件", type=["json"], key="backup_uploader"
    )
    if backup_file is not None:
      try:
        imported_data = json.load(backup_file)
        if isinstance(imported_data, list):
          if st.button("⚡ 确认恢复该备份数据", type="primary"):
            overwrite_all_records(imported_data)
            st.success(f"已恢复 {len(imported_data)} 局数据！")
            time.sleep(1)
            st.rerun()
        else:
          st.error("备份数据格式不符合要求")
      except Exception as err:
        st.error(f"读取失败: {err}")

  st.markdown("---")
  # ---------------- 管理员面板：精准删除与撤销 ----------------
  with st.expander("🔒 管理员控制台（删除/撤回）"):
    admin_pwd = st.text_input(
        "管理员密码",
        type="password",
        key="admin_pwd",
        help="默认密码 666888",
    )

    if admin_pwd == "666888":
      st.caption("✅ 身份验证通过")

      # 功能 1：一键撤销最新一局
      if current_records:
        if st.button("⏪ 撤销最新录入的一局"):
          last_idx = len(current_records) - 1
          delete_record_by_index(last_idx)
          st.toast("已成功撤销最新一局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

      # 功能 2：下拉精准删除指定对局
      if current_records:
        st.markdown("##### 🎯 精准删除指定对局")
        options = {}
        for i, r in enumerate(current_records):
          win_team = "蓝方胜" if r.get("winning_team") == "BLUE" else "红方胜"
          # 提取 2 位代表玩家名字做摘要
          player_sample = " / ".join(
              [p.get("player_name", "") for p in r.get("players", [])[:2]]
          )
          desc = f"第 {i + 1} 局 | {win_team} | {player_sample}..."
          options[i] = desc

        # 倒序显示，最新局排在最上面方便找
        selected_idx = st.selectbox(
            "选择要删除的对局",
            options=list(reversed(list(options.keys()))),
            format_func=lambda x: options[x],
        )

        if st.button("❌ 确认删除选中的这局", type="secondary"):
          delete_record_by_index(selected_idx)
          st.toast(f"已删除：{options[selected_idx]}", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

      st.divider()
      # 功能 3：彻底清空全部
      if st.button("💣 清空所有数据与截图", type="primary"):
        reset_all_records()
        st.toast("已全部清空！", icon="🧹")
        time.sleep(0.8)
        st.rerun()

    elif admin_pwd:
      st.error("密码错误，权限拒绝")


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


# ---------------- 5. 智能查重上传区 ----------------
uploaded_files = st.file_uploader(
    "📤 上传结算截图（支持多张拖入，已开启自动去重防翻倍）",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files:
  if not api_key:
    st.warning("⚠️ 请先在左侧输入你的 DeepSeek API Key！")
  else:
    if st.button("🚀 开始解析并录入", type="primary"):
      success_count = 0
      skip_count = 0
      progress_bar = st.progress(0)
      total = len(uploaded_files)

      # 收集现有已存记录的所有图片 MD5，用于秒级去重
      existing_records = load_all_records()
      existing_hashes = {
          r.get("image_hash") for r in existing_records if "image_hash" in r
      }

      for idx, file in enumerate(uploaded_files):
        img_bytes = file.read()
        img_hash = calculate_md5(img_bytes)

        # 1. 指纹查重判断：如果已经录过完全相同的图片，直接跳过并省下 API 调用
        if img_hash in existing_hashes:
          st.warning(
              f"⚠️ 跳过重复图片: 【{file.name}】 之前已经录入过，无需重复统计！"
          )
          skip_count += 1
          progress_bar.progress((idx + 1) / total)
          continue

        with st.spinner(f"正在识别 ({idx + 1}/{total}): {file.name}..."):
          try:
            result = analyze_screenshot(img_bytes, api_key)

            # 关联保存图片文件与哈希指纹
            saved_file_name = f"{int(time.time())}_{img_hash[:8]}.jpg"
            save_path = os.path.join(IMAGE_DIR, saved_file_name)
            with open(save_path, "wb") as img_file:
              img_file.write(img_bytes)

            result["image_hash"] = img_hash
            result["image_file"] = saved_file_name
            result["uploaded_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

            save_record(result)
            existing_hashes.add(img_hash)  # 防止同批次内也有重复图
            success_count += 1
            time.sleep(0.5)
          except Exception as e:
            st.error(f"❌ 解析 {file.name} 失败: {str(e)}")

        progress_bar.progress((idx + 1) / total)

      if success_count > 0:
        st.success(f"🎉 成功录入 {success_count} 局战绩！(跳过重复 {skip_count} 张)")
        time.sleep(1)
        st.rerun()
      elif skip_count > 0:
        st.info("上传的所有图片此前均已录入，未增加任何重复数据。")

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
