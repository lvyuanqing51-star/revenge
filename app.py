# 海克斯内战 · 完整单文件优化版
# 安装依赖：pip install streamlit pandas Pillow openai
# 启动：streamlit run app.py
# records.json 和 config.json 放在本文件同目录。


# ==================== hexleague/storage.py ====================
"""Atomic local storage and explicit GitHub synchronization status."""
import base64
import json
import os
from pathlib import Path
import tempfile
import urllib.request
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / 'records.json'
CONFIG_FILE = ROOT / 'config.json'

def get_secret(name, default=''):
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default

def atomic_write(path, data):
    handle, temp = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def load_config():
    default = {key: 'https://kook.top/' for key in ('main_voice', 'blue_voice', 'red_voice')}
    if CONFIG_FILE.exists():
        try:
            default.update(json.loads(CONFIG_FILE.read_text()))
        except (ValueError, OSError):
            st.warning('语音配置无法读取，已使用默认链接。')
    return default

def save_config(config):
    from urllib.parse import urlparse
    if any(urlparse(url).scheme not in ('http', 'https') or not urlparse(url).netloc for url in config.values()):
        raise ValueError('语音链接须为完整的 http / https 地址。')
    atomic_write(CONFIG_FILE, config)

def get_github_auth():
    return get_secret('GITHUB_TOKEN'), get_secret('GITHUB_REPO')

def github_request(method='GET', payload=None):
    token, repo = get_github_auth()
    request = urllib.request.Request(
        f'https://api.github.com/repos/{repo}/contents/records.json',
        data=json.dumps(payload).encode() if payload else None,
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'HexLeagueApp'},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def validate_backup(data):
    if not isinstance(data, list):
        raise ValueError('备份文件顶层须为对局列表。')
    for record in data:
        if not isinstance(record, dict) or not isinstance(record.get('players'), list) or any(not isinstance(p, dict) for p in record['players']):
            raise ValueError('每场对局须包含有效的 players 列表。')
    return [validate_recognition(record) for record in remove_result_banners(data)]

def load_records():
    local = []
    if DATA_FILE.exists():
        try:
            local = validate_backup(json.loads(DATA_FILE.read_text(encoding='utf-8')))
        except (ValueError, TypeError, OSError) as exc:
            st.error(f'战绩文件无法读取：{exc}。原文件未覆盖。请修复或恢复有效备份。')
            st.stop()
    if 'gh_checked' not in st.session_state:
        st.session_state.gh_checked = True
        token, repo = get_github_auth()
        if token and repo:
            try:
                result = github_request()
                cloud = validate_backup(json.loads(base64.b64decode(result['content'])))
                st.session_state.gh_sha = result['sha']
                # Local-only records are retained when a previous upload failed.
                merged = list(cloud)
                hashes = {r.get('md5') for r in cloud if r.get('md5')}
                for record in local:
                    if record not in cloud and (not record.get('md5') or record['md5'] not in hashes):
                        merged.append(record)
                atomic_write(DATA_FILE, merged)
                local = merged
            except Exception as exc:
                st.session_state.sync_error = f'云端读取失败：{exc}'
    return remove_result_banners(local)

def push_records_to_github(records):
    try:
        payload = {'message': 'Update match records', 'content': base64.b64encode(json.dumps(records, ensure_ascii=False).encode()).decode()}
        if st.session_state.get('gh_sha'):
            payload['sha'] = st.session_state.gh_sha
        result = github_request('PUT', payload)
        st.session_state.gh_sha = result['content']['sha']
        st.session_state.pop('sync_error', None)
        return True
    except Exception as exc:
        st.session_state.sync_error = f'云端同步失败：{exc}。如发生版本冲突，请先导出备份，再刷新页面合并云端记录。'
        return False

def save_records(records, sync_cloud=True):
    records = validate_backup(records)
    atomic_write(DATA_FILE, records)
    token, repo = get_github_auth()
    return push_records_to_github(records) if sync_cloud and token and repo else None

