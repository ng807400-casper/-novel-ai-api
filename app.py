import streamlit as st
import requests
import json
from datetime import datetime

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

st.title("✍️ 專業小說家 AI 全書寫作工作站")
st.caption("平時極簡流暢、進階可隨心調校（含動態角色視角切換）的懸疑/規則小說創作主控台")

API_URL = "https://novel-ai-api-himy.onrender.com/v1/chapter/stream"

# ================= 預設資料初始化 =================
default_data = {
    "book_title": "《失號領域》",
    "book_theme": "懸疑 / 克蘇魯 / 規則怪談 / 物理解謎",
    "book_overall_secret": "列車與區域皆為規則實驗場，13 車車票是唯一的管理員密鑰。現實時間被定格在 06:52，但列車空間內的時間與生理代謝仍在流逝。",
    
    # 規則與線索庫
    "confirmed_rules": "1. 絕不可發聲或製造劇烈物理撞擊音。\n2. 所有電子設備時間硬性鎖死在 06:52，但空間內實際時間仍在流逝。\n3. 持有 13 車車票者為標記對象。",
    "unverified_hypotheses": "1. 手機基頻微波可能是接收外部異變脈衝的唯一接收器。\n2. 鐵門扣擊聲可能是受規則支配的機械式異變導體。",
    "clues_inventory": "• 13 車車票右下角折角痕跡\n• 鎖死在 06:52 的手機時間與持續下降的電量\n• 微波定頻規律脈衝數據",

    # 道具庫
    "items_inventory": [
        {"name": "蘇默的手機", "status": "時間鎖死在 06:52，電量隨著打字與亮屏正常損耗中", "owner": "蘇默"},
        {"name": "13 車車票", "status": "右下角有特定折角痕跡", "owner": "全員"},
        {"name": "公事包與外套", "status": "用來進行物理抗衡卡住異變柱", "owner": "西裝男"}
    ],

    "volumes_list": [
        {"id": "v1", "title": "第一集：失聲火車", "target_words": 100000, "summary": "主角蘇默在時間鎖死在 06:52 的列車中醒來，利用物理知識推演規則邊界，在電量有限與無法發聲的絕境中求生。"}
    ],
    
    # 角色卡
    "character_list": [
        {
            "id": "c1", "name": "蘇默", "relation": "主角本人",
            "summary": "冷靜理智的理工男，善於利用物理知識與環境細節推算規則邊界。",
            "personality": "極度理智、數據導向、冷靜", "status": "健康但體力消耗大，手機電量損耗中",
            "sanity": "85%", "speech_style": "極度節省字數（以節省電量）", "dialogue_example": "「時間鎖死在06:52，但我們體力在消耗。省著點用手機。」"
        },
        {
            "id": "c2", "name": "水手服女生 (林欣)", "relation": "求生夥伴",
            "summary": "車廂角落的水手服女生，在無聲恐怖中保持壓抑與理智。",
            "personality": "驚恐但極力克制、細心", "status": "精神極度緊繃，無聲流淚，電量所剩不多",
            "sanity": "50%", "speech_style": "不敢發聲，僅能透過眼神與肢體交流", "dialogue_example": "（緊咬雙唇，含著眼淚對蘇默點頭）"
        },
        {
            "id": "c3", "name": "西裝男", "relation": "共犯夥伴",
            "summary": "因規則陷入半身麻痺異變的上班族，與蘇默一同用體重對抗異變柱。",
            "personality": "中年上班族，殘存求生本能", "status": "左半身完全麻痺化為木頭/菌絲狀態",
            "sanity": "60%", "speech_style": "無法發聲，透過右手在手機上艱難打字", "dialogue_example": "「死不了，但左邊身體全麻了。手機快沒電了。」"
        }
    ],

    "chapters_list": [
        {"num": 1, "title": "第 1 章：06:52 的列車", "summary": "蘇默在列車上醒來，發現所有人的手機時間均鎖死在 06:52。"},
        {"num": 5, "title": "第 5 章：訊號與叩擊", "summary": "蘇默手機接收到未知微波脈衝，前方餐車鐵門傳來扣擊聲。"},
        {"num": 6, "title": "第 6 章：鐵門後的叩擊", "summary": "蘇默與林欣戒備靠近前方車廂鐵門，觀察未知動靜。"}
    ],

    # 當前微觀寫作參數
    "current_vol_title": "第一集：失聲火車",
    "current_chap": 6,
    "target_chapter_words": 3300,
    "time_and_environment": "現實錨點：06:52 (鎖死) | 車廂內實際流逝時間：第 2 小時 | 氣溫 12°C",
    "sensory_details": "• 視覺：昏暗死寂冷白光，西裝男左半身黑綠色菌絲，手機螢幕下降的電量％數。\n• 聽覺：絕對死寂，僅有呼吸聲與低溫下金屬收縮的牙酸微響。\n• 體感/嗅覺：冷汗浸濕衣物，空氣中濃重金屬鏽蝕與腐敗血腥味。",
    "pacing_setting": "中速推演 (解謎/搜查/對話 - 長短句交替)",
    "pov_type": "第一人稱",
    "pov_character": "蘇默",
    "tone_setting": "極度壓抑、懸疑冷酷、理性推算",
    "previous_summary": "上一章（第 5 章）結尾：蘇默與西裝男用體重與公事包卡住異變柱。所有人手機時間停在 06:52，但流逝的體力與持續下降的電量提醒著蘇默時間仍在走。此時，蘇默手機收到條微波脈衝訊號，前方餐車門傳來規律叩擊聲...",
    "chapter_outline": "第六章：蘇默與林欣戒備地靠近鐵門，透過門縫觀察前方車廂，同時蘇默嘗試解析手機接收到的神秘訊號。",
    "scene_conflict": "蘇默希望能靠近鐵門解析訊號 vs 林欣因為極度恐懼與擔心電量耗盡試圖阻止",
    "scene_turn": "以為門外是其他生還乘客，透過門縫觀察後發現竟是身上別著下一站工作人員識別證的異變導體",
    "reveal_and_mystery": "• 本章揭露：06:52 是發生事故的時間錨點，列車內時間持續向前。\n• 本章懸念：門外異變體握著 14 車標記車票，且西裝男手機電量即將見底。",
    "must_include": "• 手機時間顯示 06:52 與隨使用持續下降的電量條\n• 車廂鐵門上的刺鼻金屬鏽蝕味與規律叩擊聲",
    "writing_taboos": "• 禁止任何角色開口發聲說話（必須用手機打字或眼神交流）\n• 必須注意打字消耗電量的資源限制\n• 禁止主角無故驚慌失措",
    "generated_content": ""
}

