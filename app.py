import streamlit as st
import requests
import json
from datetime import datetime

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

st.title("✍️ 專業小說家 AI 寫作工作站")
st.caption("具備長篇結構控管、動態角色卡片管理、伏筆錨點與 JSON 存檔功能的寫作介面")

# 設定 Render API 網址
API_URL = "https://novel-ai-api-himy.onrender.com/v1/chapter/stream"

# ================= 預設資料與角色清單初始化 =================
default_data = {
    "volume_title": "第一集：失聲火車",
    "target_volume_words": 100000,
    "current_chap": 6,
    "total_chaps": 30,
    "volume_overall_outline": """【失聲火車主線】
主角蘇默在陷入時間停滯與無聲鐵律的列車中醒來，必須利用理工物理知識推演規則邊界，與夥伴林欣合作，並透過 13 車車票與 1% 電量手機，在必死事故中尋找逆向解謎的唯一生路。""",
    "previous_volumes_summary": """1. 蘇默與林欣確認了「無聲鐵律」存在，全車均持 13 車車票。
2. 阿豪已發聲陣亡（已死）；西裝男半身麻痺昏迷。
3. 蘇默的手機電量鎖定在 1%，為永久規則標記。""",
    "story_bg": "列車陷入絕對死寂，時間停滯，手機電量是唯一的生命線。",
    "target_chapter_words": 3300,
    "pov_setting": "第一人稱 (蘇默視角)",
    "tone_setting": "極度壓抑、懸疑冷酷、理性推算",
    "previous_summary": "上一章（第 5 章）結尾：蘇默盯著手機螢幕上常駐的 1% 電量，突然發現畫面上閃爍出一條未知微波訊號，前方鐵門傳來輕微扣擊聲...",
    "must_include": "• 手機 1% 電量接收到的神祕微波數據\n• 車廂鐵門上的刺鼻金屬鏽蝕味",
    "chapter_outline": "第六章：蘇默與林欣戒備地靠近鐵門，透過門縫觀察前方車廂，同時蘇默嘗試解析手機接收到的神秘訊號。",
    "writing_taboos": "• 禁止出現感性說教台詞\n• 禁止主角無故陷入驚慌失措\n• 對話需簡短、注重環境物理描寫",
    "generated_content": ""
}

# 預設角色結構化列表
default_character_list = [
    {
        "id": "c1",
        "name": "蘇默",
        "relation": "主角本人",
        "summary": "冷靜理工男，善於利用物理知識與環境細節推算規則邊界。",
        "entry_chap": 1,
        "exit_chap": "存活至最後",
        "personality": "極度理智、數據導向、冷靜、理性大於感性",
        "status": "健康，手機電量永久鎖定在 1% (規則標記)",
        "speech_style": "簡短、條理分明、習慣用數據與物理現象分析局勢"
    },
    {
        "id": "c2",
        "name": "林欣",
        "relation": "生死求生夥伴",
        "summary": "細心的女性求生者，提供物資調配與心理支柱。",
        "entry_chap": 2,
        "exit_chap": "預估第 25 章",
        "personality": "細心、共情能力強、直覺敏銳",
        "status": "極度疲憊，輕微精神衰弱",
        "speech_style": "輕聲細語、著重情感與直覺反應"
    },
    {
        "id": "c3",
        "name": "西裝男",
        "relation": "暫時合作對象 / 不確定因素",
        "summary": "因規則陷入半身麻痺的神秘乘客，能感應死寂頻率。",
        "entry_chap": 1,
        "exit_chap": "預估第 15 章",
        "personality": "自私功利，但在死亡威脅下願意配合",
        "status": "半身麻痺異變，可感應微波頻率，目前處於昏迷弱化狀態",
        "speech_style": "沙啞、斷斷續續、帶有焦慮與戒心"
    },
    {
        "id": "c4",
        "name": "阿豪",
        "relation": "前期車廂乘客 (已陣亡)",
        "summary": "餐車廂極度驚恐的乘客，因違規發聲遭吞噬。",
        "entry_chap": 1,
        "exit_chap": "第 4 章 (已陣亡)",
        "personality": "極度恐慌、情緒失控",
        "status": "確定死亡 (不可出現在當前場景)",
        "speech_style": "結巴、哀求、驚恐慘叫"
    }
]

