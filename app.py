import os
import json
import hashlib
import time
import base64
import difflib
import re
import random
from io import BytesIO
from itertools import combinations
from collections import defaultdict
import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI

DATA_FILE = "records.json"
CONFIG_FILE = "config.json"
TARGET_QIANQIU = "千秋种我一栗卿#52652"

st.set_page_config(page_title="海克斯内战", page_icon="⚔️", layout="wide")

# ---------------- 高级深海蓝微光 + 全局组件与标签美化 CSS ----------------
st.markdown("""
<style>
/* 全局背景：明朗高级的深海宝石蓝流光渐变 */
.stApp {
    background: radial-gradient(circle at 50% 5%, #1d3e63 0%, #122841 50%, #0a192b 100%) !important;
    color: #e2e8f0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 顶部主标题 */
h1 {
    background: linear-gradient(90deg, #ffffff 0%, #a5f3fc 50%, #fef08a 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 800 !important;
    letter-spacing: 1.5px !important;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}
h2, h3 {
    color: #f8fafc !important;
    letter-spacing: 0.8px;
}

/* 侧边栏底色 */
section[data-testid="stSidebar"] {
    background-color: #0b1726 !important;
    border-right: 1px solid rgba(56, 189, 248, 0.2) !important;
}
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: #fef08a !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #f1f5f9 !important;
}

/* 侧边栏交互输入框与下拉框 */
section[data-testid="stSidebar"] input {
    background-color: #132438 !important;
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-radius: 6px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="input"],
section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
    background-color: #132438 !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] div[data-baseweb="base-input"] input {
    background-color: transparent !important;
    color: #ffffff !important;
    border: none !important;
}
section[data-testid="stSidebar"] div[data-baseweb="base-input"] button {
    background-color: transparent !important;
    border: none !important;
}
section[data-testid="stSidebar"] div[data-baseweb="base-input"] svg {
    fill: #38bdf8 !important;
    color: #38bdf8 !important;
}

/* ================= 核心修复：彻底消灭多选框红底，换为电竞微光蓝 ================= */
div[data-baseweb="select"] {
    background-color: #132438 !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-radius: 8px !important;
}
div[data-baseweb="select"] > div {
    background-color: #132438 !important;
    border: none !important;
}
/* 多选标签 (Tag) 彻底消灭红色 */
div[data-baseweb="tag"],
span[data-baseweb="tag"] {
    background: rgba(14, 165, 233, 0.25) !important;
    background-color: rgba(14, 165, 233, 0.25) !important;
    border: 1px solid rgba(56, 189, 248, 0.6) !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    padding: 3px 8px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}
div[data-baseweb="tag"] span,
span[data-baseweb="tag"] span {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
div[data-baseweb="tag"] svg,
span[data-baseweb="tag"] svg {
    fill: #38bdf8 !important;
    color: #38bdf8 !important;
}
div[data-baseweb="tag"]:hover {
    background: rgba(14, 165, 233, 0.4) !important;
    border-color: #38bdf8 !important;
}

/* ================= 全局按钮组件修复 ================= */
/* 次级普通按钮（如随机盲盒按钮） */
button[data-testid="stBaseButton-secondary"] {
    background: rgba(19, 36, 56, 0.85) !important;
    background-color: rgba(19, 36, 56, 0.85) !important;
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.6) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    backdrop-filter: blur(10px) !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background: #1e3d63 !important;
    background-color: #1e3d63 !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.6) !important;
}
button[data-testid="stBaseButton-secondary"] * {
    color: #ffffff !important;
    fill: #ffffff !important;
    font-weight: 700 !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* 主操作按钮（Primary Button） */
button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.8) !important;
    box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4) !important;
    font-weight: 700 !important;
}
button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.7) !important;
    border-color: #a5f3fc !important;
}

/* 语音作战室三大专属微光按钮 */
div[data-testid="stLinkButton"] a {
    border-radius: 10px !important;
    font-weight: 700 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: blur(12px) !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
div[data-testid="stLinkButton"] a:hover {
    transform: translateY(-2px);
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, rgba(234, 179, 8, 0.25), rgba(202, 138, 4, 0.15)) !important;
    border: 1px solid rgba(253, 224, 71, 0.5) !important;
    box-shadow: 0 4px 15px rgba(234, 179, 8, 0.2) !important;
    color: #fef9c3 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(234, 179, 8, 0.4) !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.35), rgba(2, 132, 199, 0.2)) !important;
    border: 1px solid rgba(56, 189, 248, 0.7) !important;
    box-shadow: 0 4px 18px rgba(14, 165, 233, 0.35) !important;
    color: #f0f9ff !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 24px rgba(56, 189, 248, 0.6) !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, rgba(244, 63, 94, 0.35), rgba(225, 29, 72, 0.2)) !important;
    border: 1px solid rgba(251, 113, 133, 0.7) !important;
    box-shadow: 0 4px 18px rgba(244, 63, 94, 0.3) !important;
    color: #fff1f2 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 24px rgba(251, 113, 133, 0.55) !important;
}

/* 独立电竞磨砂卡片系统 */
.esport-card {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 12px;
    padding: 14px 18px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-bottom: 12px;
}
.esport-card:hover {
    transform: translateY(-3px);
    background: rgba(255, 255, 255, 0.13);
    border-color: rgba(56, 189, 248, 0.6);
    box-shadow: 0 12px 30px rgba(14, 165, 233, 0.25);
}
.esport-card-title {
    font-size: 0.92rem;
    font-weight: 800;
    color: #ffffff;
    text-shadow: 0 0 10px #eab308, 0 0 18px rgba(234, 179, 8, 0.6), 1px 1px 2px #000000;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}
.esport-card-player {
    font-size: 1.22rem;
    font-weight: 800;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 6px;
}
.esport-card-delta {
    font-size: 0.82rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-block;
    width: fit-content;
}
.delta-cyan {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
}
.delta-gold {
    background: rgba(254, 240, 138, 0.15);
    color: #fef08a;
    border: 1px solid rgba(254, 240, 138, 0.3);
}
.delta-red {
    background: rgba(251, 113, 133, 0.15);
    color: #fb7185;
    border: 1px solid rgba(251, 113, 133, 0.3);
}
.delta-gray {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.3);
}

/* ================= 红蓝对阵分队看板 ================= */
.team-arena-container {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(20px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
    margin-top: 10px;
    margin-bottom: 25px;
}
.team-column-blue {
    background: linear-gradient(180deg, rgba(14, 165, 233, 0.18) 0%, rgba(15, 23, 42, 0.4) 100%);
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(14, 165, 233, 0.15);
}
.team-column-red {
    background: linear-gradient(180deg, rgba(244, 63, 94, 0.18) 0%, rgba(15, 23, 42, 0.4) 100%);
    border: 1px solid rgba(251, 113, 133, 0.4);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(244, 63, 94, 0.15);
}
.team-header-title {
    font-size: 1.15rem;
    font-weight: 800;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
}
.blue-title {
    color: #38bdf8;
    border-bottom: 2px solid rgba(56, 189, 248, 0.4);
}
.red-title {
    color: #fb7185;
    border-bottom: 2px solid rgba(251, 113, 133, 0.4);
}
.team-roster-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    transition: all 0.2s ease;
}
.team-roster-item:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(2px);
}
.player-tag {
    font-weight: 700;
    color: #ffffff;
    font-size: 1.02rem;
}
.player-score-badge {
    font-size: 0.8rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
}
.vs-divider-box {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    padding: 10px 0;
}
.vs-glow-text {
    font-size: 2.2rem;
    font-weight: 900;
    font-style: italic;
    background: linear-gradient(180deg, #fef08a 0%, #ea580c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 20px rgba(234, 88, 12, 0.8);
    margin-bottom: 6px;
}

/* 亮感磨砂电竞表格容器 */
.hextech-table-container {
    width: 100%;
    overflow-x: auto;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 12px;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    margin-top: 10px;
    margin-bottom: 25px;
}
.hextech-table {
    width: 100%;
    border-collapse: collapse;
    color: #f1f5f9;
    font-size: 0.95rem;
    text-align: center;
}
.hextech-table th {
    background: rgba(23, 49, 77, 0.8);
    color: #fef08a;
    font-weight: 700;
    letter-spacing: 0.6px;
    padding: 14px 10px;
    border-bottom: 2px solid rgba(255, 255, 255, 0.15);
}
.hextech-table td {
    padding: 13px 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    transition: background 0.2s;
}
.hextech-table tr:hover td {
    background: rgba(56, 189, 248, 0.12) !important;
}
.hextech-table tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.03);
}
.hextech-badge-win {
    color: #38bdf8;
    font-weight: 700;
    text-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
}
.hextech-badge-loss {
    color: #fb7185;
    font-weight: 700;
}
.hextech-player-name {
    text-align: left;
    padding-left: 20px !important;
    font-weight: 600;
    color: #ffffff;
}

/* 底部上传框磨砂优化 */
div[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.06) !important;
    border-radius: 10px !important;
    border: 1px dashed rgba(255, 255, 255, 0.3) !important;
    backdrop-filter: blur(12px) !important;
    padding: 12px !important;
}
</style>
""", unsafe_allow_html=True)


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
        "red_voice": "https://kook.top/"
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
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        try:
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception:
            return ""

