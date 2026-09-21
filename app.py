import base64
from collections import defaultdict
import hashlib
import io
import itertools
import json
import os
import re
import time
import zipfile
from openai import OpenAI
import pandas as pd
from PIL import Image, ImageEnhance
import streamlit as st

DATA_FILE = "records.json"
IMAGE_DIR = "saved_images"

os.makedirs(IMAGE_DIR, exist_ok=True)

st.set_page_config(
    page_title="LOL 内战战绩与整活看板",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- 核心：常用英雄参考列表与名字纠错 ----------------
COMMON_CHAMPIONS = [
    "亚索", "永恩", "李青", "卡莎", "阿狸", "锤石", "泰坦", "派克", "伊泽瑞尔", "拉克丝",
    "薇恩", "瑟提", "维克托", "赛娜", "金克丝", "格温", "佛耶戈", "劫", "塞拉斯", "阿卡丽",
    "菲兹", "崔斯特", "德莱文", "蕾欧娜", "莫甘娜", "嘉文四世", "赵信", "雷克顿", "墨菲特", "诺克萨斯之手"
]

NAME_FIX_MAP = {
    "千秋种我一粟卿": "千秋种我一栗卿",
}

def clean_player_name(raw_name: str) -> str:
    name = raw_name.strip()
    name = name.replace("一粟卿", "一栗卿")
    for wrong, right in NAME_FIX_MAP.items():
        if wrong in name:
            name = name.replace(wrong, right)
    return name

def calculate_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

# ---------------- 1. 数据持久化函数 ----------------
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

def overwrite_all_records(records_list):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records_list, f, ensure_ascii=False, indent=2)

def delete_record_by_index(target_index: int):
    records = load_all_records()
    if 0 <= target_index < len(records):
        removed = records.pop(target_index)
        img_filename = removed.get("image_file")
        if img_filename:
            img_path = os.path.join(IMAGE_DIR, img_filename)
            if os.path.exists(img_path):
                os.remove(img_path)
        overwrite_all_records(records)
        return True
    return False

def reset_all_records():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            file_path = os.path.join(IMAGE_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

# ---------------- 2. 识别核心：图像增强 + 装备反推 Prompt ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

    # 图像适度提升对比度与轮廓
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)
        enhancer_sharp = ImageEnhance.Sharpness(img)
        img = enhancer_sharp.enhance(1.2)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        processed_bytes = buffer.getvalue()
    except Exception:
        processed_bytes = image_bytes

    b64_img = base64.b64encode(processed_bytes).decode("utf-8")

    prompt = """这是一张英雄联盟结算战绩截图。
请提取整局胜负（蓝方/红方）以及全部 10 位玩家的完整数据。

【关键：结合出装与定位精准推断英雄】
英雄头像往往带有特殊皮肤与炫彩，切勿仅凭金黄、蓝色或发色草率推测！
请结合该玩家右侧的【出装道具】与【KDA/位置】辅助判定：
1. 出了暴击攻速装（如无尽、电刀、盾弓）的通常是射手或亚索/永恩；
2. 出了高法强装（如帽子、法穿杖）的为传统法师；
3. 出了辅助装/纯肉装（如鸟盾、日炎）的为辅助或坦克。
4. 全局 10 位玩家英雄必须互斥，不要输出两边重复英雄。
5. 请输出标准英雄中文通用名称（例如：亚索、卡莎、李青、锤石、阿狸、维克托等）。

【输出格式】严格输出合法的纯 JSON 对象：
{
  "winning_team": "BLUE" 或 "RED",
  "players": [
    {
      "player_name": "玩家游戏ID",
      "champion": "所选英雄名称",
      "team": "BLUE" 或 "RED",
      "kills": 0,
      "deaths": 0,
      "assists": 0,
      "is_winner": true 或 false
    }
  ]
}
"""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-flash",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                        },
                    ],
                }],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content.strip()
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            return json.loads(content)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            raise e

