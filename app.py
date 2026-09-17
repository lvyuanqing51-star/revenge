import io
import json
import os
import time
from google import genai
from google.genai import errors
from google.genai import types
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
st.title("🎮 英雄联盟对局结算智能统计看板")

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


# ---------------- 1. 持久化存储函数 ----------------
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


def reset_all_records():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            file_path = os.path.join(IMAGE_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)


# ---------------- 2. 识别 Schema ----------------
lol_schema = {
    "type": "OBJECT",
    "properties": {
        "winning_team": {
            "type": "STRING",
            "enum": ["BLUE", "RED", "UNKNOWN"],
            "description": "胜利方队伍",
        },
        "players": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "player_name": {
                        "type": "STRING",
                        "description": "玩家ID/游戏名称",
                    },
                    "champion": {
                        "type": "STRING",
                        "description": "英雄名称",
                    },
                    "team": {
                        "type": "STRING",
                        "enum": ["BLUE", "RED"],
                        "description": "所属阵营",
                    },
                    "kills": {"type": "INTEGER", "description": "击杀数"},
                    "deaths": {"type": "INTEGER", "description": "死亡数"},
                    "assists": {"type": "INTEGER", "description": "助攻数"},
                    "is_winner": {
                        "type": "BOOLEAN",
                        "description": "该玩家是否获胜",
                    },
                },
                "required": [
                    "player_name",
                    "champion",
                    "team",
                    "kills",
                    "deaths",
                    "assists",
                    "is_winner",
                ],
            },
        },
    },
    "required": ["winning_team", "players"],
}


# ---------------- 3. 带自动重试机制的 AI 识别 ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
    client = genai.Client(api_key=key)
    prompt = (
        "这是一张英雄联盟的战绩结算界面截图。"
        "请精准识别所有玩家名称（包括中英文符号，注意区分'栗'与'粟'等形近字）、所选英雄、阵营（蓝方/红方）、"
        "击杀/死亡/助攻（K/D/A）以及整场胜负。严格按照 JSON Schema 格式输出。"
    )

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=lol_schema,
                ),
            )
            return json.loads(response.text)
        except errors.APIError as e:
            if e.code in [503, 429] and attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            raise e
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            raise e


# ---------------- 4. 侧边栏配置（已严格对齐缩进与密码保护） ----------------
with st.sidebar:
    st.header("⚙️ 核心设置")
    default_key = (
        st.secrets.get("GEMINI_API_KEY", "")
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets
        else ""
    )
    api_key = st.text_input("Gemini API Key", value=default_key, type="password")

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

    if current_records:
        json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 导出战绩 JSON",
            data=json_data,
            file_name="lol_match_history.json",
            mime="application/json",
        )

    st.markdown("---")
    # 管理员折叠面板：只有输入正确密码才会展示清空按钮
    with st.expander("🔒 管理员功能（危险操作）"):
        admin_pwd = st.text_input(
            "输入管理密码",
            type="password",
            key="admin_pwd",
            help="防止他人误清空数据",
        )
        # 默认管理密码设为 666888，你可以根据需要修改
        if admin_pwd == "666888":
            if st.button("🗑️ 确认清空所有数据与原图", type="primary"):
                reset_all_records()
                st.toast("已清空所有历史数据和截图！", icon="🧹")
                st.rerun()
        elif admin_pwd:
            st.error("密码错误，无法清空")


# ---------------- 5. 榜单渲染 ----------------
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


# ---------------- 6. 主界面上传与即时刷新 ----------------
uploaded_files = st.file_uploader(
    "📤 上传结算截图（支持单张或批量拖入）",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files:
    if not api_key:
        st.warning("⚠️ 请先在左侧输入你的 Gemini API Key！")
    else:
        if st.button("🚀 开始解析并录入", type="primary"):
            success_count = 0
            progress_bar = st.progress(0)
            total = len(uploaded_files)

            for idx, file in enumerate(uploaded_files):
                with st.spinner(f"正在识别 ({idx + 1}/{total}): {file.name}..."):
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
                        time.sleep(1)
                    except Exception as e:
                        st.error(f"❌ 解析 {file.name} 失败: {str(e)}")
                progress_bar.progress((idx + 1) / total)

            if success_count > 0:
                st.success(f"🎉 成功录入 {success_count} 局战绩并归档原图！")
                st.rerun()

st.markdown("---")
render_leaderboard(load_all_records())

# ---------------- 7. 历史截图展示区 ----------------
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
