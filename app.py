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

# ---------------- 温润淡粉 (Sakura Pastel) 精准覆盖 CSS ----------------
st.markdown("""
<style>
/* 1. 全局背景：柔和樱花淡粉渐变 */
.stApp {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe4e6 50%, #fed7aa 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 2. 顶部主标题渐变 */
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

/* 3. 核心修复 1：三大连麦作战室专属发光微光按钮（找回美丽的边框与色彩） */
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
/* 大厅专属：暖金微光 */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%) !important;
    border: 2px solid #eab308 !important;
    box-shadow: 0 4px 14px rgba(234, 179, 8, 0.3) !important;
    color: #854d0e !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(234, 179, 8, 0.5) !important;
}
/* 蓝方专属：海蓝微光 */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
    border: 2px solid #0284c7 !important;
    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
    color: #0369a1 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.5) !important;
}
/* 红方专属：绯红微光 */
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%) !important;
    border: 2px solid #e11d48 !important;
    box-shadow: 0 4px 14px rgba(225, 29, 72, 0.3) !important;
    color: #9f1239 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a:hover {
    box-shadow: 0 6px 20px rgba(225, 29, 72, 0.5) !important;
}

/* 4. 核心修复 2：彻底消灭下拉菜单透明！强制纯白实体背景，拒绝文字穿透重叠 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
ul[data-baseweb="menu"],
div[data-baseweb="select"] ul {
    background-color: #ffffff !important;
    background: #ffffff !important;
    opacity: 1 !important;
    border: 2px solid #f472b6 !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 25px rgba(225, 29, 72, 0.18) !important;
}
li[data-baseweb="menu-item"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #334155 !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
}
li[data-baseweb="menu-item"]:hover {
    background-color: #fce7f3 !important;
    color: #be185d !important;
}

/* 5. 多选框外壳与选中 Tag */
div[data-testid="stMultiSelect"] > div > div,
div[data-baseweb="select"] {
    background-color: #ffffff !important;
    border: 1px solid #fbcfe8 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 6px rgba(244, 114, 182, 0.1) !important;
}
div[data-baseweb="select"] input {
    background-color: transparent !important;
    color: #334155 !important;
}
div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
span[data-baseweb="tag"] {
    background: #fce7f3 !important;
    border: 1px solid #f472b6 !important;
    border-radius: 6px !important;
    padding: 2px 8px !important;
}
span[data-baseweb="tag"] span {
    color: #9d174d !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
}
span[data-baseweb="tag"] svg {
    fill: #db2777 !important;
    color: #db2777 !important;
}

/* 6. 输入框与普通按钮 */
input, div[data-baseweb="input"] {
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

/* 7. 卡片系统 (纯白透亮 + 粉色微影) */
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

/* 8. 对阵红蓝看板与复制区 */
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

/* 9. 表格 */
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

/* 侧边栏 */
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
    return str(full_name).split("#")[0]

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.header("⚙️ 系统管理")
    default_key = st.secrets.get("DASHSCOPE_API_KEY", "") if hasattr(st, "secrets") and "DASHSCOPE_API_KEY" in st.secrets else ""
    key = st.text_input("DashScope API Key", value=default_key, type="password")

    records = load_records()
    st.metric("总计收录对局", f"{len(records)} 局")

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
            p_rows.append({
                "阵营": p.get("team", ""),
                "玩家ID": short_name(p.get("player_name", "")),
                "K/D/A": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
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

# ---------------- 主界面 2：数据汇总与分析 ----------------
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

    stats = defaultdict(lambda: {"总场次": 0, "胜场": 0, "负场": 0, "击杀": 0, "死亡": 0, "助攻": 0})
    synergy_stats = defaultdict(lambda: {"同队场次": 0, "胜场": 0, "负场": 0})
    nemesis_stats = defaultdict(lambda: {"交手场次": 0, "p1_wins": 0, "p2_wins": 0})

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

            k, d, a = int(p.get("kills", 0)), int(p.get("deaths", 0)), int(p.get("assists", 0))
            is_win = bool(p.get("is_winner"))

            stats[fname]["总场次"] += 1
            stats[fname]["胜场" if is_win else "负场"] += 1
            stats[fname]["击杀"] += k
            stats[fname]["死亡"] += d
            stats[fname]["助攻"] += a

            if k > max_single_kill["val"]:
                max_single_kill = {"player": fname, "val": k, "game_idx": game_idx + 1}
            if d > max_single_death["val"]:
                max_single_death = {"player": fname, "val": d, "game_idx": game_idx + 1}
            if a > max_single_assist["val"]:
                max_single_assist = {"player": fname, "val": a, "game_idx": game_idx + 1}

            team_side = str(p.get("team", "")).upper()
            if team_side == "BLUE":
                blue_team.append((fname, is_win))
            elif team_side == "RED":
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

        # ---------------- 板块 D：赛前红蓝对阵作战室 ----------------
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

        col_b1, col_b2, _ = st.columns([1.5, 1.5, 3])
        with col_b1:
            balance_btn = st.button("⚖️ 战力天平平衡分配", type="primary", use_container_width=True)
        with col_b2:
            random_btn = st.button("🎲 听天由命随机盲盒", use_container_width=True)

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
                st.session_state["split_mode"] = f"⚖️ 战力天平最优平衡 ({len(best_b)}v{len(best_r)})"

        elif random_btn:
            if total_chosen < 2:
                st.warning("⚠️ 至少选择 2 位玩家才能进行分队！")
            else:
                shuffled = list(selected_players)
                random.shuffle(shuffled)
                blue_size = total_chosen // 2
                st.session_state["assigned_blue"] = shuffled[:blue_size]
                st.session_state["assigned_red"] = shuffled[blue_size:]
                st.session_state["split_mode"] = f"🎲 听天由命盲盒随机 ({len(st.session_state['assigned_blue'])}v{len(st.session_state['assigned_red'])})"

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
