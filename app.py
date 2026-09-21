import base64
from collections import defaultdict
import hashlib
import io
import itertools
import json
import os
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
    page_title="LOL 内战战绩看板 (掌盟专版)",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- 常用英雄候选池（约束幻觉） ----------------
ALL_CHAMPIONS = (
    "亚索,永恩,李青,卡莎,阿狸,锤石,诺提勒斯,派克,伊泽瑞尔,拉克丝,薇恩,瑟提,维克托,赛娜,金克丝,"
    "格温,佛耶戈,劫,塞拉斯,阿卡丽,菲兹,崔斯特,德莱文,蕾欧娜,莫甘娜,嘉文四世,赵信,雷克顿,墨菲特,诺克萨斯之手,"
    "厄斐琉斯,艾希,凯特琳,烬,卢锡安,莎弥拉,霞,崔丝塔娜,韦鲁斯,克格莫,希维尔,图奇,吉格斯,"
    "盲僧,孙悟空,蔚,沃里克,辛吉德,贾克斯,伊芙琳,卡兹克,雷恩加尔,奈德丽,易,艾克,黛安娜,莫德凯撒,"
    "波比,奎桑提,奥恩,慎,盖伦,普朗克,凯南,杰斯,菲奥娜,卡蜜尔,艾瑞莉娅,锐雯,亚托克斯,纳尔,"
    "辛德拉,奥莉安娜,阿兹尔,卡萨丁,佐伊,妮蔻,丽桑卓,岩雀,乐芙兰,玛尔扎哈,卡尔玛,璐璐,娜美,"
    "索拉卡,悠米,巴德,布隆,阿利斯塔,芮尔,洛,塔姆,蒸汽机器人"
)

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


# ---------------- 1. 数据持久化 ----------------
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


# ---------------- 2. 针对掌盟 App 左列头像的切片识别 ----------------
def analyze_screenshot_for_app(image_bytes, key, max_retries=3):
  client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

  pil_img = Image.open(io.BytesIO(image_bytes))
  if pil_img.mode != "RGB":
    pil_img = pil_img.convert("RGB")

  w, h = pil_img.size

  # 图像锐度与对比度增强
  enhancer = ImageEnhance.Sharpness(pil_img)
  pil_img = enhancer.enhance(1.3)
  enhancer_c = ImageEnhance.Contrast(pil_img)
  pil_img = enhancer_c.enhance(1.1)

  def to_b64(img_obj):
    buf = io.BytesIO()
    img_obj.save(buf, format="JPEG", quality=95)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

  full_b64 = to_b64(pil_img)

  # 裁切掌盟左侧头像竖列
  left_avatar_strip = pil_img.crop(
      (0, int(h * 0.12), int(w * 0.28), int(h * 0.95))
  )
  strip_b64 = to_b64(left_avatar_strip)

  prompt = f"""这是手机端【掌上英雄联盟 App】的对局结算详情页截图。
我为你提供了两张图：
1. 第一张是【手机全图】：用于看胜利/失败阵营、每个选手的ID文字和K/D/A数据。
2. 第二张是【左侧英雄头像列单独放大图】：纯粹由左侧 10 位玩家的英雄圆形头像从上到下按顺序排列。

【关键结构（掌上英雄联盟布局）】：
- 页面自上而下通常分为两个队伍（前 5 行为上方队伍，后 5 行为下方队伍）。
- 每一行最左侧是英雄头像，往右紧接着是玩家ID、召唤师技能和 K/D/A。
- 请将【左侧头像放大图】从上到下的 10 个头像，严格按照自上而下的顺序，精准赋给对应行的 10 位玩家！

【防错要求】：
1. 头像常常有炫彩或至臻等皮肤，请看清楚面部轮廓、特征武器或发型，切勿仅凭金黄色/深蓝色盲目猜测！
2. 全局 10 位玩家英雄互斥（不重复）。
3. 英雄名称请严格从官方常用名库中匹配输出：
   [{ALL_CHAMPIONS}]

严格输出合法的纯 JSON 对象，格式如下：
{{
  "winning_team": "BLUE" 或 "RED",
  "players": [
    {{
      "player_name": "玩家游戏ID",
      "champion": "规范英雄名",
      "team": "BLUE" 或 "RED",
      "kills": 0,
      "deaths": 0,
      "assists": 0,
      "is_winner": true 或 false
    }}
  ]
}}
"""

  content_payload = [
      {"type": "text", "text": prompt},
      {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{full_b64}"}},
      {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{strip_b64}"}},
  ]

  for attempt in range(max_retries):
    try:
      response = client.chat.completions.create(
          model="deepseek-flash",
          messages=[{"role": "user", "content": content_payload}],
          response_format={"type": "json_object"},
          temperature=0.1,
      )
      content = response.choices[0].message.content.strip()

      # 安全清理 markdown 标记，避免因反引号导致的语法错误
      if content.startswith("```json"):
        content = content[7:]
      elif content.startswith("```"):
        content = content[3:]
      if content.endswith("```"):
        content = content[:-3]
      content = content.strip()

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
  with st.expander("🔒 管理员控制台（数据校准/删除）"):
    admin_pwd = st.text_input("管理员密码", type="password", key="admin_pwd_input")
    if admin_pwd == "666888":
      if current_records:
        st.markdown("##### ✏️ 英雄手动校准")
        corr_options = {i: f"第 {i + 1} 局" for i in range(len(current_records))}
        sel_corr_idx = st.selectbox(
            "选择对局",
            options=list(reversed(list(corr_options.keys()))),
            format_func=lambda x: corr_options[x],
            key="select_corr_game",
        )

        target_rec = current_records[sel_corr_idx]
        p_names = [
            clean_player_name(p.get("player_name", f"选手{k}"))
            for k, p in enumerate(target_rec.get("players", []))
        ]
        sel_p_idx = st.selectbox(
            "选择选手",
            options=list(range(len(p_names))),
            format_func=lambda x: p_names[x],
        )

        curr_champ = target_rec.get("players", [])[sel_p_idx].get("champion", "")
        st.caption(f"当前识别为：**{curr_champ}**")

        new_champ = st.text_input("修正为正确英雄", value=curr_champ)
        if st.button("💾 保存英雄修改"):
          current_records[sel_corr_idx]["players"][sel_p_idx]["champion"] = new_champ.strip()
          overwrite_all_records(current_records)
          st.toast(f"已更新为 {new_champ}！", icon="✅")
          time.sleep(0.8)
          st.rerun()

        st.divider()

        if st.button("⏪ 撤回最近的一局"):
          delete_record_by_index(len(current_records) - 1)
          st.toast("已撤回最新对局！", icon="🗑️")
          time.sleep(0.8)
          st.rerun()

        sel_del_idx = st.selectbox(
            "选择要删除的对局",
            options=list(reversed(list(corr_options.keys()))),
            format_func=lambda x: corr_options[x],
            key="select_del_game",
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

# ---------------- 4. 上传与解析 ----------------
st.header("📱 LOL 内战战绩中心 (掌盟截图版)")

uploaded_files = st.file_uploader(
    "📤 上传掌盟战绩截图（支持多图全选拖入，或直接上传 .zip 文件夹）",
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

        with st.spinner(f"正在分析掌盟截图 ({idx + 1}/{total}): {img_name}..."):
          try:
            result = analyze_screenshot_for_app(img_bytes, api_key)
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
