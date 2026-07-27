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
    * {
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }
    .stMarkdown p {
        font-size: 1.05rem !important;
        line-height: 1.8 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✍️ 專業小說家 AI 全書寫作工作站")
st.caption("主頁面分頁極簡架構（直連 Gemini Flash API） | 100% 通用現有 JSON 存檔")

# ================= 預設資料初始化 =================
default_data = {
  "book_title": "《失號領域》",
  "book_theme": "懸疑 / 克蘇魯 / 規則怪談 / 物理解謎",
  "book_overall_secret": "希靈帝國在阻止虛空大災變的過程中，意外聯絡上虛空背面的神族，得知虛空大災變真相為虛空雙向歸零的機制。",
  "confirmed_rules_list": [{"id": "r1", "content": "絕不可發聲或製造空氣震動（違者觸發黑液與菌絲吞噬）。"}],
  "hypotheses_list": [],
  "clues_list": [{"id": "cl1", "content": "收到驚慌簡訊，說明車上有東西一直發出聲音。"}],
  "items_inventory": [
    {"id": "it1", "name": "蘇默的手機", "status": "時間鎖死在 06:52，電量約93%", "owner": "蘇默"},
    {"id": "it2", "name": "蘇默的背包", "status": "裡面放著大學新生會攜帶的東西", "owner": "蘇默"}
  ],
  "location_list": [
    {
      "id": "loc1",
      "name": "失聲列車（共12節車廂）",
      "scope": "第一集主要活動範圍",
      "visual_style": "20世紀貴族風格木製裝潢",
      "physics_detail": "時間鎖死在 06:52",
      "local_rules": "絕不可發聲"
    }
  ],
  "volumes_list": [{"id": "v1", "title": "第一集：失聲火車", "target_words": 100000, "summary": "求生指南"}],
  "character_list": [
    {
      "id": "c1", "name": "蘇默", "category": "當前在場/主要角色", "faction": "理工科大學新生",
      "public_relation": "主角本人", "hidden_motive": "求生", "summary": "習慣在內心吐槽的大一新生",
      "personality": "理智、數據導向", "status": "健康", "sanity": "84%", "speech_style": "簡潔", "dialogue_example": "「06:52，時間沒動。」"
    }
  ],
  "chapters_list": [],
  "current_vol_title": "第一集：失聲火車",
  "current_chap": 2,
  "target_chapter_words": 4000,
  "time_and_environment": "現實錨點：06:52",
  "pacing_setting": "中速推演 (解謎/搜查/對話)",
  "sensory_details": "",
  "pov_type": "第一人稱",
  "pov_character": "蘇默",
  "tone_setting": "極度壓抑、懸疑冷酷",
  "previous_summary": "",
  "scene_conflict": "",
  "scene_turn": "",
  "reveal_and_mystery": "",
  "must_include": "",
  "chapter_outline": "",
  "writing_taboos": "• 禁止任何角色開口發聲說話\n• 寫作禁止直接稱呼克系",
  "generated_content": ""
}

# 全域數據綁定
if "app_data" not in st.session_state:
    st.session_state["app_data"] = default_data
if "last_uploaded_filename" not in st.session_state:
    st.session_state["last_uploaded_filename"] = None

app_data = st.session_state["app_data"]

# ================= 主頁面頂部：主分頁選單 =================
tab_main, tab_world, tab_items, tab_chars, tab_system = st.tabs([
    "✍️ 本章寫作控制台", 
    "🌌 世界觀與地圖庫", 
    "🎒 道具與規則案件牆", 
    "👥 角色卡片庫", 
    "💾 API 設定與存檔管理"
])

# ---------------- Tab 1: 本章寫作控制台 ----------------
with tab_main:
    st.subheader(f"📖 當前撰寫作品：{app_data.get('book_title', '未命名')}")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        app_data["current_vol_title"] = st.text_input("🎯 當前集數", value=app_data.get("current_vol_title", "第一集：失聲火車"))
    with col_m2:
        app_data["current_chap"] = st.number_input("目前章節", value=int(app_data.get("current_chap", 1)), min_value=1)
    with col_m3:
        app_data["target_chapter_words"] = st.number_input("🎯 本章目標字數", value=int(app_data.get("target_chapter_words", 3000)), step=500)

    app_data["previous_summary"] = st.text_area("📌 上一章結尾錨點 (銜接點)", value=app_data.get("previous_summary", ""), height=100)
    app_data["chapter_outline"] = st.text_area("🎯 本章具體大綱與情節推進 (主要寫作指令)", value=app_data.get("chapter_outline", ""), height=120)

    with st.expander("⚙️ 點此展開【本章進階微調參數】", expanded=False):
        char_names_list = [c.get('name', '蘇默') for c in app_data.get("character_list", [])]
        
        col_env1, col_env2, col_env3 = st.columns(3)
        with col_env1:
            pov_options = ["第一人稱", "第三人稱限制視角", "第三人稱全知視角"]
            cur_pov = app_data.get("pov_type", "第一人稱")
            pov_idx = pov_options.index(cur_pov) if cur_pov in pov_options else 0
            app_data["pov_type"] = st.selectbox("👁️ 視角類型", pov_options, index=pov_idx)
        with col_env2:
            cur_pov_char = app_data.get("pov_character", "蘇默")
            pchar_idx = char_names_list.index(cur_pov_char) if cur_pov_char in char_names_list else 0
            app_data["pov_character"] = st.selectbox("👤 描寫視角主角", char_names_list if char_names_list else ["蘇默"], index=pchar_idx)
        with col_env3:
            pacing_opts = ["中速推演 (解謎/搜查/對話)", "高速推進 (動作/戰鬥/逃跑)", "慢速壓抑 (鋪陳/恐懼/氛圍)"]
            cur_pacing = app_data.get("pacing_setting", "中速推演 (解謎/搜查/對話)")
            pace_idx = pacing_opts.index(cur_pacing) if cur_pacing in pacing_opts else 0
            app_data["pacing_setting"] = st.selectbox("⚡ 寫作節奏", pacing_opts, index=pace_idx)

        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            app_data["time_and_environment"] = st.text_input("⏱️ 時間線與環境狀態", value=app_data.get("time_and_environment", ""))
        with col_sub2:
            app_data["tone_setting"] = st.text_input("🎭 本章情緒基調", value=app_data.get("tone_setting", ""))

        app_data["sensory_details"] = st.text_area("🌫️ 五感描寫重點", value=app_data.get("sensory_details", ""), height=70)

        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            app_data["scene_conflict"] = st.text_area("⚔️ 本章核心衝突點", value=app_data.get("scene_conflict", ""), height=70)
            app_data["must_include"] = st.text_area("🔑 必須出現的伏筆/道具", value=app_data.get("must_include", ""), height=70)
        with col_adv2:
            app_data["scene_turn"] = st.text_area("🔄 本章局勢/認知大翻轉", value=app_data.get("scene_turn", ""), height=70)
            app_data["reveal_and_mystery"] = st.text_area("🔍 伏筆揭示與新未知懸念", value=app_data.get("reveal_and_mystery", ""), height=70)

        app_data["writing_taboos"] = st.text_area("🚫 寫作禁忌", value=app_data.get("writing_taboos", ""), height=70)

    st.divider()
    generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

# ---------------- Tab 2: 世界觀與地圖庫 ----------------
with tab_world:
    st.subheader("🌌 全書世界觀與地圖設定")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        app_data["book_title"] = st.text_input("全書書名", value=app_data.get("book_title", ""))
    with col_w2:
        app_data["book_theme"] = st.text_input("題材風格", value=app_data.get("book_theme", ""))
    
    app_data["book_overall_secret"] = st.text_area("🔒 全書終局真相", value=app_data.get("book_overall_secret", ""), height=100)
    
    st.divider()
    col_loc_t, col_loc_a = st.columns([3, 1])
    with col_loc_t: st.subheader("🗺️ 區域與地圖庫")
    with col_loc_a:
        if st.button("➕ 新增區域"):
            new_id = f"loc_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("location_list", []).append({
                "id": new_id, "name": "新區域", "scope": "適用範圍", "visual_style": "", "physics_detail": "", "local_rules": ""
            })
            st.rerun()

    loc_list = app_data.get("location_list", [])
    for loc_idx in range(len(loc_list) - 1, -1, -1):
        loc = loc_list[loc_idx]
        loc_id = loc.get("id", f"loc_{loc_idx}")
        with st.expander(f"📍 {loc.get('name', '區域')} ({loc.get('scope', '')})", expanded=True):
            loc['name'] = st.text_input("區域名稱", value=loc.get('name', ''), key=f"loc_n_{loc_id}")
            loc['scope'] = st.text_input("適用範圍", value=loc.get('scope', ''), key=f"loc_sc_{loc_id}")
            loc['visual_style'] = st.text_area("🏛️ 視覺與建築特色", value=loc.get('visual_style', ''), key=f"loc_vs_{loc_id}", height=60)
            loc['physics_detail'] = st.text_area("⚙️ 環境與物理異常", value=loc.get('physics_detail', ''), key=f"loc_pd_{loc_id}", height=60)
            loc['local_rules'] = st.text_area("🚫 區域專屬禁忌", value=loc.get('local_rules', ''), key=f"loc_lr_{loc_id}", height=60)
            if st.button("🗑️ 刪除此區域", key=f"loc_d_{loc_id}"):
                loc_list.pop(loc_idx)
                st.rerun()

