import streamlit as st
import pandas as pd
from PIL import Image
import json
import io
from google import genai
from google.genai import types

# 页面基础配置
st.set_page_config(page_title="LOL 内战战绩统计看板", page_icon="🎮", layout="wide")
st.title("🎮 英雄联盟结算截图智能统计看板")

# 侧边栏：API Key 配置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("输入你的 Gemini API Key", type="password", key="api_key")
    if st.button("清空所有累计战绩"):
        st.session_state.game_records = []
        st.rerun()

# 初始化 session 存储
if "game_records" not in st.session_state:
    st.session_state.game_records = []

# 定义结构化 JSON Schema
lol_schema = {
    "type": "OBJECT",
    "properties": {
        "winning_team": {
            "type": "STRING",
            "enum": ["BLUE", "RED", "UNKNOWN"],
            "description": "胜利方队伍，若无法判断填 UNKNOWN"
        },
        "players": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "player_name": {"type": "STRING", "description": "玩家ID/召唤师名称"},
                    "champion": {"type": "STRING", "description": "使用的英雄名字"},
                    "team": {"type": "STRING", "enum": ["BLUE", "RED"], "description": "所属阵营：蓝方或红方"},
                    "kills": {"type": "INTEGER", "description": "击杀数"},
                    "deaths": {"type": "INTEGER", "description": "死亡数"},
                    "assists": {"type": "INTEGER", "description": "助攻数"},
                    "is_winner": {"type": "BOOLEAN", "description": "该玩家所在队伍是否获胜"}
                },
                "required": ["player_name", "champion", "team", "kills", "deaths", "assists", "is_winner"]
            }
        }
    },
    "required": ["winning_team", "players"]
}

def analyze_screenshot(image_bytes, key):
    client = genai.Client(api_key=key)
    prompt = (
        "这是一张英雄联盟的战绩结算界面截图。"
        "请准确识别出所有的玩家名称（注意生僻字与特殊符号）、所选英雄、阵营（蓝方/红方）、"
        "击杀/死亡/助攻（KDA）以及整场胜负。严格按照提供的 JSON Schema 格式输出。"
    )
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=lol_schema,
            temperature=0.1
        )
    )
    return json.loads(response.text)

# 主界面：上传文件
uploaded_files = st.file_uploader("上传对局结算截图（支持同时上传多张）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files and api_key:
    if st.button("开始识别并计入排行榜"):
        with st.spinner("AI 正在逐张解析战绩图片，请稍候..."):
            for uploaded_file in uploaded_files:
                img_bytes = uploaded_file.read()
                try:
                    result = analyze_screenshot(img_bytes, api_key)
                    st.session_state.game_records.append(result)
                    st.success(f"文件 {uploaded_file.name} 解析成功！")
                except Exception as e:
                    st.error(f"解析 {uploaded_file.name} 失败: {str(e)}")

# 战绩汇总与榜单渲染
if st.session_state.game_records:
    player_stats = {}
    for record in st.session_state.game_records:
        for p in record.get("players", []):
            name = p["player_name"].strip()
            if not name:
                continue
            if name not in player_stats:
                player_stats[name] = {"总场次": 0, "胜场": 0, "负场": 0, "总击杀": 0, "总死亡": 0, "总助攻": 0}
            
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
    df["KDA"] = ((df["总击杀"] + df["助攻"] if "助攻" in df else df["总击杀"] + df["总助攻"]) / df["总死亡"].replace(0, 1)).round(2)
    
    df["胜率数值"] = df["胜场"] / df["总场次"]
    df = df.sort_values(by=["胜率数值", "总场次"], ascending=[False, False])
    df = df.drop(columns=["胜率数值"])

    st.subheader(f"🏆 玩家胜率与数据榜单（共录入 {len(st.session_state.game_records)} 局）")
    st.dataframe(df, use_container_width=True)
else:
    st.info("请在左侧填入 Gemini API Key，并在上方上传截图开始统计。")