# ---------------- 1. 名字清洗与归一 ----------------
def clean_player_name_strict(name: str) -> str:
    if not name:
        return ""
    s = re.sub(r'[\s\u200b\ufeff\u3000\r\n\t]+', '', str(name))
    s = s.replace("＃", "#").replace("—", "-").replace("–", "-")
    
    if ("千秋" in s) or ("52652" in s) or ("一栗卿" in s) or ("一粟卿" in s) or ("栗卿" in s) or ("粟卿" in s):
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
        timeout=40.0
    )
    b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    prompt = (
        "这是英雄联盟掌盟战绩结算截图。\n"
        "请识别整局胜负（BLUE或RED），以及全部10位玩家的游戏ID与KDA数值。\n"
        "不要识别英雄。\n"
        "请严格输出合法JSON：\n"
        '{"winning_team": "BLUE", "players": [{"player_name": "ID", "team": "BLUE", "kills": 0, "deaths": 0, "assists": 0, "is_winner": true}]}'
    )
    
    resp = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    raw = resp.choices[0].message.content.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    clean_str = match.group(0) if match else raw
    return json.loads(clean_str)

def short_name(full_name):
    if not full_name:
        return "未知"
    return full_name.split("#")[0]

# ---------------- 侧边栏（管理 + 对局图文核对） ----------------
with st.sidebar:
    st.header("⚙️ 系统管理")
    default_key = st.secrets.get("DASHSCOPE_API_KEY", "") if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets else ""
    key = st.text_input("DashScope API Key", value=default_key, type="password", help="sk- 开头的密钥")

    records = load_records()
    st.metric("总计收录对局", f"{len(records)} 局")

    # 逐局图文核对
    if records:
        st.markdown("---")
        st.subheader("🔍 对局图文核对")
        game_options = [f"第 {i+1} 局 ({r.get('winning_team', '未知')}方胜)" for i, r in enumerate(records)]
        selected_idx = st.selectbox("选择要核对的场次", range(len(records)), format_func=lambda i: game_options[i])
        
        curr_record = records[selected_idx]
        
        thumb_b64 = curr_record.get("image_thumb", "")
        if thumb_b64:
            st.image(f"data:image/jpeg;base64,{thumb_b64}", caption=f"第 {selected_idx + 1} 局原始结算图", use_container_width=True)
        else:
            st.caption("ℹ️ 此历史记录无缓存截图。")
        
        p_rows = []
        for p in curr_record.get("players", []):
            p_rows.append({
                "阵营": p.get("team", ""),
                "玩家ID": short_name(p.get("player_name", "")),
                "K/D/A": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                "胜负": "胜" if p.get("is_winner") else "负"
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
            save_config({"main_voice": new_main, "blue_voice": new_blue, "red_voice": new_red})
            st.success("配置已保存！")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.subheader("📦 数据备份与恢复")
    
    if records:
        json_bytes = json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8')
        st.download_button(
            label="💾 导出战绩备份 (JSON)",
            data=json_bytes,
            file_name="lol_records_backup.json",
            mime="application/json",
            help="点击下载备份文件到本地"
        )
    
    with st.expander("📥 导入恢复历史数据"):
        uploaded_backup = st.file_uploader("选择已备份的 JSON 文件", type=["json"], key="backup_uploader")
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
    admin_pwd = st.secrets.get("ADMIN_PASSWORD", "666888") if hasattr(st, "secrets") and "ADMIN_PASSWORD" in st.secrets else "666888"
    pwd = st.text_input("管理密码", type="password")
    if pwd:
        input_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
        target_hash = hashlib.sha256(admin_pwd.encode('utf-8')).hexdigest()
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
st.title("⚔️ 海克斯内战")

cfg = load_config()
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("🎙️ 进入大厅语音", cfg.get("main_voice", "https://kook.top/"), use_container_width=True)
with c2:
    st.link_button("🔵 进蓝方作战室", cfg.get("blue_voice", "https://kook.top/"), use_container_width=True)
with c3:
    st.link_button("🔴 进红方作战室", cfg.get("red_voice", "https://kook.top/"), use_container_width=True)

st.caption("💡 微信内无法直接拉起语音？请点击右上角「···」，选择「在浏览器打开」即可一键进麦。")

st.write("")

# ---------------- 主界面 2：趣味头衔、单人巅峰、双人羁绊、智能分队与胜率总榜 ----------------
records = load_records()

if not records:
    st.info("💡 暂无对局数据。请在页面底部上传战绩截图；若之前导出过备份，可在左侧侧边栏导入恢复。")
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

    stats = defaultdict(lambda: {
        "总场次": 0, "胜场": 0, "负场": 0,
        "击杀": 0, "死亡": 0, "助攻": 0
    })

    # 同队搭档统计
    synergy_stats = defaultdict(lambda: {"同队场次": 0, "胜场": 0, "负场": 0})
    # 宿敌对战统计（分属蓝红两队正面交手）
    nemesis_stats = defaultdict(lambda: {"交手场次": 0, "p1_wins": 0, "p2_wins": 0})

    # 单场巅峰记录追踪
    max_single_kill = {"player": "", "val": -1, "game_idx": 0}
    max_single_death = {"player": "", "val": -1, "game_idx": 0}
    max_single_assist = {"player": "", "val": -1, "game_idx": 0}

    for game_idx, r in enumerate(records):
        blue_team = []
        red_team = []
        
        for p in r.get("players", []):
            raw_pname = p.get("player_name", "")
            if not raw_pname:
                continue
            fname = get_final_name(raw_pname)

            kills = int(p.get("kills", 0))
            deaths = int(p.get("deaths", 0))
            assists = int(p.get("assists", 0))

            stats[fname]["总场次"] += 1
            is_win = bool(p.get("is_winner"))
            if is_win:
                stats[fname]["胜场"] += 1
            else:
                stats[fname]["负场"] += 1
            stats[fname]["击杀"] += kills
            stats[fname]["死亡"] += deaths
            stats[fname]["助攻"] += assists

            # 单场巅峰数值更新
            if kills > max_single_kill["val"]:
                max_single_kill = {"player": fname, "val": kills, "game_idx": game_idx + 1}
            if deaths > max_single_death["val"]:
                max_single_death = {"player": fname, "val": deaths, "game_idx": game_idx + 1}
            if assists > max_single_assist["val"]:
                max_single_assist = {"player": fname, "val": assists, "game_idx": game_idx + 1}

            team_side = str(p.get("team", "")).upper()
            if team_side == "BLUE":
                blue_team.append((fname, is_win))
            elif team_side == "RED":
                red_team.append((fname, is_win))

        # 1. 统计同队搭档
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

        # 2. 统计对手宿敌（蓝方成员 vs 红方成员）
        blue_unique = list({item[0]: item[1] for item in blue_team}.items())
        red_unique = list({item[0]: item[1] for item in red_team}.items())
        for (pb, b_win) in blue_unique:
            for (pr, _) in red_unique:
                if pb == pr:
                    continue
                p1, p2 = sorted([pb, pr])
                nemesis_stats[(p1, p2)]["交手场次"] += 1
                if (pb == p1 and b_win) or (pr == p1 and not b_win):
                    nemesis_stats[(p1, p2)]["p1_wins"] += 1
                else:
                    nemesis_stats[(p1, p2)]["p2_wins"] += 1

    df = pd.DataFrame.from_dict(stats, orient="index")

    if not df.empty:
        df["胜率_num"] = (df["胜场"] / df["总场次"] * 100).round(1)
        df["KD"] = (df["击杀"] / df["死亡"].replace(0, 1)).round(2)
        df["KDA_num"] = ((df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)).round(2)
        df["场均击杀"] = (df["击杀"] / df["总场次"]).round(1)

        # 战力分 (MMR) 科学重构模型（保护尽力局大腿）
        def calculate_mmr_v2(row):
            if row["总场次"] < 2:
                return 50.0
            avg_k = float(row["场均击杀"])
            kill_score = min(avg_k / 10.0, 1.2) * 35.0
            kda_val = float(row["KDA_num"])
            kda_score = min(kda_val / 5.0, 1.2) * 35.0
            wr_val = float(row["胜率_num"])
            wr_score = (wr_val / 100.0) * 30.0
            total_mmr = kill_score + kda_score + wr_score
            if avg_k >= 7.0 and kda_val >= 2.5:
                total_mmr += 5.0
            return round(total_mmr, 1)

        df["MMR"] = df.apply(calculate_mmr_v2, axis=1)

        # ---------------- 板块 A：单场巅峰纪录 (3 列) ----------------
        st.subheader("🔥 单场最高纪录")
        col_peak1, col_peak2, col_peak3 = st.columns(3)
        with col_peak1:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">单场最高击杀</div>
                    <div class="esport-card-player">{short_name(max_single_kill['player'])}</div>
                    <div class="esport-card-delta delta-gold">{max_single_kill['val']} 杀 (第 {max_single_kill['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)
        with col_peak2:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">单场最高阵亡</div>
                    <div class="esport-card-player">{short_name(max_single_death['player'])}</div>
                    <div class="esport-card-delta delta-red">{max_single_death['val']} 阵亡 (第 {max_single_death['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)
        with col_peak3:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">单场最高助攻</div>
                    <div class="esport-card-player">{short_name(max_single_assist['player'])}</div>
                    <div class="esport-card-delta delta-cyan">{max_single_assist['val']} 助攻 (第 {max_single_assist['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)

        st.write("")

        # ---------------- 板块 B：综合荣誉头衔 (4 列，严格 >= 10 局门槛) ----------------
        st.subheader("🎖️ 综合荣誉头衔 (≥10局)")
        candidates_10 = df[df["总场次"] >= 10]
        has_veteran = not candidates_10.empty

        if has_veteran:
            top_kda_name = candidates_10.sort_values(by="KDA_num", ascending=False).index[0]
            top_kill_name = candidates_10.sort_values(by="击杀", ascending=False).index[0]
            top_death_name = candidates_10.sort_values(by="死亡", ascending=False).index[0]
            top_assist_name = candidates_10.sort_values(by="助攻", ascending=False).index[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if has_veteran:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">KDA王</div>
                        <div class="esport-card-player">{short_name(top_kda_name)}</div>
                        <div class="esport-card-delta delta-cyan">KDA {df.loc[top_kda_name, 'KDA_num']}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">KDA王</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">需出场满 10 局</div>
                    </div>
                """, unsafe_allow_html=True)
        with col2:
            if has_veteran:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">累计击杀王</div>
                        <div class="esport-card-player">{short_name(top_kill_name)}</div>
                        <div class="esport-card-delta delta-gold">{int(df.loc[top_kill_name, '击杀'])} 杀</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">累计击杀王</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">需出场满 10 局</div>
                    </div>
                """, unsafe_allow_html=True)
        with col3:
            if has_veteran:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">累计白给王</div>
                        <div class="esport-card-player">{short_name(top_death_name)}</div>
                        <div class="esport-card-delta delta-red">{int(df.loc[top_death_name, '死亡'])} 阵亡</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">累计白给王</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">需出场满 10 局</div>
                    </div>
                """, unsafe_allow_html=True)
        with col4:
            if has_veteran:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">累计助攻王</div>
                        <div class="esport-card-player">{short_name(top_assist_name)}</div>
                        <div class="esport-card-delta delta-cyan">{int(df.loc[top_assist_name, '助攻'])} 助攻</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">累计助攻王</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">需出场满 10 局</div>
                    </div>
                """, unsafe_allow_html=True)

        st.write("")

        # ---------------- 板块 C：羁绊看板 (3 列，严格 >= 5 局门槛) ----------------
        st.subheader("🔗 阵营羁绊与宿敌")
        syn_list = []
        for (p1, p2), v in synergy_stats.items():
            t_games = int(v["同队场次"])
            w_games = int(v["胜场"])
            l_games = int(v["负场"])
            wr = (w_games / t_games) if t_games > 0 else 0
            syn_list.append({
                "pair_name": f"{short_name(p1)} & {short_name(p2)}",
                "games": t_games,
                "wins": w_games,
                "losses": l_games,
                "win_rate": wr
            })
        
        syn_df = pd.DataFrame(syn_list)
        best_pair, worst_pair = None, None
        if not syn_df.empty:
            syn_candidates = syn_df[syn_df["games"] >= 5]
            if not syn_candidates.empty:
                best_pair = syn_candidates.sort_values(by=["win_rate", "games"], ascending=[False, False]).iloc[0]
                worst_pair = syn_candidates.sort_values(by=["win_rate", "games"], ascending=[True, False]).iloc[0]

        nem_list = []
        for (p1, p2), v in nemesis_stats.items():
            t_games = int(v["交手场次"])
            p1_w = int(v["p1_wins"])
            p2_w = int(v["p2_wins"])
            if t_games > 0:
                if p1_w >= p2_w:
                    winner, loser = p1, p2
                    w_cnt, l_cnt = p1_w, p2_w
                else:
                    winner, loser = p2, p1
                    w_cnt, l_cnt = p2_w, p1_w
                
                dom_rate = w_cnt / t_games
                diff = abs(p1_w - p2_w)
                nem_list.append({
                    "display_name": f"{short_name(winner)} ➔ {short_name(loser)}",
                    "games": t_games,
                    "wins": w_cnt,
                    "losses": l_cnt,
                    "dom_rate": dom_rate,
                    "diff": diff
                })

        nem_df = pd.DataFrame(nem_list)
        rival_pair = None
        if not nem_df.empty:
            nem_candidates = nem_df[nem_df["games"] >= 5]
            if not nem_candidates.empty:
                rival_pair = nem_candidates.sort_values(by=["dom_rate", "diff", "games"], ascending=[False, False, False]).iloc[0]

        col_syn1, col_syn2, col_syn3 = st.columns(3)
        with col_syn1:
            if best_pair is not None:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">黄金搭档 (≥5局)</div>
                        <div class="esport-card-player">{best_pair['pair_name']}</div>
                        <div class="esport-card-delta delta-cyan">{int(best_pair['wins'])}胜{int(best_pair['losses'])}负 ({round(best_pair['win_rate']*100, 1)}%)</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">黄金搭档 (≥5局)</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">暂无同队满 5 局的搭档</div>
                    </div>
                """, unsafe_allow_html=True)
        with col_syn2:
            if worst_pair is not None:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">难兄难弟 (≥5局)</div>
                        <div class="esport-card-player">{worst_pair['pair_name']}</div>
                        <div class="esport-card-delta delta-red">{int(worst_pair['wins'])}胜{int(worst_pair['losses'])}负 ({round(worst_pair['win_rate']*100, 1)}%)</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">难兄难弟 (≥5局)</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">暂无同队满 5 局的搭档</div>
                    </div>
                """, unsafe_allow_html=True)
        with col_syn3:
            if rival_pair is not None:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">一生之敌 (≥5局)</div>
                        <div class="esport-card-player">{rival_pair['display_name']}</div>
                        <div class="esport-card-delta delta-gold">{int(rival_pair['wins'])}胜{int(rival_pair['losses'])}负 ({round(rival_pair['dom_rate']*100, 1)}%压制)</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="esport-card">
                        <div class="esport-card-title">一生之敌 (≥5局)</div>
                        <div class="esport-card-player" style="color:#94a3b8;font-size:1rem;">虚位以待</div>
                        <div class="esport-card-delta delta-gray">暂无交手满 5 局的宿敌</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ---------------- 板块 D：赛前红蓝对阵作战室（极简微光多选 + 临时战力微调） ----------------
        st.subheader("⚔️ 赛前阵营分队系统")
        
        all_known_players = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True)
        default_selection = all_known_players[:10] if len(all_known_players) >= 10 else all_known_players

        # 纯净简短的玩家ID展示（彻底告别一长串胜率战力）
        selected_players = st.multiselect(
            "选择出战群友名单（支持任意人数，如 6人、8人、10人等）：",
            options=all_known_players,
            default=default_selection,
            format_func=lambda x: short_name(x)
        )

        # 临时战力微调器（针对新人、替补或大腿外援）
        if "mmr_override" not in st.session_state:
            st.session_state["mmr_override"] = {}

        if selected_players:
            with st.expander("⚙️ 临时战力设定（针对新人群友/外援大腿）", expanded=False):
                st.caption("💡 默认采用系统根据历史战绩评定的 MMR。如果来了新人或状态特殊，可在这里临时设定分值参与平衡计算：")
                cols = st.columns(min(len(selected_players), 4))
                for i, p in enumerate(selected_players):
                    col_target = cols[i % min(len(selected_players), 4)]
                    curr_val = st.session_state["mmr_override"].get(p, float(df.loc[p, "MMR"]))
                    new_val = col_target.number_input(
                        f"{short_name(p)} 战力",
                        min_value=10.0,
                        max_value=120.0,
                        value=float(curr_val),
                        step=5.0,
                        key=f"mmr_in_{p}"
                    )
                    st.session_state["mmr_override"][p] = new_val

        col_b1, col_b2, _ = st.columns([1.5, 1.5, 3])
        with col_b1:
            balance_btn = st.button("⚖️ 战力天平平衡分配", type="primary", use_container_width=True)
        with col_b2:
            random_btn = st.button("🎲 听天由命随机盲盒", use_container_width=True)

        if "assigned_blue" not in st.session_state:
            st.session_state["assigned_blue"] = []
            st.session_state["assigned_red"] = []
            st.session_state["split_mode"] = ""

        total_chosen = len(selected_players)

        # 获取最终生效战力（优先考虑手动微调设定）
        def get_effective_mmr(player_id):
            return st.session_state.get("mmr_override", {}).get(player_id, float(df.loc[player_id, "MMR"]))

        if balance_btn:
            if total_chosen < 2:
                st.warning("⚠️ 至少需要选择 2 位玩家才能进行对抗分队！")
            else:
                player_list = list(selected_players)
                blue_size = total_chosen // 2
                best_diff = float("inf")
                best_blue = []
                best_red = []

                for candidate_blue in combinations(player_list, blue_size):
                    candidate_red = [p for p in player_list if p not in candidate_blue]
                    m_blue = sum(get_effective_mmr(p) for p in candidate_blue)
                    m_red = sum(get_effective_mmr(p) for p in candidate_red)
                    avg_blue = m_blue / len(candidate_blue)
                    avg_red = m_red / len(candidate_red)
                    
                    diff = abs(avg_blue - avg_red) if total_chosen % 2 != 0 else abs(m_blue - m_red)
                    if diff < best_diff:
                        best_diff = diff
                        best_blue = list(candidate_blue)
                        best_red = list(candidate_red)

                st.session_state["assigned_blue"] = best_blue
                st.session_state["assigned_red"] = best_red
                st.session_state["split_mode"] = f"⚖️ 战力天平最优平衡 ({len(best_blue)}v{len(best_red)})"

        elif random_btn:
            if total_chosen < 2:
                st.warning("⚠️ 至少需要选择 2 位玩家才能进行对抗分队！")
            else:
                shuffled = list(selected_players)
                random.shuffle(shuffled)
                blue_size = total_chosen // 2
                st.session_state["assigned_blue"] = shuffled[:blue_size]
                st.session_state["assigned_red"] = shuffled[blue_size:]
                st.session_state["split_mode"] = f"🎲 听天由命盲盒随机 ({len(st.session_state['assigned_blue'])}v{len(st.session_state['assigned_red'])})"

        # 渲染对阵舞台卡片
        if st.session_state["assigned_blue"] and st.session_state["assigned_red"]:
            blue_team = st.session_state["assigned_blue"]
            red_team = st.session_state["assigned_red"]

            blue_total = round(sum(get_effective_mmr(p) for p in blue_team), 1)
            red_total = round(sum(get_effective_mmr(p) for p in red_team), 1)
            blue_avg = round(blue_total / len(blue_team), 1) if blue_team else 0
            red_avg = round(red_total / len(red_team), 1) if red_team else 0
            diff_score = round(abs(blue_total - red_total), 1)
            avg_diff = round(abs(blue_avg - red_avg), 1)

            st.write("")
            st.caption(f"当前模式：**{st.session_state['split_mode']}** ｜ 双方总战力差：**{diff_score} 分** (人均均分差: **{avg_diff} 分**)")

            blue_items = []
            for p in blue_team:
                p_name = short_name(p)
                p_wr = df.loc[p, "胜率_num"]
                p_mmr = get_effective_mmr(p)
                p_ak = df.loc[p, "场均击杀"]
                blue_items.append(
                    f"<div class='team-roster-item'>"
                    f"<span class='player-tag'>🛡️ {p_name}</span>"
                    f"<span class='player-score-badge' style='background:rgba(56,189,248,0.2);color:#38bdf8;'>战力 {p_mmr} · 场均 {p_ak} 杀 (胜率 {p_wr}%)</span>"
                    f"</div>"
                )

            red_items = []
            for p in red_team:
                p_name = short_name(p)
                p_wr = df.loc[p, "胜率_num"]
                p_mmr = get_effective_mmr(p)
                p_ak = df.loc[p, "场均击杀"]
                red_items.append(
                    f"<div class='team-roster-item'>"
                    f"<span class='player-tag'>⚔️ {p_name}</span>"
                    f"<span class='player-score-badge' style='background:rgba(251,113,133,0.2);color:#fb7185;'>战力 {p_mmr} · 场均 {p_ak} 杀 (胜率 {p_wr}%)</span>"
                    f"</div>"
                )

            arena_html = (
                f"<div class='team-arena-container'>"
                f"<div style='display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;'>"
                f"<div style='flex:1;min-width:280px;' class='team-column-blue'>"
                f"<div class='team-header-title blue-title'>"
                f"<span>🔵 蓝色方 ({len(blue_team)}人)</span><span>均分: {blue_avg}</span>"
                f"</div>"
                f"{''.join(blue_items)}"
                f"</div>"
                f"<div style='flex:0 0 100px;display:flex;align-items:center;justify-content:center;' class='vs-divider-box'>"
                f"<div class='vs-glow-text'>VS</div>"
                f"<span style='font-size:0.78rem;color:#94a3b8;'>均分差 {avg_diff}</span>"
                f"</div>"
                f"<div style='flex:1;min-width:280px;' class='team-column-red'>"
                f"<div class='team-header-title red-title'>"
                f"<span>🔴 红色方 ({len(red_team)}人)</span><span>均分: {red_avg}</span>"
                f"</div>"
                f"{''.join(red_items)}"
                f"</div>"
                f"</div>"
                f"</div>"
            )

            st.markdown(arena_html, unsafe_allow_html=True)

            copy_text = (
                f"【海克斯内战·双方对阵阵容】\n"
                f"🔵 蓝方 ({len(blue_team)}人 | 均分{blue_avg}): {'、'.join([short_name(p) for p in blue_team])}\n"
                f"🔴 红方 ({len(red_team)}人 | 均分{red_avg}): {'、'.join([short_name(p) for p in red_team])}\n"
                f"⚡ 阵型模式: {st.session_state['split_mode']} | 均分分差: {avg_diff}"
            )
            st.text_area("📋 微信/群聊对战名单复制：", value=copy_text, height=100)

        st.markdown("---")
        st.subheader("📊 胜率总榜")

        # 排序
        df = df.sort_values(by=["胜率_num", "总场次", "KDA_num"], ascending=[False, False, False])

        # 亮感磨砂电竞表格拼接（严格保持行首无多余空格缩进，避免 Markdown 代码块白底陷阱）
        table_rows = []
        for player_id, row in df.iterrows():
            wr_val = row["胜率_num"]
            wr_badge = f"<span class='hextech-badge-win'>{wr_val}%</span>" if wr_val >= 50 else f"<span class='hextech-badge-loss'>{wr_val}%</span>"
            kd_str = f"{row['KD']:.2f}"
            kda_str = f"{row['KDA_num']:.2f}"
            mmr_val = f"{row['MMR']:.1f}"
            avg_kill_str = f"{row['场均击杀']:.1f}"
            p_name = short_name(player_id)

            total_games = int(row['总场次'])
            wins = int(row['胜场'])
            losses = int(row['负场'])
            kills = int(row['击杀'])
            deaths = int(row['死亡'])
            assists = int(row['助攻'])

            row_html = (
                f"<tr>"
                f"<td class='hextech-player-name'>{p_name}</td>"
                f"<td>{total_games}</td>"
                f"<td>{wins}</td>"
                f"<td>{losses}</td>"
                f"<td>{wr_badge}</td>"
                f"<td style='color:#a5f3fc;font-weight:700;'>{mmr_val}</td>"
                f"<td style='color:#fde047;font-weight:700;'>{avg_kill_str}</td>"
                f"<td style='color:#38bdf8;font-weight:700;'>{kd_str}</td>"
                f"<td style='color:#fef08a;font-weight:700;'>{kda_str}</td>"
                f"<td>{kills}</td>"
                f"<td>{deaths}</td>"
                f"<td>{assists}</td>"
                f"</tr>"
            )
            table_rows.append(row_html)

        custom_table_html = (
            f'<div class="hextech-table-container">'
            f'<table class="hextech-table">'
            f'<thead><tr>'
            f'<th style="text-align:left;padding-left:20px;">玩家</th>'
            f'<th>总场次</th><th>胜场</th><th>负场</th><th>胜率</th>'
            f'<th>战力(MMR)</th><th>场均击杀</th><th>KD比</th><th>KDA</th><th>击杀</th><th>死亡</th><th>助攻</th>'
            f'</tr></thead>'
            f'<tbody>{"".join(table_rows)}</tbody>'
            f'</table></div>'
        )

        st.markdown(custom_table_html, unsafe_allow_html=True)

# ---------------- 主界面 3：战绩上传窗口（置底） ----------------
st.markdown("---")
st.subheader("📥 战绩录入")

with st.form("upload_box", clear_on_submit=False):
    files = st.file_uploader("选择或拖拽战绩截图（支持批量多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
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
            status_box.info(f"⏳ 正在分析第 {idx+1}/{len(files)} 张: {file.name}")
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
                        p["player_name"] = clean_player_name_strict(p.get("player_name", ""))
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
