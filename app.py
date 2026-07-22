import streamlit as st
import json
import os
import google.generativeai as genai
from datetime import datetime

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

st.title("✍️ 專業小說家 AI 全書寫作工作站")
st.caption("平時極簡流暢、進階可隨心調校（直連 Gemini API 免後端）的懸疑/規則小說創作主控台")

# ================= 預設資料初始化 (忠於前六章原著) =================
default_data = {
    "book_title": "《失號領域》",
    "book_theme": "懸疑 / 克蘇魯 / 規則怪談 / 物理解謎",
    "book_overall_secret": "列車與區域皆陷入異常，現實時間被定格在 06:52，但列車空間內的時間與生理代謝仍在流逝。",
    
    # 1. 已驗證鐵律
    "confirmed_rules_list": [
        {"id": "r1", "content": "絕不可發聲或製造空氣震動（違者觸發黑液與菌絲吞噬）。"},
        {"id": "r2", "content": "車廂電子設備時間硬性鎖死在 06:52（預設 40 分鐘後的鬧鐘未響）。"},
        {"id": "r3", "content": "異變柱向上蔓延時，若受物理結構（如公事包與體重）卡托可暫時止住升高。"}
    ],

    # 2. 未驗證假說
    "hypotheses_list": [
        {"id": "h1", "content": "只要不打破絕不可發聲的鐵律，區域內暫時是安全的。"},
        {"id": "h2", "content": "門後的扣擊聲與手機接收到的微波脈衝訊號具有特定頻率聯繫。"}
    ],

    # 3. 關鍵線索庫
    "clues_list": [
        {"id": "cl1", "content": "手機右上角鎖死的 06:52 時間（時間錨點）。"},
        {"id": "cl2", "content": "天花板不到一公分處被古經理公事包卡住的異變柱。"},
        {"id": "cl3", "content": "蘇默手機收到的微波脈衝數據與文字輸入訊號。"}
    ],

    # 4. 道具庫
    "items_inventory": [
        {"name": "蘇默的手機", "status": "時間鎖死在 06:52，電量正常消耗，可進行無聲打字與微波接收", "owner": "蘇默"},
        {"name": "古經理的公事包與外套", "status": "用來墊在異變柱與木地板之間卡住頂升物理結構", "owner": "古經理(西裝男)"},
        {"name": "白色耳機", "status": "蘇默隨身攜帶，已接入手機感應微波脈衝", "owner": "蘇默"}
    ],

    "volumes_list": [
        {"id": "v1", "title": "第一集：失聲火車", "target_words": 100000, "summary": "主角蘇默在時間鎖死在 06:52 的列車中醒來，利用物理知識推演規則邊界，與左半身麻痺的古經理在絕對死寂中求生。"}
    ],
    
    # 5. 角色卡
    "character_list": [
        {
            "id": "c1", "name": "蘇默", "relation": "主角本人",
            "summary": "理智冷靜的理工男，善於利用物理知識與環境細節推算規則邊界。",
            "personality": "理智、數據導向、冷靜、觀察力強", "status": "健康但體力消耗極大，手心出冷汗，手機電量正常消耗中",
            "sanity": "85%", "speech_style": "極度節省字數（以節省手機剩餘電量）", "dialogue_example": "「06:52，時間沒動。省著用手機。」"
        },
        {
            "id": "c2", "name": "古經理 (西裝男)", "relation": "求生共犯",
            "summary": "中年上班族，陷入半身麻痺異變，與蘇默一同用體重卡住異變柱。",
            "personality": "殘存求生本能，忍痛能力強，具備執行力", "status": "左半身完全麻痺化為木頭與黑綠菌絲，右手可單手打字",
            "sanity": "60%", "speech_style": "無法發聲，透過右手在手機上記錄打字", "dialogue_example": "「死不了，但左邊身體全麻了，像一塊木頭。」"
        }
    ],

    "chapters_list": [
        {"num": 1, "title": "第 1 章：06:52 的列車", "summary": "蘇默在列車上醒來，發現手錶在走但手機與螢幕時間停留在 06:52。"},
        {"num": 2, "title": "第 2 章：無聲鐵律", "summary": "夾克男咆哮引發規則暴走，乘客瞬間融化為黑水與菌絲，車廂陷入絕對死寂。"},
        {"num": 3, "title": "第 3 章：蔓延的黑水", "summary": "黑液與菌絲在車廂地板蔓延，所有生還者被壓迫在極小空間內不敢發出聲音。"},
        {"num": 4, "title": "第 4 章：半身麻痺與物理抗衡", "summary": "古經理左半身陷入木化異變，蘇默與其合力利用公事包與體重卡住頂升的異變柱。"},
        {"num": 5, "title": "第 5 章：1% 的微波訊號", "summary": "兩人透過手機無聲打字交流，蘇默手機接收到未知的微波脈衝訊號。"},
        {"num": 6, "title": "第 6 章：突破第 10 節大門", "summary": "蘇默帶頭突破大門進入冰冷的無人餐車廂，前方門後傳來未知動靜與規律扣擊聲。"},
        {"num": 7, "title": "第 7 章：餐車廂的深處", "summary": "蘇默與古經理在餐車廂內深入探索，嘗試解析微波脈衝並應對大門外的未知威脅。"}
    ],

    # 當前寫作參數
    "current_vol_title": "第一集：失聲火車",
    "current_chap": 7,
    "target_chapter_words": 3300,
    "time_and_environment": "現實錨點：06:52 (時間鎖死) | 車廂實際時間：陷入異變約第 1 小時 | 車廂氣溫 12°C",
    "sensory_details": "• 視覺：冷白日光燈閃爍，古經理左半身黑綠菌絲與死皮，前方無人餐車廂的冷冽金屬感。\n• 聽覺：絕對死寂，僅有壓抑的呼吸聲與低溫金屬收縮的牙酸微響。\n• 體感/嗅覺：手心冷汗浸濕牛仔褲，空氣中濃重的金屬鏽蝕與刺鼻黑液味。",
    "pacing_setting": "中速推演 (解謎/搜查/對話 - 長短句交替)",
    "pov_type": "第一人稱",
    "pov_character": "蘇默",
    "tone_setting": "極度壓抑、懸疑冷酷、理性推算",
    "previous_summary": "第六章結尾：蘇默帶頭突破了第 10 節大門進入餐車廂，現場空無一人，宛如死寂的登山小屋。但空氣更加冰冷，前方通往更深處的大門正在傳來輕微而規律的叩擊聲...",
    "chapter_outline": "第七章：蘇默與古經理在餐車廂內小心搜查，嘗試利用手機剩餘電量解析接收到的微波脈衝數據，同時應對前方大門傳來的威脅。",
    "scene_conflict": "蘇默希望能靠近大門解析微波訊號與門外動靜 vs 車廂內極度死寂帶來的心理壓迫與電量消耗壓力",
    "scene_turn": "以為門外是其他生還乘客求救，透過門縫觀察後發現竟是受規則支配的異變導體",
    "reveal_and_mystery": "• 本章揭露：06:52 是發生事故那一刻的時間錨點，而列車內的實際時間正在持續向前流逝。\n• 本章懸念：門外異變導體手中的異常物品。",
    "must_include": "• 手機時間顯示 06:52 與隨打字持續下降的電量\n• 餐車廂內刺鼻的金屬鏽蝕味與規律叩擊聲",
    "writing_taboos": "• 禁止任何角色開口發聲說話（必須使用手機打字或肢體交流）\n• 注意手機打字耗電的資源限制\n• 禁止出現前六章未登場的角色",
    "generated_content": ""
}

