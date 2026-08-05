import streamlit as st
import json
import os
import google.generativeai as genai
from datetime import datetime

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

# 🔓 強制解鎖全頁面文字選取與複製 + 優化文字框換行排版
st.markdown("""
    <style>
    * {
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }
    .stMarkdown p {
        font-size: 1.1rem !important;
        line-height: 2.0 !important;
        margin-bottom: 1.2rem !important;
    }
    textarea {
        font-size: 1rem !important;
        line-height: 1.8 !important;
        white-space: pre-wrap !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("✍️ 專業小說家 AI 全書寫作工作站")
st.caption("主頁面分頁極簡架構（直連 Gemini Flash API） | 自動伏筆追蹤與長線管理 | 100% 通用現有 JSON 存檔")

# ================= 預設資料初始化 =================
default_data = {
  "book_title": "《失號領域》",
  "book_theme": "懸疑 / 克蘇魯 / 規則怪談 / 物理解謎",
  "book_overall_secret": "希靈帝國在阻止虛空大災變的過程中，意外聯絡上虛空背面的神族，得知虛空大災變真相為虛空雙向歸零的機制。",
  "confirmed_rules_list": [{"id": "r1", "content": "絕不可發聲或製造空氣震動（違者觸發黑液與菌絲吞噬）。"}],
  "hypotheses_list": [],
  "clues_list": [{"id": "cl1", "content": "收到驚慌簡訊，說明車上有東西一直發出聲音。"}],
  "foreshadowing_list": [],
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
  "generated_content": "",
  "enable_new_foreshadow": True,
  "new_foreshadow_count": 1,
  "foreshadow_black_list": "• 禁止重複出現指針逆轉的懷錶/鐘錶類道具\n• 禁止重複出現吧台下的舊報紙/傳單線索\n• 禁止重複出現神秘簡訊突然警告/預警\n• 禁止重複出現牆壁/鏡面上的血字提示"
}

# 全域 Session State 數據與版本號綁定
if "app_data" not in st.session_state:
    st.session_state["app_data"] = default_data
if "last_uploaded_filename" not in st.session_state:
    st.session_state["last_uploaded_filename"] = None
if "upload_ver" not in st.session_state:
    st.session_state["upload_ver"] = 0
if "just_generated" not in st.session_state:
    st.session_state["just_generated"] = False
if "gen_time_key" not in st.session_state:
    st.session_state["gen_time_key"] = "initial"

app_data = st.session_state["app_data"]
ver = st.session_state["upload_ver"]

# ================= 主頁面頂部：主分頁選單 =================
tab_main, tab_foreshadow, tab_world, tab_items, tab_chars, tab_system = st.tabs([
    "✍️ 本章寫作控制台", 
    "🔮 長線伏筆與案件牆",
    "🌌 世界觀與地圖庫", 
    "🎒 道具與鐵律案件牆", 
    "👥 角色卡片庫", 
    "💾 API 設定與存檔管理"
])

# ---------------- Tab 1: 本章寫作控制台 ----------------
with tab_main:
    st.subheader(f"📖 當前撰寫作品：{app_data.get('book_title', '未命名')}")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        app_data["current_vol_title"] = st.text_input("🎯 當前集數", value=app_data.get("current_vol_title", "第一集：失聲火車"), key=f"cvt_{ver}")
    with col_m2:
        app_data["current_chap"] = st.number_input("目前章節", value=int(app_data.get("current_chap", 1)), min_value=1, key=f"cc_{ver}")
    with col_m3:
        app_data["target_chapter_words"] = st.number_input("🎯 本章目標字數", value=int(app_data.get("target_chapter_words", 3000)), step=500, key=f"tcw_{ver}")

    app_data["previous_summary"] = st.text_area("📌 上一章結尾錨點 (銜接點)", value=app_data.get("previous_summary", ""), height=100, key=f"ps_{ver}")
    app_data["chapter_outline"] = st.text_area("🎯 本章具體大綱與情節推進 (主要寫作指令)", value=app_data.get("chapter_outline", ""), height=120, key=f"co_{ver}")

    with st.expander("⚙️ 點此展開【本章進階微調參數】", expanded=False):
        # 🎯 伏筆策略與防重複黑名單設定
        st.markdown("#### 🔮 伏筆發想策略與【防重複黑名單】")
        col_f_opt1, col_f_opt2 = st.columns([2, 1])
        with col_f_opt1:
            app_data["enable_new_foreshadow"] = st.checkbox("☑️ 允許 AI 在本章創作時埋下新伏筆", value=app_data.get("enable_new_foreshadow", True), key=f"enf_{ver}")
        with col_f_opt2:
            app_data["new_foreshadow_count"] = st.number_input("🎯 預期新增伏筆數量", value=int(app_data.get("new_foreshadow_count", 1)), min_value=0, max_value=5, step=1, key=f"nfc_{ver}")

        app_data["foreshadow_black_list"] = st.text_area(
            "🚫 嚴禁重複出現的伏筆類型 / 老套路黑名單 (避免出戲)",
            value=app_data.get("foreshadow_black_list", "• 禁止重複出現懷錶/舊報紙/簡訊等老套路"),
            height=100,
            key=f"fbl_{ver}"
        )

        st.divider()

        char_names_list = [c.get('name', '蘇默') for c in app_data.get("character_list", [])]
        
        col_env1, col_env2, col_env3 = st.columns(3)
        with col_env1:
            pov_options = ["第一人稱", "第三人稱限制視角", "第三人稱全知視角"]
            cur_pov = app_data.get("pov_type", "第一人稱")
            pov_idx = pov_options.index(cur_pov) if cur_pov in pov_options else 0
            app_data["pov_type"] = st.selectbox("👁️ 視角類型", pov_options, index=pov_idx, key=f"pov_t_{ver}")
        with col_env2:
            cur_pov_char = app_data.get("pov_character", "蘇默")
            pchar_idx = char_names_list.index(cur_pov_char) if cur_pov_char in char_names_list else 0
            app_data["pov_character"] = st.selectbox("👤 描寫視角主角", char_names_list if char_names_list else ["蘇默"], index=pchar_idx, key=f"pov_c_{ver}")
        with col_env3:
            pacing_opts = ["中速推演 (解謎/搜查/對話)", "高速推進 (動作/戰鬥/逃跑)", "慢速壓抑 (鋪陳/恐懼/氛圍)"]
            cur_pacing = app_data.get("pacing_setting", "中速推演 (解謎/搜查/對話)")
            pace_idx = pacing_opts.index(cur_pacing) if cur_pacing in pacing_opts else 0
            app_data["pacing_setting"] = st.selectbox("⚡ 寫作節奏", pacing_opts, index=pace_idx, key=f"pacing_{ver}")

        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            app_data["time_and_environment"] = st.text_input("⏱️ 時間線與環境狀態", value=app_data.get("time_and_environment", ""), key=f"tae_{ver}")
        with col_sub2:
            app_data["tone_setting"] = st.text_input("🎭 本章情緒基調", value=app_data.get("tone_setting", ""), key=f"ts_{ver}")

        app_data["sensory_details"] = st.text_area("🌫️ 五感描寫重點", value=app_data.get("sensory_details", ""), height=70, key=f"sd_{ver}")

        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            app_data["scene_conflict"] = st.text_area("⚔️ 本章核心衝突點", value=app_data.get("scene_conflict", ""), height=70, key=f"sc_{ver}")
            app_data["must_include"] = st.text_area("🔑 必須出現的伏筆/道具", value=app_data.get("must_include", ""), height=70, key=f"mi_{ver}")
        with col_adv2:
            app_data["scene_turn"] = st.text_area("🔄 本章局勢/認知大翻轉", value=app_data.get("scene_turn", ""), height=70, key=f"st_{ver}")
            app_data["reveal_and_mystery"] = st.text_area("🔍 伏筆揭示與新未知懸念", value=app_data.get("reveal_and_mystery", ""), height=70, key=f"rm_{ver}")

        app_data["writing_taboos"] = st.text_area("🚫 寫作禁忌", value=app_data.get("writing_taboos", ""), height=150, key=f"wt_{ver}")

    st.divider()
    generate_btn = st.button("✨ 開始生成精緻小說內文", type="primary", use_container_width=True, key=f"gen_btn_{ver}")

    if st.session_state["just_generated"]:
        st.success("🎉 最新一章小說生成完成！已依據設定完成伏筆與內文同步！")
        st.session_state["just_generated"] = False

    if app_data.get("generated_content"):
        st.markdown("---")
        st.subheader("📝 最新生成成果：")
        
        current_gen_key = st.session_state["gen_time_key"]
        st.text_area(
            "📋 複製與編輯專用文字方塊 (已自動架構與斷行)", 
            value=app_data["generated_content"], 
            height=600, 
            key=f"res_ta_{current_gen_key}_{ver}"
        )
        
        st.markdown("---")
        st.markdown("### 📖 全章閱讀預覽 Mode：")
        st.markdown(app_data["generated_content"])

# ---------------- Tab 2: 長線伏筆與案件牆 (支援進度鎖與階段揭示目標) ----------------
with tab_foreshadow:
    st.subheader("🔮 長線伏筆與謎團策劃庫")
    st.caption("💡 這裡記錄了所有 AI 寫作時自動捕捉或由你手動創建的伏筆。你可以調整『解開進度鎖』與『本章揭露邊界』，精準控制劇透節奏！")
    
    col_f_t, col_f_a = st.columns([3, 1])
    with col_f_t: st.markdown("### 📜 全書伏筆追蹤清單")
    with col_f_a:
        if st.button("➕ 手動新增伏筆", key=f"add_f_btn_{ver}"):
            new_f_id = f"f_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("foreshadowing_list", []).append({
                "id": new_f_id,
                "content": "新伏筆表面現象...",
                "progress": "0% (剛埋下/僅現象)",
                "status": "未解答",
                "current_stage_goal": "僅維持現象描寫，絕對不可解開或劇透！",
                "truth": "背後隱藏的真實真相..."
            })
            st.rerun()

    f_list = app_data.get("foreshadowing_list", [])
    
    if not f_list:
        st.info("💡 目前尚無紀錄中的伏筆。按下生成小說按鈕時，AI 會依據你的設定自動記錄新伏筆至這裡！")
    else:
        tab_f1, tab_f2, tab_f3 = st.tabs(["📌 待解答/埋下中 (0%-20%)", "🔄 揭露中/推演中 (50%-80%)", "✅ 已完全回收 (100%)"])
        
        delete_target_id = None
        status_options = ["待解答 (0%-20%)", "揭露中/推演中 (50%-80%)", "已完全回收 (100%)"]
        progress_opts = ["0% (剛埋下/僅現象)", "20% (發現甜頭/微小異常)", "50% (產生第一層誤解/疑心)", "80% (假真相/第一重反轉)", "100% (完全回收/終極真相)"]
        
        for f_idx, f_item in enumerate(f_list):
            f_id = f_item.get("id", f"f_{f_idx}")
            status_str = f_item.get("status", "待解答")
            progress_str = f_item.get("progress", "0% (剛埋下/僅現象)")
            
            if "100%" in progress_str or "回收" in status_str or "已解答" in status_str:
                target_tab = tab_f3
            elif "50%" in progress_str or "80%" in progress_str or "揭露" in status_str or "推演" in status_str:
                target_tab = tab_f2
            else:
                target_tab = tab_f1

            with target_tab:
                title_preview = f_item.get('content', '未命名伏筆')
                if len(title_preview) > 25: title_preview = title_preview[:25] + "..."
                
                with st.expander(f"🔮 伏筆：{title_preview} 【進度：{progress_str}】", expanded=True):
                    f_item['content'] = st.text_input("📍 伏筆表面現象/描寫細節", value=f_item.get('content', ''), key=f"fc_{f_id}_{ver}")
                    
                    col_fs1, col_fs2 = st.columns([1, 2])
                    with col_fs1:
                        p_idx = progress_opts.index(progress_str) if progress_str in progress_opts else 0
                        f_item['progress'] = st.selectbox("📊 解開進度鎖", progress_opts, index=p_idx, key=f"fp_{f_id}_{ver}")
                    with col_fs2:
                        f_item['status'] = st.text_input("⏱️ 詳細狀態/預計解答章節", value=f_item.get('status', '未解答'), key=f"fs_{f_id}_{ver}")

                    f_item['current_stage_goal'] = st.text_area(
                        "🎯 本章允許揭露的邊界 (告訴 AI 本章只能寫到哪，嚴禁越界)", 
                        value=f_item.get('current_stage_goal', '僅維持現象描寫，絕對不可解開或劇透！'), 
                        height=65, 
                        key=f"fcg_{f_id}_{ver}"
                    )

                    f_item['truth'] = st.text_area("🔒 終極隱藏真相 (未達 100% 前 AI 嚴禁在文中劇透)", value=f_item.get('truth', ''), height=80, key=f"ft_{f_id}_{ver}")
                    
                    if st.button("🗑️ 刪除此伏筆", key=f"fd_{f_id}_{ver}"):
                        delete_target_id = f_id

        if delete_target_id:
            app_data["foreshadowing_list"] = [item for item in app_data["foreshadowing_list"] if item.get("id") != delete_target_id]
            st.rerun()

# ---------------- Tab 3: 世界觀與地圖庫 ----------------
with tab_world:
    st.subheader("🌌 全書世界觀與地圖設定")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        app_data["book_title"] = st.text_input("全書書名", value=app_data.get("book_title", ""), key=f"bt_{ver}")
    with col_w2:
        app_data["book_theme"] = st.text_input("題材風格", value=app_data.get("book_theme", ""), key=f"bth_{ver}")
    
    app_data["book_overall_secret"] = st.text_area("🔒 全書終局真相", value=app_data.get("book_overall_secret", ""), height=100, key=f"bos_{ver}")
    
    st.divider()
    col_loc_t, col_loc_a = st.columns([3, 1])
    with col_loc_t: st.subheader("🗺️ 區域與地圖庫")
    with col_loc_a:
        if st.button("➕ 新增區域", key=f"add_loc_btn_{ver}"):
            new_id = f"loc_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("location_list", []).append({
                "id": new_id, "name": "新區域", "scope": "適用範圍", "visual_style": "", "physics_detail": "", "local_rules": ""
            })
            st.rerun()

    loc_list = app_data.get("location_list", [])
    loc_del_id = None
    for loc_idx, loc in enumerate(loc_list):
        loc_id = loc.get("id", f"loc_{loc_idx}")
        with st.expander(f"📍 {loc.get('name', '區域')} ({loc.get('scope', '')})", expanded=True):
            loc['name'] = st.text_input("區域名稱", value=loc.get('name', ''), key=f"loc_n_{loc_id}_{ver}")
            loc['scope'] = st.text_input("適用範圍", value=loc.get('scope', ''), key=f"loc_sc_{loc_id}_{ver}")
            loc['visual_style'] = st.text_area("🏛️ 視覺與建築特色", value=loc.get('visual_style', ''), key=f"loc_vs_{loc_id}_{ver}", height=60)
            loc['physics_detail'] = st.text_area("⚙️ 環境與物理異常", value=loc.get('physics_detail', ''), key=f"loc_pd_{loc_id}_{ver}", height=60)
            loc['local_rules'] = st.text_area("🚫 區域專屬禁忌", value=loc.get('local_rules', ''), key=f"loc_lr_{loc_id}_{ver}", height=60)
            if st.button("🗑️ 刪除此區域", key=f"loc_d_{loc_id}_{ver}"):
                loc_del_id = loc_id
    if loc_del_id:
        app_data["location_list"] = [l for l in app_data["location_list"] if l.get("id") != loc_del_id]
        st.rerun()

# ---------------- Tab 4: 道具與規則案件牆 ----------------
with tab_items:
    st.subheader("🎒 道具庫與案件牆")
    
    col_it_t, col_it_a = st.columns([3, 1])
    with col_it_t: st.subheader("📦 可用道具庫")
    with col_it_a:
        if st.button("➕ 新增道具", key=f"add_it_btn_{ver}"):
            new_id = f"it_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("items_inventory", []).append({"id": new_id, "name": "新道具", "status": "", "owner": ""})
            st.rerun()

    items_list = app_data.get("items_inventory", [])
    it_del_id = None
    for it_idx, item in enumerate(items_list):
        item_id = item.get("id", f"it_{it_idx}")
        with st.expander(f"📦 {item.get('name', '道具')} ({item.get('owner', '')})", expanded=True):
            item['name'] = st.text_input("名稱", value=item.get('name', ''), key=f"it_n_{item_id}_{ver}")
            item['owner'] = st.text_input("持有者", value=item.get('owner', ''), key=f"it_o_{item_id}_{ver}")
            item['status'] = st.text_input("狀態", value=item.get('status', ''), key=f"it_s_{item_id}_{ver}")
            if st.button("🗑️ 刪除此道具", key=f"it_d_{item_id}_{ver}"):
                it_del_id = item_id
    if it_del_id:
        app_data["items_inventory"] = [i for i in app_data["items_inventory"] if i.get("id") != it_del_id]
        st.rerun()

    st.divider()
    
    col_r_t, col_r_a = st.columns([3, 1])
    with col_r_t: st.subheader("✅ 已驗證鐵律")
    with col_r_a:
        if st.button("➕ 新增鐵律", key=f"add_r_btn_{ver}"):
            new_id = f"r_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("confirmed_rules_list", []).append({"id": new_id, "content": ""})
            st.rerun()
            
    rules_list = app_data.get("confirmed_rules_list", [])
    r_del_id = None
    for r_idx, r in enumerate(rules_list):
        r_id = r.get("id", f"r_{r_idx}")
        col_rx, col_rd = st.columns([5, 1])
        with col_rx: r['content'] = st.text_input(f"鐵律 {r_idx+1}", value=r.get('content', ''), key=f"r_val_{r_id}_{ver}", label_visibility="collapsed")
        with col_rd:
            if st.button("🗑️", key=f"r_del_{r_id}_{ver}"):
                r_del_id = r_id
    if r_del_id:
        app_data["confirmed_rules_list"] = [r for r in app_data["confirmed_rules_list"] if r.get("id") != r_del_id]
        st.rerun()

    col_cl_t, col_cl_a = st.columns([3, 1])
    with col_cl_t: st.subheader("🔍 關鍵線索庫")
    with col_cl_a:
        if st.button("➕ 新增線索", key=f"add_cl_btn_{ver}"):
            new_id = f"cl_{datetime.now().strftime('%M%S%f')}"
            app_data.setdefault("clues_list", []).append({"id": new_id, "content": ""})
            st.rerun()

    clues_list = app_data.get("clues_list", [])
    cl_del_id = None
    for cl_idx, cl in enumerate(clues_list):
        cl_id = cl.get("id", f"cl_{cl_idx}")
        col_clx, col_cld = st.columns([5, 1])
        with col_clx: cl['content'] = st.text_input(f"線索 {cl_idx+1}", value=cl.get('content', ''), key=f"cl_val_{cl_id}_{ver}", label_visibility="collapsed")
        with col_cld:
            if st.button("🗑️", key=f"cl_del_{cl_id}_{ver}"):
                cl_del_id = cl_id
    if cl_del_id:
        app_data["clues_list"] = [c for c in app_data["clues_list"] if c.get("id") != cl_del_id]
        st.rerun()

# ---------------- Tab 5: 角色卡片庫 ----------------
with tab_chars:
    col_char_t, col_char_a = st.columns([3, 1])
    with col_char_t: st.subheader("👥 角色卡片庫")
    with col_char_a:
        if st.button("➕ 新增角色", key=f"add_c_btn_{ver}"):
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
    c_del_id = None
    
    for c_idx, char in enumerate(char_list):
        c_id = char.get("id", f"c_{c_idx}")
        c_cat = char.get('category', '當前在場/主要角色')
        target_tab = categories.get(c_cat, tab_c1)
        
        with target_tab:
            with st.expander(f"👤 {char.get('name', '角色')} ({char.get('faction', '無陣營')})", expanded=True):
                char['name'] = st.text_input("名稱", value=char.get('name', ''), key=f"c_n_{c_id}_{ver}")
                char['category'] = st.selectbox("📌 歸類分頁", ["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"], index=["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"].index(c_cat) if c_cat in ["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"] else 0, key=f"c_cat_{c_id}_{ver}")
                char['faction'] = st.text_input("⚔️ 勢力/陣營", value=char.get('faction', ''), key=f"c_f_{c_id}_{ver}")
                char['public_relation'] = st.text_input("🤝 表面關係", value=char.get('public_relation', ''), key=f"c_pr_{c_id}_{ver}")
                char['hidden_motive'] = st.text_input("🔒 隱藏動機/暗流", value=char.get('hidden_motive', ''), key=f"c_hm_{c_id}_{ver}")
                char['summary'] = st.text_input("簡介", value=char.get('summary', ''), key=f"c_s_{c_id}_{ver}")
                char['personality'] = st.text_input("性格", value=char.get('personality', ''), key=f"c_p_{c_id}_{ver}")
                char['status'] = st.text_input("🩸 生理狀態", value=char.get('status', ''), key=f"c_st_{c_id}_{ver}")
                char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_sn_{c_id}_{ver}")
                char['speech_style'] = st.text_input("口吻風格", value=char.get('speech_style', ''), key=f"c_sp_{c_id}_{ver}")
                char['dialogue_example'] = st.text_input("💬 代表台詞", value=char.get('dialogue_example', ''), key=f"c_dg_{c_id}_{ver}")
                if st.button("🗑️ 刪除角色", key=f"c_dl_{c_id}_{ver}"):
                    c_del_id = c_id
    if c_del_id:
        app_data["character_list"] = [c for c in app_data["character_list"] if c.get("id") != c_del_id]
        st.rerun()

# ---------------- Tab 6: API 設定與存檔管理 ----------------
with tab_system:
    st.subheader("💾 系統設定與存檔管理")
    
    st.markdown("### 🔑 API Key 設定")
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("輸入 Gemini API Key", value=env_api_key, type="password", key=f"api_{ver}")
    active_api_key = api_key_input if api_key_input else env_api_key
    
    st.divider()
    st.markdown("### 📤 匯入歷史設定檔 (.json)")
    uploaded_file = st.file_uploader("選擇上傳 JSON 存檔", type=["json", "txt"], key=f"uploader_{ver}")

    if uploaded_file is not None and uploaded_file.name != st.session_state["last_uploaded_filename"]:
        try:
            loaded_data = json.load(uploaded_file)
            st.session_state["app_data"] = loaded_data
            st.session_state["last_uploaded_filename"] = uploaded_file.name
            st.session_state["upload_ver"] += 1
            st.success("✅ 成功載入歷史紀錄！畫面與輸入框已強制同步更新！")
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
        use_container_width=True,
        key=f"dl_btn_{ver}"
    )

# ================= 自動構建 Prompt 文字 (強化伏筆進度鎖控制) =================
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

# 🔮 強化伏筆 Prompt：帶入 progress 與 current_stage_goal 鎖定邊界
foreshadowing_context = "".join([
    f"• [伏筆 ID: {f.get('id')}] 表面現象描述：{f.get('content')}\n"
    f"  - 📍 當前解開進度限制：【{f.get('progress', f.get('status', '0%'))}】\n"
    f"  - 🎯 本章允許揭露的邊界/目標：{f.get('current_stage_goal', '僅維持現象描寫，絕對不可解開或劇透！')}\n"
    f"  - 🔒 終極隱藏真相（⚠️ 極重要：尚未達到 100% 前，絕對嚴禁在內文中透露以下任何字眼或答案）：\n"
    f"    {f.get('truth')}\n"
    f"----------------------------------------\n"
    for f in app_data.get("foreshadowing_list", [])
])

enable_f = app_data.get("enable_new_foreshadow", True)
f_count = int(app_data.get("new_foreshadow_count", 1))
f_blacklist = app_data.get("foreshadow_black_list", "")

if enable_f and f_count > 0:
    foreshadow_instruction = f"""
請撰寫本章內文，同時在 new_foreshadowing 中精準列出你在此章寫作時順手埋下的 {f_count} 個全新伏筆細節（包含表面現象、進度標籤如『0% (剛埋下/僅現象)』、預計解答章節與隱藏真相）。

【🔒 伏筆防重複極嚴格指令】
1. 請審視上方【目前已記錄的長線伏筆】，絕對禁止創造與既有伏筆同質化、類似道具或重複現象的新伏筆！
2. 必須嚴格避開以下【黑名單套路】：
{f_blacklist}
"""
else:
    foreshadow_instruction = "本章專注於推進劇情與回收舊伏筆，嚴禁埋下任何新伏筆！請務必將 new_foreshadowing 欄位回傳空陣列 []。"

# ================= 直連 Gemini API 生成邏輯 (Key 自動升級機制) =================
if generate_btn:
    if not active_api_key:
        st.error("❌ 找不到 Gemini API Key！請先在『💾 API 設定與存檔管理』頁面填入 Key。")
    else:
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

【目前已記錄的長線伏筆與進度鎖 (嚴禁提前解開未達 100% 的真相)】
{foreshadowing_context if foreshadowing_context else "目前暫無紀錄中的伏筆。"}
* 寫作特別規範：請嚴格審視上方伏筆的『當前解開進度限制』與『本章允許揭露的邊界』。當前寫作進度只能精準停留在該百分比！嚴禁提前洩漏『終極隱藏真相』中的任何底層原理、名詞或答案！

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

【極重要排版規範】
撰寫 novel_text 時，請務必按照中文出版小說格式，每段之間使用雙換行 (\\n\\n) 進行清晰分段，切勿將文字擠在同一行或單長段落中！

【關鍵伏筆任務與防重複要求】
{foreshadow_instruction}
"""

        try:
            genai.configure(api_key=active_api_key)
            
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "novel_text": {"type": "STRING"},
                    "new_foreshadowing": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "content": {"type": "STRING"},
                                "progress": {"type": "STRING"},
                                "status": {"type": "STRING"},
                                "current_stage_goal": {"type": "STRING"},
                                "truth": {"type": "STRING"}
                            },
                            "required": ["content", "status", "truth"]
                        }
                    }
                },
                "required": ["novel_text", "new_foreshadowing"]
            }

            target_model = "gemini-flash-latest"
            try:
                model = genai.GenerativeModel(target_model)
                st.caption(f"⚡ 成功連線模型：`{target_model}`")
            except Exception:
                target_model = "gemini-3.5-flash"
                model = genai.GenerativeModel(target_model)
                st.caption(f"⚡ 自動切換連線模型：`{target_model}`")
            
            with st.spinner("✨ 正在撰寫小說內文並比對歷史伏筆去重中..."):
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": response_schema
                    }
                )
            
            result_json = json.loads(response.text)
            novel_text = result_json.get("novel_text", "")
            new_foreshadows = result_json.get("new_foreshadowing", [])
            
            # 1. 寫入 Session State 小說內文
            app_data["generated_content"] = novel_text
            st.session_state["app_data"]["generated_content"] = novel_text

            # 2. 自動將 AI 捕捉到的新伏筆添加進伏筆庫
            if enable_f and f_count > 0:
                for nf in new_foreshadows:
                    if nf.get("content"):
                        new_f_id = f"f_{datetime.now().strftime('%M%S%f')}"
                        app_data.setdefault("foreshadowing_list", []).append({
                            "id": new_f_id,
                            "content": nf.get("content", ""),
                            "progress": nf.get("progress", "0% (剛埋下/僅現象)"),
                            "status": nf.get("status", "待解答"),
                            "current_stage_goal": nf.get("current_stage_goal", "僅維持現象描寫，絕對不可解開或劇透！"),
                            "truth": nf.get("truth", "")
                        })

            st.session_state["just_generated"] = True
            st.session_state["gen_time_key"] = datetime.now().strftime('%M%S%f')
            st.rerun()

        except Exception as e:
            st.error(f"Gemini API 呼叫或 JSON 解析失敗：{str(e)}")
