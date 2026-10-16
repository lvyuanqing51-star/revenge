import os
import json
import hashlib
import hmac
import time
import base64
import difflib
import re
import random
import math
import urllib.request
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlencode
from io import BytesIO
from itertools import combinations
from collections import defaultdict
import streamlit as st
import pandas as pd
from PIL import Image

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
    background: linear-gradient(145deg, #fbf9f8 0%, #faf5f5 100%) !important;
    background-attachment: fixed !important;
    color: #334155 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
}
.app-header-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(254, 242, 242, 0.92) 100%);
    backdrop-filter: blur(14px); border: 1.5px solid #fecdd3; border-left: 6px solid #881337;
    border-radius: 16px; padding: 20px 24px; margin-bottom: 24px;
    box-shadow: 0 3px 12px rgba(114, 9, 44, 0.04);
}
.header-title {
    font-size: 26px; font-weight: 800;
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
    background: #ffffff; border: 1px solid #ece5e2; border-radius: 14px;
    padding: 20px; margin-bottom: 24px; box-shadow: 0 3px 12px rgba(114, 9, 44, 0.03);
}
.panel-header-title {
    font-size: 18px; font-weight: 700; color: #72092c; margin: 24px 0 12px;
    border-left: 4px solid #72092c; padding-left: 10px;
}
.metric-stat-box {
    background: #ffffff; border: 1px solid #ece5e2; border-radius: 14px;
    padding: 20px; margin-bottom: 24px; box-shadow: 0 3px 10px rgba(114, 9, 44, 0.03);
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
    width: 100%; overflow-x: auto; border: 1px solid #ece5e2; border-radius: 14px;
    background: #ffffff; margin: 12px 0 24px;
}
.ladder-table { width: 100%; border-collapse: collapse; font-size: 0.94rem; text-align: right; font-variant-numeric: tabular-nums; }
.ladder-table th {
    background: #faf5f6; color: #72092c;
    font-weight: 700; padding: 14px 12px; border-bottom: 1px solid #e8dce0;
}
.ladder-table th, .ladder-table td { border-left: 0; border-right: 0; }
.ladder-table td { padding: 14px 12px; border-bottom: 1px solid #f0ebeb; }
.ladder-table tbody tr:hover { box-shadow: inset 3px 0 #881337; }
.stApp [data-testid="stCaptionContainer"] { font-size: 13px; color: #64748b; }
.stApp h3, .stApp h4 { font-size: 18px; line-height: 1.5; }
@media (max-width: 640px) {
    .app-header-bar { padding: 16px; flex-wrap: wrap; gap: 12px; }
    .header-title { font-size: 22px; }
    .ladder-table th, .ladder-table td { padding: 10px 8px; white-space: nowrap; }
}
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
    require_admin()
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
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


def admin_fingerprint():
    password = str(get_secret("ADMIN_PASSWORD", ""))
    return hashlib.sha256(password.encode("utf-8")).hexdigest() if password else ""


def is_admin():
    fingerprint = admin_fingerprint()
    return bool(
        fingerprint
        and hmac.compare_digest(st.session_state.get("admin_grant", ""), fingerprint)
        and time.time() < st.session_state.get("admin_expires", 0)
    )


def require_admin():
    if not is_admin():
        raise PermissionError("请先以管理员身份登录，才能修改数据。")


def render_admin_login():
    if is_admin():
        st.success("管理员已登录")
        if st.button("退出管理", key="admin_logout"):
            for state_key in list(st.session_state):
                if state_key.startswith(("admin_", "group_editor_", "review_", "batch_verify_")) or state_key in (
                    "verify_drafts", "verification_flash", "vision_key_input", "verify_navigation",
                ):
                    st.session_state.pop(state_key, None)
            st.rerun()
        return
    st.caption("访客模式 · 战绩只读")
    if not admin_fingerprint():
        st.info("管理功能尚未启用。请在应用 Secrets 中配置 ADMIN_PASSWORD。")
        return
    locked_until = st.session_state.get("admin_locked_until", 0)
    with st.form("admin_login_form", clear_on_submit=True):
        password = st.text_input("管理员密码", type="password")
        login = st.form_submit_button("登录管理", disabled=time.time() < locked_until)
    if time.time() < locked_until:
        st.warning("尝试次数过多，请稍后重试。")
    if login:
        expected = admin_fingerprint()
        actual = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if hmac.compare_digest(actual, expected):
            st.session_state.admin_grant = expected
            st.session_state.admin_expires = time.time() + 2 * 3600
            st.session_state.admin_failures = 0
            st.rerun()
        else:
            failures = st.session_state.get("admin_failures", 0) + 1
            st.session_state.admin_failures = failures
            if failures >= 5:
                st.session_state.admin_locked_until = time.time() + 60
                st.session_state.admin_failures = 0
            st.error("密码不正确。")


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
    require_admin()
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
    require_admin()
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


def correct_record_winner(record, winning_team, verified=True, players=None):
    """统一修正一局的胜方，并重建该局每位玩家的胜负字段。"""
    corrected = validate_recognition({
        **record, "winning_team": winning_team,
        "players": record.get("players", []) if players is None else players,
    })
    corrected["result_verified"] = bool(verified)
    corrected["groups_verified"] = bool(verified)
    corrected["result_source"] = "manual_review" if verified else "ai_unverified"
    if verified:
        corrected["result_verified_at"] = datetime.now(timezone.utc).isoformat()
    else:
        corrected.pop("result_verified_at", None)
    return corrected


def is_record_verified(record):
    return record.get("result_verified") is True and record.get("groups_verified") is True


def verification_changes(record, players, winner):
    originals = {p.get("player_name", ""): p for p in record.get("players", [])}
    changes = []
    for player in players:
        name = player.get("player_name", "")
        old = originals.get(name, {})
        old_side, new_side = old.get("team"), player.get("team")
        old_result = "胜" if old_side == record.get("winning_team") else "负"
        new_result = "胜" if new_side == winner else "负"
        if old_side != new_side or old_result != new_result:
            changes.append({"玩家 ID": name,
                "原分组": "A组" if old_side == "BLUE" else "B组",
                "新分组": "A组" if new_side == "BLUE" else "B组",
                "原结果": old_result, "新结果": new_result})
    return changes


def verification_digest(value):
    digest = hashlib.sha256()
    for chunk in json.JSONEncoder(ensure_ascii=False, sort_keys=True).iterencode(value):
        digest.update(chunk.encode("utf-8"))
    return digest.hexdigest()


def verification_record_key(record):
    revision = verification_digest(record)
    return f"{record.get('md5') or revision}_{revision[:12]}"


def prepare_batch_verification(snapshot, latest, selections):
    """先校验整批，再生成新记录；任何一局异常都不写入。"""
    if latest != snapshot:
        raise ValueError("历史记录已发生变化，请刷新页面后重新选择对局。")
    if not selections:
        raise ValueError("请至少勾选一局。")
    updated = list(latest)
    seen = set()
    for index, winner in selections:
        if type(index) is not int or not 0 <= index < len(latest) or index in seen:
            raise ValueError("对局选择无效或重复，请重新选择。")
        seen.add(index)
        record = latest[index]
        if is_record_verified(record):
            raise ValueError(f"第 {index + 1} 局已核验，请通过逐局核验修改。")
        try:
            corrected = correct_record_winner(record, winner, verified=True)
            if {p["team"] for p in corrected["players"]} != {"BLUE", "RED"}:
                raise ValueError("两组选手数据不完整，请进入逐局核验修复。")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"第 {index + 1} 局：{exc}") from exc
        updated[index] = corrected
    return updated


def render_batch_verification(records, admin_mode):
    if not st.checkbox("打开批量核验", key="batch_verify_enabled"):
        return
    with st.expander("📋 批量核验（勾选多局，一次保存）", expanded=False):
        st.caption("每页最多 10 局，仅处理待核验对局。先查看原图和完整名单，再勾选并确认胜方。玩家分组有误时请使用下方逐局核验。")
        drafts = st.session_state.get("verify_drafts", {})
        pending = [i for i in reversed(range(len(records))) if not is_record_verified(records[i])]
        eligible = [i for i in pending if verification_record_key(records[i]) not in drafts]
        if len(eligible) != len(pending):
            st.info(f"有 {len(pending) - len(eligible)} 局包含逐局核验草稿，已从批量列表排除，请在下方继续核验并保存。")
        if not eligible:
            st.info("暂无可批量核验的对局。")
            return

        snapshot_key = verification_digest(records)[:16]
        pages = (len(eligible) + 9) // 10
        page = st.selectbox("批量核验页码", range(pages),
                            format_func=lambda i: f"第 {i + 1} / {pages} 页",
                            key=f"batch_verify_page_{snapshot_key}")
        indices = eligible[page * 10:(page + 1) * 10]
        page_key = snapshot_key + "_" + "_".join(map(str, indices))
        rows = []
        for index in indices:
            record = records[index]
            groups = {
                side: [p for p in record.get("players", []) if str(p.get("team", "")).upper() == side]
                for side in ("BLUE", "RED")
            }
            current_winner = {"BLUE": "A组", "RED": "B组"}.get(record.get("winning_team"), "待选择")
            rows.append({
                "选择": False, "对局": f"第 {index + 1} 局", "获胜组": current_winner,
                "A组玩家": "、".join(str(p.get("player_name", "")) for p in groups["BLUE"]),
                "B组玩家": "、".join(str(p.get("player_name", "")) for p in groups["RED"]),
                "截图": "有" if record.get("image_thumb") else "无",
            })
        edited = st.data_editor(
            pd.DataFrame(rows), hide_index=True, use_container_width=True,
            disabled=["对局", "A组玩家", "B组玩家", "截图"] if admin_mode else True,
            key=f"batch_verify_editor_{page_key}",
            column_config={
                "选择": st.column_config.CheckboxColumn("选择", required=True),
                "获胜组": st.column_config.SelectboxColumn(
                    "获胜组", options=["待选择", "A组", "B组"], required=True,
                ),
            },
        )
        st.caption("获胜组默认沿用当前记录，可逐行修改。翻页分别提交；未勾选的对局不会保存。")
        if st.checkbox("加载截图与玩家 KDA（一次一局）", key="batch_verify_preview"):
            preview_index = st.selectbox("预览对局", indices,
                                         format_func=lambda i: f"第 {i + 1} 局",
                                         key=f"batch_verify_preview_{page_key}")
            for index in [preview_index]:
                record = records[index]
                st.markdown(f"**第 {index + 1} 局**")
                if record.get("image_thumb"):
                    st.image(f"data:image/jpeg;base64,{record['image_thumb']}", use_container_width=True)
                else:
                    st.warning("没有保存截图，请根据原始记录核对；无法确认时请勿勾选。")
                st.dataframe(pd.DataFrame([{
                    "玩家 ID": p.get("player_name", ""),
                    "分组": {"BLUE": "A组", "RED": "B组"}.get(str(p.get("team", "")).upper(), "未知"),
                    "KDA": "/".join(str(p.get(field, "?")) for field in ("kills", "deaths", "assists")),
                } for p in record.get("players", [])]), hide_index=True, use_container_width=True)

        selections = [(indices[position], {"A组": "BLUE", "B组": "RED"}.get(row["获胜组"], ""))
                      for position, (_, row) in enumerate(edited.iterrows()) if row["选择"]]
        st.caption(f"本页已选择 {len(selections)} 局。")
        confirmation_key = hashlib.sha256(json.dumps(selections).encode()).hexdigest()[:12]
        confirmed = st.checkbox(
            "我已逐局核对所选对局的玩家分组及胜负，并确认批量保存",
            key=f"batch_verify_confirm_{page_key}_{confirmation_key}", disabled=not admin_mode,
        )
        if st.button("✅ 保存所选对局的核验结果", type="primary", use_container_width=True,
                     key=f"batch_verify_save_{page_key}",
                     disabled=not admin_mode or not selections or not confirmed):
            try:
                require_admin()
                # 同一次重跑中，逐局编辑器可能尚未渲染，再检查已有草稿。
                current_drafts = st.session_state.get("verify_drafts", {})
                if any(verification_record_key(records[i]) in current_drafts for i, _ in selections):
                    raise ValueError("所选对局包含未保存的逐局草稿，请先完成逐局核验。")
                updated = prepare_batch_verification(records, load_records(), selections)
                synced = save_records(updated)
                token, repo = get_github_auth()
                cloud_failed = bool(token and repo and synced is False)
                suffix = "本地已保存，但云端同步失败，请立即导出 JSON 备份。" if cloud_failed else (
                    "已保存并同步云端。" if token and repo else "已保存到本地。"
                )
                st.session_state.verification_flash = {
                    "level": "warning" if cloud_failed else "success",
                    "text": f"已批量核验 {len(selections)} 局，所有玩家胜负字段已同步重建。{suffix}",
                }
                st.rerun()
            except Exception as exc:
                st.error(f"批量核验未完成：{exc}")


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
    # 仅在真正发起识别时加载 SDK；未安装或未使用模型时，页面其他功能仍可运行。
    from openai import OpenAI, NotFoundError
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=45.0
    )
    prompt = (
        "这是英雄联盟掌盟对局结算截图。\n"
        "把截图中靠前/靠上的第一组玩家统一记为 BLUE，把第二组统一记为 RED；"
        "这里的 BLUE/RED 只是两组代号，不代表游戏里的真实蓝红方。\n"
        "先定位双方玩家列表的标题和分隔边界，再逐行识别玩家所属组。"
        "玩家展开的英雄技能、海克斯强化、符文、装备详情和大段说明仍属于该玩家所在组，"
        "绝不能因为出现详情区、空白区或跨屏截图就切换组别。"
        "只有明确的另一组标题/列表边界才能切换组；无法确定所属组的玩家请省略，不要猜测。\n"
        "只根据两组旁边明确显示的‘胜利/失败’文字判断 winning_team；"
        "若胜负文字看不清，winning_team 必须填 null，绝不能根据击杀、KDA、颜色或玩家强弱猜测。\n"
        "请识别截图中能确认的玩家游戏ID、KDA数值；允许人数不足10人或双方人数不等。\n"
        "只从双方玩家列表中的实际玩家行提取 ID，每位玩家必须对应同一行的击杀、死亡和助攻。\n"
        "敌方胜利、我方胜利、敌方失败、我方失败、对方胜利等是界面胜负标题，绝不能当作玩家 ID。\n"
        "不要为了凑满10人而编造名字或用标题替代；看不清或缺失的玩家请省略，交由程序校验。\n"
        "敌方和我方是相对视角，不能直接等同于游戏蓝方和红方；只按两块玩家列表的顺序分组。\n"
        "若截图中有输出占比（例如 25% 或 25.4%）或承伤占比，请一并识别提取为数值（无百分号，如 25.4）。若截图中未显示输出或承伤占比，对应字段填 null。\n"
        "请严格输出合法JSON：\n"
        '{"winning_team": "BLUE", "players": [{"player_name": "ID", "team": "BLUE", "kills": 0, "deaths": 0, "assists": 0, "damage_share": 24.5, "taken_share": 20.1}]}'
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
        result["result_verified"] = False
        result["result_source"] = "ai_unverified"
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


# ---------------- 明亮酒红首屏：保留大标题与领跑者 ----------------
HERO_CSS = """
<style>
.war-room {background:linear-gradient(120deg,#fff 0%,#fcf7f7 100%);border:1px solid #e9dce0;border-radius:18px;padding:26px 30px;margin:0 0 24px;color:#334155;}
.war-top {display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:22px;}
.war-brand {display:flex;align-items:center;gap:10px;font-size:11px;letter-spacing:2px;font-weight:700;color:#881337;}
.war-logo {display:grid;place-items:center;width:28px;height:32px;background:#881337;color:#f1dfb6;clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%);font-size:20px;letter-spacing:0;}
.war-status {font-size:11px;color:#64748b;border:1px solid #e9dfe2;border-radius:20px;background:#fff;padding:6px 10px;white-space:nowrap;}
.war-body {display:grid;grid-template-columns:minmax(0,1.2fr) minmax(290px,.85fr);gap:36px;align-items:center;}
.war-kicker {color:#947c86;font-size:12px;letter-spacing:4px;margin-bottom:12px;}
.war-title {font-size:clamp(30px,4vw,50px);line-height:1.2;font-weight:800;letter-spacing:-1px;margin:0 0 14px;color:#72092c;}
.war-title span {color:#ac7d36;}.war-description {font-size:13px;color:#7c6c77;line-height:1.9;max-width:450px;}
.war-statline {display:flex;gap:28px;flex-wrap:wrap;margin-top:24px;}
.war-statline strong {display:block;color:#334155;font:600 24px/1.2 ui-monospace,SFMono-Regular,monospace;}
.war-statline small {display:block;font-size:11px;color:#8b7c85;margin-top:6px;}
.champion {padding:22px 24px;border:1px solid #e2cfaa;border-radius:14px;background:linear-gradient(130deg,#fffdf8,#fff);box-shadow:0 4px 16px #72092c05;}
.champion-eyebrow {display:flex;justify-content:space-between;gap:10px;color:#a47e3f;font-size:10px;letter-spacing:1.5px;}
.champion-name {font-size:24px;font-weight:750;color:#72092c;margin:16px 0 5px;overflow-wrap:anywhere;}
.champion-id {color:#9b8c94;font-size:11px;overflow-wrap:anywhere;}
.champion-score {display:flex;align-items:baseline;gap:9px;margin:18px 0 10px;}
.champion-score strong {font:600 48px/1 ui-monospace,SFMono-Regular,monospace;color:#881337;letter-spacing:-2px;}
.champion-score span,.champion-meta {color:#8b7c85;font-size:12px;line-height:1.8;}
.champion-form {display:flex;gap:5px;align-items:center;border-top:1px solid #efe8dc;padding-top:12px;margin-top:14px;}
.champion-form small {font-size:10px;color:#9b8c94;margin-right:7px;}
.form-win,.form-loss {display:inline-grid;place-items:center;width:24px;height:24px;font-size:11px;border-radius:5px;}
.form-win {color:#287858;background:#e9f5ee;}.form-loss {color:#a94364;background:#fbeef2;}
@media(max-width:760px) {.war-room{padding:20px}.war-top{gap:10px;flex-wrap:wrap}.war-body{grid-template-columns:1fr;gap:22px}.war-title{font-size:36px}.war-statline{gap:22px}.champion{padding:20px}}
</style>
"""


def build_war_room_html(standings, history, total, verified, selected_matches, scope):
    """All showcased values come from the same records as the displayed ranking."""
    e = lambda value: escape(str(value))
    if standings.empty:
        name, full_name, winrate, matches, rating, recent = "等待首位登顶者", "核验战绩后，榜首将在这里亮相", "—", "—", "—", ""
    else:
        ranked = standings.sort_values(["胜率_num", "总场次", "KDA_num"], ascending=False)
        full_name = str(ranked.index[0]); row = ranked.iloc[0]
        name, winrate, matches, rating = short_name(full_name), f"{row['胜率_num']:.1f}%", str(int(row['总场次'])), f"{row['MMR']:.1f}"
        recent = "".join(f'<span class="form-{"win" if won else "loss"}">{"胜" if won else "负"}</span>' for won in history[full_name]["outcomes"][-5:])
    hero = f'''<div class="war-room">
<div class="war-top"><div class="war-brand"><span class="war-logo">✦</span>HEX LEAGUE / 战情室</div><span class="war-status">已核验 {verified} / {total} 局</span></div>
<div class="war-body"><div><div class="war-kicker">海 克 斯 内 战</div><div class="war-title">今夜，<br>战力<span>全开。</span></div><div class="war-description">每一场内战，都值得被记住。<br>查看天梯、组织对局，留下属于你们的高光。</div><div class="war-statline"><div><strong>{total}</strong><small>累计收录对局</small></div><div><strong>{len(standings)}</strong><small>当前上榜选手</small></div><div><strong>{selected_matches}</strong><small>当前统计对局</small></div></div></div>
<div class="champion"><div class="champion-eyebrow"><span>当前天梯领跑者</span><span>RANK / 01</span></div><div class="champion-name">{e(name)}</div><div class="champion-id">{e(full_name)}</div><div class="champion-score"><strong>{e(winrate)}</strong><span>胜率</span></div><div class="champion-meta">{e(matches)} 场对局 · MMR {e(rating)}<br>{e(scope)}</div><div class="champion-form"><small>近5局 · 右侧最新</small>{recent or '<small>暂无记录</small>'}</div></div></div></div>'''
    return hero


def render_admin_settings(records):
    require_admin()
    admin_mode = True
    model_tab, maintenance_tab, backup_tab, voice_tab = st.tabs(["模型接口", "重新识别", "备份恢复", "语音配置"])
    with model_tab:
        default_key = get_secret("DASHSCOPE_API_KEY")
        key = st.text_input("DashScope API Key", value=default_key, type="password", placeholder="sk-...", key="vision_key_input")

        st.text_input(
            "视觉模型 ID",
            value=get_secret("DASHSCOPE_MODEL", "qwen3-vl-plus"),
            key="vision_model",
            help="填写百炼控制台中当前地域可调用的视觉模型 ID。",
            disabled=not admin_mode,
        )
        st.text_input(
            "Base URL",
            value=get_secret("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            key="vision_base_url",
            help="须与 API Key 所属地域及套餐对应；填写到 v1，不要添加 /chat/completions。",
            disabled=not admin_mode,
        )
        st.caption("默认使用北京按量付费接口；其他地域或套餐请填写控制台提供的地址。")
        st.caption("省内存模式：截图逐张识别，每批最多 10 张。")
        st.checkbox("压缩识别大图", value=True, key="optimize_image",
                    help="图片宽度最多 1920 像素；昵称较小时可关闭后重试。", disabled=not admin_mode)

    with maintenance_tab:
        st.markdown("---")
        if records and st.button("🔄 重新扫描历史截图", help="提取输出与承伤占比并补齐数据库", use_container_width=True, disabled=not admin_mode):
            require_admin()
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

    with backup_tab:
        if records:
            if admin_mode and st.checkbox("生成完整 JSON 备份（包含截图）", key="prepare_json_backup"):
                st.download_button("📤 导出完整数据 (JSON)", json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8'), "lol_records_backup.json", "application/json", use_container_width=True)
        uploaded_backup = st.file_uploader("导入备份文件", type=["json"], key="backup_uploader", disabled=not admin_mode)
        restore_checked = st.checkbox("确认用备份替换当前所有战绩", disabled=not admin_mode)
        if uploaded_backup is not None and st.button("📥 恢复数据", type="primary", use_container_width=True, disabled=not admin_mode or not restore_checked):
            try:
                save_records(json.load(uploaded_backup))
                st.success("恢复成功并已同步！")
                time.sleep(0.5); st.rerun()
            except Exception as e:
                st.error(f"导入失败: {e}")

    with voice_tab:
        cfg = load_config()
        new_main = st.text_input("大厅主语音", value=cfg.get("main_voice", ""))
        new_blue = st.text_input("🔵 蓝方语音", value=cfg.get("blue_voice", ""))
        new_red = st.text_input("🔴 红方语音", value=cfg.get("red_voice", ""))
        if st.button("💾 保存链接", use_container_width=True, disabled=not admin_mode):
            save_config({"main_voice": new_main, "blue_voice": new_blue, "red_voice": new_red})
            st.success("已保存！"); time.sleep(0.3); st.rerun()

    return key


# ---------------- 侧边栏：控制台 ----------------
with st.sidebar:
    st.markdown(HERO_CSS, unsafe_allow_html=True)
    st.markdown("### 🎛️ 系统控制台")
    render_admin_login()
    admin_mode = is_admin()
    key = ""
    records = load_records()
    total_games_all = len(records)
    verified_games_all = sum(is_record_verified(r) for r in records)
    gh_t, gh_r = get_github_auth()
    st.caption("🟢 **云端自动同步**: 已启用 (GitHub)" if gh_t and gh_r else "⚪ **云端自动同步**: 未配置 Token")
    st.caption(f"✅ **胜负已核验**: {verified_games_all}/{total_games_all} 局")
    stats_scope = st.radio(
        "胜率统计口径",
        ["仅已核验对局", "全部对局（含待核验）"],
        index=1 if st.query_params.get("stats", "") == "all" else 0,
        help="为保证胜率可信，默认排除尚未人工确认胜负的对局。",
    )

    if admin_mode:
        with st.expander("⚙️ 管理员设置", expanded=False):
            key = render_admin_settings(records)

    if records:
        with st.expander("🔍 历史对局图文复盘"):
            selected_idx = st.selectbox(
                "选择对局", range(len(records)),
                format_func=lambda i: (
                    f"第 {i+1} 局 "
                    f"({'A组' if records[i].get('winning_team') == 'BLUE' else 'B组'}胜 · "
                    f"{'已核验' if is_record_verified(records[i]) else '待核验'})"
                )
            )
            curr_record = records[selected_idx]
            if curr_record.get("image_thumb") and st.checkbox("加载复盘截图", key="show_replay_image"):
                st.image(f"data:image/jpeg;base64,{curr_record['image_thumb']}", use_container_width=True)
            p_rows = [{
                "分组": "A组" if p.get("team") == "BLUE" else "B组", "玩家": short_name(p.get("player_name", "")),
                "KDA": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                "伤害": f"{p.get('damage_share')}%" if p.get('damage_share') is not None else "--"
            } for p in curr_record.get("players", [])]
            if p_rows: st.dataframe(pd.DataFrame(p_rows), hide_index=True)
            delete_checked = st.checkbox("确认删除该局", key=f"delete_checked_{selected_idx}", disabled=not admin_mode)
            if st.button("🗑️ 删除该局", key=f"del_g_{selected_idx}", use_container_width=True, disabled=not admin_mode or not delete_checked):
                require_admin()
                records.pop(selected_idx)
                save_records(records)
                st.success("已删除该局！"); time.sleep(0.3); st.rerun()

# ---------------- 主界面 1：顶栏电竞控制台 ----------------
cfg = load_config()
front_slot = st.empty()
vc1, vc2, vc3 = st.columns(3)
with vc1: st.link_button("🎙️ 大厅语音作战室", cfg.get("main_voice", "https://kook.top/"), use_container_width=True)
with vc2: st.link_button("🔵 蓝方语音作战室", cfg.get("blue_voice", "https://kook.top/"), use_container_width=True)
with vc3: st.link_button("🔴 红方语音作战室", cfg.get("red_voice", "https://kook.top/"), use_container_width=True)
st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

if stats_scope == "仅已核验对局" and verified_games_all < total_games_all:
    st.info(
        f"当前胜率只统计 {verified_games_all} 局已核验对局；"
        f"另有 {total_games_all - verified_games_all} 局待核验，请前往「战绩核验」逐局确认。"
    )

# ---------------- 主界面 2：Tabs 视图 ----------------
active_page = st.radio("功能页面", [
    "📊 胜率天梯与荣誉榜", "⚔️ 赛前阵营分队系统", "🎯 局内战术图谱与成就馆",
    "✅ 战绩核验", "📥 战绩智能录入"
], horizontal=True, key="active_page")

ladder_min_players = 0
if active_page == "📊 胜率天梯与荣誉榜":
    size_options = ["全部对局", "7人及以上对局"]
    default_size = st.session_state.get("ladder_size_preference", "7人及以上对局" if st.query_params.get("players", "") == "7" else "全部对局")
    size_choice = st.radio("榜单对局人数", size_options, index=size_options.index(default_size), horizontal=True, key="ladder_size_widget")
    st.session_state.ladder_size_preference = size_choice
    ladder_min_players = 7 if size_choice == "7人及以上对局" else 0

def valid_player_count(record):
    return len({clean_player_name_strict(p.get("player_name", "")) for p in record.get("players", [])
                if clean_player_name_strict(p.get("player_name", "")) and not is_result_banner(p.get("player_name", ""))
                and str(p.get("team", "")).upper() in {"BLUE", "RED"}})

def match_in_stats(record):
    return (stats_scope != "仅已核验对局" or is_record_verified(record)) and valid_player_count(record) >= ladder_min_players

# ---------------- 数据清洗与统计算法引擎 ----------------
base_stats_records = (
    [r for r in records if is_record_verified(r)]
    if stats_scope == "仅已核验对局"
    else records
)
stats_records = [r for r in base_stats_records if match_in_stats(r)]
all_raw = [p.get("player_name", "") for r in base_stats_records for p in r.get("players", []) if p.get("player_name")]
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
    if not match_in_stats(r):
        continue
    players = r.get("players", [])
    valid_6p = len(players) >= 6
    blue_k = sum(int(p.get("kills", 0)) for p in players if str(p.get("team", "")).upper() == "BLUE")
    red_k = sum(int(p.get("kills", 0)) for p in players if str(p.get("team", "")).upper() == "RED")
    blue_team, red_team = [], []

    for p in players:
        if not p.get("player_name"): continue
        fname = get_final_name(p["player_name"])
        k, d, a = int(p.get("kills", 0)), int(p.get("deaths", 0)), int(p.get("assists", 0))
        side = str(p.get("team", "")).upper()
        # 统计时以整局 winning_team 为唯一事实来源，避免旧 is_winner 字段残留错误。
        is_win = side == str(r.get("winning_team", "")).upper()

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

front_standings = df[df["总场次"] >= 10] if ladder_min_players == 7 and not df.empty else df
front_slot.markdown(build_war_room_html(
    front_standings, player_history, total_games_all, verified_games_all,
    len(stats_records),
    stats_scope + (" · 7人及以上 / 至少10局上榜" if ladder_min_players == 7 else " · 全部人数"),
), unsafe_allow_html=True)

# ================= Tab 1: 胜率天梯与荣誉榜 =================
if active_page == "📊 胜率天梯与荣誉榜":
    if ladder_min_players == 7:
        st.caption("上榜条件：在当前核验口径下，参加7人及以上对局累计至少10局。")
        if not df.empty:
            df = df[df["总场次"] >= 10].copy()
    st.caption(f"当前核验口径：{stats_scope} · 纳入 {len(stats_records)} 场对局")
    if df.empty:
        if ladder_min_players == 7:
            st.info("💡 暂无选手在当前核验口径下参加至少10场7人及以上对局。可切换为全部对局榜单，或继续录入并核验战绩。")
        else:
            st.info("💡 当前核验状态下没有对局。请先录入并核验战绩。")
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
            link_scope = "all" if stats_scope == "全部对局（含待核验）" else "verified"
            wins_url = escape("?" + urlencode({"player": p_id, "result": "wins", "stats": link_scope, "players": ladder_min_players}), quote=True)
            losses_url = escape("?" + urlencode({"player": p_id, "result": "losses", "stats": link_scope, "players": ladder_min_players}), quote=True)
            name_link = f"{medal}{escape(short_name(p_id))}"
            wins_link = f"<a href='{wins_url}' target='_blank' rel='noopener noreferrer' style='color:#0284c7;'>{int(row['胜场'])}</a>"
            losses_link = f"<a href='{losses_url}' target='_blank' rel='noopener noreferrer' style='color:#e11d48;'>{int(row['负场'])}</a>"
            t_rows.append(f"<tr class='{r_cls}'><td style='text-align:left;padding-left:16px;font-weight:800;'>{name_link}</td><td>{int(row['总场次'])}</td><td>{wins_link}</td><td>{losses_link}</td><td>{wr_b}</td><td style='color:#72092c;font-weight:900;'>{row['MMR']:.1f}</td><td>{row['场均击杀']:.1f}</td><td>{row['KD']:.2f}</td><td>{kda_b}</td><td>{int(row['击杀'])}</td><td>{int(row['死亡'])}</td><td>{int(row['助攻'])}</td></tr>")
        st.markdown(f'<div class="ladder-table-box"><table class="ladder-table"><thead><tr><th style="text-align:left;padding-left:16px;">选手排位</th><th>总场次</th><th>胜局</th><th>负局</th><th>胜率</th><th>MMR战力</th><th>场均击杀</th><th>KD</th><th>KDA</th><th>总击杀</th><th>总死亡</th><th>总助攻</th></tr></thead><tbody>{"".join(t_rows)}</tbody></table></div>', unsafe_allow_html=True)

        requested_player = st.query_params.get("player", "")
        requested_result = st.query_params.get("result", "")
        with st.expander("🔎 选手档案与逐局战绩 · 选择选手或点击胜局 / 负局查看", expanded=bool(requested_player)):
            profile_options = list(df_sorted.index)
            selected_profile = st.selectbox(
                "查看选手", profile_options,
                index=profile_options.index(requested_player) if requested_player in profile_options else 0,
                key="profile_player_" + hashlib.sha256(requested_player.encode()).hexdigest()[:10],
            )
            profile_row = df.loc[selected_profile]
            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("场次", int(profile_row["总场次"]))
            pc2.metric("胜率", f"{profile_row['胜率_num']:.1f}%")
            pc3.metric("KDA", f"{profile_row['KDA_num']:.2f}")
            pc4.metric("MMR", f"{profile_row['MMR']:.1f}")
            result_options = ["全部", "胜局", "负局"]
            history_filter = st.radio(
                "筛选个人战绩", result_options,
                index={"wins": 1, "losses": 2}.get(requested_result, 0), horizontal=True,
                key="profile_result_" + hashlib.sha256((requested_player + requested_result).encode()).hexdigest()[:10],
            )
            personal_matches = []
            for original_index, match in enumerate(records):
                if not match_in_stats(match):
                    continue
                for player in match.get("players", []):
                    if get_final_name(player.get("player_name", "")) != selected_profile:
                        continue
                    won = str(player.get("team", "")).upper() == str(match.get("winning_team", "")).upper()
                    if history_filter == "胜局" and not won or history_filter == "负局" and won:
                        continue
                    personal_matches.append((original_index, match, player, won))
            if personal_matches:
                personal_table = pd.DataFrame([{
                    "对局": f"第 {i+1} 局", "结果": "胜" if won else "负",
                    "分组": "A组" if player.get("team") == "BLUE" else "B组",
                    "KDA": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
                    "核验": "已核验" if is_record_verified(match) else "待核验",
                } for i, match, player, won in reversed(personal_matches)])
                ordered_matches = list(reversed(personal_matches))
                selection_key = hashlib.sha256(json.dumps([
                    selected_profile, history_filter, stats_scope, ladder_min_players,
                    [(i, m.get("md5"), m.get("winning_team"), p.get("team")) for i,m,p,_ in ordered_matches],
                ], ensure_ascii=False).encode()).hexdigest()[:16]
                st.caption("点击任意一行，直接查看该局截图与双方玩家。")
                event = st.dataframe(personal_table, hide_index=True, use_container_width=True,
                    on_select="rerun", selection_mode="single-row", key="personal_match_rows_"+selection_key)
                if event.selection.rows and 0 <= event.selection.rows[0] < len(ordered_matches):
                    personal_game, detail, _, _ = ordered_matches[event.selection.rows[0]]
                    st.markdown(f"#### 第 {personal_game+1} 局 · 对局详情")
                    if detail.get("image_thumb"):
                        with st.container(height=520, border=True):
                            st.image(f"data:image/jpeg;base64,{detail['image_thumb']}", use_container_width=True)
                    else:
                        st.caption("这局没有保存结算截图。")
                    st.dataframe(pd.DataFrame([{
                        "玩家 ID": p.get("player_name", ""),
                        "分组": "A组" if p.get("team") == "BLUE" else "B组",
                        "结果": "胜" if p.get("team") == detail.get("winning_team") else "负",
                        "KDA": f"{p.get('kills', 0)}/{p.get('deaths', 0)}/{p.get('assists', 0)}",
                    } for p in detail.get("players", [])]), hide_index=True, use_container_width=True)
            else:
                st.info("当前筛选下没有对局。")

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

# ================= Tab 2: 赛前阵营分队系统 =================
if active_page == "⚔️ 赛前阵营分队系统":
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
if active_page == "🎯 局内战术图谱与成就馆":
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

# ================= Tab 4: 历史战绩胜负核验 =================
if active_page == "✅ 战绩核验":
    st.markdown('<div class="card-panel"><div class="panel-header-title">✅ 历史战绩胜负核验</div>', unsafe_allow_html=True)
    st.caption("A组 / B组只代表截图中的两块玩家列表，不代表游戏里的真实蓝方或红方。请以截图上的‘胜利 / 失败’文字为准。")
    if not admin_mode:
        st.info("访客可以查看核验记录；修改组别和保存核验结果需要管理员登录。")
    if verification_flash := st.session_state.pop("verification_flash", None):
        if verification_flash["level"] == "warning":
            st.warning(verification_flash["text"])
        else:
            st.success(verification_flash["text"])

    if not records:
        st.info("💡 暂无历史对局。")
    else:
        pending_indices = [i for i, r in enumerate(records) if not is_record_verified(r)]
        verified_indices = [i for i, r in enumerate(records) if is_record_verified(r)]
        vm1, vm2, vm3 = st.columns(3)
        vm1.metric("全部对局", len(records))
        vm2.metric("已核验", len(verified_indices))
        vm3.metric("待核验", len(pending_indices))

        render_batch_verification(records, admin_mode)

        navigation = st.session_state.pop("verify_navigation", None)
        if navigation:
            st.session_state["verify_scope"] = navigation["scope"]
        verify_scope = st.radio(
            "查看范围", ["待核验", "已核验", "全部"], horizontal=True,
            help="建议先逐局清空待核验列表。",
            key="verify_scope",
        )
        if verify_scope == "待核验":
            verify_choices = pending_indices
        elif verify_scope == "已核验":
            verify_choices = verified_indices
        else:
            verify_choices = list(range(len(records)))

        if not verify_choices:
            st.success("🎉 当前列表没有需要处理的对局。")
        else:
            ordered_choices = list(reversed(verify_choices))
            if navigation and navigation.get("index") in verify_choices:
                st.session_state["verify_game_index"] = navigation["index"]
            if st.session_state.get("verify_game_index") not in verify_choices:
                st.session_state["verify_game_index"] = ordered_choices[0]
            verify_idx = st.selectbox(
                "选择要核验的对局",
                ordered_choices,
                format_func=lambda i: (
                    f"第 {i+1} 局 · "
                    f"{'已核验' if is_record_verified(records[i]) else '待核验'}"
                ),
                key="verify_game_index",
            )
            verify_record = records[verify_idx]
            draft_identity = str(verify_record.get("md5") or hashlib.sha256(
                json.dumps(verify_record, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest())
            editor_revision = hashlib.sha256(json.dumps(verify_record, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
            draft_key = f"{draft_identity}_{editor_revision}"
            drafts = st.session_state.setdefault("verify_drafts", {}) if admin_mode else {}
            saved_draft = drafts.get(draft_key, {})
            st.progress((len(verified_indices) / len(records)), text=f"已完成 {len(verified_indices)} / {len(records)} 局")
            if saved_draft:
                st.caption("已恢复本次会话中的未保存草稿。关闭页面后草稿可能丢失。")
            review_layout = st.radio("核验布局", ["左右对照", "上下排列"], horizontal=True, key="review_layout")
            if review_layout == "左右对照":
                image_col, editing_col = st.columns([1.05, 1.2], gap="large")
            else:
                image_col, editing_col = st.container(), st.container()
            with image_col:
                st.markdown("#### ① 对照结算截图")
                if verify_record.get("image_thumb"):
                    st.caption("长图可独立滚动，工具栏支持全屏查看。")
                    with st.container(height=720, border=True):
                        st.image(f"data:image/jpeg;base64,{verify_record['image_thumb']}", use_container_width=True)
                else:
                    st.warning("这局没有保存截图，请根据原始记录确认；无法确认时不要核验。")
                st.caption("历史截图是压缩预览，看不清时请对照原始图片。")

            with editing_col:
                st.markdown("#### ② 核对组别和胜方")
                st.caption("点击分组单元格可把误分的玩家移回 A组 / B组。请核对完整游戏 ID；下方名单会随修改更新。")
                review_players = saved_draft.get("players", verify_record.get("players", []))
                editor_rows = [{
                    "玩家 ID": p.get("player_name", ""),
                    "分组": "A组" if str(p.get("team", "")).upper() == "BLUE" else "B组",
                    "KDA": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                } for p in review_players]
                edited_groups = st.data_editor(
                    pd.DataFrame(editor_rows), hide_index=True, use_container_width=True,
                    key=f"group_editor_{verify_idx}_{editor_revision}",
                    disabled=["玩家 ID", "KDA"] if admin_mode else True,
                    column_config={"分组": st.column_config.SelectboxColumn(
                        "分组", options=["A组", "B组"], required=True,
                    )},
                )
                corrected_players = []
                for position, player in enumerate(review_players):
                    copy = dict(player)
                    label = edited_groups.iloc[position]["分组"]
                    copy["team"] = {"A组": "BLUE", "B组": "RED"}.get(label, "")
                    corrected_players.append(copy)
                group_counts = {side: sum(p["team"] == side for p in corrected_players) for side in ("BLUE", "RED")}
                st.caption(f"当前分组：A组 {group_counts['BLUE']} 人 / B组 {group_counts['RED']} 人")
                if abs(group_counts["BLUE"] - group_counts["RED"]) > 1:
                    st.warning("两组人数差距较大，可能存在误分或漏识别；请对照截图逐个检查。人数提示不会自动改分组。")

                verify_groups = {}
                group_cols = st.columns(2)
                for group_pos, group_side in enumerate(("BLUE", "RED")):
                    group_players = [
                        p for p in corrected_players
                        if str(p.get("team", "")).upper() == group_side
                    ]
                    verify_groups[group_side] = group_players
                    group_label = "A组" if group_side == "BLUE" else "B组"
                    current_mark = " · 当前记录为获胜" if verify_record.get("winning_team") == group_side else ""
                    with group_cols[group_pos]:
                        st.markdown(f"#### {group_label}{current_mark}")
                        group_rows = [{
                            "玩家": p.get("player_name", ""),
                            "KDA": f"{int(p.get('kills', 0))}/{int(p.get('deaths', 0))}/{int(p.get('assists', 0))}",
                        } for p in group_players]
                        if group_rows:
                            st.dataframe(pd.DataFrame(group_rows), hide_index=True, use_container_width=True)
                        else:
                            st.warning(f"未识别到{group_label}玩家。")

                group_labels = {
                    side: (
                        f"{'A组' if side == 'BLUE' else 'B组'}（"
                        + "、".join(short_name(p.get("player_name", "")) for p in verify_groups[side])[:100]
                        + "）"
                    )
                    for side in ("BLUE", "RED")
                }
                corrected_winner = st.radio(
                    "对照截图，哪一组获胜？", ["BLUE", "RED"],
                    index=0 if saved_draft.get("winner", verify_record.get("winning_team")) == "BLUE" else 1,
                    format_func=lambda side: group_labels[side],
                    key=f"review_winner_{draft_key}", disabled=not admin_mode,
                )
                if admin_mode:
                    drafts[draft_key] = {"players": corrected_players, "winner": corrected_winner}
                st.markdown("#### ③ 保存前确认变化")
                changes = verification_changes(verify_record, corrected_players, corrected_winner)
                if changes:
                    result_changes = sum(row["原结果"] != row["新结果"] for row in changes)
                    st.caption(f"{len(changes)} 位玩家的记录将改变，其中 {result_changes} 位胜负改变。尚未保存。")
                    st.dataframe(pd.DataFrame(changes), hide_index=True, use_container_width=True)
                else:
                    st.info("组别和胜方未改变；保存后将确认这局的核验状态。")
                confirmation_revision = hashlib.sha256(json.dumps(
                    [corrected_players, corrected_winner], ensure_ascii=False, sort_keys=True
                ).encode()).hexdigest()[:12]
                result_checked = st.checkbox(
                    "我已逐个核对玩家组别，并确认截图中的‘胜利 / 失败’结果",
                    key=f"review_confirm_{draft_key}_{confirmation_revision}", disabled=not admin_mode,
                )
                save_col, next_col = st.columns(2)
                with save_col:
                    save_verification = st.button(
                        "💾 保存核验结果", type="primary", use_container_width=True,
                        disabled=not admin_mode, key=f"review_save_{draft_key}",
                    )
                with next_col:
                    save_and_next = st.button(
                        "✅ 保存并核验下一局", use_container_width=True,
                        disabled=not admin_mode, key=f"review_next_{draft_key}",
                    )

            if save_verification or save_and_next:
                if not result_checked:
                    st.warning("请先对照原图确认，并勾选核验声明。")
                elif not verify_groups["BLUE"] or not verify_groups["RED"]:
                    st.error("两组选手数据不完整，本次未保存。请先重新识别或修复记录。")
                else:
                    try:
                        require_admin()
                        latest_records = load_records()
                        if verify_idx >= len(latest_records) or latest_records[verify_idx] != verify_record:
                            raise ValueError("历史记录已发生变化，请刷新页面后重试。")
                        latest_records[verify_idx] = correct_record_winner(
                            latest_records[verify_idx], corrected_winner, verified=True,
                            players=corrected_players,
                        )
                        synced = save_records(latest_records)
                        sync_token, sync_repo = get_github_auth()
                        if sync_token and sync_repo and synced is False:
                            st.session_state.verification_flash = {
                                "level": "warning", "text": "本地已校正，但云端同步失败；请立即导出 JSON 备份。",
                            }
                        else:
                            save_place = "并同步云端" if sync_token and sync_repo else "到本地"
                            st.session_state.verification_flash = {
                                "level": "success", "text": f"核验结果已保存{save_place}，所有玩家的胜负字段已同步重建。",
                            }
                        drafts.pop(draft_key, None)
                        if save_and_next and not (sync_token and sync_repo and synced is False):
                            remaining = [i for i in reversed(range(len(latest_records))) if not is_record_verified(latest_records[i])]
                            later = [i for i in remaining if i < verify_idx]
                            st.session_state.verify_navigation = {
                                "scope": "待核验", "index": (later or remaining or [None])[0],
                            }
                            if not remaining:
                                st.session_state.verification_flash["text"] += " 所有对局已核验完成。"
                        else:
                            st.session_state.verify_navigation = {"scope": "已核验", "index": verify_idx}
                        st.rerun()
                    except Exception as exc:
                        st.error(f"核验结果未保存：{exc}")

    st.markdown('</div>', unsafe_allow_html=True)


# ================= Tab 5: 战绩智能录入 =================
if active_page == "📥 战绩智能录入":
    st.markdown('<div class="card-panel"><div class="panel-header-title">📸 战绩截图智能分析录入</div>', unsafe_allow_html=True)
    with st.form("upload_box", clear_on_submit=False):
        files = st.file_uploader("选择截图（支持批量多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True, disabled=not admin_mode)
        sub = st.form_submit_button("🚀 开始解析并录入", type="primary", use_container_width=True, disabled=not admin_mode)

    if not admin_mode:
        st.info("战绩录入需要管理员登录。")

    previous_report = st.session_state.get("upload_report")
    if previous_report:
        st.info(previous_report["summary"])
        for message in previous_report["errors"]:
            st.error(message)

    if sub:
        require_admin()
        if not files:
            st.warning("⚠️ 请先选择战绩截图！")
        elif len(files) > 10:
            st.warning("为降低内存占用，每批最多上传 10 张，请分批选择。")
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
                        jobs.append((index, uploaded.name, uploaded, digest))
                    del data

                bar = st.progress(0)
                status_box = st.empty()
                successes = {}
                completed = 0
                if jobs:
                    status_box.info(f"⏳ 正在逐张识别 {len(jobs)} 张截图。")
                    for index, name, uploaded, digest in jobs:
                        data = uploaded.getvalue()
                        result, error, elapsed = recognize_upload_job(data, digest, key, settings)
                        del data
                        completed += 1
                        if error:
                            errors.append(f"❌ {name} 录入失败：{error}")
                        else:
                            successes[index] = result
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
                    f"本批识别成功 {len(successes)} 张，失败 {len(jobs) - len(successes)} 张，跳过重复 {skipped} 张，"
                    f"总耗时 {total_elapsed:.1f} 秒。{sync_message}"
                    f"新记录已标记为待核验，请前往‘战绩核验’确认胜负后再计入可信胜率。"
                )
                st.session_state["upload_report"] = {"summary": summary, "errors": errors}
                status_box.empty()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