def show_save_status(result):
    if result is True:
        st.success('已保存并同步云端。')
    elif result is False:
        st.warning('本地已保存，云端同步未完成。请导出备份。')
    else:
        st.success('已保存到本地。')


# ==================== hexleague/recognition.py ====================
import base64
import difflib
import hashlib
import json
import math
import re
import time
from io import BytesIO
from PIL import Image
import streamlit as st
TARGET_QIANQIU = "千秋种我一栗卿#52652"

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
            if isinstance(value, bool) or value is None or not re.fullmatch(r"\d+(?:\.0+)?", str(value)):
                raise ValueError(f"玩家 {name} 的 KDA 不完整，本次未保存。")
            player[field] = int(float(value))
        for field in ("damage_share", "taken_share"):
            value = player.get(field)
            if value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"玩家 {name} 的占比格式不正确。")
                if not math.isfinite(value) or not 0 <= value <= 100:
                    raise ValueError(f"玩家 {name} 的占比须为 0–100。")
                player[field] = value
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
    from openai import OpenAI, NotFoundError
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



# ==================== hexleague/analytics.py ====================
from collections import defaultdict
from itertools import combinations
import pandas as pd

def calculate_stats(records):
    all_raw = [p.get("player_name", "") for r in records for p in r.get("players", []) if p.get("player_name")]
    name_mapping = build_canonical_name_map(sorted(set(all_raw)))

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


    return dict(df=df, radar_stats_pool=dict(radar_stats_pool), player_history=dict(player_history), synergy_stats=dict(synergy_stats), nemesis_stats=dict(nemesis_stats), max_single_kill=max_single_kill, max_single_death=max_single_death, max_single_assist=max_single_assist)


# ==================== hexleague/matching.py ====================
"""Pure matchmaking logic; no UI or session state dependencies."""
from itertools import combinations
import random

def assign_teams(players, ratings, rules=(), mode='balanced'):
    if not 2 <= len(players) <= 16:
        raise ValueError('请选择 2–16 位选手。')
    players = list(dict.fromkeys(players))
    size = len(players) // 2
    candidates = []
    ranked = sorted(players, key=lambda p: ratings[p], reverse=True)
    for blue_tuple in combinations(players, size):
        blue = set(blue_tuple)
        red = set(players) - blue
        if any(r['p1'] in players and r['p2'] in players and
               ((r['p1'] in blue) == (r['p2'] in blue)) != (r['type'] == 'same') for r in rules):
            continue
        if mode == 'carry' and len(players) >= 4:
            if not ((ranked[0] in blue) != (ranked[1] in blue) and
                    (ranked[-1] in blue) != (ranked[-2] in blue)):
                continue
        gap = abs(sum(ratings[p] for p in blue) / len(blue) - sum(ratings[p] for p in red) / len(red))
        candidates.append((gap, list(blue_tuple), [p for p in players if p not in blue]))
    if not candidates:
        raise ValueError('当前约束无法满足，请调整同队 / 对立规则，或切换平衡模式。')
    return random.choice(candidates) if mode == 'random' else min(candidates, key=lambda c: c[0])


# ==================== hexleague/theme.py ====================
from html import escape
import streamlit as st