# ---------------- Tab 3: 道具與規則案件牆 ----------------
with tab_items:
    st.subheader("🎒 道具庫與案件牆")
    
    # 道具庫
    col_it_t, col_it_a = st.columns([3, 1])
    with col_it_t: st.subheader("📦 可用道具庫")
    with col_it_a:
        if st.button("➕ 新增道具"):
            new_id = f"it_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("items_inventory", []).append({"id": new_id, "name": "新道具", "status": "", "owner": ""})
            st.rerun()

    items_list = app_data.get("items_inventory", [])
    for it_idx in range(len(items_list) - 1, -1, -1):
        item = items_list[it_idx]
        item_id = item.get("id", f"it_{it_idx}")
        with st.expander(f"📦 {item.get('name', '道具')} ({item.get('owner', '')})", expanded=True):
            item['name'] = st.text_input("名稱", value=item.get('name', ''), key=f"it_n_{item_id}")
            item['owner'] = st.text_input("持有者", value=item.get('owner', ''), key=f"it_o_{item_id}")
            item['status'] = st.text_input("狀態", value=item.get('status', ''), key=f"it_s_{item_id}")
            if st.button("🗑️ 刪除此道具", key=f"it_d_{item_id}"):
                items_list.pop(it_idx)
                st.rerun()

    st.divider()
    
    # 鐵律、假說、線索
    col_r_t, col_r_a = st.columns([3, 1])
    with col_r_t: st.subheader("✅ 已驗證鐵律")
    with col_r_a:
        if st.button("➕ 新增鐵律"):
            new_id = f"r_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("confirmed_rules_list", []).append({"id": new_id, "content": ""})
            st.rerun()
            
    rules_list = app_data.get("confirmed_rules_list", [])
    for r_idx in range(len(rules_list) - 1, -1, -1):
        r = rules_list[r_idx]
        r_id = r.get("id", f"r_{r_idx}")
        col_rx, col_rd = st.columns([5, 1])
        with col_rx: r['content'] = st.text_input(f"鐵律 {r_idx+1}", value=r.get('content', ''), key=f"r_val_{r_id}", label_visibility="collapsed")
        with col_rd:
            if st.button("🗑️", key=f"r_del_{r_id}"):
                rules_list.pop(r_idx)
                st.rerun()

    col_cl_t, col_cl_a = st.columns([3, 1])
    with col_cl_t: st.subheader("🔍 關鍵線索庫")
    with col_cl_a:
        if st.button("➕ 新增線索"):
            new_id = f"cl_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("clues_list", []).append({"id": new_id, "content": ""})
            st.rerun()

    clues_list = app_data.get("clues_list", [])
    for cl_idx in range(len(clues_list) - 1, -1, -1):
        cl = clues_list[cl_idx]
        cl_id = cl.get("id", f"cl_{cl_idx}")
        col_clx, col_cld = st.columns([5, 1])
        with col_clx: cl['content'] = st.text_input(f"線索 {cl_idx+1}", value=cl.get('content', ''), key=f"cl_val_{cl_id}", label_visibility="collapsed")
        with col_cld:
            if st.button("🗑️", key=f"cl_del_{cl_id}"):
                clues_list.pop(cl_idx)
                st.rerun()