# Session State 動態清單初始化
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
        
        if "character_list" in loaded_data:
            for idx, c in enumerate(loaded_data["character_list"]):
                if "id" not in c: c["id"] = f"c_{idx}_{int(datetime.now().timestamp())}"
            st.session_state["character_list"] = loaded_data["character_list"]
            
        if "volumes_list" in loaded_data: st.session_state["volumes_list"] = loaded_data["volumes_list"]
        if "chapters_list" in loaded_data: st.session_state["chapters_list"] = loaded_data["chapters_list"]
        if "items_inventory" in loaded_data: st.session_state["items_inventory"] = loaded_data["items_inventory"]
        if "confirmed_rules_list" in loaded_data: st.session_state["confirmed_rules_list"] = loaded_data["confirmed_rules_list"]
        if "hypotheses_list" in loaded_data: st.session_state["hypotheses_list"] = loaded_data["hypotheses_list"]
        if "clues_list" in loaded_data: st.session_state["clues_list"] = loaded_data["clues_list"]
        if "generated_content" in loaded_data: st.session_state["generated_text"] = loaded_data["generated_content"]
            
        st.success("✅ 成功載入全書歷史紀錄！")
    except Exception as e:
        st.error(f"檔案格式錯誤：{str(e)}")

# ================= 側邊欄：全書設定 (卡片化動態區) =================
with st.sidebar:
    st.header("🔑 Gemini API 金鑰設定")
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("輸入 Gemini API Key (可空著使用系統變數)", value=env_api_key, type="password")
    active_api_key = api_key_input if api_key_input else env_api_key

    st.divider()
    st.header("🌌 1. 全書世界觀與角色庫")
    book_title = st.text_input("全書書名", value=default_data["book_title"])
    book_theme = st.text_input("題材風格", value=default_data["book_theme"])
    book_overall_secret = st.text_area("🔒 全書終局真相", value=default_data["book_overall_secret"], height=70)
    
    st.divider()
    
    # 🎒 道具庫區
    col_it_t, col_it_a = st.columns([3, 1])
    with col_it_t: st.subheader("🎒 道具與物料庫")
    with col_it_a:
        if st.button("➕ 道具"):
            st.session_state["items_inventory"].append({"name": "新道具", "status": "狀態/特性", "owner": "持有者"})
            st.rerun()

    items_text = ""
    for it_idx, item in enumerate(st.session_state["items_inventory"]):
        with st.expander(f"📦 {item['name']} ({item['owner']})", expanded=False):
            item['name'] = st.text_input("名稱", value=item['name'], key=f"it_n_{it_idx}")
            item['owner'] = st.text_input("持有者", value=item['owner'], key=f"it_o_{it_idx}")
            item['status'] = st.text_input("狀態", value=item['status'], key=f"it_s_{it_idx}")
            if st.button("🗑️ 刪除道具", key=f"it_d_{it_idx}"):
                st.session_state["items_inventory"].pop(it_idx)
                st.rerun()
        items_text += f"• {item['name']} (持有:{item['owner']}): {item['status']}\n"

    st.divider()
    st.header("🧩 2. 規則與線索案件牆")
    
    # ✅ 已驗證鐵律
    col_r_t, col_r_a = st.columns([3, 1])
    with col_r_t: st.subheader("✅ 已驗證鐵律")
    with col_r_a:
        if st.button("➕ 鐵律"):
            st.session_state["confirmed_rules_list"].append({"id": f"r_{int(datetime.now().timestamp())}", "content": "新鐵律..."})
            st.rerun()
            
    rules_text = ""
    for r_idx, r in enumerate(st.session_state["confirmed_rules_list"]):
        col_rx, col_rd = st.columns([4, 1])
        with col_rx: r['content'] = st.text_input(f"鐵律 {r_idx+1}", value=r['content'], key=f"r_val_{r_idx}", label_visibility="collapsed")
        with col_rd:
            if st.button("🗑️", key=f"r_del_{r_idx}"):
                st.session_state["confirmed_rules_list"].pop(r_idx)
                st.rerun()
        rules_text += f"{r_idx+1}. {r['content']}\n"

    # ❓ 未驗證假說
    col_h_t, col_h_a = st.columns([3, 1])
    with col_h_t: st.subheader("❓ 未驗證假說")
    with col_h_a:
        if st.button("➕ 假說"):
            st.session_state["hypotheses_list"].append({"id": f"h_{int(datetime.now().timestamp())}", "content": "新假說..."})
            st.rerun()

    hypo_text = ""
    for h_idx, h in enumerate(st.session_state["hypotheses_list"]):
        col_hx, col_hd = st.columns([4, 1])
        with col_hx: h['content'] = st.text_input(f"假說 {h_idx+1}", value=h['content'], key=f"h_val_{h_idx}", label_visibility="collapsed")
        with col_hd:
            if st.button("🗑️", key=f"h_del_{h_idx}"):
                st.session_state["hypotheses_list"].pop(h_idx)
                st.rerun()
        hypo_text += f"{h_idx+1}. {h['content']}\n"

    # 🔍 關鍵線索庫
    col_cl_t, col_cl_a = st.columns([3, 1])
    with col_cl_t: st.subheader("🔍 關鍵線索庫")
    with col_cl_a:
        if st.button("➕ 線索"):
            st.session_state["clues_list"].append({"id": f"cl_{int(datetime.now().timestamp())}", "content": "新線索..."})
            st.rerun()

    clues_text = ""
    for cl_idx, cl in enumerate(st.session_state["clues_list"]):
        col_clx, col_cld = st.columns([4, 1])
        with col_clx: cl['content'] = st.text_input(f"線索 {cl_idx+1}", value=cl['content'], key=f"cl_val_{cl_idx}", label_visibility="collapsed")
        with col_cld:
            if st.button("🗑️", key=f"cl_del_{cl_idx}"):
                st.session_state["clues_list"].pop(cl_idx)
                st.rerun()
        clues_text += f"• {cl['content']}\n"

    st.divider()
    
    # 👥 角色卡片庫
    col_char_t, col_char_a = st.columns([3, 1])
    with col_char_t: st.subheader("👥 角色卡片庫")
    with col_char_a:
        if st.button("➕ 角色"):
            new_c_id = f"c_{int(datetime.now().timestamp())}"
            st.session_state["character_list"].append({"id": new_c_id, "name": "新角色", "relation": "關係", "summary": "簡介...", "personality": "性格", "status": "狀態", "sanity": "100%", "speech_style": "口吻", "dialogue_example": "台詞..."})
            st.rerun()

    updated_characters_text = ""
    char_names_list = []
    for c_idx, char in enumerate(st.session_state["character_list"]):
        char_names_list.append(char['name'])
        with st.expander(f"👤 {char['name']} ({char['relation']})", expanded=False):
            char['name'] = st.text_input("名稱", value=char['name'], key=f"c_n_{char['id']}")
            char['relation'] = st.text_input("關係", value=char['relation'], key=f"c_r_{char['id']}")
            char['summary'] = st.text_input("簡介", value=char['summary'], key=f"c_s_{char['id']}")
            char['personality'] = st.text_input("性格", value=char['personality'], key=f"c_p_{char['id']}")
            char['status'] = st.text_input("🩸 生理狀態", value=char['status'], key=f"c_st_{char['id']}")
            char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_sn_{char['id']}")
            char['speech_style'] = st.text_input("口吻風格", value=char['speech_style'], key=f"c_sp_{char['id']}")
            char['dialogue_example'] = st.text_input("💬 代表台詞", value=char.get('dialogue_example', ''), key=f"c_dg_{char['id']}")
            if st.button("🗑️ 刪除角色", key=f"c_dl_{char['id']}"):
                st.session_state["character_list"].pop(c_idx)
                st.rerun()
        updated_characters_text += f"【{char['name']} ({char['relation']})】\n• 簡介：{char['summary']}\n• 性格：{char['personality']}\n• 生理狀態：{char['status']} | SAN值：{char.get('sanity', '100%')}\n• 口吻：{char['speech_style']}\n• 代表台詞：{char.get('dialogue_example', '無')}\n---\n"

    volumes_summary_text = ""
    for v_idx, vol in enumerate(st.session_state["volumes_list"]):
        volumes_summary_text += f"• {vol['title']}: {vol['summary']}\n"

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