# ---------------- 3. 侧边栏与管理员纠错控制台 ----------------
with st.sidebar:
    st.title("🎮 控制台")
    default_key = st.secrets.get("DEEPSEEK_API_KEY", "") if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets else ""
    api_key = st.text_input("DeepSeek API Key", value=default_key, type="password", help="sk- 开头的密钥")

    st.markdown("---")
    current_records = load_all_records()
    st.metric("总计已战", f"{len(current_records)} 局")

    if current_records:
        json_data = json.dumps(current_records, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 导出战绩备份 (JSON)",
            data=json_data,
            file_name="lol_match_backup.json",
            mime="application/json",
            help="定期备份，防止云端重启",
        )

    with st.expander("📥 导入战绩备份"):
        backup_file = st.file_uploader("选择 JSON 备份文件", type=["json"])
        if backup_file is not None:
            try:
                imported_data = json.load(backup_file)
                if isinstance(imported_data, list):
                    if st.button("⚡ 确认导入覆写", type="primary"):
                        overwrite_all_records(imported_data)
                        st.success("恢复成功！")
                        time.sleep(1)
                        st.rerun()
            except Exception as err:
                st.error(f"读取失败: {err}")

    st.markdown("---")
    with st.expander("🔒 管理员控制台（数据纠错/管理）"):
        admin_pwd = st.text_input("管理员密码", type="password", key="admin_pwd_input")
        if admin_pwd == "666888":
            if current_records:
                # 模块 1：对局英雄手动快速纠错
                st.markdown("##### ✏️ 英雄识别手动修正")
                corr_options = {i: f"第 {i + 1} 局" for i in range(len(current_records))}
                sel_corr_idx = st.selectbox(
                    "选择要修正的对局",
                    options=list(reversed(list(corr_options.keys()))),
                    format_func=lambda x: corr_options[x],
                    key="select_corr_game"
                )
                
                target_rec = current_records[sel_corr_idx]
                p_names = [clean_player_name(p.get("player_name", f"选手{k}")) for k, p in enumerate(target_rec.get("players", []))]
                sel_p_idx = st.selectbox("选择选手", options=list(range(len(p_names))), format_func=lambda x: p_names[x])
                
                curr_champ = target_rec.get("players", [])[sel_p_idx].get("champion", "")
                st.caption(f"当前识别为：**{curr_champ}**")
                
                new_champ = st.text_input("输入修正后的英雄名称", value=curr_champ)
                if st.button("💾 保存该选手英雄修正"):
                    current_records[sel_corr_idx]["players"][sel_p_idx]["champion"] = new_champ.strip()
                    overwrite_all_records(current_records)
                    st.toast(f"已将 {p_names[sel_p_idx]} 的英雄更新为 {new_champ}！", icon="✅")
                    time.sleep(0.8)
                    st.rerun()

                st.divider()

                # 模块 2：删除与撤回
                if st.button("⏪ 撤回最近的一局"):
                    delete_record_by_index(len(current_records) - 1)
                    st.toast("已撤回最新对局！", icon="🗑️")
                    time.sleep(0.8)
                    st.rerun()

                sel_del_idx = st.selectbox(
                    "选择要删除的对局",
                    options=list(reversed(list(corr_options.keys()))),
                    format_func=lambda x: corr_options[x],
                    key="select_del_game"
                )
                if st.button("❌ 确认删除该局"):
                    delete_record_by_index(sel_del_idx)
                    st.toast("已删除该局！", icon="🗑️")
                    time.sleep(0.8)
                    st.rerun()

            if st.button("💣 清空所有历史数据", type="primary"):
                reset_all_records()
                st.rerun()
        elif admin_pwd:
            st.error("密码错误")

# ---------------- 4. 上传模块 ----------------
st.header("⚔️ 英雄联盟内战战绩中心")

uploaded_files = st.file_uploader(
    "📤 上传结算截图（支持多张图片拖入，或直接上传 .zip 文件夹）",
    type=["png", "jpg", "jpeg", "zip"],
    accept_multiple_files=True,
)