CSS = '''
<style>
:root {--ink:#172033;--muted:#64748b;--accent:#5b4de8;--line:#e5e9f2;}
.stApp {background:#f6f7fb;color:var(--ink);font-family:Inter,-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;}
.block-container {max-width:1320px;padding-top:2.3rem;padding-bottom:4rem;}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid var(--line);}
.hero {background:#111c32;border-radius:22px;padding:32px 36px;margin-bottom:22px;color:#fff;position:relative;overflow:hidden;}
.hero:after {content:"";position:absolute;width:180px;height:180px;border:35px solid #ffffff09;border-radius:38px;right:30px;top:-50px;transform:rotate(25deg);pointer-events:none;}
.eyebrow {font-size:11px;font-weight:700;letter-spacing:2px;color:#aca5ff;margin-bottom:10px;}
.hero h1 {font-size:30px;font-weight:750;margin:0;padding:0;color:#fff;letter-spacing:1px;}
.hero p {font-size:14px;color:#b7c1d4;margin:10px 0 0;}
.card-panel,.metric-stat-box {background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;margin-bottom:16px;}
.metric-title {color:var(--muted);font-size:13px;margin-bottom:10px;}
.metric-val-main {font-size:23px;font-weight:750;color:var(--ink);overflow-wrap:anywhere;}
.metric-badge,.badge-tag {display:inline-block;padding:5px 10px;border-radius:7px;font-size:12px;margin:8px 6px 0 0;background:#f1f0ff;color:#5b4de8;}
.badge-blue {background:#e9f4ff;color:#2172b8;}.badge-pink {background:#fff0f3;color:#be4565;}.badge-gold {background:#fff6df;color:#916716;}
.panel-header-title {font-weight:700;font-size:18px;margin:14px 0;color:var(--ink);}
[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;}
button[kind="primary"],button[kind="primaryFormSubmit"] {border-radius:9px;background:var(--accent);border-color:var(--accent);}
[data-testid="stLinkButton"] a {border-radius:10px;}
[data-testid="stSegmentedControl"] {margin:20px 0;}
.team-blue {border-top:3px solid #3b82f6;}.team-red {border-top:3px solid #ec6385;}
.team-member {padding:10px 0;border-bottom:1px solid #edf0f6;font-size:15px;display:flex;justify-content:space-between;gap:10px;}
.team-member span {font-size:13px;color:var(--muted);}
@media(max-width:640px) {.block-container{padding:1rem}.hero{padding:24px}.hero h1{font-size:24px}.metric-val-main{font-size:20px}}
@media(prefers-reduced-motion:reduce) {*{scroll-behavior:auto!important;transition:none!important;}}
</style>'''

def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)

def card(title, value, note=''):
    st.markdown(f'<div class="metric-stat-box"><div class="metric-title">{escape(str(title))}</div><div class="metric-val-main">{escape(str(value))}</div><div class="metric-badge">{escape(str(note))}</div></div>', unsafe_allow_html=True)

def render_team(label, players, ratings, color):
    average = sum(ratings[p] for p in players) / len(players)
    rows = ''.join(f'<div class="team-member">{escape(p)}<span>{ratings[p]:.1f} 战力</span></div>' for p in players)
    st.markdown(f'<div class="card-panel team-{color}"><div class="panel-header-title">{label}</div><div class="metric-title">{len(players)} 人 · 平均战力 {average:.1f}</div>{rows}</div>', unsafe_allow_html=True)


# ==================== hexleague/profile.py ====================
import math
from html import escape
import streamlit as st

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
            'stroke="#e2e8f0" stroke-width="1.2" stroke-dasharray="3,3"/>'
        )

    axis_lines, labels, data_pts, circles = [], [], [], []
    for i in range(total):
        ang = math.pi / 2 - 2 * math.pi * i / total
        axis_lines.append(
            f'<line x1="{cx}" y1="{cy}" '
            f'x2="{cx + r * math.cos(ang):.1f}" '
            f'y2="{cy - r * math.sin(ang):.1f}" '
            'stroke="#e2e8f0" stroke-width="1.2"/>'
        )
        labels.append(
            f'<text x="{cx + (r + 26) * math.cos(ang):.1f}" '
            f'y="{cy - (r + 14) * math.sin(ang):.1f}" '
            'font-size="11" font-weight="800" fill="#5b4de8" '
            f'text-anchor="middle" dominant-baseline="central">{categories[i]}</text>'
        )
        scale = min(max(values[i], 12.0), 100.0) / 100.0
        x = cx + r * scale * math.cos(ang)
        y = cy - r * scale * math.sin(ang)
        data_pts.append(f"{x:.1f},{y:.1f}")
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#5b4de8"/>')

    grid_svg = "".join(grid_polys)
    axes_svg = "".join(axis_lines)
    points_svg = " ".join(data_pts)
    circles_svg = "".join(circles)
    labels_svg = "".join(labels)
    return f"""
    <div style="display:flex;justify-content:center;padding:6px 0;">
        <svg style="width:100%;max-width:360px;height:auto" role="img" aria-label="选手六维战术雷达" viewBox="0 0 {size} {size}">
            {grid_svg}{axes_svg}
            <polygon points="{points_svg}" fill="rgba(91, 77, 232, 0.16)" stroke="#5b4de8" stroke-width="2.6"/>
            {circles_svg}{labels_svg}
        </svg>
    </div>
    """



