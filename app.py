import io
import json
import os
from google import genai
from google.genai import types
import pandas as pd
from PIL import Image
import streamlit as st

# 数据库文件路径（永久保存在服务器）
DATA_FILE = "records.json"

st.set_page_config(
    page_title="LOL 内战战绩看板",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🎮 英雄联盟对局结算智能统计看板")


# ---------------- 1. 持久化数据读取与保存 ----------------
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


# ---------------- 2. Gemini 识别 Schema ----------------
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


def analyze_screenshot(image_bytes, key):
    client = genai.Client(api_key=key)
    prompt = (
        "这是一张英雄联盟的战绩结算界面截图。"
        "请精准识别所有玩家名称（包括中英文符号）、所选英雄、阵营（蓝方/红方）、"
        "击杀/死亡/助攻（K/D/A）以及整场胜负。严格按照 JSON Schema 格式输出。"
    )
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=lol_schema,
            temperature=0.1,
        ),
    )
    return json.loads(response.text)


# ---------------- 3. 侧边栏配置与管理 ----------------
with st.sidebar:
    st.header("⚙️ 核心设置")
    # 优先使用 Streamlit Secrets，若未设置则让用户手动输入
    default_key = (
        st.secrets.get("GEMINI_API_KEY", "")
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets
        else ""
    )
    api_key = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        help="在 Google AI Studio 申请的免费 API Key",
    )

    st.markdown("---")
    st.header("📂 历史数据管理")
    current_records = load_all_records()
    st.metric("已永久累计录入对局", f"{len(current_records)} 局")

    if current_records:
        # 下载数据备份功能
        json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 导出历史战绩备份",
            data=json_data,
            file_name="lol_match_history.json",
            mime="application/json",
        )

    if st.button("🗑️ 清空所有历史数据", type="primary"):
        reset_all_records()
        st.toast("已清空所有历史对局！", icon="🧹")
        st.rerun()


# ---------------- 4. 战绩统计与榜单生成函数 ----------------
def render_leaderboard(records):
    if not records:
        st.info("💡 暂无历史对局数据。请在上方上传截图开始累计！")
        return

    player_stats = {}
    for record in records:
        for p in record.get("players", []):
            name = p.get("player_name", "").strip()
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

    # 生成排行榜数据表
    df = pd.DataFrame.from_dict(player_stats, orient="index")
    df["胜率"] = (df["胜场"] / df["总场次"] * 100).round(1).astype(str) + "%"
    df["K/D"] = (df["总击杀"] / df["总死亡"].replace(0, 1)).round(2)
    df["KDA"] = (
        (df["总击杀"] + df["总助攻"]) / df["总死亡"].replace(0, 1)
    ).round(2)

    # 排序：胜率最高排前面，胜率相同按场次排
    df["win_ratio"] = df["胜场"] / df["总场次"]
    df = df.sort_values(by=["win_ratio", "总场次"], ascending=[False, False])
    df = df.drop(columns=["win_ratio"])

    # 渲染
    st.subheader(f"🏆 玩家全员胜率榜单（累计收录 {len(records)} 局）")
    st.dataframe(df, use_container_width=True)


# ---------------- 5. 主页面：上传与即时刷新 ----------------
uploaded_files = st.file_uploader(
    "📤 上传结算截图（支持单张或批量拖入）",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files:
    if not api_key:
        st.warning("⚠️ 请先在左侧侧边栏填入你的 Gemini API Key！")
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
                        save_record(result)  # 实时写入硬盘文件
                        success_count += 1
                    except Exception as e:
                        st.error(f"❌ 解析 {file.name} 失败: {str(e)}")
                progress_bar.progress((idx + 1) / total)

            if success_count > 0:
                st.success(f"🎉 成功解析并永久存储了 {success_count} 局战绩！")
                st.rerun()  # 触发即时重新渲染，榜单秒刷新

# 默认展示当前最新榜单
st.markdown("---")
render_leaderboard(load_all_records())