# Session State 初始化
if "character_list" not in st.session_state: st.session_state["character_list"] = default_data["character_list"]
if "volumes_list" not in st.session_state: st.session_state["volumes_list"] = default_data["volumes_list"]
if "chapters_list" not in st.session_state: st.session_state["chapters_list"] = default_data["chapters_list"]
if "items_inventory" not in st.session_state: st.session_state["items_inventory"] = default_data["items_inventory"]

# ================= 頂部：存檔匯入與下載 =================
st.subheader("💾 紀錄與存檔管理")
col_file1, col_file2 = st.columns(2)

with col_file1:
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
                
            st.success("✅ 成功載入全書歷史紀錄！")
        except Exception as e:
            st.error(f"檔案格式錯誤：{str(e)}")

# ================= 側邊欄：全書設定 =================
with st.sidebar:
    st.header("🌌 1. 全書世界觀與角色庫")
    book_title = st.text_input("全書書名", value=default_data["book_title"])
    book_theme = st.text_input("題材風格", value=default_data["book_theme"])
    book_overall_secret = st.text_area("🔒 全書終局真相", value=default_data["book_overall_secret"], height=70)
    
    st.divider()
    
    # 關鍵道具庫區
    col_it_title, col_it_add = st.columns([3, 1])
    with col_it_title: st.subheader("🎒 道具與物料庫")
    with col_it_add:
        if st.button("➕ 道具"):
            st.session_state["items_inventory"].append({"name": "新道具", "status": "狀態/耐久", "owner": "持有者"})
            st.rerun()

    items_text = ""
    for it_idx, item in enumerate(st.session_state["items_inventory"]):
        with st.expander(f"📦 {item['name']} ({item['owner']})", expanded=False):
            item['name'] = st.text_input("道具名稱", value=item['name'], key=f"it_name_{it_idx}")
            item['owner'] = st.text_input("持有者", value=item['owner'], key=f"it_owner_{it_idx}")
            item['status'] = st.text_input("當前狀態/特性", value=item['status'], key=f"it_stat_{it_idx}")
            if st.button("🗑️ 刪除", key=f"it_del_{it_idx}"):
                st.session_state["items_inventory"].pop(it_idx)
                st.rerun()
        items_text += f"• {item['name']} (持有:{item['owner']}): {item['status']}\n"

    st.divider()
    st.subheader("🧩 規則與線索庫")
    confirmed_rules = st.text_area("✅ 已驗證鐵律", value=default_data["confirmed_rules"], height=70)
    unverified_hypotheses = st.text_area("❓ 未驗證假說", value=default_data["unverified_hypotheses"], height=70)
    clues_inventory = st.text_area("🔍 關鍵線索庫", value=default_data["clues_inventory"], height=70)

    st.divider()
    
    # 動態角色卡片清單
    col_char_title, col_char_add = st.columns([3, 1])
    with col_char_title: st.subheader("👥 角色卡片庫")
    with col_char_add:
        if st.button("➕ 角色"):
            new_c_id = f"c_{int(datetime.now().timestamp())}"
            st.session_state["character_list"].append({"id": new_c_id, "name": "新角色", "relation": "關係", "summary": "簡介...", "personality": "性格", "status": "狀態", "sanity": "100%", "speech_style": "口吻", "dialogue_example": "台詞..."})
            st.rerun()

    updated_characters_text = ""
    char_names_list = []
    for c_idx, char in enumerate(st.session_state["character_list"]):
        char_names_list.append(char['name'])
        with st.expander(f"👤 {char['name']} ({char['relation']})", expanded=False):
            char['name'] = st.text_input("名稱", value=char['name'], key=f"c_name_{char['id']}")
            char['relation'] = st.text_input("關係", value=char['relation'], key=f"c_rel_{char['id']}")
            char['summary'] = st.text_input("簡介", value=char['summary'], key=f"c_sum_{char['id']}")
            char['personality'] = st.text_input("性格", value=char['personality'], key=f"c_per_{char['id']}")
            char['status'] = st.text_input("🩸 生理狀態", value=char['status'], key=f"c_stat_{char['id']}")
            char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_san_{char['id']}")
            char['speech_style'] = st.text_input("口吻風格", value=char['speech_style'], key=f"c_speech_{char['id']}")
            char['dialogue_example'] = st.text_input("💬 代表台詞", value=char.get('dialogue_example', ''), key=f"c_diag_{char['id']}")
            if st.button("🗑️ 刪除", key=f"c_del_{char['id']}"):
                st.session_state["character_list"].pop(c_idx)
                st.rerun()
        updated_characters_text += f"【{char['name']} ({char['relation']})】\n• 簡介：{char['summary']}\n• 性格：{char['personality']}\n• 生理狀態：{char['status']} | SAN值：{char.get('sanity', '100%')}\n• 口吻：{char['speech_style']}\n• 台詞範例：{char.get('dialogue_example', '無')}\n---\n"

    volumes_summary_text = ""
    for v_idx, vol in enumerate(st.session_state["volumes_list"]):
        volumes_summary_text += f"• {vol['title']}: {vol['summary']}\n"