def render_profile(df, radar_stats_pool, player_history):
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

        st.caption("雷达基于至少 6 人的对局；缺少真实占比时使用 KDA 推估，仅供参考。")
        ds_source = "实测" if p_r["damage_shares"] else "推估"
        ts_source = "实测" if p_r["taken_shares"] else "推估"
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
                <div style="font-size:1.45rem;font-weight:900;color:#1e293b;margin-bottom:8px;">{escape(short_name(target_p))}</div>
                <div style="font-size:0.90rem;color:#475569;line-height:2.0;">
                    <div>• <b>场均伤害占比（{ds_source}）</b>: <span style="color:#72092c;font-weight:800;">{ds:.1f}%</span></div>
                    <div>• <b>场均承伤占比（{ts_source}）</b>: <span style="color:#0284c7;font-weight:800;">{ts:.1f}%</span></div>
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



# ==================== hexleague/pages.py ====================
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
import pandas as pd
import streamlit as st


def render_ladder(data):
    df = data['df']
    st.subheader('选手天梯')
    st.caption('按历史表现寻找队友。MMR 是自定义战力评分，少量对局的胜率仅供参考。')
    if df.empty:
        st.info('还没有战绩。打开「战绩录入」上传第一张结算截图。')
        return
    c1, c2, c3 = st.columns([3, 1.5, 1.5])
    query = c1.text_input('搜索选手', placeholder='昵称或完整游戏 ID')
    minimum = c2.selectbox('最少对局', [1, 5, 10, 20])
    sort = c3.selectbox('排序依据', ['胜率', '战力', 'KDA', '场次'])
    filtered = df[df['总场次'] >= minimum]
    if query:
        filtered = filtered[filtered.index.str.contains(query.strip(), case=False, regex=False)]
    columns = {'胜率': '胜率_num', '战力': 'MMR', 'KDA': 'KDA_num', '场次': '总场次'}
    filtered = filtered.sort_values([columns[sort], '总场次', 'KDA_num'], ascending=False, kind='stable')
    st.caption(f'显示 {len(filtered)} / {len(df)} 位选手')
    if filtered.empty:
        st.info('没有符合条件的选手，可以减少场次限制或更换搜索词。')
    else:
        table = filtered[['总场次', '胜场', '负场', '胜率_num', 'MMR', 'KDA_num', '场均击杀']].reset_index(names='选手')
        table.insert(0, '排名', range(1, len(table) + 1))
        table = table.rename(columns={'总场次': '场次', '胜率_num': '胜率 %', 'KDA_num': 'KDA', 'MMR': '战力'})
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            '胜率 %': st.column_config.ProgressColumn('胜率 %', min_value=0, max_value=100, format='%.1f%%'),
            '战力': st.column_config.NumberColumn(format='%.1f'), 'KDA': st.column_config.NumberColumn(format='%.2f')})
        st.download_button('导出当前榜单', table.to_csv(index=False).encode('utf-8-sig'), 'leaderboard.csv', 'text/csv')
    with st.expander('完整累计数据'):
        st.dataframe(df.reset_index(names='选手'), hide_index=True, width="stretch")
    st.subheader('单场纪录')
    for col, key, title in zip(st.columns(3), ['max_single_kill', 'max_single_death', 'max_single_assist'], ['最高击杀', '最高阵亡', '最高助攻']):
        item = data[key]
        with col:
            card(title, short_name(item['player']), f"{item['val']} · 第 {item['game_idx']} 局")
    with st.expander('荣誉与搭档', expanded=False):
        qualified = df[df['总场次'] >= 10]
        for col, field, title in zip(st.columns(4), ['KDA_num', '击杀', '死亡', '助攻'], ['KDA 之王', '累计击杀王', '累计阵亡王', '累计助攻王']):
            with col:
                if qualified.empty:
                    card(title, '虚位以待', '至少 10 局')
                else:
                    winner = qualified[field].idxmax()
                    card(title, short_name(winner), f"{qualified.loc[winner, field]:.2f}" if field == 'KDA_num' else f"{int(qualified.loc[winner, field])}")
        synergy = [{'搭档': f'{a} & {b}', '同队场次': v['同队场次'], '胜率 %': round(v['胜场'] / v['同队场次'] * 100, 1)} for (a,b),v in data['synergy_stats'].items() if v['同队场次'] >= 5]
        if synergy:
            st.dataframe(pd.DataFrame(synergy).sort_values('胜率 %', ascending=False), hide_index=True, width="stretch")
        else:
            st.caption('搭档同队满 5 局后显示关系榜。')
        rivals = []
        for (a,b),v in data['nemesis_stats'].items():
            if v['交手场次'] >= 5:
                rivals.append({'选手 A':a,'选手 B':b,'交手场次':v['交手场次'],'A 胜':v['p1_wins'],'B 胜':v['p2_wins']})
        if rivals:
            st.dataframe(pd.DataFrame(rivals).sort_values('交手场次', ascending=False), hide_index=True, width="stretch")