if uploaded_files:
    if not api_key:
        st.warning("请先在左侧侧边栏填入 DeepSeek API Key！")
    else:
        if st.button("🚀 开始解析录入", type="primary"):
            images_to_process = []
            for file in uploaded_files:
                file_bytes = file.read()
                if file.name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                            for zip_info in z.infolist():
                                if not zip_info.is_dir() and zip_info.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    img_data = z.read(zip_info.filename)
                                    if "__MACOSX" not in zip_info.filename:
                                        images_to_process.append((os.path.basename(zip_info.filename), img_data))
                    except Exception as e:
                        st.error(f"❌ 读取压缩包 {file.name} 失败: {e}")
                else:
                    images_to_process.append((file.name, file_bytes))

            success_count = 0
            skip_count = 0
            existing_records = load_all_records()
            existing_hashes = {r.get("image_hash") for r in existing_records if "image_hash" in r}
            pbar = st.progress(0)
            total = len(images_to_process)

            for idx, (img_name, img_bytes) in enumerate(images_to_process):
                img_hash = calculate_md5(img_bytes)

                if img_hash in existing_hashes:
                    st.warning(f"⚠️ {img_name} 此前已录入，自动跳过！")
                    skip_count += 1
                    pbar.progress((idx + 1) / total)
                    continue

                with st.spinner(f"正在识别 ({idx + 1}/{total}): {img_name}..."):
                    try:
                        result = analyze_screenshot(img_bytes, api_key)
                        saved_file_name = f"{int(time.time())}_{img_hash[:8]}.jpg"
                        with open(os.path.join(IMAGE_DIR, saved_file_name), "wb") as f:
                            f.write(img_bytes)

                        result["image_hash"] = img_hash
                        result["image_file"] = saved_file_name
                        result["uploaded_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

                        save_record(result)
                        existing_hashes.add(img_hash)
                        success_count += 1
                        time.sleep(0.5)
                    except Exception as e:
                        st.error(f"❌ {img_name} 识别失败: {e}")
                pbar.progress((idx + 1) / total)

            if success_count > 0:
                st.success(f"🎉 成功录入 {success_count} 局战绩！(跳过重复 {skip_count} 张)")
                time.sleep(1)
                st.rerun()

# ---------------- 5. 核心功能呈现 ----------------
records = load_all_records()

if not records:
    st.info("💡 暂无历史对局数据，请在上方上传截图开始统计！")
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 胜率风云榜",
        "⚔️ 每局对决卡片（查英雄/尽力局长）",
        "🤝 羁绊与宿命死敌",
        "👤 选手黑历史档案",
        "📸 赛后长图战报",
    ])

    # ----- Tab 1: 胜率风云榜 -----
    with tab1:
        player_stats = defaultdict(lambda: {"总场次": 0, "胜场": 0, "负场": 0, "总击杀": 0, "总死亡": 0, "总助攻": 0})
        for r in records:
            for p in r.get("players", []):
                name = clean_player_name(p.get("player_name", ""))
                if not name:
                    continue
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
        df["KDA"] = ((df["总击杀"] + df["总助攻"]) / df["总死亡"].replace(0, 1)).round(2)

        df["win_rate_num"] = df["胜场"] / df["总场次"]
        df = df.sort_values(by=["win_rate_num", "总场次", "KDA"], ascending=[False, False, False])
        df = df.drop(columns=["win_rate_num"])
        st.dataframe(df, use_container_width=True)

    # ----- Tab 2: 每局对决卡片 -----
    with tab2:
        for i, r in enumerate(reversed(records)):
            idx = len(records) - i
            win_team = r.get("winning_team")
            players = r.get("players", [])

            blue_players = [p for p in players if p.get("team") == "BLUE"]
            red_players = [p for p in players if p.get("team") == "RED"]

            loser_players = red_players if win_team == "BLUE" else (blue_players if win_team == "RED" else [])
            winner_players = blue_players if win_team == "BLUE" else (red_players if win_team == "RED" else [])

            juzhang = max(loser_players, key=lambda x: (x.get("kills", 0) + x.get("assists", 0)) / max(x.get("deaths", 1), 1)) if loser_players else None
            wodi = max(players, key=lambda x: x.get("deaths", 0)) if players else None
            datui = max(winner_players, key=lambda x: x.get("kills", 0)) if winner_players else None

            with st.container():
                win_label = "🟦 蓝方胜" if win_team == "BLUE" else ("🟥 红方胜" if win_team == "RED" else "⚪ 赛果未知")
                st.markdown(f"### 第 {idx} 局对决 【{win_label}】 <small style='color: gray; font-size: 0.85em;'>时间: {r.get('uploaded_time', '历史记录')}</small>", unsafe_allow_html=True)

                honor_tags = []
                if datui:
                    honor_tags.append(f"✨ **胜方大腿**: {clean_player_name(datui.get('player_name', ''))}（操刀 {datui.get('champion')} / 斩获 {datui.get('kills')} 杀）")
                if juzhang:
                    kda_val = round((juzhang.get('kills', 0) + juzhang.get('assists', 0)) / max(juzhang.get('deaths', 1), 1), 2)
                    honor_tags.append(f"👑 **尽力局局长**: {clean_player_name(juzhang.get('player_name', ''))}（操刀 {juzhang.get('champion')}，KDA {kda_val} 独木难支）")
                if wodi and wodi.get("deaths", 0) >= 5:
                    honor_tags.append(f"🥔 **白给王/疑似卧底**: {clean_player_name(wodi.get('player_name', ''))}（操刀 {wodi.get('champion')} / 阵亡 {wodi.get('deaths')} 次）")

                if honor_tags:
                    st.info(" ｜ ".join(honor_tags))

                col_b, col_r = st.columns(2)

                def make_team_df(t_players):
                    data = []
                    for p in t_players:
                        p_name = clean_player_name(p.get("player_name", ""))
                        champ = p.get("champion", "未知")
                        kda = f"{p.get('kills', 0)} / {p.get('deaths', 0)} / {p.get('assists', 0)}"

                        tag = "普通"
                        if datui and p_name == clean_player_name(datui.get("player_name", "")):
                            tag = "✨ 大腿"
                        elif juzhang and p_name == clean_player_name(juzhang.get("player_name", "")):
                            tag = "👑 尽力局长"
                        elif wodi and p_name == clean_player_name(wodi.get("player_name", "")):
                            tag = "🥔 白给王"

                        data.append({"玩家": p_name, "英雄": champ, "K / D / A": kda, "本局评定": tag})
                    return pd.DataFrame(data)

                with col_b:
                    st.markdown(f"**🟦 蓝方阵营 {'👑 [胜利]' if win_team == 'BLUE' else '[失败]'}**")
                    st.dataframe(make_team_df(blue_players), hide_index=True)

                with col_r:
                    st.markdown(f"**🟥 红方阵营 {'👑 [胜利]' if win_team == 'RED' else '[失败]'}**")
                    st.dataframe(make_team_df(red_players), hide_index=True)

                img_f = r.get("image_file")
                if img_f and os.path.exists(os.path.join(IMAGE_DIR, img_f)):
                    with st.expander("🔍 查看本局原始结算图"):
                        st.image(os.path.join(IMAGE_DIR, img_f), width=450, caption=f"第 {idx} 局原图")

                st.markdown("---")

    # ----- Tab 3: 羁绊与宿命死敌 -----
    with tab3:
        st.subheader("🔗 组合羁绊（搭档与表面兄弟）")
        duo_stats = defaultdict(lambda: {"total": 0, "wins": 0})
        rival_stats = defaultdict(lambda: {"total": 0, "p1_wins": 0})

        for r in records:
            players = r.get("players", [])
            blue_p = [clean_player_name(p.get("player_name", "")) for p in players if p.get("team") == "BLUE" and clean_player_name(p.get("player_name", ""))]
            red_p = [clean_player_name(p.get("player_name", "")) for p in players if p.get("team") == "RED" and clean_player_name(p.get("player_name", ""))]
            win_t = r.get("winning_team")

            for team, win_condition in [(blue_p, "BLUE"), (red_p, "RED")]:
                for p1, p2 in itertools.combinations(sorted(team), 2):
                    duo_stats[(p1, p2)]["total"] += 1
                    if win_t == win_condition:
                        duo_stats[(p1, p2)]["wins"] += 1

            for p1 in blue_p:
                for p2 in red_p:
                    pair = (p1, p2) if p1 < p2 else (p2, p1)
                    rival_stats[pair]["total"] += 1
                    if (p1 < p2 and win_t == "BLUE") or (p1 > p2 and win_t == "RED"):
                        rival_stats[pair]["p1_wins"] += 1

        duo_list = []
        for (p1, p2), s in duo_stats.items():
            if s["total"] >= 2:
                wr = round((s["wins"] / s["total"]) * 100, 1)
                duo_list.append({
                    "组合": f"{p1} & {p2}",
                    "同队场次": s["total"],
                    "合体胜场": s["wins"],
                    "同队胜率": f"{wr}%",
                    "wr_val": wr
                })

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("#### 🌟 黄金搭档（胜率最高）")
            if duo_list:
                duo_df_top = pd.DataFrame(duo_list).sort_values(by=["wr_val", "同队场次"], ascending=[False, False])
                st.dataframe(duo_df_top.drop(columns=["wr_val"]).head(5), hide_index=True)
            else:
                st.caption("暂无足够数据（需至少同队 2 局）...")

        with col_d2:
            st.markdown("#### 💔 表面兄弟（翻车二人组）")
            if duo_list:
                duo_df_bot = pd.DataFrame(duo_list).sort_values(by=["wr_val", "同队场次"], ascending=[True, False])
                st.dataframe(duo_df_bot.drop(columns=["wr_val"]).head(5), hide_index=True)
            else:
                st.caption("暂无足够数据...")

        st.markdown("---")
        st.subheader("⚔️ 一生之敌（对位克制）")
        rival_list = []
        for (p1, p2), s in rival_stats.items():
            if s["total"] >= 2:
                p1_rate = round((s["p1_wins"] / s["total"]) * 100, 1)
                rival_list.append({
                    "宿敌对位": f"{p1} vs {p2}",
                    "交手场次": s["total"],
                    "胜负对局": f"{p1} 赢 {s['p1_wins']} 局 / {p2} 赢 {s['total'] - s['p1_wins']} 局",
                    "克制率": f"{p1} 胜率 {p1_rate}%",
                })
        if rival_list:
            st.dataframe(pd.DataFrame(rival_list), hide_index=True)
        else:
            st.caption("双方交手 2 局以上解锁...")

    # ----- Tab 4: 选手档案 -----
    with tab4:
        all_players_list = sorted(list(df.index))
        target_player = st.selectbox("🔍 选择要查成分的好友:", options=all_players_list)

        if target_player:
            champs_used = defaultdict(lambda: {"total": 0, "wins": 0})
            p_records = []

            for r in records:
                for p in r.get("players", []):
                    if clean_player_name(p.get("player_name", "")) == target_player:
                        c = p.get("champion", "未知英雄")
                        champs_used[c]["total"] += 1
                        if p.get("is_winner"):
                            champs_used[c]["wins"] += 1
                        p_records.append(p)

            c_metric1, c_metric2, c_metric3 = st.columns(3)
            with c_metric1:
                st.metric("个人总场次", f"{len(p_records)} 局", delta=df.loc[target_player, "胜率"])
            with c_metric2:
                max_kill = max([p.get("kills", 0) for p in p_records], default=0)
                st.metric("单局最高击杀", f"{max_kill} 杀")
            with c_metric3:
                max_death = max([p.get("deaths", 0) for p in p_records], default=0)
                st.metric("单局最高阵亡", f"{max_death} 阵亡")

            st.markdown(f"#### 🎭 **{target_player}** 的招牌英雄池")
            champ_list = []
            for c_name, c_stat in champs_used.items():
                c_wr = round((c_stat["wins"] / c_stat["total"]) * 100, 1)
                champ_list.append({
                    "操刀英雄": c_name,
                    "出场次数": c_stat["total"],
                    "获胜场次": c_stat["wins"],
                    "英雄胜率": f"{c_wr}%",
                    "wr_val": c_wr
                })
            champ_df = pd.DataFrame(champ_list).sort_values(by=["出场次数", "wr_val"], ascending=[False, False])
            st.dataframe(champ_df.drop(columns=["wr_val"]), hide_index=True)

    # ----- Tab 5: 微信群长图战报 -----
    with tab5:
        st.subheader("📸 微信群一键发图战报")
        st.caption("长按或右键截取下方信息卡片，直接丢进群里开撕！")

        total_kills = sum(df["总击杀"])
        most_kill_p = df.sort_values(by="总击杀", ascending=False).index[0]
        most_death_p = df.sort_values(by="总死亡", ascending=False).index[0]
        best_wr_p = df[df["总场次"] >= 2].sort_values(by="KDA", ascending=False).index
        king_p = best_wr_p[0] if len(best_wr_p) > 0 else df.index[0]

        st.markdown(f"""
        > ### 🎮 **LOL 内战群封神榜战报**
        > * **🏆 综合战力王 (MVP)**: **【{king_p}】**（KDA: {df.loc[king_p, 'KDA']}）
        > * **🩸 人头收割机**: **【{most_kill_p}】**（累计击杀 {df.loc[most_kill_p, '总击杀']} 命）
        > * **🥔 峡谷慈善家**: **【{most_death_p}】**（累计送出 {df.loc[most_death_p, '总死亡']} 命）
        > * **🔥 峡谷累计产生人头**: {total_kills} 个，累计交战 {len(records)} 局。
        """)
