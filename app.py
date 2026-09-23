import os
import json
import hashlib
import time
import base64
import difflib
import re
import random
import math
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

st.set_page_config(
    page_title="海克斯内战·Hex League",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- 专业电竞级·现代化淡粉 UI 变量与组件样式 ----------------
st.markdown("""
<style>
:root, [data-theme="light"], .stApp {
    --primary-color: #f43f5e !important;
}

.stApp {
    background: radial-gradient(circle at top right, #fff1f2 0%, #fff5f5 40%, #ffe4e6 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 顶部导航控制台 */
.app-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid #fecdd3;
    border-radius: 16px;
    padding: 14px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(244, 63, 94, 0.08);
}
.header-title {
    font-size: 1.55rem;
    font-weight: 900;
    background: linear-gradient(90deg, #e11d48 0%, #db2777 50%, #9333ea 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 8px;
}
.header-sub {
    font-size: 0.82rem;
    color: #9f1239;
    font-weight: 600;
    margin-top: 2px;
}

/* 现代化卡片容器 */
.card-panel {
    background: #ffffff;
    border: 1px solid #fecdd3;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(244, 114, 182, 0.07);
    transition: all 0.25s ease;
}
.card-panel:hover {
    box-shadow: 0 6px 20px rgba(244, 63, 94, 0.12);
    border-color: #fb7185;
}

.panel-header-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #881337;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 指标卡系统 */
.metric-stat-box {
    background: #ffffff;
    border: 1px solid #fecdd3;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 2px 8px rgba(244, 114, 182, 0.06);
    transition: transform 0.2s ease;
}
.metric-stat-box:hover {
    transform: translateY(-2px);
    border-color: #f43f5e;
}
.metric-title { font-size: 0.82rem; font-weight: 700; color: #9f1239; margin-bottom: 4px; }
.metric-val-main { font-size: 1.35rem; font-weight: 900; color: #1e293b; }
.metric-badge {
    font-size: 0.78rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-block;
    margin-top: 4px;
}
.badge-pink { background: #ffe4e6; color: #e11d48; }
.badge-gold { background: #fef9c3; color: #ca8a04; }
.badge-blue { background: #e0f2fe; color: #0284c7; }
.badge-gray { background: #f1f5f9; color: #64748b; }

/* 标签与勋章 */
.badge-tag {
    display: inline-block;
    background: #fff1f2;
    border: 1px solid #fecdd3;
    color: #9f1239;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 8px;
    margin: 3px 6px 3px 0;
    box-shadow: 0 1px 3px rgba(244, 114, 182, 0.1);
    cursor: help;
    transition: all 0.2s ease;
}
.badge-tag:hover {
    background: #ffe4e6;
    border-color: #fb7185;
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(244, 63, 94, 0.2);
}

.rule-chip-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff1f2;
    border: 1px solid #fecdd3;
    border-radius: 8px;
    padding: 6px 12px;
    margin-bottom: 6px;
    font-size: 0.86rem;
}

/* 标签栏美化 (st.tabs) */
div[data-baseweb="tab-list"] {
    gap: 8px !important;
    background: transparent !important;
    border-bottom: 2px solid #fecdd3 !important;
    margin-bottom: 20px !important;
}
div[data-baseweb="tab"] {
    background: #ffffff !important;
    border: 1px solid #fbcfe8 !important;
    border-bottom: none !important;
    border-radius: 10px 10px 0 0 !important;
    color: #881337 !important;
    font-weight: 700 !important;
    padding: 8px 18px !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="tab"]:hover {
    background: #fff1f2 !important;
    color: #e11d48 !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #fff1f2 0%, #ffffff 100%) !important;
    color: #e11d48 !important;
    border-top: 3px solid #e11d48 !important;
    border-left: 1px solid #fecdd3 !important;
    border-right: 1px solid #fecdd3 !important;
}

/* 表格全局定制 */
.clean-table-box {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #fecdd3;
    border-radius: 12px;
    background: #ffffff;
    margin: 12px 0 20px 0;
    box-shadow: 0 4px 14px rgba(244, 114, 182, 0.06);
}
.clean-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
    text-align: center;
    color: #334155;
}
.clean-table th {
    background: #fff1f2;
    color: #9f1239;
    font-weight: 700;
    padding: 12px 10px;
    border-bottom: 2px solid #fecdd3;
}
.clean-table td {
    padding: 10px 8px;
    border-bottom: 1px solid #fff1f2;
}
.clean-table tr:hover td {
    background: #fff8f8;
}

/* 多选框粉晶化 */
div[data-baseweb="tag"],
span[data-baseweb="tag"],
div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background: #fce7f3 !important;
    background-color: #fce7f3 !important;
    border: 1px solid #f472b6 !important;
    border-radius: 6px !important;
    margin: 2px 4px !important;
}
div[data-baseweb="tag"] *,
div[data-testid="stMultiSelect"] [data-baseweb="tag"] * {
    color: #9d174d !important;
    font-weight: 700 !important;
    fill: #db2777 !important;
}

/* 按钮通用 */
button[data-testid="stBaseButton-primary"], button[kind="primary"] {
    background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%) !important;
    border: 1px solid #fb7185 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 12px rgba(244, 63, 94, 0.28) !important;
}
button[data-testid="stBaseButton-secondary"] {
    background: #ffffff !important;
    border: 1px solid #fbcfe8 !important;
    color: #be185d !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: #f43f5e !important;
    background: #fff1f2 !important;
}

/* 侧边栏微调 */
section[data-testid="stSidebar"] {
    background: #fff8f8 !important;
    border-right: 1px solid #fecdd3 !important;
}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    color: #881337 !important;
    font-size: 1.05rem !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- 0. 基础配置与图片压缩 ----------------
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
            if difflib.SequenceMatcher(None, cleaned, cluster).ratio() >= 0.88:
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
        "这是英雄联盟掌盟对局结算截图。\n"
        "请识别整局胜负（BLUE或RED），以及全部10位玩家的游戏ID、KDA数值。\n"
        "若截图中有输出占比（例如 25% 或 25.4%）或承伤占比，请一并识别提取为数值（无百分号，如 25.4）。若截图中未显示输出或承伤占比，对应字段填 null。\n"
        "请严格输出合法JSON：\n"
        '{"winning_team": "BLUE", "players": [{"player_name": "ID", "team": "BLUE", "kills": 0, "deaths": 0, "assists": 0, "damage_share": 24.5, "taken_share": 20.1, "is_winner": true}]}'
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
    return str(full_name).split("#")[0]

# ---------------- 2. 原生 SVG 六边形雷达生成器 ----------------
def generate_radar_svg(values, categories):
    size = 320
    cx, cy, r = size / 2, size / 2, 105
    total = len(values)
    grid_polys = []
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(total):
            angle = math.pi / 2 - (2 * math.pi * i / total)
            x = cx + r * level * math.cos(angle)
            y = cy - r * level * math.sin(angle)
            pts.append(f"{x:.1f},{y:.1f}")
        grid_polys.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#fecdd3" stroke-width="1.2" stroke-dasharray="3,3"/>')
    axis_lines = []
    labels = []
    for i in range(total):
        angle = math.pi / 2 - (2 * math.pi * i / total)
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#fecdd3" stroke-width="1.2"/>')
        tx = cx + (r + 26) * math.cos(angle)
        ty = cy - (r + 14) * math.sin(angle)
        labels.append(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="11" font-weight="700" fill="#9f1239" text-anchor="middle" dominant-baseline="central">{categories[i]}</text>')
    data_pts = []
    data_dots = []
    for i in range(total):
        val_ratio = min(max(values[i], 12.0), 100.0) / 100.0
        angle = math.pi / 2 - (2 * math.pi * i / total)
        dx = cx + r * val_ratio * math.cos(angle)
        dy = cy - r * val_ratio * math.sin(angle)
        data_pts.append(f"{dx:.1f},{dy:.1f}")
        data_dots.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="4" fill="#be185d"/>')
    polygon_svg = f'<polygon points="{" ".join(data_pts)}" fill="rgba(244, 63, 94, 0.28)" stroke="#e11d48" stroke-width="2.5"/>'
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;padding:6px 0;">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="max-width:100%;height:auto;display:block;">
            {''.join(grid_polys)}
            {''.join(axis_lines)}
            {polygon_svg}
            {''.join(data_dots)}
            {''.join(labels)}
        </svg>
    </div>
    """

# ---------------- 侧边栏：模块化工作台 ----------------
with st.sidebar:
    st.markdown("### 🎛️ 系统控制台")
    default_key = st.secrets.get("DASHSCOPE_API_KEY", "") if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets else ""
    key = st.text_input("DashScope API Key", value=default_key, type="password", placeholder="sk-...")

    records = load_records()
    total_games_all = len(records)

    st.markdown("---")
    st.markdown("#### ⚡ 智能数据工具")
    if records:
        if st.button("🔄 一键重新扫描历史截图", help="使用新 Prompt 提取输出与承伤占比并补齐到数据库", use_container_width=True):
            if not key:
                st.warning("请先在上方填入 DashScope API Key！")
            else:
                p_bar = st.progress(0)
                st_msg = st.empty()
                success_n = 0
                for idx, r in enumerate(records):
                    st_msg.info(f"重新解析第 {idx+1}/{len(records)} 局...")
                    thumb_b64 = r.get("image_thumb", "")
                    if thumb_b64:
                        try:
                            img_b = base64.b64decode(thumb_b64)
                            new_res = analyze_image(img_b, key)
                            p_map = {clean_player_name_strict(p["player_name"]): p for p in new_res.get("players", [])}
                            for old_p in r.get("players", []):
                                c_name = clean_player_name_strict(old_p.get("player_name", ""))
                                if c_name in p_map:
                                    old_p["damage_share"] = p_map[c_name].get("damage_share")
                                    old_p["taken_share"] = p_map[c_name].get("taken_share")
                            success_n += 1
                        except Exception as e:
                            st.error(f"第 {idx+1} 局失败: {e}")
                    p_bar.progress((idx + 1) / len(records))
                save_records(records)
                st_msg.empty()
                st.success(f"成功更新 {success_n} 局！")
                time.sleep(0.5)
                st.rerun()

    with st.expander("💾 数据备份与恢复"):
        if records:
            json_bytes = json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8')
            st.download_button(
                label="📤 导出完整数据 (JSON)",
                data=json_bytes,
                file_name="lol_records_backup.json",
                mime="application/json",
                use_container_width=True
            )
        uploaded_backup = st.file_uploader("导入备份文件", type=["json"], key="backup_uploader")
        if uploaded_backup is not None and st.button("📥 恢复数据", type="primary", use_container_width=True):
            try:
                imported_data = json.load(uploaded_backup)
                if isinstance(imported_data, list):
                    save_records(imported_data)
                    st.success("恢复成功！")
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                st.error(f"导入失败: {e}")

    if records:
        with st.expander("🔍 历史对局图文复盘"):
            game_options = [f"第 {i+1} 局 ({r.get('winning_team', '未知')}方胜)" for i, r in enumerate(records)]
            selected_idx = st.selectbox("选择对局", range(len(records)), format_func=lambda i: game_options[i])
            curr_record = records[selected_idx]
            thumb_b64 = curr_record.get("image_thumb", "")
            if thumb_b64:
                st.image(f"data:image/jpeg;base64,{thumb_b64}", caption=f"第 {selected_idx + 1} 局战绩图", use_container_width=True)
            p_rows = []
            for p in curr_record.get("players", []):
                dmg_s = f"{p.get('damage_share')}%" if p.get('damage_share') is not None else "--"
                p_rows.append({
                    "阵营": p.get("team", ""),
                    "玩家": short_name(p.get("player_name", "")),
                    "KDA": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                    "伤害": dmg_s
                })
            if p_rows:
                st.dataframe(pd.DataFrame(p_rows), hide_index=True)
            if st.button("🗑️ 删除该局", key=f"del_game_{selected_idx}", use_container_width=True):
                records.pop(selected_idx)
                save_records(records)
                st.success("已删除该局！")
                time.sleep(0.3)
                st.rerun()

    with st.expander("🎙️ 语音房链接配置"):
        cfg = load_config()
        new_main = st.text_input("大厅主语音", value=cfg.get("main_voice", ""))
        new_blue = st.text_input("🔵 蓝方语音", value=cfg.get("blue_voice", ""))
        new_red = st.text_input("🔴 红方语音", value=cfg.get("red_voice", ""))
        if st.button("💾 保存链接", use_container_width=True):
            save_config({"main_voice": new_main, "blue_voice": new_blue, "red_voice": new_red})
            st.success("已保存！")
            time.sleep(0.3)
            st.rerun()

# ---------------- 主界面 1：顶栏吸顶电竞控制台 ----------------
cfg = load_config()
st.markdown(f"""
<div class="app-header-bar">
    <div>
        <div class="header-title">⚔️ 海克斯内战 · 数据中心</div>
        <div class="header-sub">HEX LEAGUE ANALYTICS CONSOLE</div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
        <span class="badge-tag" style="background:#ffffff;margin:0;">📦 已收录 <b>{total_games_all}</b> 场对局</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 顶部三大语音室微光直达通道
vc1, vc2, vc3 = st.columns(3)
with vc1:
    st.link_button("🎙️ 大厅语音作战室", cfg.get("main_voice", "https://kook.top/"), use_container_width=True)
with vc2:
    st.link_button("🔵 蓝方语音作战室", cfg.get("blue_voice", "https://kook.top/"), use_container_width=True)
with vc3:
    st.link_button("🔴 红方语音作战室", cfg.get("red_voice", "https://kook.top/"), use_container_width=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ---------------- 数据清洗与统计算法引擎 ----------------
all_raw = []
for r in records:
    for p in r.get("players", []):
        raw_name = p.get("player_name", "")
        if raw_name:
            all_raw.append(raw_name)

name_mapping = build_canonical_name_map(list(set(all_raw)))

def get_final_name(pname):
    strict_name = clean_player_name_strict(pname)
    fname = name_mapping.get(pname, strict_name)
    if strict_name == TARGET_QIANQIU or "千秋" in fname:
        return TARGET_QIANQIU
    return fname

stats = defaultdict(lambda: {
    "总场次": 0, "胜场": 0, "负场": 0, "击杀": 0, "死亡": 0, "助攻": 0,
    "damage_shares": [], "taken_shares": [], "team_kill_shares": [], "kp_shares": []
})

radar_stats_pool = defaultdict(lambda: {
    "games_6p": 0, "kills": 0, "deaths": 0, "assists": 0,
    "damage_shares": [], "taken_shares": [], "kp_shares": []
})

player_history = defaultdict(lambda: {
    "outcomes": [], 
    "max_kill": 0,
    "max_death": 0,
    "max_assist": 0,
    "max_dmg_share": 0.0,
    "max_taken_share": 0.0,
    "min_death_win": 999,
    "svp_cnt": 0
})

synergy_stats = defaultdict(lambda: {"同队场次": 0, "胜场": 0, "负场": 0})
nemesis_stats = defaultdict(lambda: {"交手场次": 0, "p1_wins": 0, "p2_wins": 0})

max_single_kill = {"player": "", "val": -1, "game_idx": 0}
max_single_death = {"player": "", "val": -1, "game_idx": 0}
max_single_assist = {"player": "", "val": -1, "game_idx": 0}

for game_idx, r in enumerate(records):
    players_in_game = r.get("players", [])
    is_valid_6p_game = len(players_in_game) >= 6

    blue_team, red_team = [], []
    blue_total_k, red_total_k = 0, 0
    blue_total_d, red_total_d = 0, 0
    
    for p in players_in_game:
        side = str(p.get("team", "")).upper()
        k, d = int(p.get("kills", 0)), int(p.get("deaths", 0))
        if side == "BLUE":
            blue_total_k += k; blue_total_d += d
        elif side == "RED":
            red_total_k += k; red_total_d += d

    for p in players_in_game:
        raw_pname = p.get("player_name", "")
        if not raw_pname:
            continue
        fname = get_final_name(raw_pname)
        k, d, a = int(p.get("kills", 0)), int(p.get("deaths", 0)), int(p.get("assists", 0))
        is_win = bool(p.get("is_winner"))
        side = str(p.get("team", "")).upper()
        team_k = blue_total_k if side == "BLUE" else red_total_k

        stats[fname]["总场次"] += 1
        stats[fname]["胜场" if is_win else "负场"] += 1
        stats[fname]["击杀"] += k
        stats[fname]["死亡"] += d
        stats[fname]["助攻"] += a

        dmg_s, taken_s = p.get("damage_share"), p.get("taken_share")
        player_history[fname]["outcomes"].append(is_win)

        if is_valid_6p_game:
            if k > player_history[fname]["max_kill"]: player_history[fname]["max_kill"] = k
            if d > player_history[fname]["max_death"]: player_history[fname]["max_death"] = d
            if a > player_history[fname]["max_assist"]: player_history[fname]["max_assist"] = a
            if is_win and d < player_history[fname]["min_death_win"]: player_history[fname]["min_death_win"] = d

            ds_val = float(dmg_s) if dmg_s is not None else 0.0
            if (not is_win) and (ds_val >= 35.0 or k >= 11):
                player_history[fname]["svp_cnt"] += 1

            if ds_val > player_history[fname]["max_dmg_share"]:
                player_history[fname]["max_dmg_share"] = ds_val
            if taken_s is not None:
                try:
                    ts_val = float(taken_s)
                    if ts_val > player_history[fname]["max_taken_share"]:
                        player_history[fname]["max_taken_share"] = ts_val
                except Exception:
                    pass

            radar_stats_pool[fname]["games_6p"] += 1
            radar_stats_pool[fname]["kills"] += k
            radar_stats_pool[fname]["deaths"] += d
            radar_stats_pool[fname]["assists"] += a

            if dmg_s is not None:
                try: radar_stats_pool[fname]["damage_shares"].append(float(dmg_s))
                except Exception: pass
            if taken_s is not None:
                try: radar_stats_pool[fname]["taken_shares"].append(float(taken_s))
                except Exception: pass
            if team_k > 0:
                radar_stats_pool[fname]["kp_shares"].append((k + a) / team_k)

        if k > max_single_kill["val"]: max_single_kill = {"player": fname, "val": k, "game_idx": game_idx + 1}
        if d > max_single_death["val"]: max_single_death = {"player": fname, "val": d, "game_idx": game_idx + 1}
        if a > max_single_assist["val"]: max_single_assist = {"player": fname, "val": a, "game_idx": game_idx + 1}

        if side == "BLUE": blue_team.append((fname, is_win))
        elif side == "RED": red_team.append((fname, is_win))

    for t in [blue_team, red_team]:
        members = list({item[0]: item[1] for item in t}.items())
        if len(members) >= 2:
            for (p1, win1), (p2, _) in combinations(members, 2):
                pair_key = tuple(sorted([p1, p2]))
                synergy_stats[pair_key]["同队场次"] += 1
                synergy_stats[pair_key]["胜场" if win1 else "负场"] += 1

    b_u = list({item[0]: item[1] for item in blue_team}.items())
    r_u = list({item[0]: item[1] for item in red_team}.items())
    for (pb, b_win) in b_u:
        for (pr, _) in r_u:
            if pb == pr: continue
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

    def calculate_mmr(row):
        if row["总场次"] < 2: return 50.0
        avg_k = float(row["场均击杀"])
        kill_score = min(avg_k / 10.0, 1.2) * 35.0
        kda_val = float(row["KDA_num"])
        kda_score = min(kda_val / 5.0, 1.2) * 35.0
        wr_score = (float(row["胜率_num"]) / 100.0) * 30.0
        total_mmr = kill_score + kda_score + wr_score
        if avg_k >= 7.0 and kda_val >= 2.5: total_mmr += 5.0
        return round(total_mmr, 1)

    df["MMR"] = df.apply(calculate_mmr, axis=1)

# ---------------- 主界面 2：多 Tab 视图架构 ----------------
tab_match, tab_ladder, tab_radar, tab_upload = st.tabs([
    "⚔️ 赛前阵营分队系统",
    "📊 胜率天梯与荣誉榜",
    "🎯 局内战术图谱与成就馆",
    "📥 战绩智能录入"
])

# ==========================================
# Tab 1: 赛前阵营分队系统
# ==========================================
with tab_match:
    if df.empty:
        st.info("💡 暂无选手历史数据，请先录入对局战绩。")
    else:
        if "custom_guests" not in st.session_state:
            st.session_state["custom_guests"] = {}
        for k, v in list(st.session_state["custom_guests"].items()):
            if not isinstance(v, dict):
                st.session_state["custom_guests"][k] = {"mmr": float(v), "tier": "临时外援"}

        known_roster = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True)
        full_options = known_roster + list(st.session_state["custom_guests"].keys())
        default_selection = known_roster[:10] if len(known_roster) >= 10 else known_roster

        st.markdown('<div class="card-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header-title">👥 出战名单挑选与替补录入</div>', unsafe_allow_html=True)
        selected_players = st.multiselect(
            "选择今晚出战群友名单（支持任意人数）：",
            options=full_options,
            default=default_selection,
            format_func=lambda x: short_name(x)
        )

        cg1, cg2, cg3 = st.columns([3, 3, 1.5])
        with cg1:
            guest_name = st.text_input("外援/替补昵称", placeholder="临时外援昵称...", key="in_guest_name", label_visibility="collapsed")
        with cg2:
            guest_tier = st.selectbox(
                "外援实力评级",
                options=[80.0, 60.0, 45.0],
                format_func=lambda v: {80.0: "👑 通天大腿 (80分)", 60.0: "🛡️ 普通水平 (60分)", 45.0: "🌱 萌新挂件 (45分)"}[v],
                index=1,
                key="sel_guest_tier",
                label_visibility="collapsed"
            )
        with cg3:
            if st.button("➕ 录入外援", key="btn_add_g", use_container_width=True):
                if guest_name.strip():
                    c_name = guest_name.strip()
                    tier_label = {80.0: "通天大腿", 60.0: "普通水平", 45.0: "萌新挂件"}[guest_tier]
                    st.session_state["custom_guests"][c_name] = {"mmr": guest_tier, "tier": tier_label}
                    st.success(f"已录入: {c_name}")
                    time.sleep(0.3)
                    st.rerun()

        if st.session_state["custom_guests"]:
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            for g_name, g_info in list(st.session_state["custom_guests"].items()):
                mmr_val = g_info.get("mmr", 60.0) if isinstance(g_info, dict) else float(g_info)
                tier_str = g_info.get("tier", "外援") if isinstance(g_info, dict) else "外援"
                col_i, col_d = st.columns([5, 1])
                with col_i:
                    st.caption(f"👤 **{g_name}** · 战力分: {mmr_val} ({tier_str})")
                with col_d:
                    if st.button("🗑️ 移除", key=f"del_g_{g_name}"):
                        del st.session_state["custom_guests"][g_name]
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 人情世故与宿敌锁定器
        if "lock_rules" not in st.session_state:
            st.session_state["lock_rules"] = []

        with st.expander("🔗 人情世故与宿敌羁绊绑定 (可选 - 强制同队 / 强制对立)"):
            c_rule_a, c_rule_b, c_rule_btn1, c_rule_btn2 = st.columns([2.5, 2.5, 2, 2])
            with c_rule_a:
                rule_p1 = st.selectbox("选手 A", options=selected_players, format_func=lambda x: short_name(x), key="sel_rule_p1")
            with c_rule_b:
                rem_options = [p for p in selected_players if p != rule_p1]
                rule_p2 = st.selectbox("选手 B", options=rem_options, format_func=lambda x: short_name(x), key="sel_rule_p2") if rem_options else None
            
            with c_rule_btn1:
                if st.button("🔗 锁定同队", use_container_width=True):
                    if rule_p1 and rule_p2:
                        st.session_state["lock_rules"] = [r for r in st.session_state["lock_rules"] if not ({r["p1"], r["p2"]} == {rule_p1, rule_p2})]
                        st.session_state["lock_rules"].append({"type": "same", "p1": rule_p1, "p2": rule_p2})
                        st.rerun()
            with c_rule_btn2:
                if st.button("⚔️ 锁定对立", use_container_width=True):
                    if rule_p1 and rule_p2:
                        st.session_state["lock_rules"] = [r for r in st.session_state["lock_rules"] if not ({r["p1"], r["p2"]} == {rule_p1, rule_p2})]
                        st.session_state["lock_rules"].append({"type": "diff", "p1": rule_p1, "p2": rule_p2})
                        st.rerun()

            if st.session_state["lock_rules"]:
                st.markdown("<div style='margin-top:10px;font-size:0.86rem;font-weight:700;color:#9f1239;'>已生效的规则列表：</div>", unsafe_allow_html=True)
                del_idx_target = None
                for idx, r in enumerate(st.session_state["lock_rules"]):
                    lbl_text = "🔗 必须同队 (连体)" if r["type"] == "same" else "⚔️ 必须对立 (宿敌)"
                    lbl_color = "#e11d48" if r["type"] == "same" else "#0284c7"
                    col_txt, col_del = st.columns([5, 1])
                    with col_txt:
                        st.markdown(f"<div class='rule-chip-card'><span>👤 <b>{short_name(r['p1'])}</b> <span style='color:{lbl_color};font-weight:800;margin:0 4px;'>{lbl_text}</span> 👤 <b>{short_name(r['p2'])}</b></span></div>", unsafe_allow_html=True)
                    with col_del:
                        if st.button("❌", key=f"del_rule_{idx}", use_container_width=True):
                            del_idx_target = idx

                if del_idx_target is not None:
                    st.session_state["lock_rules"].pop(del_idx_target)
                    st.rerun()

                if st.button("🗑️ 清空所有规则", key="btn_clear_all_rules"):
                    st.session_state["lock_rules"] = []
                    st.rerun()

        # 分队操作栏
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            balance_btn = st.button("⚖️ 战力天平平衡分配", type="primary", use_container_width=True, help="全局计算，使双方总战力最接近")
        with col_b2:
            carry_spread_btn = st.button("👑 大腿均分模式", use_container_width=True, help="两大腿与两挂件分别拆开至红蓝两方，腰部选手精密配平")
        with col_b3:
            random_btn = st.button("🎲 盲盒随机抽签", use_container_width=True, help="在满足羁绊锁定的前提下，完全随机分组")

        if "assigned_blue" not in st.session_state:
            st.session_state["assigned_blue"] = []
            st.session_state["assigned_red"] = []
            st.session_state["split_mode"] = ""

        def get_player_mmr(p_id):
            if p_id in st.session_state["custom_guests"]:
                g_val = st.session_state["custom_guests"][p_id]
                return float(g_val.get("mmr", 60.0)) if isinstance(g_val, dict) else float(g_val)
            if p_id in df.index:
                return float(df.loc[p_id, "MMR"])
            return 50.0

        def check_rules_valid(team_b_set, team_r_set):
            for rule in st.session_state["lock_rules"]:
                p1, p2 = rule["p1"], rule["p2"]
                if (p1 in team_b_set or p1 in team_r_set) and (p2 in team_b_set or p2 in team_r_set):
                    if rule["type"] == "same":
                        if not ((p1 in team_b_set and p2 in team_b_set) or (p1 in team_r_set and p2 in team_r_set)):
                            return False
                    elif rule["type"] == "diff":
                        if not ((p1 in team_b_set and p2 in team_r_set) or (p1 in team_r_set and p2 in team_b_set)):
                            return False
            return True

        total_chosen = len(selected_players)

        if balance_btn:
            if total_chosen < 2:
                st.warning("⚠️ 至少选择 2 位玩家才能进行分队！")
            else:
                p_list = list(selected_players)
                blue_size = total_chosen // 2
                best_diff = float("inf")
                best_b, best_r = [], []
                for cand_b in combinations(p_list, blue_size):
                    cand_r = [p for p in p_list if p not in cand_b]
                    if not check_rules_valid(set(cand_b), set(cand_r)):
                        continue
                    m_b = sum(get_player_mmr(p) for p in cand_b)
                    m_r = sum(get_player_mmr(p) for p in cand_r)
                    avg_b, avg_r = m_b / len(cand_b), m_r / len(cand_r)
                    diff = abs(avg_b - avg_r) if total_chosen % 2 != 0 else abs(m_b - m_r)
                    if diff < best_diff:
                        best_diff = diff
                        best_b, best_r = list(cand_b), list(cand_r)
                if not best_b:
                    st.error("❌ 无法满足当前羁绊锁定规则，请检查是否存在冲突！")
                else:
                    st.session_state["assigned_blue"] = best_b
                    st.session_state["assigned_red"] = best_r
                    st.session_state["split_mode"] = f"⚖️ 战力天平平衡 ({len(best_b)}v{len(best_r)})"

        elif carry_spread_btn:
            if total_chosen < 4:
                st.warning("⚠️ 大腿均分模式至少需要 4 位出战玩家！")
            else:
                p_list = sorted(list(selected_players), key=lambda x: get_player_mmr(x), reverse=True)
                top1, top2 = p_list[0], p_list[1]
                bot1, bot2 = p_list[-1], p_list[-2]
                middle_pool = p_list[2:-2]
                blue_needed = (total_chosen // 2) - 2

                best_diff = float("inf")
                best_b, best_r = [], []
                for (b_anchor, r_anchor) in [([top1, bot2], [top2, bot1]), ([top1, bot1], [top2, bot2])]:
                    if blue_needed > 0 and middle_pool:
                        for cand_mid_b in combinations(middle_pool, blue_needed):
                            cand_mid_r = [p for p in middle_pool if p not in cand_mid_b]
                            team_b = b_anchor + list(cand_mid_b)
                            team_r = r_anchor + list(cand_mid_r)
                            if not check_rules_valid(set(team_b), set(team_r)):
                                continue
                            m_b = sum(get_player_mmr(p) for p in team_b)
                            m_r = sum(get_player_mmr(p) for p in team_r)
                            diff = abs(m_b - m_r)
                            if diff < best_diff:
                                best_diff = diff
                                best_b, best_r = team_b, team_r
                    else:
                        team_b = b_anchor + middle_pool
                        team_r = r_anchor
                        if check_rules_valid(set(team_b), set(team_r)):
                            m_b = sum(get_player_mmr(p) for p in team_b)
                            m_r = sum(get_player_mmr(p) for p in team_r)
                            diff = abs(m_b - m_r)
                            if diff < best_diff:
                                best_diff = diff
                                best_b, best_r = team_b, team_r
                if not best_b:
                    st.error("❌ 大腿与挂件均分时与设定的人情羁绊冲突，建议使用普通战力平衡模式！")
                else:
                    st.session_state["assigned_blue"] = best_b
                    st.session_state["assigned_red"] = best_r
                    st.session_state["split_mode"] = f"👑 大腿均分·带头大哥模式 ({len(best_b)}v{len(best_r)})"

        elif random_btn:
            if total_chosen < 2:
                st.warning("⚠️ 至少选择 2 位玩家才能进行分队！")
            else:
                found = False
                for _ in range(100):
                    shuffled = list(selected_players)
                    random.shuffle(shuffled)
                    blue_size = total_chosen // 2
                    cand_b = shuffled[:blue_size]
                    cand_r = shuffled[blue_size:]
                    if check_rules_valid(set(cand_b), set(cand_r)):
                        st.session_state["assigned_blue"] = cand_b
                        st.session_state["assigned_red"] = cand_r
                        st.session_state["split_mode"] = f"🎲 盲盒随机分配 ({len(cand_b)}v{len(cand_r)})"
                        found = True
                        break
                if not found:
                    st.error("❌ 随机抽签 100 次均无法满足当前羁绊锁定规则！")

        # 呈现阵营对决卡片
        if st.session_state["assigned_blue"] and st.session_state["assigned_red"]:
            blue_team = st.session_state["assigned_blue"]
            red_team = st.session_state["assigned_red"]
            blue_total = round(sum(get_player_mmr(p) for p in blue_team), 1)
            red_total = round(sum(get_player_mmr(p) for p in red_team), 1)
            blue_avg = round(blue_total / len(blue_team), 1) if blue_team else 0
            red_avg = round(red_total / len(red_team), 1) if red_team else 0
            diff_score = round(abs(blue_total - red_total), 1)
            avg_diff = round(abs(blue_avg - red_avg), 1)

            st.caption(f"当前模式：**{st.session_state['split_mode']}** ｜ 双方总战力差：**{diff_score} 分** (人均差: **{avg_diff} 分**)")

            b_htmls = []
            for p in blue_team:
                p_mmr = get_player_mmr(p)
                desc = f"胜率 {df.loc[p, '胜率_num']}% · 场均 {df.loc[p, '场均击杀']} 杀" if p in df.index else f"外援 · {st.session_state['custom_guests'].get(p,{}).get('tier','外援')}"
                b_htmls.append(f"<div class='team-roster-row'><b>🔵 {short_name(p)}</b><span style='color:#0284c7;font-size:0.85rem;'>战力 {p_mmr} ({desc})</span></div>")

            r_htmls = []
            for p in red_team:
                p_mmr = get_player_mmr(p)
                desc = f"胜率 {df.loc[p, '胜率_num']}% · 场均 {df.loc[p, '场均击杀']} 杀" if p in df.index else f"外援 · {st.session_state['custom_guests'].get(p,{}).get('tier','外援')}"
                r_htmls.append(f"<div class='team-roster-row'><b>🔴 {short_name(p)}</b><span style='color:#e11d48;font-size:0.85rem;'>战力 {p_mmr} ({desc})</span></div>")

            arena_html = f"""
                <div class="team-arena-box">
                    <div style="display:flex;gap:16px;flex-wrap:wrap;">
                        <div style="flex:1;min-width:280px;" class="team-col-blue">
                            <div style="font-size:1.1rem;font-weight:800;color:#0284c7;margin-bottom:10px;display:flex;justify-content:space-between;">
                                <span>🔵 蓝色方 ({len(blue_team)}人)</span><span>均分: {blue_avg}</span>
                            </div>
                            {''.join(b_htmls)}
                        </div>
                        <div style="flex:1;min-width:280px;" class="team-col-red">
                            <div style="font-size:1.1rem;font-weight:800;color:#e11d48;margin-bottom:10px;display:flex;justify-content:space-between;">
                                <span>🔴 红色方 ({len(red_team)}人)</span><span>均分: {red_avg}</span>
                            </div>
                            {''.join(r_htmls)}
                        </div>
                    </div>
                </div>
            """
            st.markdown(arena_html, unsafe_allow_html=True)

            blue_line = "、".join([short_name(p) for p in blue_team])
            red_line = "、".join([short_name(p) for p in red_team])
            raw_copy_text = f"【海克斯内战·双方对阵阵容】\\n🔵 蓝方 ({len(blue_team)}人 | 均分{blue_avg}): {blue_line}\\n🔴 红方 ({len(red_team)}人 | 均分{red_avg}): {red_line}\\n⚡ 战力差: {diff_score} 分 (人均差: {avg_diff} 分)"

            wechat_html = f"""
                <div class="wechat-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #fecdd3;padding-bottom:6px;margin-bottom:8px;">
                        <span style="font-size:0.9rem;font-weight:700;color:#9f1239;">📋 微信名单快捷复制</span>
                        <button id="btn_copy_wechat" onclick="
                            navigator.clipboard.writeText('{raw_copy_text}').then(() => {{
                                const btn = document.getElementById('btn_copy_wechat');
                                btn.innerText = '✅ 已成功复制！';
                                btn.style.background = '#fce7f3';
                                btn.style.borderColor = '#f43f5e';
                                btn.style.color = '#be185d';
                                setTimeout(() => {{
                                    btn.innerText = '📋 点击一键复制';
                                    btn.style.background = '#ffffff';
                                    btn.style.borderColor = '#fbcfe8';
                                    btn.style.color = '#be185d';
                                }}, 2000);
                            }}).catch(() => {{ alert('请手动长按复制'); }});
                        " style="background:#ffffff;border:1px solid #fbcfe8;color:#be185d;padding:4px 10px;border-radius:6px;font-size:0.82rem;font-weight:700;cursor:pointer;">📋 点击一键复制</button>
                    </div>
                    <div style="font-size:0.92rem;line-height:1.6;color:#334155;">
                        <div><b>【海克斯内战·双方对阵阵容】</b></div>
                        <div><span style="color:#0284c7;font-weight:700;">🔵 蓝方 ({len(blue_team)}人 | 均分{blue_avg}):</span> {blue_line}</div>
                        <div><span style="color:#e11d48;font-weight:700;">🔴 红方 ({len(red_team)}人 | 均分{red_avg}):</span> {red_line}</div>
                        <div style="font-size:0.83rem;color:#64748b;margin-top:2px;">⚡ 战力差: {diff_score} 分 (人均差: {avg_diff} 分)</div>
                    </div>
                </div>
            """
            st.markdown(wechat_html, unsafe_allow_html=True)

# ==========================================
# Tab 2: 胜率天梯与荣誉榜
# ==========================================
with tab_ladder:
    if df.empty:
        st.info("💡 暂无选手数据。")
    else:
        # 单场高光纪录
        st.markdown('<div class="panel-header-title">🔥 单场巅峰纪录</div>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown(f"""
                <div class="metric-stat-box">
                    <div class="metric-title">单场最高击杀</div>
                    <div class="metric-val-main">{short_name(max_single_kill['player'])}</div>
                    <div class="metric-badge badge-gold">{max_single_kill['val']} 杀 (第 {max_single_kill['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"""
                <div class="metric-stat-box">
                    <div class="metric-title">单场最高阵亡</div>
                    <div class="metric-val-main">{short_name(max_single_death['player'])}</div>
                    <div class="metric-badge badge-pink">{max_single_death['val']} 阵亡 (第 {max_single_death['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"""
                <div class="metric-stat-box">
                    <div class="metric-title">单场最高助攻</div>
                    <div class="metric-val-main">{short_name(max_single_assist['player'])}</div>
                    <div class="metric-badge badge-blue">{max_single_assist['val']} 助攻 (第 {max_single_assist['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # 综合荣誉头衔
        st.markdown('<div class="panel-header-title">🎖️ 综合荣誉名人堂 (≥10局)</div>', unsafe_allow_html=True)
        candidates_10 = df[df["总场次"] >= 10]
        has_vet = not candidates_10.empty
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            t_name = candidates_10.sort_values(by="KDA_num", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"KDA {df.loc[t_name, 'KDA_num']}" if has_vet else "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">KDA之王</div><div class="metric-val-main">{short_name(t_name)}</div><div class="metric-badge badge-blue">{val_str}</div></div>', unsafe_allow_html=True)
        with col2:
            t_name = candidates_10.sort_values(by="击杀", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"{int(df.loc[t_name, '击杀'])} 杀" if has_vet else "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">累计击杀王</div><div class="metric-val-main">{short_name(t_name)}</div><div class="metric-badge badge-gold">{val_str}</div></div>', unsafe_allow_html=True)
        with col3:
            t_name = candidates_10.sort_values(by="死亡", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"{int(df.loc[t_name, '死亡'])} 阵亡" if has_vet else "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">累计白给王</div><div class="metric-val-main">{short_name(t_name)}</div><div class="metric-badge badge-pink">{val_str}</div></div>', unsafe_allow_html=True)
        with col4:
            t_name = candidates_10.sort_values(by="助攻", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"{int(df.loc[t_name, '助攻'])} 助攻" if has_vet else "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">累计助攻王</div><div class="metric-val-main">{short_name(t_name)}</div><div class="metric-badge badge-blue">{val_str}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # 羁绊看板
        st.markdown('<div class="panel-header-title">🔗 阵营羁绊与宿敌</div>', unsafe_allow_html=True)
        syn_list = []
        for (p1, p2), v in synergy_stats.items():
            tg, wg, lg = int(v["同队场次"]), int(v["胜场"]), int(v["负场"])
            syn_list.append({"pair": f"{short_name(p1)} & {short_name(p2)}", "games": tg, "wins": wg, "losses": lg, "wr": wg/tg if tg>0 else 0})
        syn_df = pd.DataFrame(syn_list)
        best_pair, worst_pair = None, None
        if not syn_df.empty:
            cand = syn_df[syn_df["games"] >= 5]
            if not cand.empty:
                best_pair = cand.sort_values(by=["wr", "games"], ascending=[False, False]).iloc[0]
                worst_pair = cand.sort_values(by=["wr", "games"], ascending=[True, False]).iloc[0]

        nem_list = []
        for (p1, p2), v in nemesis_stats.items():
            tg, p1_w, p2_w = int(v["交手场次"]), int(v["p1_wins"]), int(v["p2_wins"])
            if tg > 0:
                winner, loser = (p1, p2) if p1_w >= p2_w else (p2, p1)
                w_cnt, l_cnt = max(p1_w, p2_w), min(p1_w, p2_w)
                nem_list.append({"display": f"{short_name(winner)} ➔ {short_name(loser)}", "wins": w_cnt, "losses": l_cnt, "dom": w_cnt/tg, "diff": abs(p1_w-p2_w), "games": tg})
        nem_df = pd.DataFrame(nem_list)
        rival_pair = None
        if not nem_df.empty:
            n_cand = nem_df[nem_df["games"] >= 5]
            if not n_cand.empty:
                rival_pair = n_cand.sort_values(by=["dom", "diff", "games"], ascending=[False, False, False]).iloc[0]

        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            p_text, d_text = (best_pair['pair'], f"{int(best_pair['wins'])}胜{int(best_pair['losses'])}负") if best_pair is not None else ("虚位以待", "同队需满 5 局")
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">黄金搭档 (≥5局)</div><div class="metric-val-main">{p_text}</div><div class="metric-badge badge-blue">{d_text}</div></div>', unsafe_allow_html=True)
        with cs2:
            p_text, d_text = (worst_pair['pair'], f"{int(worst_pair['wins'])}胜{int(worst_pair['losses'])}负") if worst_pair is not None else ("虚位以待", "同队需满 5 局")
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">难兄难弟 (≥5局)</div><div class="metric-val-main">{p_text}</div><div class="metric-badge badge-pink">{d_text}</div></div>', unsafe_allow_html=True)
        with cs3:
            p_text, d_text = (rival_pair['display'], f"{int(rival_pair['wins'])}胜{int(rival_pair['losses'])}负") if rival_pair is not None else ("虚位以待", "交手需满 5 局")
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">一生之敌 (≥5局)</div><div class="metric-val-main">{p_text}</div><div class="metric-badge badge-gold">{d_text}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # 胜率天梯总榜
        st.markdown('<div class="panel-header-title">📊 选手胜率总排行榜</div>', unsafe_allow_html=True)
        df_sorted = df.sort_values(by=["胜率_num", "总场次", "KDA_num"], ascending=[False, False, False])
        table_rows = []
        for player_id, row in df_sorted.iterrows():
            wr_val = row["胜率_num"]
            wr_badge = f"<span style='color:#0284c7;font-weight:700;'>{wr_val}%</span>" if wr_val >= 50 else f"<span style='color:#e11d48;font-weight:700;'>{wr_val}%</span>"
            row_html = (
                f"<tr>"
                f"<td style='text-align:left;padding-left:16px;font-weight:800;color:#1e293b;'>{short_name(player_id)}</td>"
                f"<td>{int(row['总场次'])}</td>"
                f"<td>{int(row['胜场'])}</td>"
                f"<td>{int(row['负场'])}</td>"
                f"<td>{wr_badge}</td>"
                f"<td style='font-weight:800;color:#e11d48;'>{row['MMR']:.1f}</td>"
                f"<td>{row['场均击杀']:.1f}</td>"
                f"<td>{row['KD']:.2f}</td>"
                f"<td style='font-weight:800;'>{row['KDA_num']:.2f}</td>"
                f"<td>{int(row['击杀'])}</td>"
                f"<td>{int(row['死亡'])}</td>"
                f"<td>{int(row['助攻'])}</td>"
                f"</tr>"
            )
            table_rows.append(row_html)

        custom_table_html = (
            f'<div class="clean-table-box">'
            f'<table class="clean-table">'
            f'<thead><tr>'
            f'<th style="text-align:left;padding-left:16px;">选手</th>'
            f'<th>总场次</th><th>胜</th><th>负</th><th>胜率</th>'
            f'<th>MMR战力</th><th>场均杀</th><th>KD</th><th>KDA</th><th>总击杀</th><th>总死亡</th><th>总助攻</th>'
            f'</tr></thead>'
            f'<tbody>{"".join(table_rows)}</tbody>'
            f'</table></div>'
        )
        st.markdown(custom_table_html, unsafe_allow_html=True)

# ==========================================
# Tab 3: 局内战术图谱与成就馆
# ==========================================
with tab_radar:
    active_player_options = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True) if not df.empty else []
    if not active_player_options:
        st.info("💡 暂无选手数据。")
    else:
        c_sel, _ = st.columns([2.5, 3.5])
        with c_sel:
            target_p = st.selectbox("选择要分析的选手：", active_player_options, format_func=lambda x: short_name(x))
        
        p_radar = radar_stats_pool[target_p]
        valid_g = p_radar["games_6p"]
        p_g_total = int(df.loc[target_p, "总场次"])
        
        if valid_g > 0:
            p_kills = float(p_radar["kills"] / valid_g)
            p_deaths = float(p_radar["deaths"] / valid_g)
            p_assists = float(p_radar["assists"] / valid_g)
            dmg_list = p_radar["damage_shares"]
            dmg_share = (sum(dmg_list) / len(dmg_list)) if dmg_list else (p_kills * 2.3)
            taken_list = p_radar["taken_shares"]
            taken_share = (sum(taken_list) / len(taken_list)) if taken_list else (p_deaths * 2.4)
            kp_list = p_radar["kp_shares"]
            avg_kp = (sum(kp_list) / len(kp_list)) if kp_list else (p_kills + p_assists) / max(1.0, p_kills + p_assists + 5.0)
            sample_desc = f"{valid_g} 局标准对局 (已剔除残局)"
        else:
            p_kills = float(df.loc[target_p, "击杀"] / p_g_total)
            p_deaths = float(df.loc[target_p, "死亡"] / p_g_total)
            p_assists = float(df.loc[target_p, "助攻"] / p_g_total)
            dmg_share = p_kills * 2.3
            taken_share = p_deaths * 2.4
            avg_kp = (p_kills + p_assists) / max(1.0, p_kills + p_assists + 5.0)
            sample_desc = f"{p_g_total} 局全局对局"

        # 科学平滑六维打分
        score_dmg = max(18.0, min(96.0, (25.0 + (dmg_share / 20.0) * 35.0) if dmg_share <= 20.0 else (60.0 + min(1.0, (dmg_share - 20.0) / 14.0) * 35.0)))
        score_tank = max(18.0, min(96.0, (25.0 + (taken_share / 20.0) * 35.0) if taken_share <= 20.0 else (60.0 + min(1.0, (taken_share - 20.0) / 14.0) * 35.0)))
        score_kp = max(18.0, min(96.0, (25.0 + (avg_kp / 0.55) * 35.0) if avg_kp <= 0.55 else (60.0 + min(1.0, (avg_kp - 0.55) / 0.22) * 35.0)))
        
        ka_total = max(1.0, p_kills + p_assists)
        kill_bias = p_kills / ka_total
        score_kill = max(20.0, min(95.0, 25.0 + min(1.0, p_kills / 10.0) * 45.0 + (kill_bias * 25.0)))
        score_assist = max(20.0, min(95.0, 25.0 + min(1.0, p_assists / 12.0) * 45.0 + ((1.0 - kill_bias) * 25.0)))
        score_surv = max(20.0, min(95.0, (60.0 + ((6.0 - p_deaths) / 4.0) * 32.0) if p_deaths <= 6.0 else (60.0 - ((p_deaths - 6.0) / 5.0) * 32.0)))

        categories = ['伤害输出', '承受伤害', '参团活跃', '人头收割', '助攻开团', '保命能力']
        values = [round(score_dmg, 1), round(score_tank, 1), round(score_kp, 1), round(score_kill, 1), round(score_assist, 1), round(score_surv, 1)]

        if score_dmg >= 78 and score_kill >= 75:
            style_title, style_badge = "🗡️ 绝对主C / 团队核心火力", "badge-pink"
        elif score_tank >= 78 and score_assist >= 70:
            style_title, style_badge = "🛡️ 铁血开团 / 护航巨盾", "badge-blue"
        elif score_kp >= 78:
            style_title, style_badge = "🌐 全图游走 / 节奏发动机", "badge-gold"
        elif score_surv >= 75 and score_dmg <= 50:
            style_title, style_badge = "🕊️ 稳健拉扯 / 保命大师", "badge-gray"
        elif score_kill >= 75 and score_surv <= 45:
            style_title, style_badge = "🩸 突进刺客 / 绝命换头", "badge-pink"
        else:
            style_title, style_badge = "⚖️ 均衡打法 / 团队中坚", "badge-pink"

        p_hist = player_history[target_p]
        recent_games = p_hist["outcomes"][-3:] if p_hist["outcomes"] else []
        if len(recent_games) >= 2 and all(recent_games):
            recent_status, status_tip, status_color = "🔥 连胜狂飙中", "手感发烫：最近对局连续取胜，状态极佳！", "#e11d48"
        elif len(recent_games) >= 2 and not any(recent_games):
            recent_status, status_tip, status_color = "🧊 连败急需吸氧", "水逆预警：最近遭遇连败，急需给力队友带躺！", "#0284c7"
        else:
            recent_status, status_tip, status_color = "⚖️ 状态起伏平稳", "发挥稳定：胜负交替，在场上保持中流砥柱表现。", "#64748b"

        # 勋章库
        badges_data = []
        if p_hist["max_dmg_share"] >= 38.0 or score_dmg >= 92:
            badges_data.append(("💥 血条消失术", "【核爆级主C】曾在正规局单场打出 38%+ 恐怖输出占比，融化血条"))
        if p_hist["max_taken_share"] >= 38.0 or score_tank >= 92:
            badges_data.append(("🛡️ 叹息之壁", "【铁血不坏身】曾在正规局单场吸收 38%+ 承伤占比，如山般掩护全队"))
        if p_hist["max_kill"] >= 16 or score_kill >= 92:
            badges_data.append(("🩸 绝命赏金客", "【超神收割机】曾在正规局单场斩获 16+ 击杀，无情屠戮敌阵"))
        if p_hist["max_death"] >= 10:
            badges_data.append(("🎰 慈善赌圣", "【全自动取款机】曾单场阵亡 10+ 次，给对手送出巨额悬赏！"))
        if p_hist["min_death_win"] <= 1 and p_g_total >= 3:
            badges_data.append(("🏕️ 泉水指挥官", "【保分艺术家】胜局中曾打出 0 阵亡或仅死 1 次，拉扯玩成艺术"))
        if p_hist["max_assist"] >= 18 or score_assist >= 90:
            badges_data.append(("🚑 全图救护车", "【团战发动机】单场豪取 18+ 助攻，全图到处都有他的掩护"))
        if p_hist["svp_cnt"] >= 2:
            badges_data.append(("🪓 悲情孤勇者", "【尽力局局长】多次在落败局打出 35%+ 火力或 11+ 杀，奈何带不动队友"))
        if p_kills >= 6.0 and dmg_share <= 18.0:
            badges_data.append(("🎯 致命K头怪", "【经济吸收器】击杀数名列前茅但输出占比偏低，人头收割手艺纯熟"))
        if total_games_all >= 12 and (p_g_total / total_games_all) >= 0.80:
            badges_data.append(("🏛️ 内战活化石", f"【真·全勤标兵】在总计 {total_games_all} 场内战中出战 {p_g_total} 场 (出勤率 {(p_g_total/total_games_all)*100:.0f}%)"))
        elif p_g_total >= 10:
            badges_data.append(("🎖️ 资深百战将", f"【久经沙场】内战累计出战已达 {p_g_total} 局，经验老道的中流砥柱"))
        if not badges_data:
            badges_data.append(("🌱 未来可期", "【新晋潜能股】正在积蓄战力，距离解锁首个高光/趣味勋章仅差一步"))

        badges_html = "".join([f'<span class="badge-tag" title="{tip}">{name}</span>' for name, tip in badges_data])

        col_radar, col_detail = st.columns([1.2, 1])
        with col_radar:
            st.markdown(generate_radar_svg(values, categories), unsafe_allow_html=True)
        with col_detail:
            st.markdown(f"""
                <div class="card-panel" style="margin-top:10px;">
                    <div class="panel-header-title">局内战术定位</div>
                    <div style="font-size:1.4rem;font-weight:900;color:#1e293b;margin-bottom:6px;">{short_name(target_p)}</div>
                    <div class="metric-badge {style_badge}">{style_title}</div>
                    <div style="font-size:0.88rem;color:#475569;line-height:2.0;margin-top:12px;">
                        <div>• <b>统计基准</b>: {sample_desc}</div>
                        <div>• <b>场均伤害占比</b>: <span style="color:#e11d48;font-weight:800;">{dmg_share:.1f}%</span></div>
                        <div>• <b>场均承伤占比</b>: <span style="color:#0284c7;font-weight:800;">{taken_share:.1f}%</span></div>
                        <div>• <b>团战参团率</b>: <span style="color:#ca8a04;font-weight:800;">{round(avg_kp * 100, 1)}%</span></div>
                        <div>• <b>场均KDA</b>: {p_kills:.1f} 杀 / {p_deaths:.1f} 亡 / {p_assists:.1f} 助</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # 荣誉勋章馆展示卡
        st.markdown(f"""
            <div class="card-panel" style="margin-top:4px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #fecdd3;padding-bottom:8px;margin-bottom:10px;">
                    <span style="font-size:1.02rem;font-weight:800;color:#9f1239;">🏅 【{short_name(target_p)}】个人荣誉与成就档案馆</span>
                    <span class="badge-tag" title="{status_tip}" style="font-size:0.82rem;font-weight:700;color:{status_color};background:#ffffff;margin:0;">{recent_status}</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;font-size:0.88rem;color:#334155;margin-bottom:12px;">
                    <div>⚡ <b>单场最高击杀</b>: <span style="color:#e11d48;font-weight:800;">{p_hist['max_kill'] if p_hist['max_kill'] > 0 else '--'} 杀</span></div>
                    <div>💥 <b>最高输出占比</b>: <span style="color:#e11d48;font-weight:800;">{f"{p_hist['max_dmg_share']:.1f}%" if p_hist['max_dmg_share'] > 0 else '--'}</span></div>
                    <div>🛡️ <b>最高承伤占比</b>: <span style="color:#0284c7;font-weight:800;">{f"{p_hist['max_taken_share']:.1f}%" if p_hist['max_taken_share'] > 0 else '--'}</span></div>
                    <div>🕊️ <b>胜局最低阵亡</b>: <span style="color:#0284c7;font-weight:800;">{p_hist['min_death_win'] if p_hist['min_death_win'] != 999 else '--'} 次</span></div>
                </div>
                <div style="border-top:1px dashed #fecdd3;padding-top:10px;">
                    <span style="font-size:0.84rem;color:#881337;font-weight:700;margin-right:8px;">已解锁成就勋章 (悬停查看详情):</span>
                    {badges_html}
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("📖 查阅全部勋章达成标准与图鉴指南"):
            st.markdown(f"""
            - 💥 **「血条消失术」**：曾单场正规对局打出 **$\ge 38\%$ 输出占比** 或局内输出评分达 92 分以上。
            - 🛡️ **「叹息之壁」**：曾单场正规对局吸收 **$\ge 38\%$ 承伤占比** 或前排承伤评分达 92 分以上。
            - 🩸 **「绝命赏金客」**：曾单场正规对局砍下 **$\ge 16$ 次击杀** 或人头收割评分达 92 分以上。
            - 🎰 **「慈善赌圣」**：曾单场阵亡 **$\ge 10$ 次**，对面发家致富的幕后功臣。
            - 🏕️ **「泉水指挥官」**：在胜利局中**阵亡 $\le 1$ 次**，生存保命的拉扯大师。
            - 🚑 **「全图救护车」**：单场豪取 **$\ge 18$ 次助攻**，哪里打架哪里有他。
            - 🪓 **「悲情孤勇者」**：累计至少 2 场在**落败局打出 $\ge 35\%$ 火力或 11+ 击杀**。
            - 🎯 **「致命K头怪」**：场均击杀 $\ge 6$ 但场均输出占比 $\le 18\%$，收残血绝活哥。
            - 🏛️ **「内战活化石」**：全群总场次 $\ge 12$ 局且出勤率 $\ge 80\%$ 的真·全勤元老（当前全群已录入 **{total_games_all}** 局）。
            - 🎖️ **「资深百战将」**：内战累计总出战局数满 **10 局**。
            - 🌱 **「未来可期」**：新晋出战群友，各项高光数据正在积蓄中。
            """)

# ==========================================
# Tab 4: 战绩智能录入
# ==========================================
with tab_upload:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header-title">📸 战绩截图智能分析录入</div>', unsafe_allow_html=True)
    st.caption("支持拖拽上传多张掌盟结算详情截图，系统通过 DashScope Qwen-VL 视觉模型自动识别两队阵容、胜负、KDA、伤害与承伤占比。")

    with st.form("upload_box", clear_on_submit=False):
        files = st.file_uploader("选择或拖拽战绩截图（支持批量多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        submit_btn = st.form_submit_button("🚀 开始解析并录入", type="primary", use_container_width=True)

    if submit_btn:
        if not files:
            st.warning("⚠️ 请先选择战绩截图！")
        elif not key:
            st.warning("⚠️ 请在左侧控制台填入 DashScope API Key！")
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
                    st.warning(f"⚠️ {file.name} 已录入过，跳过。")
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
                time.sleep(0.6)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