# ---------------- Tab 4: 角色卡片庫 ----------------
with tab_chars:
    col_char_t, col_char_a = st.columns([3, 1])
    with col_char_t: st.subheader("👥 角色卡片庫")
    with col_char_a:
        if st.button("➕ 新增角色"):
            new_c_id = f"c_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("character_list", []).append({
                "id": new_c_id, "name": "新角色", "category": "當前在場/主要角色", 
                "faction": "", "public_relation": "", "hidden_motive": "",
                "summary": "", "personality": "", "status": "", "sanity": "100%", "speech_style": "", "dialogue_example": ""
            })
            st.rerun()

    tab_c1, tab_c2, tab_c3 = st.tabs(["🔥 在場/主要", "📡 場外/通訊", "🪦 離場/變異"])
    categories = {"當前在場/主要角色": tab_c1, "場外/通訊角色": tab_c2, "離場/變異/歷史角色": tab_c3}
    
    char_list = app_data.get("character_list", [])
    
    for c_idx in range(len(char_list) - 1, -1, -1):
        char = char_list[c_idx]
        c_id = char.get("id", f"c_{c_idx}")
        
        c_cat = char.get('category', '當前在場/主要角色')
        target_tab = categories.get(c_cat, tab_c1)
        
        with target_tab:
            with st.expander(f"👤 {char.get('name', '角色')} ({char.get('faction', '無陣營')})", expanded=True):
                char['name'] = st.text_input("名稱", value=char.get('name', ''), key=f"c_n_{c_id}")
                char['category'] = st.selectbox("📌 歸類分頁", ["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"], index=["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"].index(c_cat) if c_cat in ["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"] else 0, key=f"c_cat_{c_id}")
                char['faction'] = st.text_input("⚔️ 勢力/陣營", value=char.get('faction', ''), key=f"c_f_{c_id}")
                char['public_relation'] = st.text_input("🤝 表面關係", value=char.get('public_relation', ''), key=f"c_pr_{c_id}")
                char['hidden_motive'] = st.text_input("🔒 隱藏動機/暗流", value=char.get('hidden_motive', ''), key=f"c_hm_{c_id}")
                char['summary'] = st.text_input("簡介", value=char.get('summary', ''), key=f"c_s_{c_id}")
                char['personality'] = st.text_input("性格", value=char.get('personality', ''), key=f"c_p_{c_id}")
                char['status'] = st.text_input("🩸 生理狀態", value=char.get('status', ''), key=f"c_st_{c_id}")
                char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_sn_{c_id}")
                char['speech_style'] = st.text_input("口吻風格", value=char.get('speech_style', ''), key=f"c_sp_{c_id}")
                char['dialogue_example'] = st.text_input("💬 代表台詞", value=char.get('dialogue_example', ''), key=f"c_dg_{c_id}")
                if st.button("🗑️ 刪除角色", key=f"c_dl_{c_id}"):
                    char_list.pop(c_idx)
                    st.rerun()

