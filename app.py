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
  # 阿里云百炼兼容 OpenAI SDK 接口地址
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
          model="qwen-vl-max",  # 阿里云百炼旗舰视觉大模型
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
    if admin_pwd == "666888":
      if current_records:
        if st.button("⏪ 撤回最近的一局"):
          delete_record_by_index(len(current_records) - 1)
          st.toast("已撤回最新对局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

        corr_options = {
            i: f"第 {i + 1} 局" for i in range(len(current_records))
        }
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
        reset_all_records()
        st.rerun()
    elif admin_pwd:
      st.error("密码错误")

# ---------------- 4. 截图上传与解析 ----------------
uploaded_files = st.file_uploader(
    "📤 上传对局战绩截图（支持多张全选拖入，或直接上传 .zip 文件夹）",
    type=["png", "jpg", "jpeg", "zip"],
    accept_multiple_files=True,
)

if uploaded_files:
  if not api_key:
    st.warning("⚠️ 请先在左侧侧边栏填入通义千问 API Key！")
  else:
    if st.button("🚀 开始解析并计入胜率", type="primary"):
      images_to_process = []
      for file in uploaded_files:
        file_bytes = file.read()
        if file.name.lower().endswith(".zip"):
          try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
              for zip_info in z.infolist():
                if not zip_info.is_dir() and zip_info.filename.lower().endswith(
                    (".png", ".jpg", ".jpeg")
                ):
                  img_data = z.read(zip_info.filename)
                  if "__MACOSX" not in zip_info.filename:
                    images_to_process.append(
                        (os.path.basename(zip_info.filename), img_data)
                    )
          except Exception as e:
            st.error(f"❌ 读取压缩包 {file.name} 失败: {e}")
        else:
          images_to_process.append((file.name, file_bytes))

      success_count = 0
      skip_count = 0
      existing_records = load_all_records()
      existing_hashes = {
          r.get("image_hash") for r in existing_records if "image_hash" in r
      }
      pbar = st.progress(0)
      total = len(images_to_process)

      for idx, (img_name, img_bytes) in enumerate(images_to_process):
        img_hash = calculate_md5(img_bytes)

        if img_hash in existing_hashes:
          st.warning(f"⚠️ {img_name} 此前已录入，已自动跳过！")
          skip_count += 1
          pbar.progress((idx + 1) / total)
          continue

        with st.spinner(f"正在分析 ({idx + 1}/{total}): {img_name}..."):
          try:
            result = analyze_screenshot(img_bytes, api_key)
            saved_file_name = f"{int(time.time())}_{img_hash[:8]}.jpg"
            with open(os.path.join(IMAGE_DIR, saved_file_name), "wb") as f:
              f.write(img_bytes)

            result["image_hash"] = img_hash
            result["image_file"] = saved_file_name
            result["uploaded_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

            save_record(result)
            existing_hashes.add(img_hash)
            success_count += 1
            time.sleep(0.3)
          except Exception as e:
            st.error(f"❌ {img_name} 录入失败: {e}")
        pbar.progress((idx + 1) / total)

      if success_count > 0:
        st.success(f"🎉 成功录入 {success_count} 局战绩！(跳过重复 {skip_count} 张)")
        time.sleep(1)
        st.rerun()

st.markdown("---")

# ---------------- 5. 纯净胜率总榜展示 ----------------
records = load_all_records()

st.subheader("📊 玩家胜率与战绩总榜")

if not records:
  st.info("💡 暂无历史对局数据。请在上方上传截图开始统计！")
else:
  player_stats = defaultdict(
      lambda: {
          "总场次": 0,
          "胜场": 0,
          "负场": 0,
          "总击杀": 0,
          "总死亡": 0,
          "总助攻": 0,
      }
  )

  for r in records:
    for p in r.get("players", []):
      name = clean_player_name(p.get("player_name", ""))
      if not name:
        continue
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

  df["win_rate_num"] = df["胜场"] / df["总场次"]
  df = df.sort_values(
      by=["win_rate_num", "总场次", "KDA"], ascending=[False, False, False]
  )
  df = df.drop(columns=["win_rate_num"])

  st.dataframe(df, use_container_width=True)
