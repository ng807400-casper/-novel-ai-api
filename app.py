import streamlit as st
import requests
import json
from datetime import datetime

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 全書寫作工作站", page_icon="✍️", layout="wide")

st.title("✍️ 專業小說家 AI 全書寫作工作站 (完全體)")
st.caption("整合三層架構、動態角色卡、時間線/SAN值、規則線索庫與 JSON 全備份的終極介面")

API_URL = "https://novel-ai-api-himy.onrender.com/v1/chapter/stream"

# ================= 預設資料初始化 =================
default_data = {
    "book_title": "《失號領域》",
    "book_theme": "懸疑 / 克蘇魯 / 物理規則解謎",
    "book_overall_secret": "列車與所有區域皆為規則實驗場，13 車車票是唯一的管理員密鑰。",
    
    # 規則與線索庫
    "confirmed_rules": "1. 絕不可發聲。\n2. 車廂時間停滯。\n3. 持有 13 車車票者為標記對象。",
    "unverified_hypotheses": "1. 手機電量 1% 可能是感應外部微波的接收器。\n2. 鐵門扣擊聲可能不是人類發出的。",
    "clues_inventory": "• 13 車車票的特定折角痕跡\n• 手機 1% 電量閃爍的固定波長數據",

    "volumes_list": [
        {"id": "v1", "title": "第一集：失聲火車", "target_words": 100000, "summary": "主角蘇默在陷入時間停滯與無聲鐵律的列車中醒來，利用物理知識推演規則邊界。"},
        {"id": "v2", "title": "第二集：深淵迴響", "target_words": 120000, "summary": "進入第二異變區域，常駐 1% 電量的手機開始接收到外部微波訊息。"}
    ],
    
    "character_list": [
        {
            "id": "c1", "name": "蘇默", "relation": "主角本人",
            "summary": "冷靜理工男，善於利用物理知識推算規則邊界。",
            "entry_chap": 1, "exit_chap": "存活至最後", "personality": "極度理智、數據導向",
            "status": "健康，手機電量鎖定 1%", "sanity": "90% (高度冷靜理性)", "speech_style": "簡短、條理分明"
        },
        {
            "id": "c2", "name": "林欣", "relation": "生死求生夥伴",
            "summary": "細心的女性求生者，提供物資調配與心理支柱。",
            "entry_chap": 2, "exit_chap": "預估第 25 章", "personality": "細心、共情能力強",
            "status": "極度疲憊", "sanity": "55% (精神緊繃，有幻聽傾向)", "speech_style": "輕聲細語、著重情感"
        }
    ],

    "chapters_list": [
        {"num": 5, "title": "第 5 章：1% 的訊號", "summary": "蘇默發現手機電量鎖定在 1%，並接收到神秘微波。"},
        {"num": 6, "title": "第 6 章：鐵門後的叩擊", "summary": "蘇默與林欣戒備靠近前方車廂鐵門，觀察未知動靜。"}
    ],

    "current_vol_title": "第一集：失聲火車",
    "current_chap": 6,
    "total_chaps": 30,
    "target_chapter_words": 3300,
    "time_and_environment": "故事時間：陷入異變後第 8 小時 | 環境：車廂溫度 12°C，空氣帶有濃重刺鼻金屬鏽蝕味",
    "pov_setting": "第一人稱 (蘇默視角)",
    "tone_setting": "極度壓抑、懸疑冷酷、理性推算",
    "previous_summary": "上一章結尾：蘇默盯著手機 1% 電量，發現未知的微波訊號，前方鐵門傳來扣擊聲...",
    "must_include": "• 手機 1% 電量接收到的神祕微波數據\n• 車廂鐵門上的刺鼻金屬鏽蝕味",
    "chapter_outline": "第六章：蘇默與林欣戒備地靠近鐵門，透過門縫觀察前方車廂，同時蘇默嘗試解析手機接收到的神秘訊號。",
    "scene_conflict": "蘇默希望主動開門探查訊號來源 vs 林欣害怕觸發未知規則試圖阻止",
    "scene_turn": "以為門外是其他生還者扣門，透過門縫觀察後發現竟是受規則支配的機械式異變導體",
    "writing_taboos": "• 禁止出現感性說教台詞\n• 禁止主角無故驚慌失措\n• 對話需簡短、注重環境物理描寫",
    "generated_content": ""
}

if "character_list" not in st.session_state:
    st.session_state["character_list"] = default_data["character_list"]
if "volumes_list" not in st.session_state:
    st.session_state["volumes_list"] = default_data["volumes_list"]
if "chapters_list" not in st.session_state:
    st.session_state["chapters_list"] = default_data["chapters_list"]

# ================= 頂部：檔案匯入/匯出控制區 =================
st.subheader("💾 紀錄與存檔管理")
col_file1, col_file2 = st.columns(2)