# ---------------- Tab 5: API 設定與存檔管理 ----------------
with tab_system:
    st.subheader("💾 系統設定與存檔管理")
    
    st.markdown("### 🔑 API Key 設定")
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("輸入 Gemini API Key", value=env_api_key, type="password")
    active_api_key = api_key_input if api_key_input else env_api_key
    
    st.divider()
    st.markdown("### 📤 匯入歷史設定檔 (.json)")
    uploaded_file = st.file_uploader("選擇上傳 JSON 存檔", type=["json", "txt"])

    if uploaded_file is not None and uploaded_file.name != st.session_state["last_uploaded_filename"]:
        try:
            loaded_data = json.load(uploaded_file)
            st.session_state["app_data"] = loaded_data
            st.session_state["last_uploaded_filename"] = uploaded_file.name
            st.success("✅ 成功載入歷史紀錄！主頁面資料已全數同步！")
            st.rerun()
        except Exception as e:
            st.error(f"檔案格式錯誤：{str(e)}")

    st.divider()
    st.markdown("### 📥 下載當前全書設定檔 (.json)")
    app_data["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_string = json.dumps(app_data, ensure_ascii=False, indent=2)
    filename = f"{app_data.get('book_title', '小說')}_{app_data.get('current_vol_title', '第一集')}_第{app_data.get('current_chap', 1)}章.json"

    st.download_button(
        label="📥 下載當前設定檔 (.json)",
        data=json_string,
        file_name=filename,
        mime="application/json",
        use_container_width=True
    )

# ================= 自動構建 Prompt 文字 =================
locations_text = "".join([
    f"【{l.get('name', '')} ({l.get('scope', '')})】\n• 建築特色：{l.get('visual_style', '')}\n• 環境異常：{l.get('physics_detail', '')}\n• 區域規則：{l.get('local_rules', '')}\n---\n"
    for l in app_data.get("location_list", [])
])

items_text = "".join([
    f"• {i.get('name', '')} (持有:{i.get('owner', '')}): {i.get('status', '')}\n"
    for i in app_data.get("items_inventory", [])
])

rules_text = "".join([
    f"{idx+1}. {r.get('content', '')}\n"
    for idx, r in enumerate(app_data.get("confirmed_rules_list", []))
])

updated_characters_text = "".join([
    f"【{c.get('name', '')} ({c.get('faction', '')})】\n• 簡介：{c.get('summary', '')}\n• 狀態：{c.get('status', '')}\n---\n"
    for c in app_data.get("character_list", [])
])

# ================= 直連 Gemini API 生成邏輯 (鎖定 Flash 模型) =================
if generate_btn:
    if not active_api_key:
        st.error("❌ 找不到 Gemini API Key！請先在『💾 API 設定與存檔管理』頁面填入 Key。")
    else:
        st.markdown("---")
        st.subheader("📝 本章生成成果：")
        
        pov_type = app_data.get("pov_type", "第一人稱")
        pov_character = app_data.get("pov_character", "蘇默")

        if pov_type == "第一人稱":
            perspective_instruction = f"""
• 描寫視角：【第一人稱】
• 限制要求：你現在就是角色【{pov_character}】！必須全程以【{pov_character}】的第一人稱『我』進行寫作。
• 視角禁忌：嚴禁出現任何高維觀察者、系統監控日誌（如【監控端日誌】）、作者旁白或第三人稱視角。所有數據與狀態（如SAN值、心率）必須自然融入【{pov_character}】的個人體感與心理思考中。
"""
        else:
            perspective_instruction = f"""
• 描寫視角：【{pov_type}】(焦點角色：{pov_character})
• 限制要求：請以專業小說敘事者（旁白）的視角進行描寫，圍繞主角【{pov_character}】的行動與所見所聞展開。
• 視角禁忌：嚴禁輸出遊戲化/系統化的數據標籤（如【監控端日誌】、【SAN值評估】），請將數據轉化為小說中的客觀環境描寫與角色身體反應細節。
"""

        prompt = f"""
你是一位頂級的懸疑 / 克蘇魯 / 規則怪談小說作家。請根據以下完整的全書世界觀、區域設定與本章微調指令，為我撰寫小說最新一章的純內文。

【全書背景】
• 書名：{app_data.get('book_title')} ({app_data.get('book_theme')})
• 全書終局真相：{app_data.get('book_overall_secret')}

【區域與環境地圖設定】
{locations_text}

【規則與線索案件牆】
• 已驗證鐵律：
{rules_text}
• 當前可用道具庫：
{items_text}

【登場角色與複雜關係鏈】
{updated_characters_text}

【上一章銜接點】
{app_data.get('previous_summary')}

【本章撰寫精準指令】
• 當前章節：{app_data.get('current_vol_title')} 第 {app_data.get('current_chap')} 章
• 本章大綱：{app_data.get('chapter_outline')}
• 目標字數：約 {app_data.get('target_chapter_words')} 字
{perspective_instruction}
• 時間與環境：{app_data.get('time_and_environment')}
• 五感描寫重點：\n{app_data.get('sensory_details')}
• 核心衝突：{app_data.get('scene_conflict')}
• 認知大翻轉：{app_data.get('scene_turn')}
• 必須包含元素：\n{app_data.get('must_include')}
• 寫作禁忌 (Negative Prompt)：\n{app_data.get('writing_taboos')}

【寫作與格式極嚴格要求】
1. **直接輸出純小說內文**，不要帶有任何開場白、結語、分析文字或系統日誌標籤。
2. 保持極度壓抑、嚴密符合物理消能與規則怪談的氣氛。
3. 嚴格遵循「寫作禁忌」，特別是絕對不允許角色開口發聲說話。
"""

        try:
            genai.configure(api_key=active_api_key)
            
            # ⚡ 優先採用標準 API 上的 gemini-1.5-flash，若無則降級回退至 flash-latest，100% 能調通！
            target_model = "gemini-3.5-flash"
            try:
                model = genai.GenerativeModel(target_model)
                st.caption(f"⚡ 成功連線高速 Flash 模型：`{target_model}`")
            except Exception:
                target_model = "gemini-flash-latest"
                model = genai.GenerativeModel(target_model)
                st.caption(f"⚡ 自動切換連線模型：`{target_model}`")
            
            output_box = st.empty()
            full_text = ""
            text_buffer = ""
            
            # 🚀 平滑緩衝區渲染：每 20 個字刷新一次 UI，畫面順暢不卡頓
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    text_buffer += chunk.text
                    if len(text_buffer) >= 20:
                        output_box.markdown(full_text)
                        text_buffer = ""
            
            output_box.markdown(full_text)
            app_data["generated_content"] = full_text
            st.success("🎉 本章生成完成！")
            
        except Exception as e:
            st.error(f"Gemini API 呼叫失敗：{str(e)}")

# 展示生成的成果與複製功能
if app_data.get("generated_content"):
    st.markdown("---")
    st.subheader("📝 本章生成成果：")
    
    escaped_text = json.dumps(app_data["generated_content"])
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
    st.text_area("📋 複製專用純文字框", value=app_data["generated_content"], height=300)
    st.markdown("---")
    st.write(app_data["generated_content"])
