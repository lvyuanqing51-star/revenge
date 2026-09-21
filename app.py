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

# ---------------- 核心：玩家名字纠错映射 ----------------
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


# ---------------- 1. 数据持久化与维护 ----------------
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


# ---------------- 2. DeepSeek 视觉解析（带清晰度增强与防皮肤混淆） ----------------
def analyze_screenshot(image_bytes, key, max_retries=3):
  client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

  # 图像轻度增强：提升对比度和边缘锐度，让头像特征更分明
  try:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
      img = img.convert("RGB")
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

  prompt = """这是一张《英雄联盟》(League of Legends) 的对局结算界面截图。
请精准提取整局胜负结果（蓝方/红方）以及全部 10 位玩家的对局战绩。

【英雄识别关键指导原则（极其重要，避免皮肤混淆）】：
1. 英雄圆形头像常带有皮肤或炫彩，切勿仅凭金黄、深蓝、白发、暗黑等主色调粗暴猜测！
2. 请仔细比对英雄的面部五官、标志性发型、特征饰品或武器构图：
   - 严加区分易混淆英雄：如亚索与永恩、卡莎与阿狸/伊芙琳、锤石与派克/泰坦、伊泽瑞尔与拉克丝等。
3. 英雄互斥约束：正常对局中，全局 10 位玩家所使用的英雄各不相同，若识别出重复英雄，请务必核实修正。
4. 英雄名称请输出标准规范的中文常用名（如：亚索、卡莎、李青、锤石、阿狸、瑟提、维克托等）。

【信息精度要求】：
1. 玩家昵称请准确提取，特别区分'栗'与'粟'等形近字。
2. 击杀/死亡/助攻 (K/D/A) 必须精准对应。

严格输出合法的纯 JSON 对象，格式如下：
{
  "winning_team": "BLUE" 或 "RED",
  "players": [
    {
      "player_name": "玩家游戏ID",
      "champion": "所选英雄规范名称",
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
                      "image_url": {
                          "url": f"data:image/jpeg;base64,{b64_img}"
                      },
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


# ---------------- 3. 侧边栏与管理功能 ----------------
with st.sidebar:
  st.title("🎮 控制台")
  default_key = (
      st.secrets.get("DEEPSEEK_API_KEY", "")
      if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets
      else ""
  )
  api_key = st.text_input(
      "DeepSeek API Key",
      value=default_key,
      type="password",
      help="sk- 开头的密钥",
  )

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
        help="定期下载备份，防止 Streamlit 休眠清空数据",
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
  with st.expander("🔒 管理员控制台"):
    admin_pwd = st.text_input("管理员密码", type="password")
    if admin_pwd == "666888":
      if current_records:
        if st.button("⏪ 撤回最近的一局"):
          delete_record_by_index(len(current_records) - 1)
          st.toast("已撤回最新对局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

        st.markdown("##### 精准删除指定局")
        options = {}
        for i, r in enumerate(current_records):
          win_team = "蓝方胜" if r.get("winning_team") == "BLUE" else "红方胜"
          time_str = r.get("uploaded_time", "")
          options[i] = f"第 {i + 1} 局 ({win_team}) - {time_str}"

        sel_idx = st.selectbox(
            "选择对局",
            options=list(reversed(list(options.keys()))),
            format_func=lambda x: options[x],
        )
        if st.button("❌ 确认删除选中局"):
          delete_record_by_index(sel_idx)
          st.toast("已删除该局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

      if st.button("💣 清空所有历史数据", type="primary"):
        reset_all_records()
        st.rerun()
    elif admin_pwd:
      st.error("密码错误")

# ---------------- 4. 上传与解析模块（支持直接传 ZIP 文件夹） ----------------
st.header("⚔️ 英雄联盟内战战绩中心")

uploaded_files = st.file_uploader(
    "📤 上传结算截图（支持多张图片全选拖入，或直接把整个图片文件夹打包为 .zip 上传）",
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
                if not zip_info.is_dir() and zip_info.filename.lower().endswith(
                    (".png", ".jpg", ".jpeg")
                ):
                  img_data = z.read(zip_info.filename)
                  if "__MACOSX" not in zip_info.filename:
                    images_to_process.append(
                        (os.path.basename(zip_info.filename), img_data)
                    )
          except Exception as e:
            st.error(f"❌ 读取压缩包 {file.name} 失败: {e}")
        else:
          images_to_process.append((file.name, file_bytes))

      success_count = 0
      skip_count = 0
      existing_records = load_all_records()
      existing_hashes = {
          r.get("image_hash") for r in existing_records if "image_hash" in r
      }
      pbar = st.progress(0)
      total = len(images_to_process)

      for idx, (img_name, img_bytes) in enumerate(images_to_process):
        img_hash = calculate_md5(img_bytes)

        if img_hash in existing_hashes:
          st.warning(f"⚠️ {img_name} 此前已录入，自动跳过！")
          skip_count += 1
          pbar.progress((idx + 1) / total)
          continue

        with st.spinner(f"正在精准解析 ({idx + 1}/{total}): {img_name}..."):
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
      elif skip_count > 0:
        st.info("所有图片此前均已录入，未增加任何重复数据。")

# ---------------- 5. 核心数据呈现 ----------------
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
    player_stats = defaultdict(
        lambda: {
            "总场次": 0,
            "胜场": 0,
            "负场": 0,
            "总击杀": 0,
            "总死亡": 0,
            "总助攻": 0,
        }
    )
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
    df["KDA"] = (
        (df["总击杀"] + df["总助攻"]) / df["总死亡"].replace(0, 1)
    ).round(2)

    df["win_rate_num"] = df["胜场"] / df["总场次"]
    df = df.sort_values(
        by=["win_rate_num", "总场次", "KDA"], ascending=[False, False, False]
    )
    df = df.drop(columns=["win_rate_num"])
    st.dataframe(df, use_container_width=True)

  # ----- Tab 2: 每局对决卡片（查英雄、局长、卧底） -----
  with tab2:
    st.caption("💡 汇总每局双方所选英雄与对决战况，自动评定大腿、尽力局长与卧底！")

    for i, r in enumerate(reversed(records)):
      idx = len(records) - i
      win_team = r.get("winning_team")
      players = r.get("players", [])

      blue_players = [p for p in players if p.get("team") == "BLUE"]
      red_players = [p for p in players if p.get("team") == "RED"]

      loser_players = (
          red_players
          if win_team == "BLUE"
          else blue_players
          if win_team == "RED"
          else []
      )
      winner_players = (
          blue_players
          if win_team == "BLUE"
          else red_players
          if win_team == "RED"
          else []
      )

      juzhang = None
      if loser_players:
        juzhang = max(
            loser_players,
            key=lambda x: (x.get("kills", 0) + x.get("assists", 0))
            / max(x.get("deaths", 1), 1),
        )

      wodi = max(players, key=lambda x: x.get("deaths", 0)) if players else None

      datui = (
          max(winner_players, key=lambda x: x.get("kills", 0))
          if winner_players
          else None
      )

      with st.container():
        win_label = (
            "🟦 蓝方胜"
            if win_team == "BLUE"
            else "🟥 红方胜"
            if win_team == "RED"
            else "⚪ 赛果未知"
        )
        st.markdown(
            f"### 第 {idx} 局对决 【{win_label}】  "
            f"<small style='color: gray; font-size: 0.85em;'>录入时间:"
            f" {r.get('uploaded_time', '历史记录')}</small>",
            unsafe_allow_html=True,
        )

        honor_tags = []
        if datui:
          honor_tags.append(
              f"✨ **胜方大腿**: {clean_player_name(datui.get('player_name', ''))}（操刀"
              f" {datui.get('champion')} / 斩获 {datui.get('kills')} 杀）"
          )
        if juzhang:
          kda_val = round(
              (juzhang.get("kills", 0) + juzhang.get("assists", 0))
              / max(juzhang.get("deaths", 1), 1),
              2,
          )
          honor_tags.append(
              f"👑 **尽力局局长**: {clean_player_name(juzhang.get('player_name', ''))}（操刀"
              f" {juzhang.get('champion')}，KDA {kda_val} 独木难支）"
          )
        if wodi and wodi.get("deaths", 0) >= 5:
          honor_tags.append(
              f"🥔 **白给王/疑似卧底**:"
              f" {clean_player_name(wodi.get('player_name', ''))}（操刀"
              f" {wodi.get('champion')} / 阵亡 {wodi.get('deaths')} 次）"
          )

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
            if datui and p_name == clean_player_name(
                datui.get("player_name", "")
            ):
              tag = "✨ 大腿"
            elif juzhang and p_name == clean_player_name(
                juzhang.get("player_name", "")
            ):
              tag = "👑 尽力局长"
            elif wodi and p_name == clean_player_name(
                wodi.get("player_name", "")
            ):
              tag = "🥔 白给王"

            data.append(
                {"玩家": p_name, "英雄": champ, "K / D / A": kda, "本局评定": tag}
            )
          return pd.DataFrame(data)

        with col_b:
          is_win = "👑 [胜利]" if win_team == "BLUE" else "[失败]"
          st.markdown(f"**🟦 蓝方阵营 {is_win}**")
          st.dataframe(make_team_df(blue_players), hide_index=True)

        with col_r:
          is_win = "👑 [胜利]" if win_team == "RED" else "[失败]"
          st.markdown(f"**🟥 红方阵营 {is_win}**")
          st.dataframe(make_team_df(red_players), hide_index=True)

        img_f = r.get("image_file")
        if img_f and os.path.exists(os.path.join(IMAGE_DIR, img_f)):
          with st.expander("🔍 查看本局原始结算图"):
            st.image(
                os.path.join(IMAGE_DIR, img_f), width=450, caption=f"第 {idx} 局原图"
            )

        st.markdown("---")

  # ----- Tab 3: 羁绊与宿命死敌 -----
  with tab3:
    st.subheader("🔗 组合羁绊（搭档与表面兄弟）")

    duo_stats = defaultdict(lambda: {"total": 0, "wins": 0})
    rival_stats = defaultdict(lambda: {"total": 0, "p1_wins": 0})

    for r in records:
      players = r.get("players", [])
      blue_p = [
          clean_player_name(p.get("player_name", ""))
          for p in players
          if p.get("team") == "BLUE" and clean_player_name(p.get("player_name", ""))
      ]
      red_p = [
          clean_player_name(p.get("player_name", ""))
          for p in players
          if p.get("team") == "RED" and clean_player_name(p.get("player_name", ""))
      ]
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
            "wr_val": wr,
        })

    col_d1, col_d2 = st.columns(2)
    with col_d1:
      st.markdown("#### 🌟 黄金搭档（胜率最高）")
      if duo_list:
        duo_df_top = pd.DataFrame(duo_list).sort_values(
            by=["wr_val", "同队场次"], ascending=[False, False]
        )
        st.dataframe(
            duo_df_top.drop(columns=["wr_val"]).head(5), hide_index=True
        )
      else:
        st.caption("暂无足够数据（需至少同队 2 局）...")

    with col_d2:
      st.markdown("#### 💔 表面兄弟（翻车二人组）")
      if duo_list:
        duo_df_bot = pd.DataFrame(duo_list).sort_values(
            by=["wr_val", "同队场次"], ascending=[True, False]
        )
        st.dataframe(duo_df_bot.drop(columns=["wr_val"]).head(5), hide_index=True)
      else:
        st.caption("暂无足够数据...")

    st.markdown("---")
    st.subheader("⚔️ 一生之敌（对立阵营对抗时的胜率克制）")
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

  # ----- Tab 4: 选手个人黑历史档案 -----
  with tab4:
    all_players_list = sorted(list(df.index))
    target_player = st.selectbox(
        "🔍 选择要查成分的好友:",
        options=all_players_list,
    )

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
        st.metric(
            "个人总场次", f"{len(p_records)} 局", delta=df.loc[target_player, "胜率"]
        )
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
            "wr_val": c_wr,
        })
      champ_df = pd.DataFrame(champ_list).sort_values(
          by=["出场次数", "wr_val"], ascending=[False, False]
      )
      st.dataframe(champ_df.drop(columns=["wr_val"]), hide_index=True)

  # ----- Tab 5: 赛后战报长图 -----
  with tab5:
    st.subheader("📸 微信群一键发图战报")
    st.caption("长按或右键截取下方信息卡片，直接丢进微信群！")

    total_kills = sum(df["总击杀"])
    most_kill_p = df.sort_values(by="总击杀", ascending=False).index[0]
    most_death_p = df.sort_values(by="总死亡", ascending=False).index[0]
    best_wr_p = (
        df[df["总场次"] >= 2]
        .sort_values(by="KDA", ascending=False)
        .index
    )
    king_p = best_wr_p[0] if len(best_wr_p) > 0 else df.index[0]

    st.markdown(f"""
    > ### 🎮 **LOL 内战群封神榜战报**
    > * **🏆 综合战力王 (MVP)**: **【{king_p}】**（KDA: {df.loc[king_p, 'KDA']}）
    > * **🩸 人头收割机**: **【{most_kill_p}】**（累计击杀 {df.loc[most_kill_p, '总击杀']} 命）
    > * **🥔 峡谷慈善家**: **【{most_death_p}】**（累计送出 {df.loc[most_death_p, '总死亡']} 命）
    > * **🔥 峡谷累计产生人头**: {total_kills} 个，累计交战 {len(records)} 局。
    """)
