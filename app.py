import os
import json
import hashlib
import time
import base64
import difflib
import re
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

st.set_page_config(page_title="峡谷内战控制台", page_icon="⚔️", layout="wide")

# ---------------- 高级深海蓝微光 + 侧边栏文字穿透高亮 CSS ----------------
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

    /* 侧边栏所有文字强力穿透提亮，彻底杜绝隐藏 */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 22, 36, 0.96) !important;
        border-right: 1px solid rgba(56, 189, 248, 0.2) !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #fef08a !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] summary {
        color: #f1f5f9 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    section[data-testid="stSidebar"] summary:hover {
        color: #38bdf8 !important;
    }
    section[data-testid="stSidebar"] input {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
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
    /* 大厅主语音 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.25), rgba(202, 138, 4, 0.15)) !important;
        border: 1px solid rgba(253, 224, 71, 0.5) !important;
        box-shadow: 0 4px 15px rgba(234, 179, 8, 0.2) !important;
        color: #fef9c3 !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a:hover {
        box-shadow: 0 6px 20px rgba(234, 179, 8, 0.4) !important;
    }
    /* 蓝方作战室 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.35), rgba(2, 132, 199, 0.2)) !important;
        border: 1px solid rgba(56, 189, 248, 0.7) !important;
        box-shadow: 0 4px 18px rgba(14, 165, 233, 0.35) !important;
        color: #f0f9ff !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a:hover {
        box-shadow: 0 6px 24px rgba(56, 189, 248, 0.6) !important;
    }
    /* 红方作战室 */
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

    /* 胜率榜名字超链接按钮美化 */
    div.player-click-box button {
        background: rgba(56, 189, 248, 0.12) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 6px !important;
        color: #e0f2fe !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 3px 8px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    div.player-click-box button:hover {
        background: rgba(56, 189, 248, 0.28) !important;
        border-color: #38bdf8 !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.5) !important;
        transform: translateY(-1px);
    }

    /* AI 锐评弹窗卡片全局样式 */
    .ai-modal-box {
        background: radial-gradient(circle at 50% 10%, #1a385c 0%, #0d1e31 100%);
        border: 1px solid rgba(56, 189, 248, 0.5);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.7);
        margin: 15px 0 25px 0;
        animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .ai-tag {
        display: inline-block;
        background: rgba(234, 179, 8, 0.25);
        color: #fef08a;
        border: 1px solid rgba(234, 179, 8, 0.5);
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.85rem;
        font-weight: 800;
        margin-left: 10px;
    }
    .ai-quote {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #38bdf8;
        padding: 10px 14px;
        margin: 14px 0;
        color: #bae6fd;
        font-style: italic;
        font-size: 0.95rem;
        border-radius: 0 8px 8px 0;
    }
    .ai-roast-body {
        color: #f1f5f9;
        font-size: 0.95rem;
        line-height: 1.7;
        padding: 8px 4px;
    }

    /* 底部上传框 */
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

def generate_player_roast(player_name, p_stats, api_key):
    """调用通义千问大模型进行趣味电竞打法点评"""
    if not api_key:
        return {
            "tag": "神秘大掌门",
            "quote": "人在峡谷飘，全凭感觉捞。",
            "roast": "请在左侧侧边栏填入正确的 DashScope API Key，即可解锁专业电竞解说锐评与战术定位！"
        }
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=15.0
    )
    
    prompt = f"""
你是一位毒舌幽默、深谙英雄联盟内战文化的金牌电竞解说兼老六裁判。
请根据玩家【{player_name}】的内战统计数据，生成一份风趣幽默、一针见血的选手打法风格鉴定书。

【玩家数据】：
- 总出场: {p_stats['总场次']} 场
- 战绩: {p_stats['胜场']} 胜 / {p_stats['负场']} 负 (胜率: {p_stats['胜率_num']}%)
- KD击杀死亡比: {p_stats['KD']}
- 综合KDA: {p_stats['KDA']}
- 总击杀: {p_stats['击杀']} | 总阵亡: {p_stats['死亡']} | 总助攻: {p_stats['助攻']}

【要求】：
1. 必须输出标准 JSON，格式如下：
{{
    "tag": "4-6字选手风格标签（如：峡谷收税官、敢死队大队长、躺赢界天花板、军训受害人）",
    "quote": "一句精辟搞笑的经典语录或座右铭（15字内）",
    "roast": "一段120字左右的风趣锐评：结合他的KDA、击杀或阵亡特点点评他的打法风格、在队伍中的战术定位（是大爹、诱饵、气氛组还是团灭发动机）"
}}
2. 语言生动风趣、带电竞梗（如K头、白给、尽力局、红温），评价务必贴合数据。
"""
    try:
        resp = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        raw = resp.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(match.group(0) if match else raw)
    except Exception as e:
        return {
            "tag": "电竞隐世高人",
            "quote": "顺风全靠吹，逆风全是推。",
            "roast": f"AI 解说在赶来的路上遭遇反蹲，暂未生成评论（报错: {e}）。"
        }

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
st.title("⚔️ 峡谷内战控制台")

cfg = load_config()
c1, c2, c3 = st.columns(3)
with c1:
    st.link_button("🎙️ 进入大厅语音", cfg.get("main_voice", "https://kook.top/"), use_container_width=True)
with c2:
    st.link_button("🔵 进蓝方作战室", cfg.get("blue_voice", "https://kook.top/"), use_container_width=True)
with c3:
    st.link_button("🔴 进红方作战室", cfg.get("red_voice", "https://kook.top/"), use_container_width=True)

st.write("")

# ---------------- 主界面 2：趣味头衔、双人羁绊与胜率总榜 ----------------
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

    synergy_stats = defaultdict(lambda: {"同队场次": 0, "胜场": 0, "负场": 0})

    for r in records:
        blue_team = []
        red_team = []
        
        for p in r.get("players", []):
            raw_pname = p.get("player_name", "")
            if not raw_pname:
                continue
            fname = get_final_name(raw_pname)

            stats[fname]["总场次"] += 1
            is_win = bool(p.get("is_winner"))
            if is_win:
                stats[fname]["胜场"] += 1
            else:
                stats[fname]["负场"] += 1
            stats[fname]["击杀"] += int(p.get("kills", 0))
            stats[fname]["死亡"] += int(p.get("deaths", 0))
            stats[fname]["助攻"] += int(p.get("assists", 0))

            team_side = str(p.get("team", "")).upper()
            if team_side == "BLUE":
                blue_team.append((fname, is_win))
            elif team_side == "RED":
                red_team.append((fname, is_win))

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

    df = pd.DataFrame.from_dict(stats, orient="index")

    if not df.empty:
        df["胜率_num"] = (df["胜场"] / df["总场次"] * 100).round(1)
        df["KD"] = (df["击杀"] / df["死亡"].replace(0, 1)).round(2)
        df["KDA_num"] = ((df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)).round(2)
        df["KDA"] = df["KDA_num"].astype(str)

        # 1. 4 大单人头衔
        kda_candidates = df[df["总场次"] >= 2]
        if kda_candidates.empty:
            kda_candidates = df
            
        top_kda_name = kda_candidates.sort_values(by="KDA_num", ascending=False).index[0]
        top_kill_name = df.sort_values(by="击杀", ascending=False).index[0]
        top_death_name = df.sort_values(by="死亡", ascending=False).index[0]
        top_assist_name = df.sort_values(by="助攻", ascending=False).index[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">KDA王</div>
                    <div class="esport-card-player">{short_name(top_kda_name)}</div>
                    <div class="esport-card-delta delta-cyan">KDA {df.loc[top_kda_name, 'KDA_num']}</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">击杀王</div>
                    <div class="esport-card-player">{short_name(top_kill_name)}</div>
                    <div class="esport-card-delta delta-gold">{int(df.loc[top_kill_name, '击杀'])} 杀</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">白给王</div>
                    <div class="esport-card-player">{short_name(top_death_name)}</div>
                    <div class="esport-card-delta delta-red">{int(df.loc[top_death_name, '死亡'])} 阵亡</div>
                </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
                <div class="esport-card">
                    <div class="esport-card-title">助攻王</div>
                    <div class="esport-card-player">{short_name(top_assist_name)}</div>
                    <div class="esport-card-delta delta-cyan">{int(df.loc[top_assist_name, '助攻'])} 助攻</div>
                </div>
            """, unsafe_allow_html=True)

        # 2. 双人羁绊
        if synergy_stats:
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
            if not syn_df.empty:
                syn_candidates = syn_df[syn_df["games"] >= 2]
                if syn_candidates.empty:
                    syn_candidates = syn_df
                
                best_pair = syn_candidates.sort_values(by=["win_rate", "games"], ascending=[False, False]).iloc[0]
                worst_pair = syn_candidates.sort_values(by=["win_rate", "games"], ascending=[True, False]).iloc[0]

                st.write("")
                col_syn1, col_syn2 = st.columns(2)
                with col_syn1:
                    st.markdown(f"""
                        <div class="esport-card">
                            <div class="esport-card-title">黄金搭档</div>
                            <div class="esport-card-player">{best_pair['pair_name']}</div>
                            <div class="esport-card-delta delta-cyan">{int(best_pair['wins'])}胜{int(best_pair['losses'])}负 ({round(best_pair['win_rate']*100, 1)}%)</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_syn2:
                    st.markdown(f"""
                        <div class="esport-card">
                            <div class="esport-card-title">难兄难弟</div>
                            <div class="esport-card-player">{worst_pair['pair_name']}</div>
                            <div class="esport-card-delta delta-red">{int(worst_pair['wins'])}胜{int(worst_pair['losses'])}负 ({round(worst_pair['win_rate']*100, 1)}%)</div>
                        </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 胜率总榜 (点击玩家名即可查看 AI 风格锐评)")

        # 排序
        df = df.sort_values(by=["胜率_num", "总场次", "KDA_num"], ascending=[False, False, False])

        # ---------------- AI 锐评全端兼容模态框 ----------------
        if "selected_player" in st.session_state and st.session_state["selected_player"]:
            target_pid = st.session_state["selected_player"]
            if target_pid in df.index:
                p_row = df.loc[target_pid].to_dict()
                target_name = short_name(target_pid)
                
                cache_key = f"roast_{target_pid}_{p_row['总场次']}_{p_row['胜场']}"
                if cache_key not in st.session_state:
                    with st.spinner(f"🎙️ 金牌解说正在锐评【{target_name}】的比赛录像..."):
                        st.session_state[cache_key] = generate_player_roast(target_name, p_row, key)
                
                roast_data = st.session_state[cache_key]
                
                # 弹出精美磨砂锐评卡片
                st.markdown(f"""
                    <div class="ai-modal-box">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-size:1.5rem; font-weight:800; color:#ffffff;">{target_name}</span>
                                <span class="ai-tag">{roast_data.get('tag', '特约嘉宾')}</span>
                            </div>
                            <div style="color:#94a3b8; font-size:0.9rem;">内战出场: {int(p_row['总场次'])} 局 | 胜率: {p_row['胜率_num']}%</div>
                        </div>
                        <div class="ai-quote">“{roast_data.get('quote', '战术撤退，绝非白给。')}”</div>
                        <div class="ai-roast-body">{roast_data.get('roast', '')}</div>
                        <div style="display:flex; gap:16px; margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.1); font-size:0.88rem; color:#cbd5e1;">
                            <div>击杀比 (KD): <b style="color:#38bdf8;">{p_row['KD']}</b></div>
                            <div>综合 KDA: <b style="color:#fef08a;">{p_row['KDA']}</b></div>
                            <div>击杀/阵亡/助攻: <b>{int(p_row['击杀'])} / {int(p_row['死亡'])} / {int(p_row['助攻'])}</b></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("✖️ 收起选手评价", key="close_roast_btn"):
                    st.session_state["selected_player"] = None
                    st.rerun()

        # 表头
        col_widths = [2.2, 1, 1, 1, 1.2, 1.1, 1.1, 1, 1, 1]
        th_cols = st.columns(col_widths)
        headers = ["玩家 (点击)", "总场次", "胜场", "负场", "胜率", "KD比", "KDA", "击杀", "死亡", "助攻"]
        for col, title in zip(th_cols, headers):
            col.markdown(f"<div style='text-align:center; font-weight:700; color:#fef08a; padding:6px 0;'>{title}</div>", unsafe_allow_html=True)

        # 数据行渲染
        for player_id, row in df.iterrows():
            p_name = short_name(player_id)
            wr_val = row["胜率_num"]
            wr_badge = f"<span style='color:#38bdf8;font-weight:700;'>{wr_val}%</span>" if wr_val >= 50 else f"<span style='color:#fb7185;font-weight:700;'>{wr_val}%</span>"
            kd_str = f"{row['KD']:.2f}"
            kda_str = f"{row['KDA_num']:.2f}"

            r_cols = st.columns(col_widths)
            
            with r_cols[0]:
                st.markdown('<div class="player-click-box">', unsafe_allow_html=True)
                if st.button(f"🔍 {p_name}", key=f"btn_p_{player_id}"):
                    st.session_state["selected_player"] = player_id
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            r_cols[1].markdown(f"<div style='text-align:center; padding-top:6px;'>{int(row['总场次'])}</div>", unsafe_allow_html=True)
            r_cols[2].markdown(f"<div style='text-align:center; padding-top:6px;'>{int(row['胜场'])}</div>", unsafe_allow_html=True)
            r_cols[3].markdown(f"<div style='text-align:center; padding-top:6px;'>{int(row['负场'])}</div>", unsafe_allow_html=True)
            r_cols[4].markdown(f"<div style='text-align:center; padding-top:6px;'>{wr_badge}</div>", unsafe_allow_html=True)
            r_cols[5].markdown(f"<div style='text-align:center; padding-top:6px; color:#38bdf8; font-weight:700;'>{kd_str}</div>", unsafe_allow_html=True)
            r_cols[6].markdown(f"<div style='text-align:center; padding-top:6px; color:#fef08a; font-weight:700;'>{kda_str}</div>", unsafe_allow_html=True)
            r_cols[7].markdown(f"<div style='text-align:center; padding-top:6px;'>{int(row['击杀'])}</div>", unsafe_allow_html=True)
            r_cols[8].markdown(f"<div style='text-align:center; padding-top:6px;'>{int(row['死亡'])}</div>", unsafe_allow_html=True)
            r_cols[9].markdown(f"<div style='text-align:center; padding-top:6px;'>{int(row['助攻'])}</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom: 1px solid rgba(255,255,255,0.06); margin: 3px 0;'></div>", unsafe_allow_html=True)

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