# ================= 主畫面：寫作工作區 =================
st.subheader(f"📖 2. 當前撰寫：{book_title}")

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    vol_options = [v['title'] for v in st.session_state['volumes_list']]
    current_vol_title = st.selectbox("🎯 當前集數", vol_options if vol_options else ["第一集：失聲火車"])
with col_m2: current_chap = st.number_input("目前章節", value=default_data["current_chap"], min_value=1)
with col_m3: target_chapter_words = st.number_input("🎯 本章目標字數", value=default_data["target_chapter_words"], step=500)

previous_summary = st.text_area("📌 上一章結尾錨點 (銜接點)", value=default_data["previous_summary"], height=80)
chapter_outline = st.text_area("🎯 本章具體大綱與情節推進 (主要寫作指令)", value=default_data["chapter_outline"], height=100)

# ⚙️ 進階選單：加入動態角色視角選擇
with st.expander("⚙️ 點此展開【本章進階微調參數】(視角切換、五感、衝突翻轉)", expanded=False):
    col_env1, col_env2, col_env3 = st.columns(3)
    
    with col_env1:
        pov_type_list = ["第一人稱", "第三人稱限制視角", "第三人稱全知視角"]
        pov_type = st.selectbox("👁️ 視角類型", pov_type_list, index=0)
        
    with col_env2:
        # 動態抓取角色列表作為第一人稱主角
        default_pov_char = default_data.get("pov_character", "蘇默")
        pov_char_index = char_names_list.index(default_pov_char) if default_pov_char in char_names_list else 0
        pov_character = st.selectbox("👤 描寫視角主角 (第一人稱視角主導者)", char_names_list if char_names_list else ["蘇默"], index=pov_char_index)
        
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