def render_match(df):
    st.subheader('赛前分队')
    st.caption('选择出战名单 → 设置约束 → 生成阵容。支持无历史战绩的外援。')
    guests = st.session_state.setdefault('guests', {})
    known = sorted(df.index, key=lambda p: df.loc[p,'总场次'], reverse=True) if not df.empty else []
    with st.expander('添加 / 移除外援', expanded=not known):
        with st.form('guest_form'):
            name = st.text_input('外援游戏 ID', placeholder='建议填写 昵称#编号')
            rating = st.selectbox('外援战力', [45.,60.,80.], index=1, format_func=lambda x:f'{x:.0f} 分')
            if st.form_submit_button('添加外援'):
                name = name.strip()
                if not name or name in known or name in guests:
                    st.warning('请输入未重复的游戏 ID。')
                else:
                    guests[name] = rating
                    st.rerun()
        if guests:
            remove = st.multiselect('移除外援', list(guests))
            if st.button('移除所选外援', disabled=not remove):
                for p in remove: guests.pop(p)
                st.session_state.pop('roster', None)
                st.rerun()
    roster = known + list(guests)
    if 'roster' not in st.session_state:
        st.session_state.roster = known[:10]
    else:
        st.session_state.roster = [p for p in st.session_state.roster if p in roster]
    selected = st.multiselect('出战选手', roster, key='roster', max_selections=16)
    st.caption(f'已选 {len(selected)} 人'+(' · 奇数人数将分为人数相差 1 的两队，按平均战力平衡。' if len(selected)%2 else ''))
    rules = st.session_state.setdefault('rules', [])
    with st.expander('同队 / 对立约束'):
        if len(selected)>=2:
            a,b,c = st.columns(3)
            p1 = a.selectbox('选手 A', selected)
            p2 = b.selectbox('选手 B', [p for p in selected if p != p1])
            relation = c.selectbox('关系', ['同队','对立'])
            if st.button('添加约束'):
                rules[:] = [r for r in rules if {r['p1'],r['p2']} != {p1,p2}]
                rules.append({'p1':p1,'p2':p2,'type':'same' if relation=='同队' else 'diff'})
                st.rerun()
        for i,rule in enumerate(list(rules)):
            c,d = st.columns([5,1])
            active = rule['p1'] in selected and rule['p2'] in selected
            c.caption(f"{rule['p1']} · {'同队' if rule['type']=='same' else '对立'} · {rule['p2']}" + ('' if active else '（当前未生效）'))
            if d.button('移除',key=f'rule_{i}'):
                rules.pop(i); st.rerun()
    mode = st.radio('分队方式', ['战力平衡','大腿均分','随机抽签'], horizontal=True)
    ratings = {p:float(guests[p] if p in guests else df.loc[p,'MMR']) for p in selected}
    signature = json.dumps([selected, ratings, rules, mode], ensure_ascii=False, sort_keys=True)
    if st.session_state.get('team_signature') != signature:
        st.session_state.pop('teams', None)
    if st.button('生成分队', type='primary', disabled=len(selected)<2, width="stretch"):
        try:
            st.session_state.teams = assign_teams(selected, ratings, rules, {'战力平衡':'balanced','大腿均分':'carry','随机抽签':'random'}[mode])
            st.session_state.team_signature = signature
        except ValueError as exc:
            st.error(str(exc))
    if 'teams' in st.session_state:
        gap, blue, red = st.session_state.teams
        st.success(f'平均战力差 {gap:.1f} 分')
        b,r = st.columns(2)
        with b: render_team('蓝色方', blue, ratings, 'blue')
        with r: render_team('红色方', red, ratings, 'red')
        text = '蓝色方：'+'、'.join(blue)+'\n红色方：'+'、'.join(red)+f'\n平均战力差：{gap:.1f}'
        st.download_button('下载分队名单',text,'teams.txt','text/plain')


