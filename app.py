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

st.set_page_config(page_title="海克斯内战", page_icon="⚔️", layout="wide")

# ---------------- 页面 CSS ----------------
st.markdown("""
<style>
:root, [data-theme="light"], .stApp {
    --primary-color: #f43f5e !important;
}

.stApp {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe4e6 50%, #fed7aa 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

h1 {
    background: linear-gradient(90deg, #e11d48 0%, #db2777 50%, #9333ea 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 800 !important;
    letter-spacing: 1px !important;
}
h2, h3 { 
    color: #881337 !important; 
    font-weight: 700 !important;
}

div[data-baseweb="tag"],
span[data-baseweb="tag"],
li[data-baseweb="tag"],
div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background: #fce7f3 !important;
    background-color: #fce7f3 !important;
    border: 1px solid #f472b6 !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 3px rgba(244, 114, 182, 0.2) !important;
    margin: 2px 4px !important;
    padding: 2px 8px !important;
}
div[data-baseweb="tag"] *,
span[data-baseweb="tag"] *,
div[data-testid="stMultiSelect"] [data-baseweb="tag"] * {
    color: #9d174d !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    fill: #db2777 !important;
}

div[data-testid="stMultiSelect"] > div > div,
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid #fbcfe8 !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(244, 114, 182, 0.08) !important;
    padding: 4px 8px !important;
}
div[data-baseweb="select"] input,
div[data-baseweb="select"] input:focus,
div[data-baseweb="select"] div[data-baseweb="base-input"] {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
    background-color: transparent !important;
    color: #334155 !important;
}

div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
ul[data-baseweb="menu"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
    border: 2px solid #f472b6 !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 25px rgba(225, 29, 72, 0.18) !important;
}
li[data-baseweb="menu-item"] {
    background-color: #ffffff !important;
    color: #334155 !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
}
li[data-baseweb="menu-item"]:hover {
    background-color: #fce7f3 !important;
    color: #be185d !important;
}

div[data-testid="stLinkButton"] a {
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 10px 16px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: blur(8px) !important;
    text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}
div[data-testid="stLinkButton"] a:hover {
    transform: translateY(-2px);
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%) !important;
    border: 2px solid #eab308 !important;
    box-shadow: 0 4px 14px rgba(234, 179, 8, 0.3) !important;
    color: #854d0e !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(234, 179, 8, 0.5) !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
    border: 2px solid #0284c7 !important;
    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
    color: #0369a1 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.5) !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%) !important;
    border: 2px solid #e11d48 !important;
    box-shadow: 0 4px 14px rgba(225, 29, 72, 0.3) !important;
    color: #9f1239 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(225, 29, 72, 0.5) !important;
}

div[data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    border: 1px solid #fbcfe8 !important;
    border-radius: 6px !important;
    color: #334155 !important;
}
button[data-testid="stBaseButton-primary"],
button[kind="primary"] {
    background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%) !important;
    border: 1px solid #fb7185 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(244, 63, 94, 0.3) !important;
}
button[data-testid="stBaseButton-secondary"] {
    background: #ffffff !important;
    border: 1px solid #fbcfe8 !important;
    color: #be185d !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: #f43f5e !important;
    background: #fff1f2 !important;
}

.stat-card {
    background: #ffffff;
    border: 1px solid #fecdd3;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 4px 14px rgba(244, 114, 182, 0.12);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-bottom: 12px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(244, 63, 94, 0.2);
    border-color: #fb7185;
}
.stat-card-title { font-size: 0.88rem; font-weight: 700; color: #9f1239; margin-bottom: 4px; }
.stat-card-player { font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-bottom: 6px; }
.stat-card-delta { font-size: 0.82rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; display: inline-block; width: fit-content; }
.delta-pink { background: #ffe4e6; color: #e11d48; }
.delta-gold { background: #fef9c3; color: #ca8a04; }
.delta-blue { background: #e0f2fe; color: #0284c7; }
.delta-gray { background: #f1f5f9; color: #64748b; }

.badge-tag {
    display: inline-block;
    background: #fff1f2;
    border: 1px solid #fecdd3;
    color: #9f1239;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
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

.team-arena-box {
    background: #ffffff;
    border: 1px solid #fecdd3;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 16px rgba(244, 63, 94, 0.1);
    margin: 14px 0;
}
.team-col-blue { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 14px; }
.team-col-red { background: #fff1f2; border: 1px solid #fecdd3; border-radius: 10px; padding: 14px; }
.team-roster-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border: 1px solid #fed7aa;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
}
.wechat-card {
    background: #ffffff;
    border: 1px solid #fbcfe8;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 14px;
    box-shadow: 0 4px 12px rgba(244, 114, 182, 0.1);
}

.clean-table-box {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #fecdd3;
    border-radius: 10px;
    background: #ffffff;
    margin: 14px 0 25px 0;
    box-shadow: 0 4px 14px rgba(244, 114, 182, 0.08);
}
.clean-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.93rem;
    text-align: center;
    color: #334155;
}
.clean-table th {
    background: #fff1f2;
    color: #9f1239;
    font-weight: 700;
    padding: 12px 8px;
    border-bottom: 2px solid #fecdd3;
}
.clean-table td {
    padding: 10px 6px;
    border-bottom: 1px solid #fff1f2;
}
.clean-table tr:hover td {
    background: #fff5f5;
}

section[data-testid="stSidebar"] {
    background-color: #fff5f5 !important;
    border-right: 1px solid #fecdd3 !important;
}
section[data-testid="stSidebar"] * {
    color: #475569 !important;
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

    svg_content = f"""
    <div style="display:flex;justify-content:center;align-items:center;padding:10px 0;">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="max-width:100%;height:auto;display:block;">
            {''.join(grid_polys)}
            {''.join(axis_lines)}
            {polygon_svg}
            {''.join(data_dots)}
            {''.join(labels)}
        </svg>
    </div>
    """
    return svg_content

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.header("⚙️ 系统管理")
    default_key = st.secrets.get("DASHSCOPE_API_KEY", "") if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets else ""
    key = st.text_input("DashScope API Key", value=default_key, type="password")

    records = load_records()
    total_games_all = len(records)
    st.metric("总计收录对局", f"{total_games_all} 局")

    if records:
        if st.button("🔄 一键重扫历史截图 (补充输出/承伤)", help="读取 records.json 里的截图，让 AI 提取输出与承伤"):
            if not key:
                st.warning("⚠️ 请先在上方填入 DashScope API Key！")
            else:
                p_bar = st.progress(0)
                st_msg = st.empty()
                success_n = 0
                for idx, r in enumerate(records):
                    st_msg.info(f"⏳ 正在重新解析第 {idx+1}/{len(records)} 局截图...")
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
                            st.error(f"第 {idx+1} 局解析失败: {e}")
                    p_bar.progress((idx + 1) / len(records))
                
                save_records(records)
                st_msg.empty()
                st.success(f"🎉 成功补充更新 {success_n} 局历史对局！")
                time.sleep(0.6)
                st.rerun()

    if records:
        st.markdown("---")
        st.subheader("🔍 对局图文核对")
        game_options = [f"第 {i+1} 局 ({r.get('winning_team', '未知')}方胜)" for i, r in enumerate(records)]
        selected_idx = st.selectbox("选择要核对的场次", range(len(records)), format_func=lambda i: game_options[i])
        
        curr_record = records[selected_idx]
        thumb_b64 = curr_record.get("image_thumb", "")
        if thumb_b64:
            st.image(f"data:image/jpeg;base64,{thumb_b64}", caption=f"第 {selected_idx + 1} 局原始截图", use_container_width=True)
        
        p_rows = []
        for p in curr_record.get("players", []):
            dmg_s = f"{p.get('damage_share')}%" if p.get('damage_share') is not None else "--"
            p_rows.append({
                "阵营": p.get("team", ""),
                "玩家ID": short_name(p.get("player_name", "")),
                "K/D/A": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                "输出占比": dmg_s,
                "胜负": "胜" if p.get("is_winner") else "负"
            })
        if p_rows:
            st.dataframe(pd.DataFrame(p_rows), hide_index=True)
        
        if st.button("🗑️ 删除本局记录", key=f"del_game_{selected_idx}"):
            records.pop(selected_idx)
            save_records(records)
            st.success("已删除该局！")
            time.sleep(0.4)
            st.rerun()

    with st.expander("🎙️ 语音房链接配置"):
        cfg = load_config()
        new_main = st.text_input("大厅主语音", value=cfg.get("main_voice", ""))
        new_blue = st.text_input("🔵 蓝方语音", value=cfg.get("blue_voice", ""))
        new_red = st.text_input("🔴 红方语音", value=cfg.get("red_voice", ""))
        if st.button("💾 保存语音房"):
            save_config({"main_voice": new_main, "blue_voice": new_blue, "red_voice": new_red})
            st.success("已保存！")
            time.sleep(0.4)
            st.rerun()

    st.markdown("---")
    if records:
        json_bytes = json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8')
        st.download_button(
            label="💾 导出战绩备份 (JSON)",
            data=json_bytes,
            file_name="lol_records_backup.json",
            mime="application/json"
        )
    
    with st.expander("📥 导入恢复数据"):
        uploaded_backup = st.file_uploader("选择备份文件", type=["json"], key="backup_uploader")
        if uploaded_backup is not None and st.button("⚡ 确认导入", type="primary"):
            try:
                imported_data = json.load(uploaded_backup)
                if isinstance(imported_data, list):
                    save_records(imported_data)
                    st.success("恢复成功！")
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                st.error(f"导入失败: {e}")

# ---------------- 主界面 1：标题与三大微光语音室 ----------------
st.title("⚔️ 海克斯内战战绩中心")

cfg = load_config()
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("🎙️ 大厅语音", cfg.get("main_voice", "https://kook.top/"), use_container_width=True)
with c2:
    st.link_button("🔵 蓝方作战室", cfg.get("blue_voice", "https://kook.top/"), use_container_width=True)
with c3:
    st.link_button("🔴 红方作战室", cfg.get("red_voice", "https://kook.top/"), use_container_width=True)

# ---------------- 主界面 2：数据汇总与硬核指标提取 ----------------
records = load_records()

if not records:
    st.info("💡 暂无对局数据。请在页面底部上传战绩截图。")
else:
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

        blue_team = []
        red_team = []
        blue_total_k, red_total_k = 0, 0
        blue_total_d, red_total_d = 0, 0
        
        for p in players_in_game:
            side = str(p.get("team", "")).upper()
            k = int(p.get("kills", 0))
            d = int(p.get("deaths", 0))
            if side == "BLUE":
                blue_total_k += k
                blue_total_d += d
            elif side == "RED":
                red_total_k += k
                red_total_d += d

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

            dmg_s = p.get("damage_share")
            taken_s = p.get("taken_share")

            player_history[fname]["outcomes"].append(is_win)

            if is_valid_6p_game:
                if k > player_history[fname]["max_kill"]:
                    player_history[fname]["max_kill"] = k
                if d > player_history[fname]["max_death"]:
                    player_history[fname]["max_death"] = d
                if a > player_history[fname]["max_assist"]:
                    player_history[fname]["max_assist"] = a
                if is_win and d < player_history[fname]["min_death_win"]:
                    player_history[fname]["min_death_win"] = d
                
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
                    try:
                        radar_stats_pool[fname]["damage_shares"].append(float(dmg_s))
                    except Exception:
                        pass
                
                if taken_s is not None:
                    try:
                        radar_stats_pool[fname]["taken_shares"].append(float(taken_s))
                    except Exception:
                        pass

                if team_k > 0:
                    radar_stats_pool[fname]["kp_shares"].append((k + a) / team_k)

            if k > max_single_kill["val"]:
                max_single_kill = {"player": fname, "val": k, "game_idx": game_idx + 1}
            if d > max_single_death["val"]:
                max_single_death = {"player": fname, "val": d, "game_idx": game_idx + 1}
            if a > max_single_assist["val"]:
                max_single_assist = {"player": fname, "val": a, "game_idx": game_idx + 1}

            if side == "BLUE":
                blue_team.append((fname, is_win))
            elif side == "RED":
                red_team.append((fname, is_win))

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

        def calculate_mmr(row):
            if row["总场次"] < 2:
                return 50.0
            avg_k = float(row["场均击杀"])
            kill_score = min(avg_k / 10.0, 1.2) * 35.0
            kda_val = float(row["KDA_num"])
            kda_score = min(kda_val / 5.0, 1.2) * 35.0
            wr_score = (float(row["胜率_num"]) / 100.0) * 30.0
            total_mmr = kill_score + kda_score + wr_score
            if avg_k >= 7.0 and kda_val >= 2.5:
                total_mmr += 5.0
            return round(total_mmr, 1)

        df["MMR"] = df.apply(calculate_mmr, axis=1)

        # ---------------- 板块 A：单场纪录 ----------------
        st.subheader("🔥 单场最高纪录")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-title">单场最高击杀</div>
                    <div class="stat-card-player">{short_name(max_single_kill['player'])}</div>
                    <div class="stat-card-delta delta-gold">{max_single_kill['val']} 杀 (第 {max_single_kill['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-title">单场最高阵亡</div>
                    <div class="stat-card-player">{short_name(max_single_death['player'])}</div>
                    <div class="stat-card-delta delta-pink">{max_single_death['val']} 阵亡 (第 {max_single_death['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-title">单场最高助攻</div>
                    <div class="stat-card-player">{short_name(max_single_assist['player'])}</div>
                    <div class="stat-card-delta delta-blue">{max_single_assist['val']} 助攻 (第 {max_single_assist['game_idx']} 局)</div>
                </div>
            """, unsafe_allow_html=True)

        # ---------------- 板块 B：综合荣誉 ----------------
        st.subheader("🎖️ 综合荣誉头衔 (≥10局)")
        candidates_10 = df[df["总场次"] >= 10]
        has_vet = not candidates_10.empty

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            t_name = candidates_10.sort_values(by="KDA_num", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"KDA {df.loc[t_name, 'KDA_num']}" if has_vet else "需满 10 局"
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">KDA之王</div><div class="stat-card-player">{short_name(t_name)}</div><div class="stat-card-delta delta-blue">{val_str}</div></div>', unsafe_allow_html=True)
        with col2:
            t_name = candidates_10.sort_values(by="击杀", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"{int(df.loc[t_name, '击杀'])} 杀" if has_vet else "需满 10 局"
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">累计击杀王</div><div class="stat-card-player">{short_name(t_name)}</div><div class="stat-card-delta delta-gold">{val_str}</div></div>', unsafe_allow_html=True)
        with col3:
            t_name = candidates_10.sort_values(by="死亡", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"{int(df.loc[t_name, '死亡'])} 阵亡" if has_vet else "需满 10 局"
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">累计白给王</div><div class="stat-card-player">{short_name(t_name)}</div><div class="stat-card-delta delta-pink">{val_str}</div></div>', unsafe_allow_html=True)
        with col4:
            t_name = candidates_10.sort_values(by="助攻", ascending=False).index[0] if has_vet else "虚位以待"
            val_str = f"{int(df.loc[t_name, '助攻'])} 助攻" if has_vet else "需满 10 局"
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">累计助攻王</div><div class="stat-card-player">{short_name(t_name)}</div><div class="stat-card-delta delta-blue">{val_str}</div></div>', unsafe_allow_html=True)

        # ---------------- 板块 C：羁绊看板 ----------------
        st.subheader("🔗 阵营羁绊与宿敌")
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
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">黄金搭档 (≥5局)</div><div class="stat-card-player">{p_text}</div><div class="stat-card-delta delta-blue">{d_text}</div></div>', unsafe_allow_html=True)
        with cs2:
            p_text, d_text = (worst_pair['pair'], f"{int(worst_pair['wins'])}胜{int(worst_pair['losses'])}负") if worst_pair is not None else ("虚位以待", "同队需满 5 局")
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">难兄难弟 (≥5局)</div><div class="stat-card-player">{p_text}</div><div class="stat-card-delta delta-pink">{d_text}</div></div>', unsafe_allow_html=True)
        with cs3:
            p_text, d_text = (rival_pair['display'], f"{int(rival_pair['wins'])}胜{int(rival_pair['losses'])}负") if rival_pair is not None else ("虚位以待", "交手需满 5 局")
            st.markdown(f'<div class="stat-card"><div class="stat-card-title">一生之敌 (≥5局)</div><div class="stat-card-player">{p_text}</div><div class="stat-card-delta delta-gold">{d_text}</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # ---------------- 板块 D：赛前红蓝对阵作战室 (新增：👑 大腿均分模式) ----------------
        st.subheader("⚔️ 赛前阵营分队系统")
        
        if "custom_guests" not in st.session_state:
            st.session_state["custom_guests"] = {}

        for k, v in list(st.session_state["custom_guests"].items()):
            if not isinstance(v, dict):
                st.session_state["custom_guests"][k] = {"mmr": float(v), "tier": "临时外援"}

        known_roster = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True)
        full_options = known_roster + list(st.session_state["custom_guests"].keys())
        default_selection = known_roster[:10] if len(known_roster) >= 10 else known_roster

        selected_players = st.multiselect(
            "选择出战群友名单（支持任意人数）：",
            options=full_options,
            default=default_selection,
            format_func=lambda x: short_name(x)
        )

        with st.container():
            cg1, cg2, cg3 = st.columns([3, 3, 1.5])
            with cg1:
                guest_name = st.text_input("临时外援/替补昵称", placeholder="输入昵称...", key="in_guest_name", label_visibility="collapsed")
            with cg2:
                guest_tier = st.selectbox(
                    "实力评级",
                    options=[80.0, 60.0, 45.0],
                    format_func=lambda v: {80.0: "👑 通天大腿 (80分)", 60.0: "🛡️ 普通水平 (60分)", 45.0: "🌱 萌新挂件 (45分)"}[v],
                    index=1,
                    key="sel_guest_tier",
                    label_visibility="collapsed"
                )
            with cg3:
                if st.button("➕ 加入外援", key="btn_add_g", use_container_width=True):
                    if guest_name.strip():
                        c_name = guest_name.strip()
                        tier_label = {80.0: "通天大腿", 60.0: "普通水平", 45.0: "萌新挂件"}[guest_tier]
                        st.session_state["custom_guests"][c_name] = {"mmr": guest_tier, "tier": tier_label}
                        st.success(f"已录入外援: {c_name}")
                        time.sleep(0.3)
                        st.rerun()

        if st.session_state["custom_guests"]:
            for g_name, g_info in list(st.session_state["custom_guests"].items()):
                mmr_val = g_info.get("mmr", 60.0) if isinstance(g_info, dict) else float(g_info)
                tier_str = g_info.get("tier", "外援") if isinstance(g_info, dict) else "外援"
                col_i, col_d = st.columns([5, 1])
                with col_i:
                    st.caption(f"👤 **{g_name}** · 战力分: {mmr_val} ({tier_str})")
                with col_d:
                    if st.button("🗑️ 删除", key=f"del_g_{g_name}"):
                        del st.session_state["custom_guests"][g_name]
                        st.rerun()

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            balance_btn = st.button("⚖️ 战力天平平衡", type="primary", use_container_width=True, help="全局计算，使双方总战力最接近")
        with col_b2:
            carry_spread_btn = st.button("👑 大腿均分模式", use_container_width=True, help="强制将最强的两大腿与最弱的两挂件分别拆开至红蓝两边，腰部选手精密配平")
        with col_b3:
            random_btn = st.button("🎲 盲盒随机分配", use_container_width=True, help="完全随机打乱分组")

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

        total_chosen = len(selected_players)

        # 模式 1：全局纯战力平衡
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
                    m_b = sum(get_player_mmr(p) for p in cand_b)
                    m_r = sum(get_player_mmr(p) for p in cand_r)
                    avg_b, avg_r = m_b / len(cand_b), m_r / len(cand_r)
                    diff = abs(avg_b - avg_r) if total_chosen % 2 != 0 else abs(m_b - m_r)
                    if diff < best_diff:
                        best_diff = diff
                        best_b, best_r = list(cand_b), list(cand_r)

                st.session_state["assigned_blue"] = best_b
                st.session_state["assigned_red"] = best_r
                st.session_state["split_mode"] = f"⚖️ 战力天平平衡 ({len(best_b)}v{len(best_r)})"

        # 模式 2：👑 大腿均分模式（核心新功能）
        elif carry_spread_btn:
            if total_chosen < 4:
                st.warning("⚠️ 大腿均分模式至少需要 4 位出战玩家！")
            else:
                p_list = sorted(list(selected_players), key=lambda x: get_player_mmr(x), reverse=True)
                
                # 提取最强大哥两位，与最小挂件两位
                top1, top2 = p_list[0], p_list[1]
                bot1, bot2 = p_list[-1], p_list[-2]

                # 中坚力量
                middle_pool = p_list[2:-2]
                blue_needed = (total_chosen // 2) - 2 # 蓝方还需补几个人

                best_diff = float("inf")
                best_b, best_r = [], []

                # 两种大哥和挂件交叉搭配方案：
                # 方案 A: 蓝方=(top1, bot2), 红方=(top2, bot1)
                # 方案 B: 蓝方=(top1, bot1), 红方=(top2, bot2)
                for (b_anchor, r_anchor) in [([top1, bot2], [top2, bot1]), ([top1, bot1], [top2, bot2])]:
                    if blue_needed > 0 and middle_pool:
                        for cand_mid_b in combinations(middle_pool, blue_needed):
                            cand_mid_r = [p for p in middle_pool if p not in cand_mid_b]
                            team_b = b_anchor + list(cand_mid_b)
                            team_r = r_anchor + list(cand_mid_r)
                            
                            m_b = sum(get_player_mmr(p) for p in team_b)
                            m_r = sum(get_player_mmr(p) for p in team_r)
                            diff = abs(m_b - m_r)
                            if diff < best_diff:
                                best_diff = diff
                                best_b, best_r = team_b, team_r
                    else:
                        team_b = b_anchor + middle_pool
                        team_r = r_anchor
                        m_b = sum(get_player_mmr(p) for p in team_b)
                        m_r = sum(get_player_mmr(p) for p in team_r)
                        diff = abs(m_b - m_r)
                        if diff < best_diff:
                            best_diff = diff
                            best_b, best_r = team_b, team_r

                st.session_state["assigned_blue"] = best_b
                st.session_state["assigned_red"] = best_r
                st.session_state["split_mode"] = f"👑 大腿均分·带头大哥模式 ({len(best_b)}v{len(best_r)})"

        # 模式 3：随机盲盒
        elif random_btn:
            if total_chosen < 2:
                st.warning("⚠️ 至少选择 2 位玩家才能进行分队！")
            else:
                shuffled = list(selected_players)
                random.shuffle(shuffled)
                blue_size = total_chosen // 2
                st.session_state["assigned_blue"] = shuffled[:blue_size]
                st.session_state["assigned_red"] = shuffled[blue_size:]
                st.session_state["split_mode"] = f"🎲 盲盒随机分配 ({len(st.session_state['assigned_blue'])}v{len(st.session_state['assigned_red'])})"

        # 渲染对阵结果
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
                    <div style="font-size:0.95rem;line-height:1.6;color:#334155;">
                        <div><b>【海克斯内战·双方对阵阵容】</b></div>
                        <div><span style="color:#0284c7;font-weight:700;">🔵 蓝方 ({len(blue_team)}人 | 均分{blue_avg}):</span> {blue_line}</div>
                        <div><span style="color:#e11d48;font-weight:700;">🔴 红方 ({len(red_team)}人 | 均分{red_avg}):</span> {red_line}</div>
                        <div style="font-size:0.85rem;color:#64748b;margin-top:2px;">⚡ 战力差: {diff_score} 分 (人均差: {avg_diff} 分)</div>
                    </div>
                </div>
            """
            st.markdown(wechat_html, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 胜率总榜")

        df = df.sort_values(by=["胜率_num", "总场次", "KDA_num"], ascending=[False, False, False])

        table_rows = []
        for player_id, row in df.iterrows():
            wr_val = row["胜率_num"]
            wr_badge = f"<span style='color:#0284c7;font-weight:700;'>{wr_val}%</span>" if wr_val >= 50 else f"<span style='color:#e11d48;font-weight:700;'>{wr_val}%</span>"
            row_html = (
                f"<tr>"
                f"<td style='text-align:left;padding-left:16px;font-weight:700;color:#1e293b;'>{short_name(player_id)}</td>"
                f"<td>{int(row['总场次'])}</td>"
                f"<td>{int(row['胜场'])}</td>"
                f"<td>{int(row['负场'])}</td>"
                f"<td>{wr_badge}</td>"
                f"<td style='font-weight:700;color:#e11d48;'>{row['MMR']:.1f}</td>"
                f"<td>{row['场均击杀']:.1f}</td>"
                f"<td>{row['KD']:.2f}</td>"
                f"<td style='font-weight:700;'>{row['KDA_num']:.2f}</td>"
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
            f'<th style="text-align:left;padding-left:16px;">玩家</th>'
            f'<th>总场次</th><th>胜场</th><th>负场</th><th>胜率</th>'
            f'<th>MMR战力</th><th>场均击杀</th><th>KD</th><th>KDA</th><th>击杀</th><th>死亡</th><th>助攻</th>'
            f'</tr></thead>'
            f'<tbody>{"".join(table_rows)}</tbody>'
            f'</table></div>'
        )
        st.markdown(custom_table_html, unsafe_allow_html=True)

        # ---------------- 板块 E：雷达图 + 专属荣誉档案勋章馆 ----------------
        st.markdown("---")
        st.subheader("🎯 选手局内战术图谱与个人荣誉档案")

        active_player_options = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True)

        if not active_player_options:
            st.info("💡 暂无群友数据。录入对局截图后自动生成档案！")
        else:
            c_sel, _ = st.columns([2.5, 3.5])
            with c_sel:
                target_p = st.selectbox("选择要分析的群友档案：", active_player_options, format_func=lambda x: short_name(x))
            
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
                sample_desc = f"{valid_g} 局 (已剔除残局)"
            else:
                p_kills = float(df.loc[target_p, "击杀"] / p_g_total)
                p_deaths = float(df.loc[target_p, "死亡"] / p_g_total)
                p_assists = float(df.loc[target_p, "助攻"] / p_g_total)
                dmg_share = p_kills * 2.3
                taken_share = p_deaths * 2.4
                avg_kp = (p_kills + p_assists) / max(1.0, p_kills + p_assists + 5.0)
                sample_desc = f"{p_g_total} 局 (全局数据)"

            # 1. 伤害输出
            if dmg_share <= 20.0:
                score_dmg = 25.0 + (dmg_share / 20.0) * 35.0
            else:
                score_dmg = 60.0 + min(1.0, (dmg_share - 20.0) / 14.0) * 35.0
            score_dmg = max(18.0, min(96.0, score_dmg))

            # 2. 承受伤害
            if taken_share <= 20.0:
                score_tank = 25.0 + (taken_share / 20.0) * 35.0
            else:
                score_tank = 60.0 + min(1.0, (taken_share - 20.0) / 14.0) * 35.0
            score_tank = max(18.0, min(96.0, score_tank))

            # 3. 参团活跃
            if avg_kp <= 0.55:
                score_kp = 25.0 + (avg_kp / 0.55) * 35.0
            else:
                score_kp = 60.0 + min(1.0, (avg_kp - 0.55) / 0.22) * 35.0
            score_kp = max(18.0, min(96.0, score_kp))

            # 4 & 5. 收割与助攻
            ka_total = max(1.0, p_kills + p_assists)
            kill_bias = p_kills / ka_total
            
            k_base = min(1.0, p_kills / 10.0)
            score_kill = 25.0 + k_base * 45.0 + (kill_bias * 25.0)
            score_kill = max(20.0, min(95.0, score_kill))

            a_base = min(1.0, p_assists / 12.0)
            score_assist = 25.0 + a_base * 45.0 + ((1.0 - kill_bias) * 25.0)
            score_assist = max(20.0, min(95.0, score_assist))

            # 6. 保命能力
            if p_deaths <= 6.0:
                score_surv = 60.0 + ((6.0 - p_deaths) / 4.0) * 32.0
            else:
                score_surv = 60.0 - ((p_deaths - 6.0) / 5.0) * 32.0
            score_surv = max(20.0, min(95.0, score_surv))

            categories = ['伤害输出', '承受伤害', '参团活跃', '人头收割', '助攻开团', '保命能力']
            values = [round(score_dmg, 1), round(score_tank, 1), round(score_kp, 1), round(score_kill, 1), round(score_assist, 1), round(score_surv, 1)]

            if score_dmg >= 78 and score_kill >= 75:
                style_title, style_badge = "🗡️ 绝对主C / 团队核心火力", "delta-pink"
            elif score_tank >= 78 and score_assist >= 70:
                style_title, style_badge = "🛡️ 铁血开团 / 护航巨盾", "delta-blue"
            elif score_kp >= 78:
                style_title, style_badge = "🌐 全图游走 / 节奏发动机", "delta-gold"
            elif score_surv >= 75 and score_dmg <= 50:
                style_title, style_badge = "🕊️ 稳健拉扯 / 保命大师", "delta-gray"
            elif score_kill >= 75 and score_surv <= 45:
                style_title, style_badge = "🩸 突进刺客 / 绝命换头", "delta-pink"
            else:
                style_title, style_badge = "⚖️ 均衡打法 / 团队中坚", "delta-pink"

            dmg_disp = f"{dmg_share:.1f}%"
            tank_disp = f"{taken_share:.1f}%"
            kp_disp = f"{round(avg_kp * 100, 1)}%"

            # 近期状态判定 (取最近3场有效对局)
            p_hist = player_history[target_p]
            recent_games = p_hist["outcomes"][-3:] if p_hist["outcomes"] else []
            if len(recent_games) >= 2 and all(recent_games):
                recent_status = "🔥 连胜狂飙中"
                status_tip = "手感发烫：最近对局连续取胜，正处于爆发期！"
                status_color = "#e11d48"
            elif len(recent_games) >= 2 and not any(recent_games):
                recent_status = "🧊 连败急需吸氧"
                status_tip = "水逆预警：最近遭遇连败，急需给力队友带躺一把！"
                status_color = "#0284c7"
            else:
                recent_status = "⚖️ 状态起伏平稳"
                status_tip = "发挥稳定：胜负交替，在场上保持中流砥柱表现。"
                status_color = "#64748b"

            # ---------------- 严谨且趣味满分的勋章体系 ----------------
            badges_data = []

            # 1. 极致高光类（严格门槛）
            if p_hist["max_dmg_share"] >= 38.0 or score_dmg >= 92:
                badges_data.append((
                    "💥 血条消失术",
                    "【核爆级主C】曾在正规局单场打出 38%+ 恐怖输出占比，瞬间融化对手血条"
                ))
            if p_hist["max_taken_share"] >= 38.0 or score_tank >= 92:
                badges_data.append((
                    "🛡️ 叹息之壁",
                    "【铁血不坏身】曾在正规局单场吸收 38%+ 承伤占比，如高山般掩护全队"
                ))
            if p_hist["max_kill"] >= 16 or score_kill >= 92:
                badges_data.append((
                    "🩸 绝命赏金客",
                    "【超神收割机】曾在正规局单场斩获 16+ 击杀，无情屠戮敌阵"
                ))

            # 2. 趣味行为 & 梗标签
            if p_hist["max_death"] >= 10:
                badges_data.append((
                    "🎰 慈善赌圣",
                    "【全自动取款机】曾单场阵亡 10+ 次，给对手送出巨额悬赏经济！"
                ))
            if p_hist["min_death_win"] <= 1 and p_g_total >= 3:
                badges_data.append((
                    "🏕️ 泉水指挥官",
                    "【保分艺术家】胜局中曾打出 0 阵亡或仅死 1 次，拉扯保命玩成艺术"
                ))
            if p_hist["max_assist"] >= 18 or score_assist >= 90:
                badges_data.append((
                    "🚑 全图救护车",
                    "【团战发动机】单场豪取 18+ 助攻，全图到处都有他的控制与掩护"
                ))
            if p_hist["svp_cnt"] >= 2:
                badges_data.append((
                    "🪓 悲情孤勇者",
                    "【尽力局局长】多次在落败局打出 35%+ 火力或 11+ 杀，奈何带不动队友"
                ))
            if p_kills >= 6.0 and dmg_share <= 18.0:
                badges_data.append((
                    "🎯 致命K头怪",
                    "【经济吸收器】击杀数名列前茅但输出占比偏低，人头收割手艺纯熟"
                ))

            # 3. 真实全勤老将（杜绝 8 局就全勤）
            if total_games_all >= 12 and (p_g_total / total_games_all) >= 0.80:
                badges_data.append((
                    "🏛️ 内战活化石",
                    f"【真·全勤标兵】在总计 {total_games_all} 场内战中出战 {p_g_total} 场 (出勤率 {(p_g_total/total_games_all)*100:.0f}%)"
                ))
            elif p_g_total >= 10:
                badges_data.append((
                    "🎖️ 资深百战将",
                    f"【久经沙场】内战累计出战已达 {p_g_total} 局，经验老道的中流砥柱"
                ))

            if not badges_data:
                badges_data.append((
                    "🌱 未来可期",
                    "【新晋潜能股】正在积蓄战力，距离解锁首个高光/趣味勋章仅差一步"
                ))

            badges_html = "".join([
                f'<span class="badge-tag" title="{tip}">{name}</span>' 
                for name, tip in badges_data
            ])

            col_radar, col_detail = st.columns([1.2, 1])

            with col_radar:
                st.markdown(generate_radar_svg(values, categories), unsafe_allow_html=True)

            with col_detail:
                st.markdown(f"""
                    <div class="stat-card" style="margin-top:20px;">
                        <div class="stat-card-title">局内战术角色画像</div>
                        <div class="stat-card-player">{short_name(target_p)}</div>
                        <div class="stat-card-delta {style_badge}">{style_title}</div>
                        <div style="font-size:0.88rem;color:#475569;line-height:2.0;margin-top:10px;">
                            <div>• <b>有效样本来源</b>: {sample_desc}</div>
                            <div>• <b>场均伤害占比</b>: <span style="color:#e11d48;font-weight:700;">{dmg_disp}</span></div>
                            <div>• <b>场均承伤占比</b>: <span style="color:#0284c7;font-weight:700;">{tank_disp}</span></div>
                            <div>• <b>平均团战参团率</b>: <span style="color:#ca8a04;font-weight:700;">{kp_disp}</span></div>
                            <div>• <b>场均基础战绩</b>: {p_kills:.1f} 杀 / {p_deaths:.1f} 亡 / {p_assists:.1f} 助</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # 个人专属档案与成就勋章卡
            st.markdown(f"""
                <div class="stat-card" style="margin-top:6px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #fecdd3;padding-bottom:8px;margin-bottom:10px;">
                        <span style="font-size:0.95rem;font-weight:800;color:#9f1239;">🏅 【{short_name(target_p)}】个人荣誉与成就档案馆</span>
                        <span class="badge-tag" title="{status_tip}" style="font-size:0.82rem;font-weight:700;color:{status_color};background:#ffffff;margin:0;">{recent_status}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;font-size:0.88rem;color:#334155;margin-bottom:10px;">
                        <div>⚡ <b>正规局单场最高击杀</b>: <span style="color:#e11d48;font-weight:700;">{p_hist['max_kill'] if p_hist['max_kill'] > 0 else '--'} 杀</span></div>
                        <div>💥 <b>正规局最高输出占比</b>: <span style="color:#e11d48;font-weight:700;">{f"{p_hist['max_dmg_share']:.1f}%" if p_hist['max_dmg_share'] > 0 else '--'}</span></div>
                        <div>🛡️ <b>正规局最高承伤占比</b>: <span style="color:#0284c7;font-weight:700;">{f"{p_hist['max_taken_share']:.1f}%" if p_hist['max_taken_share'] > 0 else '--'}</span></div>
                        <div>🕊️ <b>胜局最低阵亡纪录</b>: <span style="color:#0284c7;font-weight:700;">{p_hist['min_death_win'] if p_hist['min_death_win'] != 999 else '--'} 次</span></div>
                    </div>
                    <div style="border-top:1px dashed #fecdd3;padding-top:8px;">
                        <span style="font-size:0.82rem;color:#881337;font-weight:700;margin-right:6px;">已解锁成就勋章 (鼠标悬停查看详情):</span>
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

# ---------------- 主界面 3：战绩录入 (置底) ----------------
st.markdown("---")
st.subheader("📥 战绩录入")

with st.form("upload_box", clear_on_submit=False):
    files = st.file_uploader("选择或拖拽战绩截图（支持批量多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    submit_btn = st.form_submit_button("🚀 开始录入战绩", type="primary")

if submit_btn:
    if not files:
        st.warning("⚠️ 请先选择战绩截图！")
    elif not key:
        st.warning("⚠️ 请在左侧输入 DashScope API Key！")
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