st.divider()

generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

if "generated_text" not in st.session_state:
    st.session_state["generated_text"] = default_data.get("generated_content", "")

# ================= 生成與成果展示 =================
if generate_btn:
    st.markdown("---")
    st.subheader("📝 本章生成成果：")
    
    # 組合精準的視角指令
    pov_final_instruction = f"{pov_type} (以角色【{pov_character}】作為第一人稱『我』來進行全身心描寫與心理思考)"
    
    combined_chapter_outline = f"""
    【本章大綱】：{chapter_outline}
    【目標字數】：約 {target_chapter_words} 字
    【描寫視角與核心主角】：{pov_final_instruction}
    【故事時間線與環境】：{time_and_environment}
    【寫作節奏與句式】：{pacing_setting}
    【情緒基調】：{tone_setting}
    【環境五感描寫重點】：
    {sensory_details}
    【核心衝突】：{scene_conflict}
    【局勢/認知翻轉】：{scene_turn}
    【伏筆揭示與新懸念】：
    {reveal_and_mystery}
    【必須包含的伏筆/道具】：
    {must_include}
    【寫作禁忌】：
    {writing_taboos}
    """
    
    combined_background = f"""
    【全書名稱】：{book_title} ({book_theme})
    【全書終局真相】：{book_overall_secret}
    【已知鐵律】：
    {confirmed_rules}
    【當前未驗證假說】：
    {unverified_hypotheses}
    【手邊線索庫】：
    {clues_inventory}
    【當前可用道具庫】：
    {items_text}
    【各集結構總覽】：
    {volumes_summary_text}
    """
    
    payload = {
        "volume_title": current_vol_title,
        "target_volume_words": 100000,
        "current_chapter": current_chap,
        "total_chapters": default_data.get("total_chaps", 30),
        "previous_volumes_summary": volumes_summary_text,
        "story_background": combined_background,
        "character_profiles": updated_characters_text,
        "chapter_outline": combined_chapter_outline,
        "previous_summary": previous_summary
    }
    
    try:
        response = requests.post(API_URL, json=payload, stream=True)
        if response.status_code == 200:
            output_box = st.empty()
            full_text = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    full_text += chunk
                    output_box.write(full_text)
            st.session_state["generated_text"] = full_text
        else:
            st.error(f"生成失敗，伺服器回應狀態碼：{response.status_code}")
    except Exception as e:
        st.error(f"連線發生錯誤：{str(e)}")

# 展示成果與 JSON 存檔導出
if st.session_state["generated_text"]:
    if not generate_btn:
        st.markdown("---")
        st.subheader("📝 本章生成成果（目前紀錄）：")
        st.write(st.session_state["generated_text"])

    current_export_data = {
        "book_title": book_title,
        "book_theme": book_theme,
        "book_overall_secret": book_overall_secret,
        "confirmed_rules": confirmed_rules,
        "unverified_hypotheses": unverified_hypotheses,
        "clues_inventory": clues_inventory,
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

    with col_file2:
        st.download_button(
            label="📥 下載全書設定與當前草稿 (.json)",
            data=json_string,
            file_name=filename,
            mime="application/json"
        )