def render_upload(records, api_key):
    st.subheader('战绩录入')
    st.caption('上传截图 → 自动识别 → 核对选手与胜方 → 确认保存。识别期间请保持页面打开。')
    files = st.file_uploader('完整结算截图',type=['png','jpg','jpeg'],accept_multiple_files=True)
    if st.button('识别截图',type='primary',disabled=not files):
        if not api_key:
            st.warning('请在侧栏「识别设置」填写 API Key。')
            return
        try:
            settings = get_vision_settings()
        except ValueError as exc:
            st.error(str(exc)); return
        pending = st.session_state.setdefault('pending', {})
        seen = {r.get('md5') for r in records} | set(pending)
        jobs = []
        skipped = 0
        for f in files:
            raw = f.getvalue(); digest = get_md5(raw)
            if digest in seen: skipped += 1; continue
            seen.add(digest); jobs.append((f.name,raw,digest))
        progress = st.progress(0, text='正在识别…')
        errors = []
        if jobs:
            with ThreadPoolExecutor(max_workers=min(len(jobs),st.session_state.get('vision_workers',3))) as executor:
                futures = {executor.submit(recognize_upload_job,raw,digest,api_key,settings):(name,digest,i) for i,(name,raw,digest) in enumerate(jobs)}
                results = []
                for count,future in enumerate(as_completed(futures),1):
                    name,digest,index = futures[future]
                    result,error,elapsed = future.result()
                    if error: errors.append(f'{name}：{error}')
                    else: results.append((index,digest,{'name':name,'record':result}))
                    progress.progress(count/len(jobs),text=f'已识别 {count}/{len(jobs)} 张')
                for _,digest,item in sorted(results): pending[digest] = item
        progress.empty()
        st.session_state.upload_report = (f'待核对 {len(pending)} 张 · 跳过重复 {skipped} 张 · 失败 {len(errors)} 张',errors)
    if report := st.session_state.get('upload_report'):
        st.info(report[0])
        for error in report[1]: st.error(error)
    pending = st.session_state.setdefault('pending', {})
    for digest,item in list(pending.items()):
        with st.expander(f"核对 · {item['name']}", expanded=True):
            record = item['record']
            if record.get('image_thumb'):
                st.image('data:image/jpeg;base64,'+record['image_thumb'],width=520)
            with st.form('review_'+digest):
                winner = st.radio('获胜阵营',['BLUE','RED'],index=0 if record['winning_team']=='BLUE' else 1,format_func=lambda x:'蓝色方' if x=='BLUE' else '红色方', horizontal=True)
                table = pd.DataFrame(record['players']).drop(columns=['is_winner'], errors='ignore')
                edited = st.data_editor(table,num_rows='dynamic',hide_index=True,width="stretch",key='editor_'+digest,column_config={
                    'team':st.column_config.SelectboxColumn('阵营',options=['BLUE','RED'],required=True),
                    'player_name':st.column_config.TextColumn('游戏 ID',required=True),
                    **{k:st.column_config.NumberColumn(label,min_value=0,step=1,required=True) for k,label in [('kills','击杀'),('deaths','死亡'),('assists','助攻')]},
                    'damage_share':st.column_config.NumberColumn('伤害 %',min_value=0,max_value=100),
                    'taken_share':st.column_config.NumberColumn('承伤 %',min_value=0,max_value=100)})
                confirm = st.checkbox('已核对选手 ID、阵营、胜方和 KDA',key='confirm_'+digest)
                submitted = st.form_submit_button('确认保存', type='primary')
            if submitted:
                if not confirm:
                    st.warning('请先核对并勾选确认。')
                else:
                    try:
                        players = json.loads(edited.to_json(orient='records',force_ascii=False))
                        candidate = validate_recognition({**record,'players':players,'winning_team':winner})
                        # Read newest local file before commit, avoiding a stale page snapshot.
                        current = load_records()
                        if digest not in {r.get('md5') for r in current}:
                            result = save_records(current+[candidate])
                            st.session_state.save_result = result
                        pending.pop(digest)
                        st.rerun()
                    except (ValueError,TypeError,OSError) as exc:
                        st.error(f'尚未保存：{exc}')
            if st.button('放弃此张',key='discard_'+digest):
                pending.pop(digest); st.rerun()


