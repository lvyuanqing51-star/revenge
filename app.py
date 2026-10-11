import os
import json
import hashlib
import time
import base64
import difflib
import re
import random
import math
import urllib.request
from io import BytesIO
from itertools import combinations
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI, NotFoundError

DATA_FILE = "records.json"
CONFIG_FILE = "config.json"
TARGET_QIANQIU = "千秋种我一栗卿#52652"

st.set_page_config(
    page_title="海克斯内战",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- 专业级·黑金与醇厚酒红视觉系统 ----------------
st.markdown("""
<style>
:root, [data-theme="light"], .stApp { --primary-color: #881337 !important; }
.stApp {
    background: radial-gradient(circle at 10% 20%, #fff1f2 0%, #fff5f5 45%, #fed7aa 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
}
.app-header-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(254, 242, 242, 0.92) 100%);
    backdrop-filter: blur(14px); border: 1.5px solid #fecdd3; border-left: 6px solid #881337;
    border-radius: 16px; padding: 16px 26px; margin-bottom: 22px;
    box-shadow: 0 6px 24px rgba(114, 9, 44, 0.08);
}
.header-title {
    font-size: 1.70rem; font-weight: 900;
    background: linear-gradient(90deg, #881337 0%, #b91c1c 45%, #d97706 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px;
}
div[data-testid="stLinkButton"] a {
    border-radius: 14px !important; font-weight: 800 !important; font-size: 0.96rem !important;
    padding: 12px 18px !important; transition: all 0.28s ease !important; text-align: center;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #1e1b18 0%, #292524 50%, #1c1917 100%) !important;
    border: 2px solid #d97706 !important; color: #fef08a !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #0c1e33 0%, #1e293b 50%, #0f172a 100%) !important;
    border: 2px solid #38bdf8 !important; color: #e0f2fe !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #380718 0%, #4c0519 50%, #1f040d 100%) !important;
    border: 2px solid #f43f5e !important; color: #ffe4e6 !important;
}
div[data-baseweb="tab-list"] {
    gap: 12px !important; background: transparent !important;
    border-bottom: 2.5px solid #fecdd3 !important; margin-bottom: 22px !important;
}
div[data-baseweb="tab"] {
    background: #ffffff !important; border: 1.5px solid #fbcfe8 !important; border-bottom: none !important;
    border-radius: 12px 12px 0 0 !important; color: #881337 !important; font-weight: 800 !important;
    font-size: 1.06rem !important; padding: 11px 22px !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%) !important;
    color: #72092c !important; border-top: 3.5px solid #72092c !important;
}
.card-panel {
    background: #ffffff; border: 1.2px solid #fecdd3; border-radius: 14px;
    padding: 20px 24px; margin-bottom: 18px; box-shadow: 0 4px 16px rgba(114, 9, 44, 0.06);
}
.panel-header-title {
    font-size: 1.15rem; font-weight: 800; color: #72092c; margin-bottom: 14px;
    border-left: 4px solid #72092c; padding-left: 10px;
}
.metric-stat-box {
    background: #ffffff; border: 1.2px solid #fecdd3; border-radius: 14px;
    padding: 16px 18px; box-shadow: 0 3px 10px rgba(114, 9, 44, 0.05);
}
.metric-title { font-size: 0.85rem; font-weight: 700; color: #881337; margin-bottom: 4px; }
.metric-val-main { font-size: 1.45rem; font-weight: 900; color: #1e293b; }
.metric-badge {
    font-size: 0.80rem; font-weight: 800; padding: 3px 9px; border-radius: 6px;
    display: inline-block; margin-top: 5px;
}
.badge-pink { background: #ffe4e6; color: #9f1239; }
.badge-gold { background: #fef9c3; color: #b45309; }
.badge-blue { background: #e0f2fe; color: #0369a1; }
.badge-gray { background: #f1f5f9; color: #64748b; }
.badge-burgundy { background: #fce7f3; color: #72092c; border: 1px solid #f472b6; }
.badge-tag {
    display: inline-block; background: #fff1f2; border: 1px solid #fecdd3;
    color: #72092c; font-size: 0.84rem; font-weight: 700; padding: 4px 11px;
    border-radius: 8px; margin: 3px 6px 3px 0; cursor: help;
}
.ladder-table-box {
    width: 100%; overflow-x: auto; border: 1.5px solid #fecdd3; border-radius: 14px;
    background: #ffffff; margin: 10px 0 22px 0;
}
.ladder-table { width: 100%; border-collapse: collapse; font-size: 0.94rem; text-align: center; }
.ladder-table th {
    background: linear-gradient(180deg, #fff1f2 0%, #ffe4e6 100%); color: #72092c;
    font-weight: 800; padding: 14px 10px; border-bottom: 2px solid #fbcfe8;
}
.ladder-table td { padding: 12px 8px; border-bottom: 1px solid #fff1f2; }
.rank-1 { background: rgba(254, 240, 138, 0.25) !important; }
.rank-2 { background: rgba(241, 245, 249, 0.4) !important; }
.rank-3 { background: rgba(254, 215, 170, 0.22) !important; }
button[kind="primary"] {
    background: linear-gradient(135deg, #72092c 0%, #9f1239 100%) !important;
    border: 1px solid #be123c !important; color: #ffffff !important;
    border-radius: 10px !important; font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- 0. 基础配置与压缩 ----------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"main_voice": "https://kook.top/", "blue_voice": "https://kook.top/", "red_voice": "https://kook.top/"}

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
            img = img.resize((max_w, int(h * (max_w / float(w)))), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        return base64.b64encode(img_bytes).decode('utf-8')

# ---------------- 1. 名字清洗与归一 ----------------
def clean_player_name_strict(name: str) -> str:
    if not name: return ""
    s = re.sub(r'[\s\u200b\ufeff\u3000\r\n\t]+', '', str(name)).replace("＃", "#").replace("—", "-").replace("–", "-")
    if ("千秋" in s) or ("52652" in s) or ("一栗卿" in s) or ("一粟卿" in s) or ("栗卿" in s) or ("粟卿" in s):
        return TARGET_QIANQIU
    return s.replace("丶", "").replace("、", "").replace(",", "")

def build_canonical_name_map(all_raw_names: list) -> dict:
    mapping, clusters = {}, []
    for raw in all_raw_names:
        cleaned = clean_player_name_strict(raw)
        if not cleaned: continue
        if cleaned == TARGET_QIANQIU:
            mapping[raw] = TARGET_QIANQIU
            continue
        matched = None
        for c in clusters:
            if cleaned == c or difflib.SequenceMatcher(None, cleaned, c).ratio() >= 0.88:
                matched = c
                break
        if matched:
            mapping[raw] = matched
        else:
            clusters.append(cleaned)
            mapping[raw] = cleaned
    return mapping

def get_md5(data): return hashlib.md5(data).hexdigest()

# ---------------- 1.5 GitHub 云端持久化引擎 ----------------
def get_secret(name, default=""):
    # 未配置 secrets.toml 时，仍允许打开页面和使用本地战绩。
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


def get_github_auth():
    return get_secret("GITHUB_TOKEN"), get_secret("GITHUB_REPO")

def fetch_records_from_github():
    token, repo = get_github_auth()
    if not token or not repo: return None
    url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "HexLeagueApp"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parsed = json.loads(base64.b64decode(data.get("content", "")).decode('utf-8'))
            if isinstance(parsed, list): return parsed
    except Exception:
        pass
    return None

def push_records_to_github(records):
    token, repo = get_github_auth()
    if not token or not repo: return False
    url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "HexLeagueApp"}
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            sha = json.loads(resp.read().decode('utf-8')).get("sha")
    except Exception:
        pass
    payload = {"message": "Auto-sync records.json", "content": base64.b64encode(json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')}
    if sha: payload["sha"] = sha
    try:
        put_req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
        with urllib.request.urlopen(put_req, timeout=10):
            return True
    except Exception:
        return False

def load_records():
    local_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, list): local_data = d
        except Exception:
            local_data = []
    if "gh_synced" not in st.session_state:
        st.session_state["gh_synced"] = True
        cloud_data = fetch_records_from_github()
        if cloud_data and len(cloud_data) >= len(local_data):
            try:
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(cloud_data, f, ensure_ascii=False, indent=2)
            except Exception: pass
            return remove_result_banners(cloud_data)
    return remove_result_banners(local_data)

def save_records(records, sync_cloud=True):
    records = remove_result_banners(records)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    if sync_cloud:
        return push_records_to_github(records)
    return None

# ---------------- 智能视觉识别 ----------------
def is_result_banner(name):
    # 只匹配完整标题；“敌方胜利#12345”等真实 ID 不按标题删除。
    compact = re.sub(r"[\s\u200b\ufeff]+", "", str(name or ""))
    compact = compact.strip("!！:：。.")
    return compact in {"敌方胜利", "我方胜利", "敌方失败", "我方失败", "对方胜利", "对方失败"}


def remove_result_banners(records):
    # 历史文件、云端同步和备份恢复均可能带入旧的误识别条目。
    # 只排除标题行，保留该局其他玩家及全部对局信息。
    cleaned = []
    for record in records:
        copy = dict(record)
        copy["players"] = [
            dict(player) for player in record.get("players", [])
            if not is_result_banner(player.get("player_name"))
            and not is_result_banner(clean_player_name_strict(player.get("player_name", "")))
        ]
        cleaned.append(copy)
    return cleaned


def validate_recognition(result):
    if not isinstance(result, dict) or not isinstance(result.get("players"), list):
        raise ValueError("识别结果缺少玩家列表，本次未保存，请重新上传清晰的完整结算截图。")
    winner = str(result.get("winning_team", "")).strip().upper()
    if winner not in {"BLUE", "RED"}:
        raise ValueError("无法确定蓝红双方胜负，本次未保存；请上传能看清双方阵营的截图。")
    players = []
    for raw_player in result["players"]:
        if not isinstance(raw_player, dict):
            raise ValueError("玩家数据格式异常，本次未保存。")
        if is_result_banner(raw_player.get("player_name")):
            continue
        player = dict(raw_player)
        name = clean_player_name_strict(player.get("player_name", ""))
        side = str(player.get("team", "")).strip().upper()
        if not name or side not in {"BLUE", "RED"}:
            raise ValueError("存在无法确认的玩家 ID 或阵营，本次未保存，请重新上传截图。")
        player.update(player_name=name, team=side, is_winner=(side == winner))
        for field in ("kills", "deaths", "assists"):
            value = player.get(field)
            if isinstance(value, bool) or value is None or not re.fullmatch(r"\d+", str(value)):
                raise ValueError(f"玩家 {name} 的 KDA 不完整，本次未保存。")
            player[field] = int(value)
        players.append(player)
    if not players:
        raise ValueError("排除胜负标题后没有识别到有效玩家，本次未保存。")
    if len({p["player_name"] for p in players}) != len(players):
        raise ValueError("玩家 ID 存在重复，本次未保存，请检查截图清晰度。")
    return {**result, "winning_team": winner, "players": players}


def get_vision_settings():
    model_name = st.session_state.get(
        "vision_model", get_secret("DASHSCOPE_MODEL", "qwen3-vl-plus")
    ).strip()
    base_url = st.session_state.get(
        "vision_base_url",
        get_secret("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    ).strip().rstrip("/")
    if not model_name or not base_url:
        raise ValueError("请在左侧模型接口设置中填写模型 ID 和 Base URL。")
    return {
        "model_name": model_name,
        "base_url": base_url,
        "optimize_image": st.session_state.get("optimize_image", True),
    }


def prepare_vision_image(img_bytes, optimize=True):
    with Image.open(BytesIO(img_bytes)) as img:
        original_mime = Image.MIME.get(img.format, "image/jpeg")
        if not optimize:
            return base64.b64encode(img_bytes).decode("utf-8"), original_mime
        original_size = img.size
        # 限制宽度，保留长截图的高度，避免将小字缩得过小。
        if img.width > 1920:
            img = img.resize(
                (1920, max(1, round(img.height * 1920 / img.width))),
                Image.Resampling.LANCZOS,
            )
        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=92)
        encoded = buf.getvalue()
        if img.size == original_size and len(encoded) >= len(img_bytes):
            return base64.b64encode(img_bytes).decode("utf-8"), original_mime
        return base64.b64encode(encoded).decode("utf-8"), "image/jpeg"


def analyze_image(img_bytes, api_key, settings=None):
    # 工作线程传入配置快照，不读取 Streamlit 的 session_state 或 secrets。
    if settings is None:
        settings = get_vision_settings()
    model_name, base_url = settings["model_name"], settings["base_url"]
    b64, image_mime = prepare_vision_image(img_bytes, settings.get("optimize_image", True))
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=45.0
    )
    prompt = (
        "这是英雄联盟掌盟对局结算截图。\n"
        "请识别整局胜负（BLUE或RED），以及截图中能确认的玩家游戏ID、KDA数值；允许人数不足10人或双方人数不等。\n"
        "只从双方玩家列表中的实际玩家行提取 ID，每位玩家必须对应同一行的击杀、死亡和助攻。\n"
        "敌方胜利、我方胜利、敌方失败、我方失败、对方胜利等是界面胜负标题，绝不能当作玩家 ID。\n"
        "不要为了凑满10人而编造名字或用标题替代；看不清或缺失的玩家请省略，交由程序校验。\n"
        "敌方和我方是相对视角，不能直接等同于红方和蓝方；必须根据截图阵营信息判断，不能确定则 winning_team 填 null。\n"
        "若截图中有输出占比（例如 25% 或 25.4%）或承伤占比，请一并识别提取为数值（无百分号，如 25.4）。若截图中未显示输出或承伤占比，对应字段填 null。\n"
        "请严格输出合法JSON：\n"
        '{"winning_team": "BLUE", "players": [{"player_name": "ID", "team": "BLUE", "kills": 0, "deaths": 0, "assists": 0, "damage_share": 24.5, "taken_share": 20.1, "is_winner": true}]}'
    )
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{b64}"}}
            ]}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
    except NotFoundError as exc:
        raise ValueError(
            f"接口返回 404，当前模型：{model_name}，Base URL：{base_url}。"
            "请核对百炼控制台中的模型 ID、服务开通状态、API Key 所属地域及套餐对应的接口地址。"
            "可在左侧模型接口设置中修改。原始错误："
            f"{exc}"
        ) from exc
    finally:
        client.close()
    raw = resp.choices[0].message.content.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    clean_str = match.group(0) if match else raw
    return validate_recognition(json.loads(clean_str))


def recognize_upload_job(data, digest, api_key, settings):
    started = time.perf_counter()
    try:
        result = analyze_image(data, api_key, settings=settings)
        result["md5"] = digest
        result["image_thumb"] = compress_image_to_b64(data)
        return result, None, time.perf_counter() - started
    except Exception as exc:
        return None, str(exc), time.perf_counter() - started

def short_name(full_name):
    return str(full_name).split("#")[0] if full_name else "未知"

# ---------------- 2. 原生 SVG 六边形雷达生成器 ----------------
def generate_radar_svg(values, categories):
    size, r = 320, 105
    cx = cy = size / 2
    total = len(values)
    grid_polys = []
    for lvl in [0.25, 0.5, 0.75, 1.0]:
        points = []
        for i in range(total):
            ang = math.pi / 2 - 2 * math.pi * i / total
            points.append(
                f"{cx + r * lvl * math.cos(ang):.1f},"
                f"{cy - r * lvl * math.sin(ang):.1f}"
            )
        points_str = " ".join(points)
        grid_polys.append(
            f'<polygon points="{points_str}" fill="none" '
            'stroke="#fbcfe8" stroke-width="1.2" stroke-dasharray="3,3"/>'
        )

    axis_lines, labels, data_pts, circles = [], [], [], []
    for i in range(total):
        ang = math.pi / 2 - 2 * math.pi * i / total
        axis_lines.append(
            f'<line x1="{cx}" y1="{cy}" '
            f'x2="{cx + r * math.cos(ang):.1f}" '
            f'y2="{cy - r * math.sin(ang):.1f}" '
            'stroke="#fbcfe8" stroke-width="1.2"/>'
        )
        labels.append(
            f'<text x="{cx + (r + 26) * math.cos(ang):.1f}" '
            f'y="{cy - (r + 14) * math.sin(ang):.1f}" '
            'font-size="11" font-weight="800" fill="#72092c" '
            f'text-anchor="middle" dominant-baseline="central">{categories[i]}</text>'
        )
        scale = min(max(values[i], 12.0), 100.0) / 100.0
        x = cx + r * scale * math.cos(ang)
        y = cy - r * scale * math.sin(ang)
        data_pts.append(f"{x:.1f},{y:.1f}")
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#881337"/>')

    grid_svg = "".join(grid_polys)
    axes_svg = "".join(axis_lines)
    points_svg = " ".join(data_pts)
    circles_svg = "".join(circles)
    labels_svg = "".join(labels)
    return f"""
    <div style="display:flex;justify-content:center;padding:6px 0;">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            {grid_svg}{axes_svg}
            <polygon points="{points_svg}" fill="rgba(114, 9, 44, 0.25)" stroke="#72092c" stroke-width="2.6"/>
            {circles_svg}{labels_svg}
        </svg>
    </div>
    """


# ---------------- 侧边栏：控制台 ----------------
with st.sidebar:
    st.markdown("### 🎛️ 系统控制台")
    default_key = get_secret("DASHSCOPE_API_KEY")
    key = st.text_input("DashScope API Key", value=default_key, type="password", placeholder="sk-...")

    with st.expander("⚙️ 模型接口设置"):
        st.text_input(
            "视觉模型 ID",
            value=get_secret("DASHSCOPE_MODEL", "qwen3-vl-plus"),
            key="vision_model",
            help="填写百炼控制台中当前地域可调用的视觉模型 ID。",
        )
        st.text_input(
            "Base URL",
            value=get_secret("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            key="vision_base_url",
            help="须与 API Key 所属地域及套餐对应；填写到 v1，不要添加 /chat/completions。",
        )
        st.caption("默认使用北京按量付费接口；其他地域或套餐请填写控制台提供的地址。")
        st.slider("同时识别张数", 1, 3, value=3, key="vision_workers")
        st.checkbox("压缩识别大图", value=True, key="optimize_image",
                    help="图片宽度最多 1920 像素；昵称较小时可关闭后重试。")

    records = load_records()
    total_games_all = len(records)
    gh_t, gh_r = get_github_auth()
    st.caption("🟢 **云端自动同步**: 已启用 (GitHub)" if gh_t and gh_r else "⚪ **云端自动同步**: 未配置 Token")

    st.markdown("---")
    if records and st.button("🔄 重新扫描历史截图", help="提取输出与承伤占比并补齐数据库", use_container_width=True):
        if not key:
            st.warning("请先填入 DashScope API Key！")
        else:
            p_bar = st.progress(0)
            success_n = 0
            for idx, r in enumerate(records):
                thumb_b64 = r.get("image_thumb", "")
                if thumb_b64:
                    try:
                        new_res = analyze_image(base64.b64decode(thumb_b64), key)
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
            st.success(f"成功更新 {success_n} 局并同步！")
            time.sleep(0.5)
            st.rerun()

    with st.expander("💾 数据备份与恢复"):
        if records:
            st.download_button("📤 导出完整数据 (JSON)", json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8'), "lol_records_backup.json", "application/json", use_container_width=True)
        uploaded_backup = st.file_uploader("导入备份文件", type=["json"], key="backup_uploader")
        if uploaded_backup is not None and st.button("📥 恢复数据", type="primary", use_container_width=True):
            try:
                save_records(json.load(uploaded_backup))
                st.success("恢复成功并已同步！")
                time.sleep(0.5); st.rerun()
            except Exception as e:
                st.error(f"导入失败: {e}")

    if records:
        with st.expander("🔍 历史对局图文复盘"):
            selected_idx = st.selectbox("选择对局", range(len(records)), format_func=lambda i: f"第 {i+1} 局 ({records[i].get('winning_team', '未知')}方胜)")
            curr_record = records[selected_idx]
            if curr_record.get("image_thumb"):
                st.image(f"data:image/jpeg;base64,{curr_record['image_thumb']}", use_container_width=True)
            p_rows = [{
                "阵营": p.get("team", ""), "玩家": short_name(p.get("player_name", "")),
                "KDA": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                "伤害": f"{p.get('damage_share')}%" if p.get('damage_share') is not None else "--"
            } for p in curr_record.get("players", [])]
            if p_rows: st.dataframe(pd.DataFrame(p_rows), hide_index=True)
            if st.button("🗑️ 删除该局", key=f"del_g_{selected_idx}", use_container_width=True):
                records.pop(selected_idx)
                save_records(records)
                st.success("已删除该局！"); time.sleep(0.3); st.rerun()

    with st.expander("🎙️ 语音房链接配置"):
        cfg = load_config()
        new_main = st.text_input("大厅主语音", value=cfg.get("main_voice", ""))
        new_blue = st.text_input("🔵 蓝方语音", value=cfg.get("blue_voice", ""))
        new_red = st.text_input("🔴 红方语音", value=cfg.get("red_voice", ""))
        if st.button("💾 保存链接", use_container_width=True):
            save_config({"main_voice": new_main, "blue_voice": new_blue, "red_voice": new_red})
            st.success("已保存！"); time.sleep(0.3); st.rerun()

# ---------------- 主界面 1：顶栏电竞控制台 ----------------
cfg = load_config()
st.markdown(f"""
<div class="app-header-bar">
    <div class="header-title">⚔️ 海克斯内战 · 战绩中心</div>
    <span class="badge-tag" style="background:#ffffff;border-color:#72092c;color:#72092c;margin:0;">📦 已收录 <b>{total_games_all}</b> 场对局</span>
</div>
""", unsafe_allow_html=True)

vc1, vc2, vc3 = st.columns(3)
with vc1: st.link_button("🎙️ 大厅语音作战室", cfg.get("main_voice", "https://kook.top/"), use_container_width=True)
with vc2: st.link_button("🔵 蓝方语音作战室", cfg.get("blue_voice", "https://kook.top/"), use_container_width=True)
with vc3: st.link_button("🔴 红方语音作战室", cfg.get("red_voice", "https://kook.top/"), use_container_width=True)
st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ---------------- 数据清洗与统计算法引擎 ----------------
all_raw = [p.get("player_name", "") for r in records for p in r.get("players", []) if p.get("player_name")]
name_mapping = build_canonical_name_map(list(set(all_raw)))

def get_final_name(pname):
    strict_name = clean_player_name_strict(pname)
    fname = name_mapping.get(pname, strict_name)
    return TARGET_QIANQIU if (strict_name == TARGET_QIANQIU or "千秋" in fname) else fname

stats = defaultdict(lambda: {"总场次": 0, "胜场": 0, "负场": 0, "击杀": 0, "死亡": 0, "助攻": 0})
radar_stats_pool = defaultdict(lambda: {"games_6p": 0, "kills": 0, "deaths": 0, "assists": 0, "damage_shares": [], "taken_shares": [], "kp_shares": []})
player_history = defaultdict(lambda: {"outcomes": [], "max_kill": 0, "max_death": 0, "max_assist": 0, "max_dmg_share": 0.0, "max_taken_share": 0.0, "min_death_win": 999, "svp_cnt": 0})
synergy_stats = defaultdict(lambda: {"同队场次": 0, "胜场": 0, "负场": 0})
nemesis_stats = defaultdict(lambda: {"交手场次": 0, "p1_wins": 0, "p2_wins": 0})

max_single_kill = {"player": "", "val": -1, "game_idx": 0}
max_single_death = {"player": "", "val": -1, "game_idx": 0}
max_single_assist = {"player": "", "val": -1, "game_idx": 0}

for game_idx, r in enumerate(records):
    players = r.get("players", [])
    valid_6p = len(players) >= 6
    blue_k = sum(int(p.get("kills", 0)) for p in players if str(p.get("team", "")).upper() == "BLUE")
    red_k = sum(int(p.get("kills", 0)) for p in players if str(p.get("team", "")).upper() == "RED")
    blue_team, red_team = [], []

    for p in players:
        if not p.get("player_name"): continue
        fname = get_final_name(p["player_name"])
        k, d, a = int(p.get("kills", 0)), int(p.get("deaths", 0)), int(p.get("assists", 0))
        is_win = bool(p.get("is_winner"))
        side = str(p.get("team", "")).upper()

        stats[fname]["总场次"] += 1
        stats[fname]["胜场" if is_win else "负场"] += 1
        stats[fname]["击杀"] += k; stats[fname]["死亡"] += d; stats[fname]["助攻"] += a
        player_history[fname]["outcomes"].append(is_win)

        dmg_s, taken_s = p.get("damage_share"), p.get("taken_share")
        if valid_6p:
            if k > player_history[fname]["max_kill"]: player_history[fname]["max_kill"] = k
            if d > player_history[fname]["max_death"]: player_history[fname]["max_death"] = d
            if a > player_history[fname]["max_assist"]: player_history[fname]["max_assist"] = a
            if is_win and d < player_history[fname]["min_death_win"]: player_history[fname]["min_death_win"] = d
            ds_val = float(dmg_s) if dmg_s is not None else 0.0
            if (not is_win) and (ds_val >= 35.0 or k >= 11): player_history[fname]["svp_cnt"] += 1
            if ds_val > player_history[fname]["max_dmg_share"]: player_history[fname]["max_dmg_share"] = ds_val
            if taken_s is not None:
                try:
                    if float(taken_s) > player_history[fname]["max_taken_share"]: player_history[fname]["max_taken_share"] = float(taken_s)
                except Exception: pass
            
            radar_stats_pool[fname]["games_6p"] += 1
            radar_stats_pool[fname]["kills"] += k; radar_stats_pool[fname]["deaths"] += d; radar_stats_pool[fname]["assists"] += a
            if dmg_s is not None:
                try: radar_stats_pool[fname]["damage_shares"].append(float(dmg_s))
                except Exception: pass
            if taken_s is not None:
                try: radar_stats_pool[fname]["taken_shares"].append(float(taken_s))
                except Exception: pass
            tk = blue_k if side == "BLUE" else red_k
            if tk > 0: radar_stats_pool[fname]["kp_shares"].append((k + a) / tk)

        if k > max_single_kill["val"]: max_single_kill = {"player": fname, "val": k, "game_idx": game_idx + 1}
        if d > max_single_death["val"]: max_single_death = {"player": fname, "val": d, "game_idx": game_idx + 1}
        if a > max_single_assist["val"]: max_single_assist = {"player": fname, "val": a, "game_idx": game_idx + 1}

        if side == "BLUE": blue_team.append((fname, is_win))
        elif side == "RED": red_team.append((fname, is_win))

    for t in [blue_team, red_team]:
        m = list({item[0]: item[1] for item in t}.items())
        for (p1, win1), (p2, _) in combinations(m, 2):
            pair = tuple(sorted([p1, p2]))
            synergy_stats[pair]["同队场次"] += 1
            synergy_stats[pair]["胜场" if win1 else "负场"] += 1

    bu = list({item[0]: item[1] for item in blue_team}.items())
    ru = list({item[0]: item[1] for item in red_team}.items())
    for (pb, b_win) in bu:
        for (pr, _) in ru:
            if pb == pr: continue
            pair = tuple(sorted([pb, pr]))
            nemesis_stats[pair]["交手场次"] += 1
            if (pb == pair[0] and b_win) or (pr == pair[0] and not b_win): nemesis_stats[pair]["p1_wins"] += 1
            else: nemesis_stats[pair]["p2_wins"] += 1

df = pd.DataFrame.from_dict(stats, orient="index")
if not df.empty:
    df["胜率_num"] = (df["胜场"] / df["总场次"] * 100).round(1)
    df["KD"] = (df["击杀"] / df["死亡"].replace(0, 1)).round(2)
    df["KDA_num"] = ((df["击杀"] + df["助攻"]) / df["死亡"].replace(0, 1)).round(2)
    df["场均击杀"] = (df["击杀"] / df["总场次"]).round(1)
    def calc_mmr(r):
        if r["总场次"] < 2: return 50.0
        tot = min(float(r["场均击杀"])/10.0, 1.2)*35.0 + min(float(r["KDA_num"])/5.0, 1.2)*35.0 + (float(r["胜率_num"])/100.0)*30.0
        return round(tot + (5.0 if float(r["场均击杀"]) >= 7.0 and float(r["KDA_num"]) >= 2.5 else 0.0), 1)
    df["MMR"] = df.apply(calc_mmr, axis=1)

# ---------------- 主界面 2：Tabs 视图 ----------------
tab_ladder, tab_match, tab_radar, tab_upload = st.tabs([
    "📊 胜率天梯与荣誉榜", "⚔️ 赛前阵营分队系统", "🎯 局内战术图谱与成就馆", "📥 战绩智能录入"
])

# ================= Tab 1: 胜率天梯与荣誉榜 =================
with tab_ladder:
    if df.empty:
        st.info("💡 暂无选手数据。请在战绩智能录入页面上传截图！")
    else:
        st.markdown('<div class="panel-header-title">🏆 选手全胜率天梯榜单</div>', unsafe_allow_html=True)
        df_sorted = df.sort_values(by=["胜率_num", "总场次", "KDA_num"], ascending=[False, False, False])
        t_rows = []
        for r_idx, (p_id, row) in enumerate(df_sorted.iterrows()):
            wr = row["胜率_num"]
            wr_b = f"<span style='background:#72092c;color:#fff;font-weight:900;padding:2px 8px;border-radius:6px;'>{wr}% 👑</span>" if wr >= 60 else (f"<span style='color:#0284c7;font-weight:800;'>{wr}%</span>" if wr >= 50 else f"<span style='color:#be123c;font-weight:700;'>{wr}%</span>")
            kda_b = f"<span style='color:#b45309;font-weight:900;background:#fef9c3;padding:1px 6px;border-radius:4px;'>{row['KDA_num']:.2f}</span>" if row["KDA_num"] >= 3.5 else f"<b>{row['KDA_num']:.2f}</b>"
            medal = "🥇 " if r_idx == 0 else ("🥈 " if r_idx == 1 else ("🥉 " if r_idx == 2 else f"{r_idx+1} "))
            r_cls = "rank-1" if r_idx == 0 else ("rank-2" if r_idx == 1 else ("rank-3" if r_idx == 2 else ""))
            t_rows.append(f"<tr class='{r_cls}'><td style='text-align:left;padding-left:16px;font-weight:800;'>{medal}{short_name(p_id)}</td><td>{int(row['总场次'])}</td><td style='color:#0284c7;'>{int(row['胜场'])}</td><td style='color:#e11d48;'>{int(row['负场'])}</td><td>{wr_b}</td><td style='color:#72092c;font-weight:900;'>{row['MMR']:.1f}</td><td>{row['场均击杀']:.1f}</td><td>{row['KD']:.2f}</td><td>{kda_b}</td><td>{int(row['击杀'])}</td><td>{int(row['死亡'])}</td><td>{int(row['助攻'])}</td></tr>")
        st.markdown(f'<div class="ladder-table-box"><table class="ladder-table"><thead><tr><th style="text-align:left;padding-left:16px;">选手排位</th><th>总场次</th><th>胜局</th><th>负局</th><th>胜率</th><th>MMR战力</th><th>场均击杀</th><th>KD</th><th>KDA</th><th>总击杀</th><th>总死亡</th><th>总助攻</th></tr></thead><tbody>{"".join(t_rows)}</tbody></table></div>', unsafe_allow_html=True)

        st.markdown('<div class="panel-header-title">🔥 单场巅峰纪录</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-stat-box"><div class="metric-title">单场最高击杀</div><div class="metric-val-main">{short_name(max_single_kill["player"])}</div><div class="metric-badge badge-gold">{max_single_kill["val"]} 杀 (第 {max_single_kill["game_idx"]} 局)</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-stat-box"><div class="metric-title">单场最高阵亡</div><div class="metric-val-main">{short_name(max_single_death["player"])}</div><div class="metric-badge badge-pink">{max_single_death["val"]} 阵亡 (第 {max_single_death["game_idx"]} 局)</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-stat-box"><div class="metric-title">单场最高助攻</div><div class="metric-val-main">{short_name(max_single_assist["player"])}</div><div class="metric-badge badge-blue">{max_single_assist["val"]} 助攻 (第 {max_single_assist["game_idx"]} 局)</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="panel-header-title">🎖️ 综合荣誉名人堂 (≥10局)</div>', unsafe_allow_html=True)
        cand10 = df[df["总场次"] >= 10]
        h10 = not cand10.empty
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            if h10:
                n1 = cand10.sort_values(by="KDA_num", ascending=False).index[0]
                badge_kda_str = f"KDA {df.loc[n1, 'KDA_num']:.2f}"
                name1_str = short_name(n1)
            else:
                name1_str, badge_kda_str = "虚位以待", "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">KDA之王</div><div class="metric-val-main">{name1_str}</div><div class="metric-badge badge-blue">{badge_kda_str}</div></div>', unsafe_allow_html=True)
        with m2:
            if h10:
                n2 = cand10.sort_values(by="击杀", ascending=False).index[0]
                badge_k_str = f"{int(df.loc[n2, '击杀'])} 杀"
                name2_str = short_name(n2)
            else:
                name2_str, badge_k_str = "虚位以待", "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">累计击杀王</div><div class="metric-val-main">{name2_str}</div><div class="metric-badge badge-gold">{badge_k_str}</div></div>', unsafe_allow_html=True)
        with m3:
            if h10:
                n3 = cand10.sort_values(by="死亡", ascending=False).index[0]
                badge_d_str = f"{int(df.loc[n3, '死亡'])} 阵亡"
                name3_str = short_name(n3)
            else:
                name3_str, badge_d_str = "虚位以待", "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">累计白给王</div><div class="metric-val-main">{name3_str}</div><div class="metric-badge badge-pink">{badge_d_str}</div></div>', unsafe_allow_html=True)
        with m4:
            if h10:
                n4 = cand10.sort_values(by="助攻", ascending=False).index[0]
                badge_a_str = f"{int(df.loc[n4, '助攻'])} 助攻"
                name4_str = short_name(n4)
            else:
                name4_str, badge_a_str = "虚位以待", "需满 10 局"
            st.markdown(f'<div class="metric-stat-box"><div class="metric-title">累计助攻王</div><div class="metric-val-main">{name4_str}</div><div class="metric-badge badge-blue">{badge_a_str}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="panel-header-title">🔗 阵营羁绊与宿敌</div>', unsafe_allow_html=True)
        syn_list = [{"p": f"{short_name(k[0])} & {short_name(k[1])}", "w": v["胜场"], "l": v["负场"], "wr": v["胜场"]/v["同队场次"] if v["同队场次"]>0 else 0} for k, v in synergy_stats.items() if v["同队场次"] >= 5]
        s_df = pd.DataFrame(syn_list)
        bp = s_df.sort_values(by=["wr"], ascending=False).iloc[0] if not s_df.empty else None
        wp = s_df.sort_values(by=["wr"], ascending=True).iloc[0] if not s_df.empty else None

        nem_list = []
        for (p1, p2), v in nemesis_stats.items():
            if v["交手场次"] >= 5:
                w, l = (p1, p2) if v["p1_wins"] >= v["p2_wins"] else (p2, p1)
                nem_list.append({"d": f"{short_name(w)} ➔ {short_name(l)}", "w": max(v["p1_wins"], v["p2_wins"]), "l": min(v["p1_wins"], v["p2_wins"])})
        n_df = pd.DataFrame(nem_list)
        rp = n_df.iloc[0] if not n_df.empty else None

        bp_txt = bp["p"] if bp is not None else "虚位以待"
        bp_score = f"{int(bp['w'])}胜{int(bp['l'])}负" if bp is not None else "同队需满 5 局"
        wp_txt = wp["p"] if wp is not None else "虚位以待"
        wp_score = f"{int(wp['w'])}胜{int(wp['l'])}负" if wp is not None else "同队需满 5 局"
        rp_txt = rp["d"] if rp is not None else "虚位以待"
        rp_score = f"{int(rp['w'])}胜{int(rp['l'])}负" if rp is not None else "交手需满 5 局"

        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f'<div class="metric-stat-box"><div class="metric-title">黄金搭档 (≥5局)</div><div class="metric-val-main">{bp_txt}</div><div class="metric-badge badge-blue">{bp_score}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="metric-stat-box"><div class="metric-title">难兄难弟 (≥5局)</div><div class="metric-val-main">{wp_txt}</div><div class="metric-badge badge-pink">{wp_score}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="metric-stat-box"><div class="metric-title">一生之敌 (≥5局)</div><div class="metric-val-main">{rp_txt}</div><div class="metric-badge badge-gold">{rp_score}</div></div>', unsafe_allow_html=True)

# ================= Tab 2: 赛前阵营分队系统 =================
with tab_match:
    if df.empty:
        st.info("💡 暂无选手历史数据，请先录入对局战绩。")
    else:
        if "custom_guests" not in st.session_state: st.session_state["custom_guests"] = {}
        known = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True)
        full_roster = known + list(st.session_state["custom_guests"].keys())
        st.markdown('<div class="card-panel"><div class="panel-header-title">👥 出战名单挑选与替补录入</div>', unsafe_allow_html=True)
        selected_players = st.multiselect("选择出战名单：", options=full_roster, default=known[:10] if len(known)>=10 else known, format_func=lambda x: short_name(x))
        
        cg1, cg2, cg3 = st.columns([3, 3, 1.5])
        with cg1: g_name = st.text_input("外援昵称", placeholder="输入昵称...", label_visibility="collapsed")
        with cg2: g_tier = st.selectbox("外援评级", [80.0, 60.0, 45.0], format_func=lambda v: {80.0: "👑 通天大腿 (80分)", 60.0: "🛡️ 普通水平 (60分)", 45.0: "🌱 萌新挂件 (45分)"}[v], index=1, label_visibility="collapsed")
        with cg3:
            if st.button("➕ 录入外援", use_container_width=True) and g_name.strip():
                st.session_state["custom_guests"][g_name.strip()] = {"mmr": g_tier, "tier": {80.0: "通天大腿", 60.0: "普通", 45.0: "萌新"}[g_tier]}
                st.rerun()
        if st.session_state["custom_guests"]:
            for k_g, v_g in list(st.session_state["custom_guests"].items()):
                ci, cd = st.columns([5, 1])
                with ci: st.caption(f"👤 {k_g} · 战力 {v_g['mmr']} ({v_g['tier']})")
                with cd:
                    if st.button("🗑️", key=f"del_{k_g}"):
                        del st.session_state["custom_guests"][k_g]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if "lock_rules" not in st.session_state: st.session_state["lock_rules"] = []
        with st.expander("🔗 人情世故与宿敌羁绊绑定 (强制同队 / 强制对立)"):
            ra, rb, r1, r2 = st.columns([2.5, 2.5, 2, 2])
            with ra: rp1 = st.selectbox("选手 A", selected_players, format_func=lambda x: short_name(x), key="rp1")
            with rb: rp2 = st.selectbox("选手 B", [p for p in selected_players if p != rp1], format_func=lambda x: short_name(x), key="rp2") if len(selected_players)>1 else None
            with r1:
                if st.button("🔗 锁定同队", use_container_width=True) and rp1 and rp2:
                    st.session_state["lock_rules"] = [r for r in st.session_state["lock_rules"] if not ({r["p1"], r["p2"]} == {rp1, rp2})]
                    st.session_state["lock_rules"].append({"type": "same", "p1": rp1, "p2": rp2})
                    st.rerun()
            with r2:
                if st.button("⚔️ 锁定对立", use_container_width=True) and rp1 and rp2:
                    st.session_state["lock_rules"] = [r for r in st.session_state["lock_rules"] if not ({r["p1"], r["p2"]} == {rp1, rp2})]
                    st.session_state["lock_rules"].append({"type": "diff", "p1": rp1, "p2": rp2})
                    st.rerun()
            if st.session_state["lock_rules"]:
                for idx, r in enumerate(st.session_state["lock_rules"]):
                    cx, cy = st.columns([5, 1])
                    with cx: st.caption(f"👤 {short_name(r['p1'])} {'🔗 必须同队' if r['type']=='same' else '⚔️ 必须对立'} 👤 {short_name(r['p2'])}")
                    with cy:
                        if st.button("❌", key=f"del_r_{idx}"):
                            st.session_state["lock_rules"].pop(idx); st.rerun()

        def get_mmr(p):
            if p in st.session_state["custom_guests"]: return float(st.session_state["custom_guests"][p]["mmr"])
            return float(df.loc[p, "MMR"]) if p in df.index else 50.0

        def check_rules(tb, tr):
            for r in st.session_state["lock_rules"]:
                p1, p2 = r["p1"], r["p2"]
                if (p1 in tb or p1 in tr) and (p2 in tb or p2 in tr):
                    if r["type"] == "same" and not ((p1 in tb and p2 in tb) or (p1 in tr and p2 in tr)): return False
                    if r["type"] == "diff" and not ((p1 in tb and p2 in tr) or (p1 in tr and p2 in tb)): return False
            return True

        if "assigned_b" not in st.session_state: st.session_state["assigned_b"] = []
        if "assigned_r" not in st.session_state: st.session_state["assigned_r"] = []

        b1, b2, b3 = st.columns(3)
        with b1: btn_bal = st.button("⚖️ 战力天平平衡分配", type="primary", use_container_width=True)
        with b2: btn_car = st.button("👑 大腿均分模式", use_container_width=True)
        with b3: btn_rnd = st.button("🎲 盲盒随机抽签", use_container_width=True)

        tot_p = len(selected_players)
        if btn_bal and tot_p >= 2:
            best_diff, bb, br = float("inf"), [], []
            for cb in combinations(selected_players, tot_p // 2):
                cr = [p for p in selected_players if p not in cb]
                if check_rules(set(cb), set(cr)):
                    diff = abs(sum(get_mmr(p) for p in cb) - sum(get_mmr(p) for p in cr))
                    if diff < best_diff: best_diff, bb, br = diff, list(cb), list(cr)
            if bb: st.session_state["assigned_b"], st.session_state["assigned_r"] = bb, br
            else: st.error("❌ 无法满足当前羁绊约束！")
        elif btn_car and tot_p >= 4:
            s_p = sorted(selected_players, key=lambda x: get_mmr(x), reverse=True)
            top1, top2, bot1, bot2 = s_p[0], s_p[1], s_p[-1], s_p[-2]
            mid = s_p[2:-2]
            best_diff, bb, br = float("inf"), [], []
            for cand_mid in combinations(mid, (tot_p // 2) - 2):
                cb, cr = [top1, bot2] + list(cand_mid), [top2, bot1] + [p for p in mid if p not in cand_mid]
                if check_rules(set(cb), set(cr)):
                    diff = abs(sum(get_mmr(p) for p in cb) - sum(get_mmr(p) for p in cr))
                    if diff < best_diff: best_diff, bb, br = diff, cb, cr
            if bb: st.session_state["assigned_b"], st.session_state["assigned_r"] = bb, br
            else: st.error("❌ 冲突，建议使用战力天平模式！")
        elif btn_rnd and tot_p >= 2:
            found = False
            for _ in range(100):
                sh = list(selected_players); random.shuffle(sh)
                cb, cr = sh[:tot_p//2], sh[tot_p//2:]
                if check_rules(set(cb), set(cr)):
                    st.session_state["assigned_b"], st.session_state["assigned_r"] = cb, cr
                    found = True; break
            if not found: st.error("❌ 100次尝试均无法满足羁绊锁定！")

        if st.session_state["assigned_b"] and st.session_state["assigned_r"]:
            tb, tr = st.session_state["assigned_b"], st.session_state["assigned_r"]
            avg_b, avg_r = round(sum(get_mmr(p) for p in tb)/len(tb), 1), round(sum(get_mmr(p) for p in tr)/len(tr), 1)
            b_str, r_str = "、".join([short_name(p) for p in tb]), "、".join([short_name(p) for p in tr])
            st.markdown(f"""
            <div style="background:#fff;border:1.5px solid #fecdd3;border-radius:14px;padding:16px;margin:12px 0;">
                <div style="color:#0284c7;font-weight:800;margin-bottom:6px;">🔵 蓝色方 ({len(tb)}人 | 均分 {avg_b}): {b_str}</div>
                <div style="color:#72092c;font-weight:800;margin-bottom:6px;">🔴 红色方 ({len(tr)}人 | 均分 {avg_r}): {r_str}</div>
                <div style="color:#64748b;font-size:0.85rem;">⚡ 人均分差: {abs(avg_b - avg_r):.1f} 分</div>
            </div>
            """, unsafe_allow_html=True)

# ================= Tab 3: 局内战术图谱与成就馆 =================
with tab_radar:
    active_p = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True) if not df.empty else []
    if not active_p:
        st.info("💡 暂无选手数据。")
    else:
        target_p = st.selectbox("选择要分析的选手档案：", active_p, format_func=lambda x: short_name(x))
        p_r = radar_stats_pool[target_p]
        vg = p_r["games_6p"]
        if vg > 0:
            pk, pd_cnt, pa = p_r["kills"]/vg, p_r["deaths"]/vg, p_r["assists"]/vg
            ds = sum(p_r["damage_shares"])/len(p_r["damage_shares"]) if p_r["damage_shares"] else pk * 2.3
            ts = sum(p_r["taken_shares"])/len(p_r["taken_shares"]) if p_r["taken_shares"] else pd_cnt * 2.4
            kp = sum(p_r["kp_shares"])/len(p_r["kp_shares"]) if p_r["kp_shares"] else 0.5
        else:
            pk, pd_cnt, pa = df.loc[target_p, "击杀"]/df.loc[target_p, "总场次"], df.loc[target_p, "死亡"]/df.loc[target_p, "总场次"], df.loc[target_p, "助攻"]/df.loc[target_p, "总场次"]
            ds, ts, kp = pk * 2.3, pd_cnt * 2.4, 0.5

        scores = [
            round(max(18.0, min(96.0, 25.0 + (ds/20.0)*35.0 if ds<=20 else 60.0 + min(1.0, (ds-20)/14)*35.0)), 1),
            round(max(18.0, min(96.0, 25.0 + (ts/20.0)*35.0 if ts<=20 else 60.0 + min(1.0, (ts-20)/14)*35.0)), 1),
            round(max(18.0, min(96.0, 25.0 + (kp/0.55)*35.0 if kp<=0.55 else 60.0 + min(1.0, (kp-0.55)/0.22)*35.0)), 1),
            round(max(20.0, min(95.0, 25.0 + min(1.0, pk/10.0)*45.0 + (pk/max(1.0, pk+pa))*25.0)), 1),
            round(max(20.0, min(95.0, 25.0 + min(1.0, pa/12.0)*45.0 + (pa/max(1.0, pk+pa))*25.0)), 1),
            round(max(20.0, min(95.0, 60.0 + ((6.0 - pd_cnt)/4.0)*32.0 if pd_cnt<=6 else 60.0 - ((pd_cnt - 6.0)/5.0)*32.0)), 1)
        ]
        col_rad, col_info = st.columns([1.2, 1])
        with col_rad: st.markdown(generate_radar_svg(scores, ['伤害', '承伤', '参团', '击杀', '助攻', '保命']), unsafe_allow_html=True)
        with col_info:
            st.markdown(f"""
            <div class="card-panel">
                <div class="panel-header-title">选手战术定位</div>
                <div style="font-size:1.45rem;font-weight:900;color:#1e293b;margin-bottom:8px;">{short_name(target_p)}</div>
                <div style="font-size:0.90rem;color:#475569;line-height:2.0;">
                    <div>• <b>场均伤害占比</b>: <span style="color:#72092c;font-weight:800;">{ds:.1f}%</span></div>
                    <div>• <b>场均承伤占比</b>: <span style="color:#0284c7;font-weight:800;">{ts:.1f}%</span></div>
                    <div>• <b>团战参团率</b>: <span style="color:#ca8a04;font-weight:800;">{kp*100:.1f}%</span></div>
                    <div>• <b>场均KDA</b>: {pk:.1f} / {pd_cnt:.1f} / {pa:.1f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        ph = player_history[target_p]
        badges = []
        if ph["max_dmg_share"] >= 38.0: badges.append("💥 血条消失术 (单场输出≥38%)")
        if ph["max_taken_share"] >= 38.0: badges.append("🛡️ 叹息之壁 (单场承伤≥38%)")
        if ph["max_kill"] >= 16: badges.append("🩸 绝命赏金客 (单场击杀≥16)")
        if ph["max_death"] >= 10: badges.append("🎰 慈善赌圣 (单场阵亡≥10)")
        if ph["min_death_win"] <= 1: badges.append("🏕️ 泉水指挥官 (胜局阵亡≤1)")
        if ph["max_assist"] >= 18: badges.append("🚑 全图救护车 (单场助攻≥18)")
        if ph["svp_cnt"] >= 2: badges.append("🪓 悲情孤勇者 (败局C位多次尽力)")
        if not badges: badges.append("🌱 未来可期 (新晋选手积蓄战力)")

        badge_spans = " ".join([f'<span class="badge-tag">{b}</span>' for b in badges])
        st.markdown(f"""
        <div class="card-panel">
            <div class="panel-header-title">🏅 个人成就勋章</div>
            <div>{badge_spans}</div>
        </div>
        """, unsafe_allow_html=True)

# ================= Tab 4: 战绩智能录入 =================
with tab_upload:
    st.markdown('<div class="card-panel"><div class="panel-header-title">📸 战绩截图智能分析录入</div>', unsafe_allow_html=True)
    with st.form("upload_box", clear_on_submit=False):
        files = st.file_uploader("选择截图（支持批量多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        sub = st.form_submit_button("🚀 开始解析并录入", type="primary", use_container_width=True)

    previous_report = st.session_state.get("upload_report")
    if previous_report:
        st.info(previous_report["summary"])
        for message in previous_report["errors"]:
            st.error(message)

    if sub:
        if not files:
            st.warning("⚠️ 请先选择战绩截图！")
        elif not key:
            st.warning("⚠️ 请在左侧控制台填入 DashScope API Key！")
        else:
            try:
                settings = get_vision_settings()
            except ValueError as exc:
                st.error(str(exc))
            else:
                batch_started = time.perf_counter()
                records = load_records()
                base_records = list(records)
                seen = {r.get("md5") for r in records if "md5" in r}
                jobs, errors, skipped = [], [], 0
                for index, uploaded in enumerate(files):
                    data = uploaded.getvalue()
                    digest = get_md5(data)
                    if digest in seen:
                        skipped += 1
                    else:
                        # 同一批上传的重复文件也只请求一次模型。
                        seen.add(digest)
                        jobs.append((index, uploaded.name, data, digest))

                bar = st.progress(0)
                status_box = st.empty()
                successes = {}
                completed = 0
                workers = min(st.session_state.get("vision_workers", 3), len(jobs))
                if jobs:
                    status_box.info(f"⏳ 正在识别 {len(jobs)} 张截图，同时处理 {workers} 张。")
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = {
                            executor.submit(recognize_upload_job, data, digest, key, settings): (index, name)
                            for index, name, data, digest in jobs
                        }
                        for future in as_completed(futures):
                            index, name = futures[future]
                            result, error, elapsed = future.result()
                            completed += 1
                            if error:
                                errors.append(f"❌ {name} 录入失败：{error}")
                            else:
                                successes[index] = result
                                # 完成顺序可能不同；按上传顺序保存，维持对局时间顺序。
                                records = base_records + [successes[i] for i in sorted(successes)]
                                save_records(records, sync_cloud=False)
                            bar.progress(completed / len(jobs))
                            status_box.info(
                                f"已完成 {completed}/{len(jobs)} 张，成功 {len(successes)} 张；"
                                f"刚完成 {name}，耗时 {elapsed:.1f} 秒。"
                            )

                sync_message = ""
                if successes:
                    token, repo = get_github_auth()
                    if token and repo:
                        status_box.info("☁️ 识别已完成，正在统一同步 GitHub……")
                        sync_started = time.perf_counter()
                        synced = push_records_to_github(records)
                        sync_elapsed = time.perf_counter() - sync_started
                        if synced:
                            sync_message = f"云端同步完成（{sync_elapsed:.1f} 秒）。"
                        else:
                            sync_message = "本地已保存，云端同步失败。"
                            errors.append("请检查网络和 GitHub 配置；可先导出 JSON 备份，避免部署重启后丢失本地新记录。")
                    else:
                        sync_message = "已保存到本地，未配置云端同步。"

                total_elapsed = time.perf_counter() - batch_started
                summary = (
                    f"本批成功 {len(successes)} 张，识别失败 {len(jobs) - len(successes)} 张，跳过重复 {skipped} 张，"
                    f"总耗时 {total_elapsed:.1f} 秒。{sync_message}"
                )
                st.session_state["upload_report"] = {"summary": summary, "errors": errors}
                status_box.empty()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