with col_file1:
    uploaded_file = st.file_uploader("📤 匯入歷史設定檔 (.json)", type=["json"])
    if uploaded_file is not None:
        try:
            loaded_data = json.load(uploaded_file)
            default_data.update(loaded_data)
            if "character_list" in loaded_data:
                st.session_state["character_list"] = loaded_data["character_list"]
            if "volumes_list" in loaded_data:
                st.session_state["volumes_list"] = loaded_data["volumes_list"]
            if "chapters_list" in loaded_data:
                st.session_state["chapters_list"] = loaded_data["chapters_list"]
            st.success("✅ 成功載入全書歷史紀錄！")
        except Exception as e:
            st.error(f"檔案格式錯誤：{str(e)}")

# ================= 側邊欄：全書宇宙觀、線索庫與角色卡 =================
with st.sidebar:
    st.header("🌌 1. 全書頂層宇宙觀")
    book_title = st.text_input("全書書名", value=default_data["book_title"])
    book_theme = st.text_input("全書題材/風格", value=default_data["book_theme"])
    book_overall_secret = st.text_area("🔒 全書終局真相 (AI 參考)", value=default_data["book_overall_secret"], height=70)
    
    st.divider()
    st.subheader("🧩 規則與線索庫 (克蘇魯/懸疑對照)")
    confirmed_rules = st.text_area("✅ 已驗證鐵律", value=default_data["confirmed_rules"], height=80)
    unverified_hypotheses = st.text_area("❓ 未驗證假說 (推測)", value=default_data["unverified_hypotheses"], height=80)
    clues_inventory = st.text_area("🔍 當前關鍵線索庫", value=default_data["clues_inventory"], height=80)

    st.divider()
    
    # 多集規劃
    col_v_title, col_v_add = st.columns([3, 1])
    with col_v_title: st.subheader("📚 各集規劃庫")
    with col_v_add:
        if st.button("➕ 集"):
            new_v_id = f"v_{int(datetime.now().timestamp())}"
            st.session_state["volumes_list"].append({"id": new_v_id, "title": f"第 {len(st.session_state['volumes_list'])+1} 集", "target_words": 100000, "summary": "大綱..."})
            st.rerun()

    volumes_summary_text = ""
    for v_idx, vol in enumerate(st.session_state["volumes_list"]):
        with st.expander(f"📘 {vol['title']}", expanded=False):
            vol['title'] = st.text_input("本集名稱", value=vol['title'], key=f"v_title_{vol['id']}")
            vol['target_words'] = st.number_input("目標字數", value=vol['target_words'], step=10000, key=f"v_words_{vol['id']}")
            vol['summary'] = st.text_area("主線大綱", value=vol['summary'], height=70, key=f"v_sum_{vol['id']}")
            if st.button("🗑️ 刪除", key=f"v_del_{vol['id']}"):
                st.session_state["volumes_list"].pop(v_idx)
                st.rerun()
        volumes_summary_text += f"• {vol['title']}: {vol['summary']}\n"

    st.divider()
    
    # 動態角色卡片清單 (含 SAN 值)
    col_char_title, col_char_add = st.columns([3, 1])
    with col_char_title: st.subheader("👥 角色卡片庫")
    with col_char_add:
        if st.button("➕ 角色"):
            new_c_id = f"c_{int(datetime.now().timestamp())}"
            st.session_state["character_list"].append({"id": new_c_id, "name": "新角色", "relation": "關係", "summary": "簡介...", "entry_chap": 1, "exit_chap": "未定", "personality": "性格", "status": "狀態", "sanity": "100%", "speech_style": "口吻"})
            st.rerun()

    updated_characters_text = ""
    for c_idx, char in enumerate(st.session_state["character_list"]):
        with st.expander(f"👤 {char['name']} ({char['relation']})", expanded=False):
            st.caption(f"💡 {char['summary']}")
            char['name'] = st.text_input("名稱", value=char['name'], key=f"c_name_{char['id']}")
            char['relation'] = st.text_input("關係", value=char['relation'], key=f"c_rel_{char['id']}")
            char['summary'] = st.text_input("簡介", value=char['summary'], key=f"c_sum_{char['id']}")
            char['personality'] = st.text_input("性格", value=char['personality'], key=f"c_per_{char['id']}")
            char['status'] = st.text_input("🩸 生理狀態", value=char['status'], key=f"c_stat_{char['id']}")
            char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_san_{char['id']}")
            char['speech_style'] = st.text_input("口吻風格", value=char['speech_style'], key=f"c_speech_{char['id']}")
            if st.button("🗑️ 刪除", key=f"c_del_{char['id']}"):
                st.session_state["character_list"].pop(c_idx)
                st.rerun()
        updated_characters_text += f"【{char['name']} ({char['relation']})】\n• 簡介：{char['summary']}\n• 性格：{char['personality']}\n• 生理狀態：{char['status']} | SAN值：{char.get('sanity', '100%')}\n• 口吻：{char['speech_style']}\n---\n"

