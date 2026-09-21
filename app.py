import base64
from collections import defaultdict
import difflib
import hashlib
import io
from itertools import combinations
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

try:
    os.makedirs(IMAGE_DIR, exist_ok=True)
except Exception:
    pass

st.set_page_config(
    page_title="LOL内战战绩统计",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏆 英雄联盟内战战绩与羁绊看板")

# ---------------- 核心：名字纠错与模糊匹配 ----------------
KNOWN_PLAYERS = ["千秋种我一栗卿"]

NAME_FIX_MAP = {
    "千秋种我一粟卿": "千秋种我一栗卿",
    "千秋种我一卵卿": "千秋种我一栗卿",
    "千秋种我一桑卿": "千秋种我一栗卿",
    "千秋种我一梁卿": "千秋种我一栗卿",
}

def clean_player_name(raw_name: str) -> str:
    name = str(raw_name).strip()
    if name.startswith("千秋种我") and (name.endswith("卿") or len(name) >= 6):
        return "千秋种我一栗卿"
    for wrong, right in NAME_FIX_MAP.items():
        if wrong in name:
            name = name.replace(wrong, right)
    name = name.replace("一粟卿", "一栗卿").replace("一卵卿", "一栗卿")
    matches = difflib.get_close_matches(name, KNOWN_PLAYERS, n=1, cutoff=0.7)
    if matches:
        return matches[0]
    return name

def calculate_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

# ---------------- 1. 数据持久化 ----------------
def load_all_records():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_record(new_record):
    records = load_all_records()
    records.append(new_record)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存失败: {e}")

def overwrite_all_records(records_list):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(records_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"覆写失败: {e}")

def delete_record_by_index(target_index: int):
    records = load_all_records()
    if 0 <= target_index < len(records):
        removed = records.pop(target_index)
        img_filename = removed.get("image_file")
        if img_filename:
            img_path = os.path.join(IMAGE_DIR, img_filename)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass
        overwrite_all_records(records)
        return True
    return False

def reset_all_records():
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
        except Exception:
            pass
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            file_path = os.path.join(IMAGE_DIR, f)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

def sanitize_database():
    records = load_all_records()
    modified = False
    for r in records:
        for p in r.get("players", []):
            old_name = p.get("player_name", "")
            fixed_name = clean_player_name(old_name)
            if old_name != fixed_name:
                p["player_name"] = fixed_name
                modified = True
    if modified:
        overwrite_all_records(records)
    return modified

# ---------------- 2. Qwen-VL 识别 ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
    client = OpenAI(
        api_key=key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    prompt = """这是掌上英雄联盟App或客户端结算截图。
请精准识别整局胜负（蓝方/红方），以及所有选手ID和击杀/死亡/助攻(K/D/A)。
注意：选手名字有“千秋种我一栗卿”，是“栗”不是“粟”或“卵”。
输出纯JSON：
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
}"""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="qwen-vl-max",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())
            for p in data.get("players", []):
                p["player_name"] = clean_player_name(p.get("player_name", ""))
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

# ---------------- 3. 控制面板 ----------------
with st.sidebar:
    st.title("⚙️ 控制面板")
    default_key = ""
    try:
        if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets:
            default_key = st.secrets["DASHSCOPE_API_KEY"]
    except Exception:
        pass

    api_key = st.text_input("通义千问 API Key", value=default_key, type="password")
    current_records = load_all_records()
    st.metric("收录对局", f"{len(current_records)} 局")

    if current_records:
        json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
        st.download_button("💾 导出备份", data=json_data, file_name="lol_backup.json", mime="application/json")

    with st.expander("📥 导入备份"):
        backup_file = st.file_uploader("选择备份文件", type=["json"], key="up_backup")
        if backup_file and st.button("确认导入", key="btn_restore"):
            try:
                imp = json.load(backup_file)
                if isinstance(imp, list):
                    overwrite_all_records(imp)
                    st.success("恢复成功！")
                    time.sleep(1)
                    st.rerun()
            except Exception as err:
                st.error(f"导入失败: {err}")

    with st.expander("🔒 管理员"):
        admin_pwd = st.text_input("管理员密码", type="password", key="inp_pwd")
        admin_target = "666888"
        try:
            if hasattr(st, "secrets") and "ADMIN_PWD" in st.secrets:
                admin_target = st.secrets["ADMIN_PWD"]
        except Exception:
            pass

        if admin_pwd == admin_target:
            if st.button("🧹 清洗别字", key="btn_clean"):
                if sanitize_database():
                    st.toast("清洗完成！", icon="✨")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.info("数据正常，无别字。")

            if current_records:
                if st.button("⏪ 撤回最近一局", key="btn_undo"):
                    delete_record_by_index(len(current_records) - 1)
                    st.toast("已撤回！")
                    time.sleep(0.8)
                    st.rerun()

                opts = {i: f"第 {i+1} 局" for i in range(len(current_records))}
                sel_idx = st.selectbox("删除对局", options=list(reversed(list(opts.keys()))), format_func=lambda x: opts[x])
                if st.button("❌ 确认删除", key="btn_del"):
                    delete_record_by_index(sel_idx)
                    st.toast("已删除！")
                    time.sleep(0.8)
                    st.rerun()

            if st.button("💣 清空数据", type="primary", key="btn_clear"):
                reset_all_records()
                st.rerun()

# ==================== 顶部：折叠上传区 ====================
if "staging_records" not in st.session_state:
    st.session_state.staging_records = []

expand_upload = len(st.session_state.staging_records) > 0

with st.expander("📤 录入新对局（点击展开）", expanded=expand_upload):
    uploaded_files = st.file_uploader(
        "选择截图或压缩包：",
        type=["png", "jpg", "jpeg", "zip"],
        accept_multiple_files=True,
        key="main_uploader"
    )

    if uploaded_files:
        if not api_key:
            st.warning("⚠️ 请先在侧边栏填入 API Key！")
        else:
            btn_start = st.button("🚀 开始解析", type="primary", key="btn_ai_run")
            if btn_start:
                images_to_process = []
                for f in uploaded_files:
                    file_bytes = f.getvalue()
                    if f.name.lower().endswith(".zip"):
                        try:
                            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                                for zip_info in z.infolist():
                                    if not zip_info.is_dir() and zip_info.filename.lower().endswith(('.png', '.jpg', '.jpeg')) and "__MACOSX" not in zip_info.filename:
                                        img_data = z.read(zip_info.filename)
                                        images_to_process.append((os.path.basename(zip_info.filename), img_data))
                        except Exception as err:
                            st.error(f"解压失败: {err}")
                    else:
                        images_to_process.append((f.name, file_bytes))

                existing_records = load_all_records()
                existing_hashes = {r.get("image_hash") for r in existing_records if "image_hash" in r}

                st.session_state.staging_records = []
                pbar = st.progress(0)
                total = len(images_to_process) if images_to_process else 1

                for idx, (img_name, img_bytes) in enumerate(images_to_process):
                    img_hash = calculate_md5(img_bytes)
                    if img_hash in existing_hashes:
                        st.warning(f"⚠️ {img_name} 已存在，跳过！")
                        pbar.progress((idx + 1) / total)
                        continue

                    with st.spinner(f"解析中 ({idx + 1}/{total}): {img_name}"):
                        try:
                            result = analyze_screenshot(img_bytes, api_key)
                            item_data = {
                                "filename": img_name,
                                "image_bytes": img_bytes,
                                "image_hash": img_hash,
                                "winning_team": result.get("winning_team", "BLUE"),
                                "players": result.get("players", [])
                            }
                            st.session_state.staging_records.append(item_data)
                        except Exception as e:
                            st.error(f"❌ {img_name} 出错: {e}")
                    pbar.progress((idx + 1) / total)

                if st.session_state.staging_records:
                    st.success(f"🎉 成功解析 {len(st.session_state.staging_records)} 局！")
                    time.sleep(0.5)
                    st.rerun()

    # 复核交互表格
    if st.session_state.staging_records:
        st.markdown("---")
        st.markdown("#### 🔍 识别结果复核与修改")
        for i, item in enumerate(st.session_state.staging_records):