# ⚙️ 進階選單 (自動折疊)
with st.expander("⚙️ 點此展開【本章進階微調參數】(視角切換、五感、衝突翻轉)", expanded=False):
    col_env1, col_env2, col_env3 = st.columns(3)
    
    with col_env1:
        pov_type_list = ["第一人稱", "第三人稱限制視角", "第三人稱全知視角"]
        pov_type = st.selectbox("👁️ 視角類型", pov_type_list, index=0)
        
    with col_env2:
        default_pov_char = default_data.get("pov_character", "蘇默")
        pov_char_index = char_names_list.index(default_pov_char) if default_pov_char in char_names_list else 0
        pov_character = st.selectbox("👤 描寫視角主角", char_names_list if char_names_list else ["蘇默"], index=pov_char_index)
        
    with col_env3:
        pacing_list = ["中速推演 (解謎/搜查/對話 - 長短句交替)", "高速推進 (動作/戰鬥/逃跑 - 短句為主)", "慢速壓抑 (鋪陳/恐懼/氛圍 - 細節拉長)"]
        pacing_setting = st.selectbox("⚡ 寫作節奏與速度感", pacing_list, index=0)

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1: time_and_environment = st.text_input("⏱️ 時間線與環境狀態", value=default_data["time_and_environment"])
    with col_sub2: tone_setting = st.text_input("🎭 本章情緒基調", value=default_data["tone_setting"])

    sensory_details = st.text_area("🌫️ 五感描寫重點 (視覺/聽覺/嗅覺/體感)", value=default_data["sensory_details"], height=70)

    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        scene_conflict = st.text_area("⚔️ 本章核心衝突點", value=default_data["scene_conflict"], height=70)
        must_include = st.text_area("🔑 必須出現的伏筆/道具", value=default_data["must_include"], height=70)
    with col_adv2:
        scene_turn = st.text_area("🔄 本章局勢/認知大翻轉 (Turn)", value=default_data["scene_turn"], height=70)
        reveal_and_mystery = st.text_area("🔍 伏筆揭示與新未知懸念", value=default_data["reveal_and_mystery"], height=70)

    writing_taboos = st.text_area("🚫 寫作禁忌 (Negative Prompt)", value=default_data["writing_taboos"], height=70)