# Session State 初始化
if "character_list" not in st.session_state:
    st.session_state["character_list"] = default_character_list

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
            st.success("✅ 成功載入歷史紀錄與角色卡清單！")
        except Exception as e:
            st.error(f"檔案格式錯誤：{str(e)}")

# ================= 側邊欄：宏觀架構與動態角色卡管理 =================
with st.sidebar:
    st.header("📚 1. 宏觀架構 (本冊/全書設定)")
    volume_title = st.text_input("本冊/本集名稱", value=default_data["volume_title"])
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        target_volume_words = st.number_input("本集目標總字數", value=default_data["target_volume_words"], step=10000)
        current_chap = st.number_input("目前撰寫章節", value=default_data["current_chap"], min_value=1)
    with col_v2:
        total_chaps = st.number_input("預估本集總章數", value=default_data["total_chaps"], min_value=1)
        suggested_words = int(target_volume_words / total_chaps)
        st.info(f"💡 建議單章字數：約 {suggested_words} 字")
        
    st.divider()
    
    volume_overall_outline = st.text_area("🗺️ 本集整體大綱與核心主線", value=default_data["volume_overall_outline"], height=120)
    previous_volumes_summary = st.text_area("📜 既定歷史與前情總結 (AI 不可違背)", value=default_data["previous_volumes_summary"], height=120)
    story_bg = st.text_area("🌌 世界觀與運作鐵律", value=default_data["story_bg"], height=80)
    
    st.divider()
    
    # ---------------- 互動式角色卡清單區 ----------------
    col_char_title, col_char_add = st.columns([3, 1])
    with col_char_title:
        st.subheader("👥 角色清單庫")
    with col_char_add:
        if st.button("➕ 新增", help="點擊新增一位角色"):
            new_id = f"c_{int(datetime.now().timestamp())}"
            st.session_state["character_list"].append({
                "id": new_id,
                "name": "新角色名稱",
                "relation": "與主角關係",
                "summary": "一句話簡介（方便快速識別）",
                "entry_chap": current_chap,
                "exit_chap": "未定",
                "personality": "性格特質",
                "status": "當前生理/異變狀態",
                "speech_style": "對話/口吻風格"
            })
            st.rerun()

    # 渲染卡片式可折疊角色列表
    updated_characters_text = ""
    for idx, char in enumerate(st.session_state["character_list"]):
        header_label = f"👤 {char['name']} ({char['relation']})"
        with st.expander(header_label, expanded=False):
            st.caption(f"💡 **簡介**：{char['summary']}")
            
            char['name'] = st.text_input("角色名稱", value=char['name'], key=f"name_{char['id']}")
            char['relation'] = st.text_input("與主角關係", value=char['relation'], key=f"rel_{char['id']}")
            char['summary'] = st.text_input("一句話簡介 (顯示於封面下欄)", value=char['summary'], key=f"sum_{char['id']}")
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                char['entry_chap'] = st.text_input("登場章節", value=str(char['entry_chap']), key=f"entry_{char['id']}")
            with c_col2:
                char['exit_chap'] = st.text_input("預計退場/陣亡章節", value=str(char['exit_chap']), key=f"exit_{char['id']}")
                
            char['personality'] = st.text_area("性格特質", value=char['personality'], height=70, key=f"per_{char['id']}")
            char['status'] = st.text_area("🩸 當前生理 / 異變狀態", value=char['status'], height=70, key=f"stat_{char['id']}")
            char['speech_style'] = st.text_input("對話 / 口吻風格", value=char['speech_style'], key=f"speech_{char['id']}")
            
            if st.button("🗑️ 刪除此角色", key=f"del_{char['id']}"):
                st.session_state["character_list"].pop(idx)
                st.rerun()

        # 自動組裝發送給 AI 的提示文字
        updated_characters_text += f"""
【角色：{char['name']}】
• 關係：{char['relation']} | 簡介：{char['summary']}
• 登場：第 {char['entry_chap']} 章 | 退場：{char['exit_chap']}
• 性格：{char['personality']}
• 當前生理/異變狀態：{char['status']}
• 說話風格：{char['speech_style']}
---
"""

