import streamlit as st
import json
import os
import google.generativeai as genai
from datetime import datetime
import streamlit.components.v1 as components

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

# 🔓 強制解鎖全頁面文字選取與複製 (全瀏覽器 / 手機相容)
st.markdown("""
    <style>
    /* 強制所有元素皆可選取複製 */
    * {
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }
    /* 強化小說內文的字體大小與排版 */
    .stMarkdown p {
        font-size: 1.05rem !important;
        line-height: 1.8 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✍️ 專業小說家 AI 全書寫作工作站")
st.caption("平時極簡流暢、進階可隨心調校（直連 Gemini API 免後端）的懸疑/規則小說創作主控台")

# ================= 預設資料初始化 (套用第八章最新 JSON 設定) =================
default_data = {
  "book_title": "《失號領域》",
  "book_theme": "懸疑 / 克蘇魯 / 規則怪談 / 物理解謎",
  "book_overall_secret": "希靈帝國在阻止虛空大災變的過程中，意外聯絡上虛空背面的神族（即蘇默這側虛空範圍內統稱為克系神靈），得知虛空大災變真相為虛空雙向歸零的機制，因虛空正反面資訊互不相容、互相無法解譯，當虛空一側的資訊溢出到另一側時，就會引發虛空大災變。而主角蘇默因第一集列車遭遇交通事故後被星域神族的成員選中進入列車事件中，進行培養虛空雙向資訊互譯的能力中脫穎而出",
  "confirmed_rules_list": [
    {
      "id": "r1",
      "content": "絕不可發聲或製造空氣震動（違者觸發黑液與菌絲吞噬）。"
    }
  ],
  "hypotheses_list": [
    {
      "id": "h1",
      "content": "只要不打破絕不可發聲的鐵律，區域內暫時是安全的。"
    }
  ],
  "clues_list": [
    {
      "id": "cl1",
      "content": "在蘇默醒來後不久，收到了一封語氣非常驚慌（哇啊啊啊啊）的簡訊，說明車上有東西一直發出聲音，再這樣下去列車會壞掉的"
    }
  ],
  "items_inventory": [
    {
      "id": "it1",
      "name": "蘇默的手機",
      "status": "時間鎖死在 06:52，電量約93%，電量正常消耗中",
      "owner": "蘇默"
    },
    {
      "id": "it2",
      "name": "西裝男的金屬萬年筆",
      "status": "筆尖極硬，由西裝男借給蘇默，可用於微觀力學卡位與物理阻斷",
      "owner": "西裝男 (借予蘇默)"
    }
  ],
  "volumes_list": [
    {
      "id": "v1",
      "title": "第一集：失聲火車",
      "target_words": 100000,
      "summary": "主角蘇默在時間鎖死在 06:52 的列車中醒來，利用物理知識推演規則邊界，與左半身麻痺的西裝男在絕對死寂中求生。"
    }
  ],
  "character_list": [
    {
      "id": "c1",
      "name": "蘇默",
      "relation": "主角本人",
      "summary": "剛要上大學第一天的理工科新生，因習慣用數據與物理公式抽象化恐怖現象來維持理智，在極度恐懼中展現出過人的邏輯推算能力。",
      "personality": "理智、數據導向、冷靜、觀察力強",
      "status": "健康但體力消耗極大，手心出冷汗，手機電量消耗至93%",
      "sanity": "84%",
      "speech_style": "極度節省字數（以節省手機剩餘電量）",
      "dialogue_example": "「06:52，時間沒動。省著用手機。」"
    },
    {
      "id": "c2",
      "name": "西裝男",
      "relation": "在11節車廂中偶遇",
      "summary": "中年上班族，陷入半身麻痺異變，與蘇默一同用體重卡住異變柱。",
      "personality": "殘存求生本能，忍痛能力強，具備執行力",
      "status": "左半身完全麻痺化為木頭與黑綠菌絲，右手可單手打字",
      "sanity": "60%",
      "speech_style": "無法發聲，透過右手在手機上記錄打字",
      "dialogue_example": "「死不了，但左邊身體全麻了，像一塊木頭。」"
    }
  ],
  "chapters_list": [
    {
      "num": 1,
      "title": "第 1 章：06:52 的列車",
      "summary": "蘇默在列車上醒來，發現手錶在走但手機與螢幕時間停留在 06:52。"
    },
    {
      "num": 7,
      "title": "第 7 章：阻尼與黏滯力",
      "summary": "蘇默利用沙發墊衝量消能，卻因黏滯力導致異變體首級扭轉180度並發出咕嚕聲！"
    }
  ],
  "current_vol_title": "第一集：失聲火車",
  "current_chap": 8,
  "target_chapter_words": 3300,
  "time_and_environment": "現實錨點：06:52 (時間鎖死) | 車廂實際時間：陷入異變約第 1.5 小時 | 車廂氣溫 24°C",
  "pacing_setting": "中速推演 (解謎/搜查/對話 - 長短句交替)",
  "sensory_details": "• 視覺：異變體死寂翻白的眼珠直勾勾盯著蘇默，喉部皮下黑液微幅痙攣。\n• 聽覺：死寂中異變體喉嚨傳出極其微弱但致命的『咕嚕……咕嚕……』肌肉痙攣聲。\n• 體感/嗅覺：冷汗瞬間浸透內衣，手心冷汗發涼。",
  "pov_type": "第一人稱",
  "pov_character": "蘇默",
  "tone_setting": "極度壓抑、懸疑冷酷、慌亂中努力維持理性物理推理",
  "previous_summary": "異變體那折斷在左肩上的頭顱突然順時針扭轉了180度，死寂的雙眼直勾勾盯著離它只有半米遠的蘇默，喉嚨裡開始發出一陣極其微弱、但在死寂車廂內無異於雷鳴的『咕嚕……咕嚕……』肌肉痙攣聲！它要發聲了！",
  "scene_conflict": "異變體即將發聲引發全車廂毀滅 vs 蘇默必須在極限狀態下進行無聲阻斷",
  "scene_turn": "以為需要專業刺喉，最後急中生智直接抄起第二個沙發墊像枕頭一樣狠狠物理悶壓住其面部與喉嚨，徹底吸附聲音",
  "reveal_and_mystery": "• 本章揭露：異變體受到遠程微波訊號驅動。\n• 本章懸念：9號車廂廣播室通電連結中。",
  "must_include": "• 抄起第二個沙發墊物理悶壓異變體面部與喉嚨\n• 手機收到解譯文字：【終端 04 已離線……第 9 號車廂廣播室連結中】",
  "chapter_outline": "異變體即將發聲的瞬間，蘇默急中生智抄起隔壁卡座的第二個沙發墊，像大枕頭一樣狠狠物理悶壓在異變體的面部與喉嚨上！隔著沙發墊用全身體重死死壓住，聲音被海綿完全吸附悶死。異變體徹底失去驅動癱瘓後，手機跳出廣播室連結警報。",
  "writing_taboos": "• 禁止任何角色開口發聲說話（必須使用手機打字或肢體交流）\n• 寫作禁止直接稱呼克系",
  "generated_content": ""
}

# Session State 動態清單正確初始化
if "character_list" not in st.session_state: st.session_state["character_list"] = default_data["character_list"]
if "volumes_list" not in st.session_state: st.session_state["volumes_list"] = default_data["volumes_list"]
if "chapters_list" not in st.session_state: st.session_state["chapters_list"] = default_data["chapters_list"]
if "items_inventory" not in st.session_state: st.session_state["items_inventory"] = default_data["items_inventory"]
if "confirmed_rules_list" not in st.session_state: st.session_state["confirmed_rules_list"] = default_data["confirmed_rules_list"]
if "hypotheses_list" not in st.session_state: st.session_state["hypotheses_list"] = default_data["hypotheses_list"]
if "clues_list" not in st.session_state: st.session_state["clues_list"] = default_data["clues_list"]
if "generated_text" not in st.session_state: st.session_state["generated_text"] = default_data.get("generated_content", "")

# ================= 頂部：存檔匯入與下載 =================
st.subheader("💾 紀錄與存檔管理")

uploaded_file = st.file_uploader("📤 匯入歷史設定檔 (.json / .txt)", type=["json", "txt"])
if uploaded_file is not None:
    try:
        loaded_data = json.load(uploaded_file)
        default_data.update(loaded_data)
        
        if "character_list" in loaded_data: st.session_state["character_list"] = loaded_data["character_list"]
        if "volumes_list" in loaded_data: st.session_state["volumes_list"] = loaded_data["volumes_list"]
        if "chapters_list" in loaded_data: st.session_state["chapters_list"] = loaded_data["chapters_list"]
        if "items_inventory" in loaded_data: st.session_state["items_inventory"] = loaded_data["items_inventory"]
        if "confirmed_rules_list" in loaded_data: st.session_state["confirmed_rules_list"] = loaded_data["confirmed_rules_list"]
        if "hypotheses_list" in loaded_data: st.session_state["hypotheses_list"] = loaded_data["hypotheses_list"]
        if "clues_list" in loaded_data: st.session_state["clues_list"] = loaded_data["clues_list"]
        if "generated_content" in loaded_data: st.session_state["generated_text"] = loaded_data["generated_content"]
            
        st.success("✅ 成功載入歷史紀錄！")
    except Exception as e:
        st.error(f"檔案格式錯誤：{str(e)}")

# ================= 側邊欄：全書設定 (修正動態新增刪除邏輯) =================
with st.sidebar:
    st.header("🔑 Gemini API 金鑰設定")
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("輸入 Gemini API Key", value=env_api_key, type="password")
    active_api_key = api_key_input if api_key_input else env_api_key

    st.divider()
    st.header("🌌 1. 全書世界觀")
    book_title = st.text_input("全書書名", value=default_data["book_title"])
    book_theme = st.text_input("題材風格", value=default_data["book_theme"])
    book_overall_secret = st.text_area("🔒 全書終局真相", value=default_data["book_overall_secret"], height=100)
    
    st.divider()
    
    # 🎒 道具庫區 (修正邏輯)
    col_it_t, col_it_a = st.columns([3, 1])
    with col_it_t: st.subheader("🎒 道具庫")
    with col_it_a:
        if st.button("➕ 道具"):
            new_id = f"it_{datetime.now().strftime('%M%S%f')}"
            st.session_state["items_inventory"].append({"id": new_id, "name": "新道具", "status": "狀態/特性", "owner": "持有者"})
            st.rerun()

    items_text = ""
    for it_idx in range(len(st.session_state["items_inventory"]) - 1, -1, -1):
        item = st.session_state["items_inventory"][it_idx]
        item_id = item.get("id", f"it_{it_idx}")
        with st.expander(f"📦 {item['name']} ({item['owner']})", expanded=False):
            item['name'] = st.text_input("名稱", value=item['name'], key=f"it_n_{item_id}")
            item['owner'] = st.text_input("持有者", value=item['owner'], key=f"it_o_{item_id}")
            item['status'] = st.text_input("狀態", value=item['status'], key=f"it_s_{item_id}")
            if st.button("🗑️ 刪除", key=f"it_d_{item_id}"):
                st.session_state["items_inventory"].pop(it_idx)
                st.rerun()
        items_text += f"• {item['name']} (持有:{item['owner']}): {item['status']}\n"

    st.divider()
    st.header("🧩 2. 規則與線索案件牆")
    
    # ✅ 已驗證鐵律 (修正邏輯)
    col_r_t, col_r_a = st.columns([3, 1])
    with col_r_t: st.subheader("✅ 已驗證鐵律")
    with col_r_a:
        if st.button("➕ 鐵律"):
            new_id = f"r_{datetime.now().strftime('%M%S%f')}"
            st.session_state["confirmed_rules_list"].append({"id": new_id, "content": "新鐵律..."})
            st.rerun()
            
    rules_text = ""
    for r_idx in range(len(st.session_state["confirmed_rules_list"]) - 1, -1, -1):
        r = st.session_state["confirmed_rules_list"][r_idx]
        r_id = r.get("id", f"r_{r_idx}")
        col_rx, col_rd = st.columns([4, 1])
        with col_rx: r['content'] = st.text_input(f"鐵律 {r_idx+1}", value=r['content'], key=f"r_val_{r_id}", label_visibility="collapsed")
        with col_rd:
            if st.button("🗑️", key=f"r_del_{r_id}"):
                st.session_state["confirmed_rules_list"].pop(r_idx)
                st.rerun()
        rules_text += f"{r_idx+1}. {r['content']}\n"

    # ❓ 未驗證假說 (修正邏輯)
    col_h_t, col_h_a = st.columns([3, 1])
    with col_h_t: st.subheader("❓ 未驗證假說")
    with col_h_a:
        if st.button("➕ 假說"):
            new_id = f"h_{datetime.now().strftime('%M%S%f')}"
            st.session_state["hypotheses_list"].append({"id": new_id, "content": "新假說..."})
            st.rerun()

    hypo_text = ""
    for h_idx in range(len(st.session_state["hypotheses_list"]) - 1, -1, -1):
        h = st.session_state["hypotheses_list"][h_idx]
        h_id = h.get("id", f"h_{h_idx}")
        col_hx, col_hd = st.columns([4, 1])
        with col_hx: h['content'] = st.text_input(f"假說 {h_idx+1}", value=h['content'], key=f"h_val_{h_id}", label_visibility="collapsed")
        with col_hd:
            if st.button("🗑️", key=f"h_del_{h_id}"):
                st.session_state["hypotheses_list"].pop(h_idx)
                st.rerun()
        hypo_text += f"{h_idx+1}. {h['content']}\n"

    # 🔍 關鍵線索庫 (修正邏輯)
    col_cl_t, col_cl_a = st.columns([3, 1])
    with col_cl_t: st.subheader("🔍 關鍵線索庫")
    with col_cl_a:
        if st.button("➕ 線索"):
            new_id = f"cl_{datetime.now().strftime('%M%S%f')}"
            st.session_state["clues_list"].append({"id": new_id, "content": "新線索..."})
            st.rerun()

    clues_text = ""
    for cl_idx in range(len(st.session_state["clues_list"]) - 1, -1, -1):
        cl = st.session_state["clues_list"][cl_idx]
        cl_id = cl.get("id", f"cl_{cl_idx}")
        col_clx, col_cld = st.columns([4, 1])
        with col_clx: cl['content'] = st.text_input(f"線索 {cl_idx+1}", value=cl['content'], key=f"cl_val_{cl_id}", label_visibility="collapsed")
        with col_cld:
            if st.button("🗑️", key=f"cl_del_{cl_id}"):
                st.session_state["clues_list"].pop(cl_idx)
                st.rerun()
        clues_text += f"• {cl['content']}\n"

    st.divider()
    
    # 👥 角色卡片庫 (修正邏輯)
    col_char_t, col_char_a = st.columns([3, 1])
    with col_char_t: st.subheader("👥 角色卡片庫")
    with col_char_a:
        if st.button("➕ 角色"):
            new_c_id = f"c_{datetime.now().strftime('%M%S%f')}"
            st.session_state["character_list"].append({"id": new_c_id, "name": "新角色", "relation": "關係", "summary": "簡介...", "personality": "性格", "status": "狀態", "sanity": "100%", "speech_style": "口吻", "dialogue_example": "台詞..."})
            st.rerun()

    updated_characters_text = ""
    char_names_list = []
    for c_idx in range(len(st.session_state["character_list"]) - 1, -1, -1):
        char = st.session_state["character_list"][c_idx]
        c_id = char.get("id", f"c_{c_idx}")
        char_names_list.append(char['name'])
        with st.expander(f"👤 {char['name']} ({char['relation']})", expanded=False):
            char['name'] = st.text_input("名稱", value=char['name'], key=f"c_n_{c_id}")
            char['relation'] = st.text_input("關係", value=char['relation'], key=f"c_r_{c_id}")
            char['summary'] = st.text_input("簡介", value=char['summary'], key=f"c_s_{c_id}")
            char['personality'] = st.text_input("性格", value=char['personality'], key=f"c_p_{c_id}")
            char['status'] = st.text_input("🩸 生理狀態", value=char['status'], key=f"c_st_{c_id}")
            char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_sn_{c_id}")
            char['speech_style'] = st.text_input("口吻風格", value=char['speech_style'], key=f"c_sp_{c_id}")
            char['dialogue_example'] = st.text_input("💬 代表台詞", value=char.get('dialogue_example', ''), key=f"c_dg_{c_id}")
            if st.button("🗑️ 刪除角色", key=f"c_dl_{c_id}"):
                st.session_state["character_list"].pop(c_idx)
                st.rerun()
        updated_characters_text += f"【{char['name']} ({char['relation']})】\n• 簡介：{char['summary']}\n• 生理狀態：{char['status']} | SAN值：{char.get('sanity', '100%')}\n---\n"

# ================= 主畫面：寫作工作區 =================
st.subheader(f"📖 3. 當前撰寫：{book_title}")

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    vol_options = [v['title'] for v in st.session_state['volumes_list']]
    current_vol_title = st.selectbox("🎯 當前集數", vol_options if vol_options else ["第一集：失聲火車"])
with col_m2: current_chap = st.number_input("目前章節", value=default_data["current_chap"], min_value=1)
with col_m3: target_chapter_words = st.number_input("🎯 本章目標字數", value=default_data["target_chapter_words"], step=500)

previous_summary = st.text_area("📌 上一章結尾錨點 (銜接點)", value=default_data["previous_summary"], height=80)
chapter_outline = st.text_area("🎯 本章具體大綱與情節推進 (主要寫作指令)", value=default_data["chapter_outline"], height=100)

# ⚙️ 進階選單
with st.expander("⚙️ 點此展開【本章進階微調參數】", expanded=False):
    col_env1, col_env2, col_env3 = st.columns(3)
    with col_env1: pov_type = st.selectbox("👁️ 視角類型", ["第一人稱", "第三人稱限制視角", "第三人稱全知視角"], index=0)
    with col_env2: pov_character = st.selectbox("👤 描寫視角主角", char_names_list if char_names_list else ["蘇默"], index=0)
    with col_env3: pacing_setting = st.selectbox("⚡ 寫作節奏", ["中速推演 (解謎/搜查/對話)", "高速推進 (動作/戰鬥/逃跑)", "慢速壓抑 (鋪陳/恐懼/氛圍)"], index=0)

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1: time_and_environment = st.text_input("⏱️ 時間線與環境狀態", value=default_data["time_and_environment"])
    with col_sub2: tone_setting = st.text_input("🎭 本章情緒基調", value=default_data["tone_setting"])

    sensory_details = st.text_area("🌫️ 五感描寫重點", value=default_data["sensory_details"], height=70)

    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        scene_conflict = st.text_area("⚔️ 本章核心衝突點", value=default_data["scene_conflict"], height=70)
        must_include = st.text_area("🔑 必須出現的伏筆/道具", value=default_data["must_include"], height=70)
    with col_adv2:
        scene_turn = st.text_area("🔄 本章局勢/認知大翻轉", value=default_data["scene_turn"], height=70)
        reveal_and_mystery = st.text_area("🔍 伏筆揭示與新未知懸念", value=default_data["reveal_and_mystery"], height=70)

    writing_taboos = st.text_area("🚫 寫作禁忌", value=default_data["writing_taboos"], height=70)

# 動態打包 JSON 下載
current_export_data = {
    "book_title": book_title,
    "book_theme": book_theme,
    "book_overall_secret": book_overall_secret,
    "confirmed_rules_list": st.session_state["confirmed_rules_list"],
    "hypotheses_list": st.session_state["hypotheses_list"],
    "clues_list": st.session_state["clues_list"],
    "items_inventory": st.session_state["items_inventory"],
    "volumes_list": st.session_state["volumes_list"],
    "character_list": st.session_state["character_list"],
    "chapters_list": st.session_state["chapters_list"],
    "current_vol_title": current_vol_title,
    "current_chap": current_chap,
    "target_chapter_words": target_chapter_words,
    "time_and_environment": time_and_environment,
    "pacing_setting": pacing_setting,
    "sensory_details": sensory_details,
    "pov_type": pov_type,
    "pov_character": pov_character,
    "tone_setting": tone_setting,
    "previous_summary": previous_summary,
    "scene_conflict": scene_conflict,
    "scene_turn": scene_turn,
    "reveal_and_mystery": reveal_and_mystery,
    "must_include": must_include,
    "chapter_outline": chapter_outline,
    "writing_taboos": writing_taboos,
    "generated_content": st.session_state["generated_text"],
    "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

json_string = json.dumps(current_export_data, ensure_ascii=False, indent=2)
filename = f"{book_title}_{current_vol_title}_第{current_chap}章_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

st.download_button(
    label="📥 下載當前全書設定檔 (.json)",
    data=json_string,
    file_name=filename,
    mime="application/json",
    use_container_width=True
)

st.divider()

generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

# ================= 直連 Gemini API 生成邏輯 =================
if generate_btn:
    if not active_api_key:
        st.error("❌ 找不到 Gemini API Key！請在側邊欄填入 Key。")
    else:
        st.markdown("---")
        st.subheader("📝 本章生成成果：")
        
        prompt = f"""
你是一位頂級的懸疑 / 克蘇魯 / 規則怪談小說作家。請根據以下設定撰寫最新一章小說內文：

【全書背景】
• 書名：{book_title} ({book_theme})
• 全書終局真相：{book_overall_secret}
• 已驗證鐵律：
{rules_text}
• 當前可用道具庫：
{items_text}

【登場角色】
{updated_characters_text}

【上一章銜接點】
{previous_summary}

【本章指令】
• 當前章節：{current_vol_title} 第 {current_chap} 章
• 本章大綱：{chapter_outline}
• 目標字數：約 {target_chapter_words} 字
• 描寫視角：{pov_type} (以角色【{pov_character}】作為『我』)
• 時間與環境：{time_and_environment}
• 五感描寫重點：\n{sensory_details}
• 核心衝突：{scene_conflict}
• 認知大翻轉：{scene_turn}
• 必須包含元素：\n{must_include}
• 寫作禁忌：\n{writing_taboos}

【要求】直接輸出小說內文，保持極度壓抑、嚴密符合物理消能與規則怪談的氣氛。絕對不允許角色開口發聲。
"""

        try:
            genai.configure(api_key=active_api_key)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            selected_model_name = None
            for preferred in ["models/gemini-flash-latest", "models/gemini-2.0-flash", "models/gemini-pro-latest"]:
                if preferred in available_models:
                    selected_model_name = preferred
                    break
            
            if not selected_model_name and available_models:
                selected_model_name = available_models[0]
                
            clean_name = selected_model_name.replace("models/", "")
            st.caption(f"🤖 自動連接可用模型：`{clean_name}`")
            
            model = genai.GenerativeModel(clean_name)
            output_box = st.empty()
            full_text = ""
            
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    output_box.markdown(full_text)
                    
            st.session_state["generated_text"] = full_text
            st.success("🎉 本章生成完成！")
            
        except Exception as e:
            st.error(f"Gemini API 呼叫失敗：{str(e)}")

# 展示生成的成果與複製功能
if st.session_state["generated_text"]:
    st.markdown("---")
    st.subheader("📝 本章生成成果：")
    
    escaped_text = json.dumps(st.session_state["generated_text"])
    copy_button_html = f"""
        <button id="copyBtn" style="
            background-color: #FF4B4B; color: white; border: none; padding: 10px 20px;
            font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%;
        ">📋 一鍵複製全章內文至剪貼簿</button>
        <script>
            document.getElementById('copyBtn').addEventListener('click', function() {{
                var text = {escaped_text};
                navigator.clipboard.writeText(text).then(function() {{
                    alert('✅ 已成功將小說全章複製到剪貼簿！');
                }}, function(err) {{
                    alert('❌ 複製失敗，請使用純文字框複製。');
                }});
            }});
        </script>
    """
    components.html(copy_button_html, height=60)
    st.text_area("📋 複製專用純文字框", value=st.session_state["generated_text"], height=300)
    st.markdown("---")
    st.write(st.session_state["generated_text"])