# ==================== app.py ====================
import base64
import json
import streamlit as st

st.set_page_config(page_title='海克斯内战 · 战绩中心', page_icon='⚔️', layout='wide')
apply_theme()
records = load_records()
cfg = load_config()

with st.sidebar:
    st.markdown('### ⚔️ 海克斯内战')
    st.caption('HEX LEAGUE · 战绩中心')
    token,repo = get_github_auth()
    st.caption('GitHub 同步已配置' if token and repo else '本地存储 · 建议定期导出备份')
    if error := st.session_state.get('sync_error'):
        st.warning(error)
    with st.expander('识别设置'):
        api_key = st.text_input('DashScope API Key',value=get_secret('DASHSCOPE_API_KEY'),type='password')
        st.text_input('视觉模型 ID',value=get_secret('DASHSCOPE_MODEL','qwen3-vl-plus'),key='vision_model')
        st.text_input('Base URL',value=get_secret('DASHSCOPE_BASE_URL','https://dashscope.aliyuncs.com/compatible-mode/v1'),key='vision_base_url')
        st.slider('同时识别张数',1,3,3,key='vision_workers')
        st.checkbox('压缩识别大图',value=True,key='optimize_image',help='昵称较小时可关闭后重试。')
    with st.expander('数据备份与恢复'):
        st.download_button('导出完整备份',json.dumps(records,ensure_ascii=False,indent=2).encode(),'records_backup.json','application/json',width="stretch")
        backup = st.file_uploader('导入 JSON 备份',type=['json'])
        if backup is not None:
            try:
                restored = validate_backup(json.loads(backup.getvalue()))
                st.caption(f'有效备份：{len(restored)} 场；恢复将替换当前 {len(records)} 场。')
                agree = st.checkbox('确认用此备份替换当前战绩')
                if st.button('恢复备份',disabled=not agree):
                    st.session_state.save_result = save_records(restored)
                    st.rerun()
            except (ValueError,TypeError) as exc:
                st.error(f'无效备份：{exc}')
    with st.expander('语音房配置'):
        with st.form('voice'):
            main = st.text_input('大厅语音',value=cfg['main_voice'])
            blue = st.text_input('蓝方语音',value=cfg['blue_voice'])
            red = st.text_input('红方语音',value=cfg['red_voice'])
            if st.form_submit_button('保存链接'):
                try:
                    save_config(dict(main_voice=main,blue_voice=blue,red_voice=red)); st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with st.expander('历史截图重新识别'):
        st.caption('用于补齐伤害 / 承伤占比；旧缩略图可能丢失细节，会调用模型并产生费用。')
        agree = st.checkbox('确认重新扫描全部历史缩略图')
        if st.button('开始重新扫描',disabled=not records or not agree or not api_key):
            progress = st.progress(0)
            count = 0
            for i,record in enumerate(records):
                if record.get('image_thumb'):
                    try:
                        result = analyze_image(base64.b64decode(record['image_thumb']),api_key)
                        mapping = {p['player_name']:p for p in result['players']}
                        for player in record['players']:
                            if new := mapping.get(clean_player_name_strict(player['player_name'])):
                                for field in ['damage_share','taken_share']:
                                    if new.get(field) is not None: player[field] = new[field]
                        count += 1
                    except Exception as exc:
                        st.error(f'第 {i+1} 局识别失败：{exc}')
                progress.progress((i+1)/len(records))
            if count:
                st.session_state.save_result = save_records(records)
                st.rerun()