# ================= 主畫面：微觀單章寫作與控管 =================
st.subheader(f"📖 2. 微觀寫作：{volume_title} — 第 {current_chap} 章 / 共 {total_chaps} 章")

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    target_chapter_words = st.number_input("🎯 本章目標字數", value=default_data.get("target_chapter_words", suggested_words), step=500)
with col_m2:
    pov_list = ["第一人稱 (蘇默視角)", "第三人稱限制視角", "第三人稱全知視角"]
    pov_index = pov_list.index(default_data["pov_setting"]) if default_data["pov_setting"] in pov_list else 0
    pov_setting = st.selectbox("👁️ 寫作視角", pov_list, index=pov_index)
with col_m3:
    tone_setting = st.text_input("🎭 本章情緒基調", value=default_data["tone_setting"])

st.divider()

col_l, col_r = st.columns(2)
with col_l:
    previous_summary = st.text_area("📌 上一章結尾錨點 (畫面/局勢銜接點)", value=default_data["previous_summary"], height=120)
    must_include = st.text_area("🔑 本章必須出現的伏筆/關鍵道具", value=default_data["must_include"], height=100)

with col_r:
    chapter_outline = st.text_area("🎯 本章具體大綱與情節推進", value=default_data["chapter_outline"], height=120)
    writing_taboos = st.text_area("🚫 寫作禁忌與風格避雷 (Negative Prompt)", value=default_data["writing_taboos"], height=100)

generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

# 用於儲存生成結果
if "generated_text" not in st.session_state:
    st.session_state["generated_text"] = default_data.get("generated_content", "")

# ================= 生成與成果展示 =================
if generate_btn:
    st.markdown("---")
    st.subheader("📝 本章生成成果：")
    
    combined_chapter_outline = f"""
    【本章大綱】：{chapter_outline}
    【本章目標字數】：約 {target_chapter_words} 字
    【寫作視角】：{pov_setting}
    【情緒基調】：{tone_setting}
    【必須包含的伏筆/道具】：
    {must_include}
    【寫作禁忌與避雷】：
    {writing_taboos}
    """
    
    combined_background = f"""
    【世界觀與鐵律】：
    {story_bg}
    【本集整體大綱】：
    {volume_overall_outline}
    """
    
    payload = {
        "volume_title": volume_title,
        "target_volume_words": target_volume_words,
        "current_chapter": current_chap,
        "total_chapters": total_chaps,
        "previous_volumes_summary": previous_volumes_summary,
        "story_background": combined_background,
        "character_profiles": updated_characters_text, # 傳入動態組裝的角色陣容
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

# 展示目前的文字成果並提供下載按鈕
if st.session_state["generated_text"]:
    if not generate_btn:
        st.markdown("---")
        st.subheader("📝 本章生成成果（目前紀錄）：")
        st.write(st.session_state["generated_text"])

    current_export_data = {
        "volume_title": volume_title,
        "target_volume_words": target_volume_words,
        "current_chap": current_chap,
        "total_chapters": total_chaps,
        "volume_overall_outline": volume_overall_outline,
        "previous_volumes_summary": previous_volumes_summary,
        "story_bg": story_bg,
        "character_list": st.session_state["character_list"], # 存檔時保存完整角色卡結構
        "target_chapter_words": target_chapter_words,
        "pov_setting": pov_setting,
        "tone_setting": tone_setting,
        "previous_summary": previous_summary,
        "must_include": must_include,
        "chapter_outline": chapter_outline,
        "writing_taboos": writing_taboos,
        "generated_content": st.session_state["generated_text"],
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    json_string = json.dumps(current_export_data, ensure_ascii=False, indent=2)
    filename = f"{volume_title}_第{current_chap}章_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    with col_file2:
        st.download_button(
            label="📥 下載當前設定與草稿 (.json)",
            data=json_string,
            file_name=filename,
            mime="application/json"
        )