# ================= 主畫面：章節目錄庫與單章創作 =================
st.subheader(f"📖 2. 當前撰寫：{book_title}")

with st.expander("📑 章節目錄大綱清單 (預寫與對照區)", expanded=False):
    col_ch_t, col_ch_a = st.columns([3, 1])
    with col_ch_t: st.write("預先規劃各章大綱：")
    with col_ch_a:
        if st.button("➕ 新增章節"):
            next_num = len(st.session_state["chapters_list"]) + 1
            st.session_state["chapters_list"].append({"num": next_num, "title": f"第 {next_num} 章", "summary": "大綱..."})
            st.rerun()
            
    for ch_idx, ch in enumerate(st.session_state["chapters_list"]):
        col_c1, col_c2, col_c3 = st.columns([1, 2, 4])
        with col_c1: ch['num'] = st.number_input("章號", value=ch['num'], key=f"ch_num_{ch_idx}")
        with col_c2: ch['title'] = st.text_input("標題", value=ch['title'], key=f"ch_title_{ch_idx}")
        with col_c3: ch['summary'] = st.text_input("簡要大綱", value=ch['summary'], key=f"ch_sum_{ch_idx}")

st.divider()

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    vol_options = [v['title'] for v in st.session_state['volumes_list']]
    current_vol_title = st.selectbox("🎯 當前集數", vol_options if vol_options else ["第一集：失聲火車"])
with col_m2: current_chap = st.number_input("目前章節", value=default_data["current_chap"], min_value=1)
with col_m3: total_chaps = st.number_input("預估總章數", value=default_data["total_chaps"], min_value=1)
with col_m4: target_chapter_words = st.number_input("🎯 本章目標字數", value=default_data["target_chapter_words"], step=500)

time_and_environment = st.text_input("⏱️ 當前故事時間線與環境狀況", value=default_data["time_and_environment"])

col_s1, col_s2 = st.columns(2)
with col_s1:
    pov_list = ["第一人稱 (蘇默視角)", "第三人稱限制視角", "第三人稱全知視角"]
    pov_setting = st.selectbox("👁️ 寫作視角", pov_list, index=0)
with col_s2: tone_setting = st.text_input("🎭 本章情緒基調", value=default_data["tone_setting"])

st.divider()

col_l, col_r = st.columns(2)
with col_l:
    previous_summary = st.text_area("📌 上一章結尾錨點 (銜接點)", value=default_data["previous_summary"], height=100)
    scene_conflict = st.text_area("⚔️ 本章核心衝突點", value=default_data["scene_conflict"], height=90)
    must_include = st.text_area("🔑 必須出現的伏筆/道具", value=default_data["must_include"], height=90)

with col_r:
    chapter_outline = st.text_area("🎯 本章具體大綱與情節推進", value=default_data["chapter_outline"], height=100)
    scene_turn = st.text_area("🔄 本章局勢/認知大翻轉 (Turn)", value=default_data["scene_turn"], height=90)
    writing_taboos = st.text_area("🚫 寫作禁忌 (Negative Prompt)", value=default_data["writing_taboos"], height=90)

generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

if "generated_text" not in st.session_state:
    st.session_state["generated_text"] = default_data.get("generated_content", "")

# ================= 生成與成果展示 =================
if generate_btn:
    st.markdown("---")
    st.subheader("📝 本章生成成果：")
    
    combined_chapter_outline = f"""
    【本章大綱】：{chapter_outline}
    【目標字數】：約 {target_chapter_words} 字
    【故事時間線與環境】：{time_and_environment}
    【寫作視角】：{pov_setting} | 【情緒基調】：{tone_setting}
    【核心衝突】：{scene_conflict}
    【局勢/認知翻轉】：{scene_turn}
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
    【各集結構總覽】：
    {volumes_summary_text}
    """
    
    payload = {
        "volume_title": current_vol_title,
        "target_volume_words": 100000,
        "current_chapter": current_chap,
        "total_chapters": total_chaps,
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
        "volumes_list": st.session_state["volumes_list"],
        "character_list": st.session_state["character_list"],
        "chapters_list": st.session_state["chapters_list"],
        "current_vol_title": current_vol_title,
        "current_chap": current_chap,
        "total_chaps": total_chaps,
        "target_chapter_words": target_chapter_words,
        "time_and_environment": time_and_environment,
        "pov_setting": pov_setting,
        "tone_setting": tone_setting,
        "previous_summary": previous_summary,
        "scene_conflict": scene_conflict,
        "scene_turn": scene_turn,
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