@st.cache_data(show_spinner=False)
def cached_stats(data):
    return calculate_stats(data)

stats = cached_stats([{'players': r['players'], 'winning_team': r['winning_team']} for r in records])
st.markdown('<div class="hero"><div class="eyebrow">HEX LEAGUE / MATCH CENTER</div><h1>每一场内战，都有战绩。</h1><p>查看选手表现，组织均衡对局，记录属于你们的高光时刻。</p></div>',unsafe_allow_html=True)
c1,c2,c3,c4 = st.columns(4)
c1.metric('累计对局',len(records))
c2.metric('参战选手',len(stats['df']))
c3.metric('待核对截图',len(st.session_state.get('pending',{})))
c4.metric('数据存储','GitHub + 本地' if token and repo else '本地')
a,b,c = st.columns(3)
a.link_button('大厅语音 ↗',cfg['main_voice'],width="stretch")
b.link_button('蓝方语音 ↗',cfg['blue_voice'],width="stretch")
c.link_button('红方语音 ↗',cfg['red_voice'],width="stretch")
if 'save_result' in st.session_state:
    show_save_status(st.session_state.pop('save_result'))
page = st.segmented_control('功能导航',['选手天梯','赛前分队','选手档案','战绩录入','历史对局'],default='选手天梯',key='page',label_visibility='collapsed')
if page == '选手天梯': render_ladder(stats)
elif page == '赛前分队': render_match(stats['df'])
elif page == '选手档案': render_profile(stats['df'],stats['radar_stats_pool'],stats['player_history'])
elif page == '战绩录入': render_upload(records,api_key)
elif page == '历史对局':
    st.subheader('历史对局')
    if not records:
        st.info('还没有对局记录。')
    else:
        index = st.selectbox('选择对局',list(reversed(range(len(records)))),format_func=lambda i:f"第 {i+1} 局 · {'蓝方' if records[i]['winning_team']=='BLUE' else '红方'}获胜")
        record = records[index]
        if record.get('image_thumb'):
            with st.expander('结算截图'):
                st.image('data:image/jpeg;base64,'+record['image_thumb'],width="stretch")
        st.dataframe(record['players'],hide_index=True,width="stretch")
        with st.expander('删除此局'):
            confirm = st.checkbox('确认删除此局，统计将立即更新',key=f'delete_confirm_{index}')
            if st.button('删除',disabled=not confirm):
                records.pop(index)
                st.session_state.save_result = save_records(records)
                st.rerun()