# 預先對照的章節目錄清單
with st.expander("📑 章節目錄大綱庫 (預先規劃對照區)", expanded=False):
    col_ch_t, col_ch_a = st.columns([3, 1])
    with col_ch_t: st.write("預先規劃各章大綱：")
    with col_ch_a:
        if st.button("➕ 新增預寫章節"):
            next_num = len(st.session_state["chapters_list"]) + 1
            st.session_state["chapters_list"].append({"num": next_num, "title": f"第 {next_num} 章", "summary": "大綱..."})
            st.rerun()
            
    for ch_idx, ch in enumerate(st.session_state["chapters_list"]):
        col_c1, col_c2, col_c3 = st.columns([1, 2, 4])
        with col_c1: ch['num'] = st.number_input("章號", value=ch['num'], key=f"ch_num_{ch_idx}")
        with col_c2: ch['title'] = st.text_input("標題", value=ch['title'], key=f"ch_title_{ch_idx}")
        with col_c3: ch['summary'] = st.text_input("簡要大綱", value=ch['summary'], key=f"ch_sum_{ch_idx}")

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
        st.error("❌ 找不到 Gemini API Key！請在側邊欄填入 Key，或在 Render 設定 GEMINI_API_KEY 環境變數。")
    else:
        st.markdown("---")
        st.subheader("📝 本章生成成果：")
        
        pov_final_instruction = f"{pov_type} (以角色【{pov_character}】作為第一人稱『我』來進行全身心描寫與心理思考)"
        
        prompt = f"""
你是一位頂級的懸疑 / 克蘇魯 / 規則怪談小說作家。請根據以下完整的全書世界觀、角色狀態與本章微調指令，為我撰寫小說最新一章的內文。

【全書世界觀與背景】
• 書名：{book_title} ({book_theme})
• 全書終局真相：{book_overall_secret}
• 已驗證鐵律：
{rules_text}
• 當前未驗證假說：
{hypo_text}
• 手邊線索庫：
{clues_text}
• 當前可用道具庫：
{items_text}

【登場角色陣容】
{updated_characters_text}

【上一章結尾銜接點】
{previous_summary}

【本章撰寫精準指令】
• 當前章節：{current_vol_title} 第 {current_chap} 章
• 本章大綱：{chapter_outline}
• 目標字數：約 {target_chapter_words} 字
• 描寫視角：{pov_final_instruction}
• 故事時間線與環境：{time_and_environment}
• 寫作節奏：{pacing_setting}
• 情緒基調：{tone_setting}
• 五感描寫重點：\n{sensory_details}
• 核心衝突：{scene_conflict}
• 局勢/認知大翻轉：{scene_turn}
• 伏筆揭示與新懸念：\n{reveal_and_mystery}
• 必須包含元素：\n{must_include}
• 寫作禁忌 (Negative Prompt)：\n{writing_taboos}

【寫作要求】
1. 直接輸出小說內文，不要帶有任何開場白或結語。
2. 保持極度壓抑、冷酷、嚴密符合物理解謎與規則怪談的氣氛。
3. 嚴格遵循「寫作禁忌」，特別是絕對不允許角色違規開口發聲。
"""

        try:
            genai.configure(api_key=active_api_key)

# 替換為最新的免費主力模型：
model = genai.GenerativeModel('gemini-2.5-flash')

            output_box = st.empty()
            full_text = ""
            
            # 使用流式輸出 (Stream) 實現打字機效果
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    output_box.markdown(full_text)
                    
            st.session_state["generated_text"] = full_text
            st.success("🎉 本章生成完成！已更新備份資料。")
            
        except Exception as e:
            st.error(f"Gemini API 呼叫失敗：{str(e)}")

# 展示目前的成果紀錄
if st.session_state["generated_text"] and not generate_btn:
    st.markdown("---")
    st.subheader("📝 本章生成成果（目前紀錄）：")
    st.write(st.session_state["generated_text"])
