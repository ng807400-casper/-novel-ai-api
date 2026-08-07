import streamlit as st
import json
import os
import google.generativeai as genai
from datetime import datetime

# ================= 1. 頁面基本與 CSS 樣式設定 =================
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

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

# ================= 2. 預設資料初始化 (已徹底清除物理標籤) =================
default_data = {
  "book_title": "《克蘇魯的遊樂園》",
  "book_theme": "懸疑 / 克蘇魯 / 規則怪談 / 心理博弈 / 高智商解謎",
  "book_overall_secret": "希靈帝國在阻止虛空大災變的過程中，意外聯絡上虛空背面的神族，得知虛空大災變真相為虛空雙向歸零的機制。",
  "world_event": {
    "title": "車頭核心震盪與第10車廂失壓異變",
    "scope": "全列車第 8 ~ 12 車廂",
    "description": "列車突然發生無聲劇烈震動，窗外的虛空廢墟黑液狂暴湧動，第10車廂的菌絲擴散速度瞬間提升三倍，所有車廂連結門開始無規律關閉！",
    "impact_hero": "蘇默原本的搜查計畫被打亂，必須在車廂門永久鎖死前找出安全的通過方式。",
    "impact_allies": "西裝男左半身木化加速擴散，求生本能壓倒理智，開始密謀搶奪蘇默隨身攜帶的防護道具。",
    "impact_villains": "高維觀察者將列車污染等級提升，開始向後方車廂投放高階變異體進行極限壓力測試。"
  },
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
      "physics_detail": "時間鎖死在 06:52，空氣中瀰漫陳舊木材與腐敗發酵酸臭",
      "local_rules": "絕不可發聲"
    }
  ],
  "volumes_list": [{"id": "v1", "title": "第一集：失聲火車", "target_words": 100000, "summary": "求生指南"}],
  "character_list": [
    {
      "id": "c1", "name": "蘇默", "category": "當前在場/主要角色", "faction": "大學新生",
      "public_relation": "主角本人", "hidden_motive": "求生", "summary": "習慣在內心吐槽的大一新生",
      "personality": "冷靜、觀察力極強、習慣內心吐槽", "status": "健康", "sanity": "84%", "speech_style": "簡潔", "dialogue_example": "「06:52，時間沒動。」"
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
  "tone_setting": "描述懸疑、驚悚、恐懼、營造氣氛、對話時採用「遠瞳」的「深海餘燼」這本小說的撰寫方式；描述戰鬥時採用「那一只蚊子」的「輪迴樂園」這本小說的撰寫方式。",
  "style_suspense": "比照「遠瞳」《深海餘燼》：注重客觀白描、恢弘壓抑的氛圍營造、深邃詭異的宏大感、冷酷環境與主角內心微吐槽的妙趣反差。",
  "style_battle": "比照「那一只蚊子」《輪迴樂園》：極致乾脆利落、肌肉與神經動能的微米級白描、生死博弈的冷酷果斷、刀刀見血的死鬥拉扯感。",
  "previous_summary": "",
  "scene_conflict": "",
  "scene_turn": "",
  "reveal_and_mystery": "",
  "must_include": "",
  "chapter_outline": "",
  "writing_taboos": "• 禁止任何角色開口發聲說話\n• 寫作禁止直接稱呼克系\n• 嚴禁出現任何物理公式、教科書推導與物理單位名詞（如阻尼、熱力學、分貝等）\n• 重點放在感官異常、心理恐懼、規則博弈與生死拉扯",
  "generated_content": "",
  "enable_new_foreshadow": True,
  "new_foreshadow_count": 1,
  "foreshadow_black_list": "• 禁止重複出現指針逆轉的懷錶/鐘錶類道具\n• 禁止重複出現吧台下的舊報紙/傳單線索\n• 禁止重複出現神秘簡訊突然警告/預警\n• 禁止重複出現牆壁/鏡面上的血字提示"
}

# Session State 管理
if "app_data" not in st.session_state: st.session_state["app_data"] = default_data
if "last_uploaded_filename" not in st.session_state: st.session_state["last_uploaded_filename"] = None
if "upload_ver" not in st.session_state: st.session_state["upload_ver"] = 0
if "just_generated" not in st.session_state: st.session_state["just_generated"] = False
if "gen_time_key" not in st.session_state: st.session_state["gen_time_key"] = "initial"
if "director_script" not in st.session_state: st.session_state["director_script"] = ""

app_data = st.session_state["app_data"]
ver = st.session_state["upload_ver"]

if "world_event" not in app_data:
    app_data["world_event"] = default_data["world_event"]

# ================= 3. 頂部狀態列看板 =================
st.title(f"📖 {app_data.get('book_title', '未命名作品')}")

col_dash1, col_dash2, col_dash3, col_dash4 = st.columns(4)
with col_dash1: st.metric("🎯 當前進度", f"{app_data.get('current_vol_title', '第一集')} 第 {app_data.get('current_chap', 1)} 章")
with col_dash2: st.metric("📝 目標字數", f"{app_data.get('target_chapter_words', 4000)} 字")
with col_dash3: st.metric("🔮 追蹤伏筆數", f"{len(app_data.get('foreshadowing_list', []))} 個")
with col_dash4: st.metric("🌪️ 當前大事件", app_data["world_event"].get("title", "無事件"))

st.markdown("---")

# ================= 4. 主選單五大架構分類 =================
tab_write, tab_event_hub, tab_foreshadow_hub, tab_world_hub, tab_system_hub = st.tabs([
    "🎬 【本章寫作與導演區】", 
    "🌪️ 【世界大事件與局勢推演】",
    "🔮 【伏筆智庫與進度鎖】",
    "🌌 【世界觀、地圖與案件牆】", 
    "👥 【角色與系統存檔管理】"
])

# ---------------- Tab 1: 本章寫作與導演區 ----------------
with tab_write:
    col_w_top1, col_w_top2, col_w_top3 = st.columns(3)
    with col_w_top1: app_data["current_vol_title"] = st.text_input("🎯 當前集數", value=app_data.get("current_vol_title", "第一集：失聲火車"), key=f"cvt_{ver}")
    with col_w_top2: app_data["current_chap"] = st.number_input("目前章節", value=int(app_data.get("current_chap", 1)), min_value=1, key=f"cc_{ver}")
    with col_w_top3: app_data["target_chapter_words"] = st.number_input("🎯 目標字數", value=int(app_data.get("target_chapter_words", 4000)), step=500, key=f"tcw_{ver}")

    st.info(f"⚡ **當前觸發世界大事件**：【{app_data['world_event'].get('title')}】（已融入 API 生成背景中）")

    app_data["previous_summary"] = st.text_area("📌 上一章銜接點 (Previous Summary)", value=app_data.get("previous_summary", ""), height=90, key=f"ps_{ver}")
    app_data["chapter_outline"] = st.text_area("🎯 本章具體大綱 (主要寫作指令)", value=app_data.get("chapter_outline", ""), height=120, key=f"co_{ver}")

    st.markdown("### ⚡ 雙階 AI 生成工作流")
    col_act1, col_act2 = st.columns(2)
    with col_act1: btn_director = st.button("🎬 第一步：AI 導演分鏡與邏輯檢查", use_container_width=True, key=f"dir_btn_{ver}")
    with col_act2: generate_btn = st.button("✨ 第二步：正式生成精緻小說正文", type="primary", use_container_width=True, key=f"gen_btn_{ver}")

    if st.session_state["director_script"]:
        with st.expander("🎬 導演分鏡腳本報告 (已點擊拆解)", expanded=True):
            st.markdown(st.session_state["director_script"])

    with st.expander("⚙️ 本章進階鏡頭與環境微調 (點擊展開)", expanded=False):
        char_names_list = [c.get('name', '蘇默') for c in app_data.get("character_list", [])]
        col_env1, col_env2, col_env3 = st.columns(3)
        with col_env1:
            pov_options = ["第一人稱", "第三人稱限制視角", "第三人稱全知視角"]
            cur_pov = app_data.get("pov_type", "第一人稱")
            app_data["pov_type"] = st.selectbox("👁️ 視角類型", pov_options, index=pov_options.index(cur_pov) if cur_pov in pov_options else 0, key=f"pov_t_{ver}")
        with col_env2:
            cur_pov_char = app_data.get("pov_character", "蘇默")
            app_data["pov_character"] = st.selectbox("👤 視角主角", char_names_list if char_names_list else ["蘇默"], index=char_names_list.index(cur_pov_char) if cur_pov_char in char_names_list else 0, key=f"pov_c_{ver}")
        with col_env3:
            pacing_opts = ["中速推演 (解謎/搜查/對話)", "高速推進 (動作/戰鬥/逃跑)", "慢速壓抑 (鋪陳/恐懼/氛圍)"]
            cur_pacing = app_data.get("pacing_setting", "中速推演 (解謎/搜查/對話)")
            app_data["pacing_setting"] = st.selectbox("⚡ 寫作節奏", pacing_opts, index=pacing_opts.index(cur_pacing) if cur_pacing in pacing_opts else 0, key=f"pacing_{ver}")

        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            app_data["time_and_environment"] = st.text_input("⏱️ 時間線與環境狀態", value=app_data.get("time_and_environment", ""), key=f"tae_{ver}")
            app_data["scene_conflict"] = st.text_area("⚔️ 本章核心衝突", value=app_data.get("scene_conflict", ""), height=70, key=f"sc_{ver}")
            app_data["must_include"] = st.text_area("🔑 必須出現的道具/伏筆", value=app_data.get("must_include", ""), height=70, key=f"mi_{ver}")
        with col_sub2:
            app_data["sensory_details"] = st.text_input("🌫️ 五感描寫重點", value=app_data.get("sensory_details", ""), key=f"sd_{ver}")
            app_data["scene_turn"] = st.text_area("🔄 局勢/認知大翻轉", value=app_data.get("scene_turn", ""), height=70, key=f"st_{ver}")
            app_data["reveal_and_mystery"] = st.text_area("🔍 伏筆揭示與新懸念", value=app_data.get("reveal_and_mystery", ""), height=70, key=f"rm_{ver}")

        app_data["writing_taboos"] = st.text_area("🚫 寫作禁忌 (Negative Prompt)", value=app_data.get("writing_taboos", ""), height=100, key=f"wt_{ver}")

    if st.session_state["just_generated"]:
        st.success("🎉 最新一章小說生成完成！已自動完成世界大事件、伏筆與銜接點同步！")
        st.session_state["just_generated"] = False

    if app_data.get("generated_content"):
        st.markdown("---")
        st.subheader("📝 最新生成成果：")
        current_gen_key = st.session_state["gen_time_key"]
        st.text_area("📋 複製與編輯專用區", value=app_data["generated_content"], height=500, key=f"res_ta_{current_gen_key}_{ver}")
        st.markdown("---")
        st.markdown("### 📖 全章閱讀預覽 Mode：")
        st.markdown(app_data["generated_content"])

# ---------------- Tab 2: 世界大事件與局勢推演 ----------------
with tab_event_hub:
    st.subheader("🌪️ 世界線大事件與連鎖局勢推演引擎")
    st.caption("💡 在這裡設定宏觀世界爆發的大事件，AI 會自動推演並強制改變各陣營角色的決策與行動！")

    we = app_data["world_event"]
    
    col_we1, col_we2 = st.columns([2, 1])
    with col_we1: we["title"] = st.text_input("💥 當前世界大事件名稱", value=we.get("title", ""), key=f"we_t_{ver}")
    with col_we2: we["scope"] = st.text_input("📍 事件影響範圍/波及區域", value=we.get("scope", ""), key=f"we_s_{ver}")

    we["description"] = st.text_area("📜 事件詳細狀況與環境巨變描寫", value=we.get("description", ""), height=100, key=f"we_d_{ver}")

    st.markdown("### 🔗 陣營連鎖反應設定 (Domino Effect)")
    col_imp1, col_imp2, col_imp3 = st.columns(3)
    with col_imp1: we["impact_hero"] = st.text_area("👤 對主角（蘇默）的直接影響", value=we.get("impact_hero", ""), height=120, key=f"we_ih_{ver}")
    with col_imp2: we["impact_allies"] = st.text_area("👥 對配角/盟友的影響與動搖", value=we.get("impact_allies", ""), height=120, key=f"we_ia_{ver}")
    with col_imp3: we["impact_villains"] = st.text_area("👁️ 對反派/高維存在的波及", value=we.get("impact_villains", ""), height=120, key=f"we_iv_{ver}")

    btn_sim_event = st.button("🎲 點此讓 AI 自動推演『大事件對全場角色的連鎖衝擊』", type="primary", use_container_width=True, key=f"sim_ev_btn_{ver}")

# ---------------- Tab 3: 伏筆智庫與進度鎖 ----------------
with tab_foreshadow_hub:
    st.subheader("🔮 伏筆智庫與階段控制面板")
    
    with st.expander("🎯 點此開啟【AI 伏筆靈感定向發想面板】", expanded=True):
        col_f_dir1, col_f_dir2 = st.columns([1, 2])
        with col_f_dir1:
            f_type_selected = st.selectbox("🏷️ 指定伏筆類型", ["隨機發想 (不限題材)", "🎒 隨身道具/古典物品類", "🏚️ 車廂環境/異象類", "👥 配角秘密/身體異變類", "🔒 鐵律漏洞/高維真相類"], key=f"f_type_{ver}")
        with col_f_dir2:
            f_custom_prompt = st.text_input("💬 輸入具體發想方向或關鍵字 (選填)", placeholder="例如：第九節餐車廂憑空出現的純銀藥盒，可延遲反噬聲音污染...", key=f"f_custom_{ver}")

    col_f_t, col_f_a1, col_f_a2 = st.columns([2, 1, 1])
    with col_f_t: st.markdown("### 📜 全書伏筆追蹤清單")
    with col_f_a1:
        if st.button("➕ 手動新增伏筆", key=f"add_f_btn_{ver}", use_container_width=True):
            app_data.setdefault("foreshadowing_list", []).append({
                "id": f"f_{datetime.now().strftime('%M%S%f')}", "content": "新伏筆表面現象...", "progress": "0% (剛埋下/僅現象)", "status": "未解答", "current_stage_goal": "僅維持現象描寫，絕對不可解開！", "truth": "背後隱藏真相..."
            })
            st.rerun()
    with col_f_a2:
        btn_ai_f = st.button("🤖 依指定方向發想伏筆", type="primary", key=f"ai_gen_f_btn_{ver}", use_container_width=True)

    f_list = app_data.get("foreshadowing_list", [])
    if not f_list:
        st.info("💡 目前尚無紀錄中的伏筆。手動新增或使用 AI 定向發想！")
    else:
        tab_f1, tab_f2, tab_f3 = st.tabs(["📌 待解答/埋下中 (0%-20%)", "🔄 揭露中/推演中 (50%-80%)", "✅ 已完全回收 (100%)"])
        delete_target_id = None
        progress_opts = ["0% (剛埋下/僅現象)", "20% (發現甜頭/微小異常)", "50% (產生第一層誤解/疑心)", "80% (假真相/第一重反轉)", "100% (完全回收/終極真相)"]
        
        for f_idx, f_item in enumerate(f_list):
            f_id = f_item.get("id", f"f_{f_idx}")
            progress_str = f_item.get("progress", "0% (剛埋下/僅現象)")
            target_tab = tab_f3 if ("100%" in progress_str or "回收" in f_item.get("status", "")) else (tab_f2 if ("50%" in progress_str or "80%" in progress_str) else tab_f1)

            with target_tab:
                title_preview = f_item.get('content', '未命名伏筆')
                if len(title_preview) > 25: title_preview = title_preview[:25] + "..."
                
                with st.expander(f"🔮 伏筆：{title_preview} 【進度：{progress_str}】", expanded=True):
                    f_item['content'] = st.text_input("📍 伏筆表面現象/描寫細節", value=f_item.get('content', ''), key=f"fc_{f_id}_{ver}")
                    col_fs1, col_fs2 = st.columns([1, 2])
                    with col_fs1:
                        f_item['progress'] = st.selectbox("📊 解開進度鎖", progress_opts, index=progress_opts.index(progress_str) if progress_str in progress_opts else 0, key=f"fp_{f_id}_{ver}")
                    with col_fs2:
                        f_item['status'] = st.text_input("⏱️ 詳細狀態/預計解答章節", value=f_item.get('status', '未解答'), key=f"fs_{f_id}_{ver}")

                    f_item['current_stage_goal'] = st.text_area("🎯 本章允許揭露的邊界 (嚴禁越界)", value=f_item.get('current_stage_goal', '僅維持現象描寫，絕對不可解開！'), height=65, key=f"fcg_{f_id}_{ver}")
                    f_item['truth'] = st.text_area("🔒 終極隱藏真相 (未達 100% 前嚴禁劇透)", value=f_item.get('truth', ''), height=80, key=f"ft_{f_id}_{ver}")
                    if st.button("🗑️ 刪除此伏筆", key=f"fd_{f_id}_{ver}"): delete_target_id = f_id

        if delete_target_id:
            app_data["foreshadowing_list"] = [item for item in app_data["foreshadowing_list"] if item.get("id") != delete_target_id]
            st.rerun()

# ---------------- Tab 4: 世界觀、地圖與案件牆 ----------------
with tab_world_hub:
    st.subheader("🌌 世界觀、地圖與戰術案件牆")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1: app_data["book_title"] = st.text_input("全書書名", value=app_data.get("book_title", ""), key=f"bt_{ver}")
    with col_w2: app_data["book_theme"] = st.text_input("題材風格", value=app_data.get("book_theme", ""), key=f"bth_{ver}")
    app_data["book_overall_secret"] = st.text_area("🔒 全書終局真相 (最高機密)", value=app_data.get("book_overall_secret", ""), height=80, key=f"bos_{ver}")

    st.divider()
    sub_w1, sub_w2 = st.tabs(["🗺️ 區域與地圖庫", "🎒 道具庫與鐵律案件牆"])
    
    with sub_w1:
        if st.button("➕ 新增區域", key=f"add_loc_btn_{ver}"):
            app_data.setdefault("location_list", []).append({"id": f"loc_{datetime.now().strftime('%M%S%f')}", "name": "新區域", "scope": "", "visual_style": "", "physics_detail": "", "local_rules": ""})
            st.rerun()
        loc_del_id = None
        for loc_idx, loc in enumerate(app_data.get("location_list", [])):
            loc_id = loc.get("id", f"loc_{loc_idx}")
            with st.expander(f"📍 {loc.get('name', '區域')} ({loc.get('scope', '')})", expanded=True):
                loc['name'] = st.text_input("區域名稱", value=loc.get('name', ''), key=f"loc_n_{loc_id}_{ver}")
                loc['scope'] = st.text_input("適用範圍", value=loc.get('scope', ''), key=f"loc_sc_{loc_id}_{ver}")
                loc['visual_style'] = st.text_area("🏛️ 視覺建築特色", value=loc.get('visual_style', ''), key=f"loc_vs_{loc_id}_{ver}", height=60)
                loc['physics_detail'] = st.text_area("🌫️ 環境異常與異變現象", value=loc.get('physics_detail', ''), key=f"loc_pd_{loc_id}_{ver}", height=60)
                loc['local_rules'] = st.text_area("🚫 區域專屬禁忌", value=loc.get('local_rules', ''), key=f"loc_lr_{loc_id}_{ver}", height=60)
                if st.button("🗑️ 刪除區域", key=f"loc_d_{loc_id}_{ver}"): loc_del_id = loc_id
        if loc_del_id: app_data["location_list"] = [l for l in app_data["location_list"] if l.get("id") != loc_del_id]; st.rerun()

    with sub_w2:
        col_i_t, col_i_a = st.columns([3, 1])
        with col_i_t: st.markdown("#### 📦 可用道具庫")
        with col_i_a:
            if st.button("➕ 新增道具", key=f"add_it_btn_{ver}"):
                app_data.setdefault("items_inventory", []).append({"id": f"it_{datetime.now().strftime('%M%S%f')}", "name": "新道具", "status": "", "owner": ""})
                st.rerun()
        it_del_id = None
        for it_idx, item in enumerate(app_data.get("items_inventory", [])):
            item_id = item.get("id", f"it_{it_idx}")
            with st.expander(f"📦 {item.get('name', '道具')} ({item.get('owner', '')})", expanded=True):
                item['name'] = st.text_input("名稱", value=item.get('name', ''), key=f"it_n_{item_id}_{ver}")
                item['owner'] = st.text_input("持有者", value=item.get('owner', ''), key=f"it_o_{item_id}_{ver}")
                item['status'] = st.text_input("狀態", value=item.get('status', ''), key=f"it_s_{item_id}_{ver}")
                if st.button("🗑️ 刪除道具", key=f"it_d_{item_id}_{ver}"): it_del_id = item_id
        if it_del_id: app_data["items_inventory"] = [i for i in app_data["items_inventory"] if i.get("id") != it_del_id]; st.rerun()

        st.divider()
        st.markdown("#### ✅ 已驗證鐵律")
        r_del_id = None
        for r_idx, r in enumerate(app_data.get("confirmed_rules_list", [])):
            r_id = r.get("id", f"r_{r_idx}")
            col_rx, col_rd = st.columns([5, 1])
            with col_rx: r['content'] = st.text_input(f"鐵律 {r_idx+1}", value=r.get('content', ''), key=f"r_val_{r_id}_{ver}", label_visibility="collapsed")
            with col_rd:
                if st.button("🗑️", key=f"r_del_{r_id}_{ver}"): r_del_id = r_id
        if r_del_id: app_data["confirmed_rules_list"] = [r for r in app_data["confirmed_rules_list"] if r.get("id") != r_del_id]; st.rerun()

# ---------------- Tab 5: 角色與系統存檔管理 ----------------
with tab_system_hub:
    st.subheader("👥 角色卡片庫、雙文風與系統存檔")
    
    sub_s1, sub_s2, sub_s3 = st.tabs(["👥 角色卡片庫", "🎭 雙神級作者文風", "💾 API 設定與 JSON 存檔"])
    
    with sub_s1:
        if st.button("➕ 新增角色", key=f"add_c_btn_{ver}"):
            app_data.setdefault("character_list", []).append({
                "id": f"c_{datetime.now().strftime('%M%S%f')}", "name": "新角色", "category": "當前在場/主要角色", "faction": "", "public_relation": "", "hidden_motive": "", "summary": "", "personality": "", "status": "", "sanity": "100%", "speech_style": "", "dialogue_example": ""
            })
            st.rerun()
        
        tab_c1, tab_c2, tab_c3 = st.tabs(["🔥 在場/主要", "📡 場外/通訊", "🪦 離場/變異"])
        categories = {"當前在場/主要角色": tab_c1, "場外/通訊角色": tab_c2, "離場/變異/歷史角色": tab_c3}
        c_del_id = None
        
        for c_idx, char in enumerate(app_data.get("character_list", [])):
            c_id = char.get("id", f"c_{c_idx}")
            c_cat = char.get('category', '當前在場/主要角色')
            with categories.get(c_cat, tab_c1):
                with st.expander(f"👤 {char.get('name', '角色')} ({char.get('faction', '無陣營')})", expanded=True):
                    char['name'] = st.text_input("名稱", value=char.get('name', ''), key=f"c_n_{c_id}_{ver}")
                    char['category'] = st.selectbox("📌 歸類分頁", ["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"], index=["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"].index(c_cat) if c_cat in ["當前在場/主要角色", "場外/通訊角色", "離場/變異/歷史角色"] else 0, key=f"c_cat_{c_id}_{ver}")
                    char['faction'] = st.text_input("⚔️ 勢力/陣營", value=char.get('faction', ''), key=f"c_f_{c_id}_{ver}")
                    char['status'] = st.text_input("🩸 生理狀態", value=char.get('status', ''), key=f"c_st_{c_id}_{ver}")
                    char['sanity'] = st.text_input("🧠 理智度 (SAN值)", value=char.get('sanity', '100%'), key=f"c_sn_{c_id}_{ver}")
                    char['summary'] = st.text_input("簡介", value=char.get('summary', ''), key=f"c_s_{c_id}_{ver}")
                    char['personality'] = st.text_input("性格", value=char.get('personality', ''), key=f"c_p_{c_id}_{ver}")
                    char['hidden_motive'] = st.text_input("🔒 隱藏動機", value=char.get('hidden_motive', ''), key=f"c_hm_{c_id}_{ver}")
                    if st.button("🗑️ 刪除角色", key=f"c_dl_{c_id}_{ver}"): c_del_id = c_id
        if c_del_id: app_data["character_list"] = [c for c in app_data["character_list"] if c.get("id") != c_del_id]; st.rerun()

    with sub_s2:
        st.markdown("#### 🎭 雙神級作者文風控制")
        app_data["style_suspense"] = st.text_area("🌊 懸疑/氛圍/對話文風 (遠瞳《深海餘燼》)", value=app_data.get("style_suspense", ""), height=100, key=f"ss_{ver}")
        app_data["style_battle"] = st.text_area("⚔️ 戰鬥/生死博弈文風 (那一只蚊子《輪迴樂園》)", value=app_data.get("style_battle", ""), height=100, key=f"sb_{ver}")

    with sub_s3:
        st.markdown("#### 🔑 API Key 與存檔管理")
        env_api_key = os.environ.get("GEMINI_API_KEY", "")
        api_key_input = st.text_input("Gemini API Key", value=env_api_key, type="password", key=f"api_{ver}")
        active_api_key = api_key_input if api_key_input else env_api_key
        
        st.divider()
        uploaded_file = st.file_uploader("匯入歷史設定檔 (.json)", type=["json", "txt"], key=f"uploader_{ver}")
        if uploaded_file is not None and uploaded_file.name != st.session_state["last_uploaded_filename"]:
            try:
                st.session_state["app_data"] = json.load(uploaded_file)
                st.session_state["last_uploaded_filename"] = uploaded_file.name
                st.session_state["upload_ver"] += 1
                st.success("✅ 成功載入歷史紀錄！")
                st.rerun()
            except Exception as e: st.error(f"檔案格式錯誤：{str(e)}")

        st.divider()
        app_data["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        json_string = json.dumps(app_data, ensure_ascii=False, indent=2)
        st.download_button("📥 下載當前全書設定檔 (.json)", data=json_string, file_name=f"{app_data.get('book_title', '小說')}_{app_data.get('current_vol_title', '第一集')}_第{app_data.get('current_chap', 1)}章.json", mime="application/json", use_container_width=True, key=f"dl_btn_{ver}")

# ================= 5. 後端 Prompt 與 API 邏輯 =================
locations_text = "".join([f"【{l.get('name', '')} ({l.get('scope', '')})】\n• 建築特色：{l.get('visual_style', '')}\n• 環境異象：{l.get('physics_detail', '')}\n• 區域規則：{l.get('local_rules', '')}\n---\n" for l in app_data.get("location_list", [])])
items_text = "".join([f"• {i.get('name', '')} (持有:{i.get('owner', '')}): {i.get('status', '')}\n" for i in app_data.get("items_inventory", [])])
rules_text = "".join([f"{idx+1}. {r.get('content', '')}\n" for idx, r in enumerate(app_data.get("confirmed_rules_list", []))])
updated_characters_text = "".join([f"【{c.get('name', '')} ({c.get('faction', '')})】\n• 簡介：{c.get('summary', '')}\n• 狀態：{c.get('status', '')}\n• 隱藏動態：{c.get('hidden_motive', '')}\n---\n" for c in app_data.get("character_list", [])])
foreshadowing_context = "".join([f"• [伏筆 ID: {f.get('id')}] 表面現象描述：{f.get('content')}\n  - 📍 當前解開進度限制：【{f.get('progress', f.get('status', '0%'))}】\n  - 🎯 本章允許揭露邊界：{f.get('current_stage_goal', '僅維持現象描寫，絕對不可解開！')}\n  - 🔒 終極隱藏真相（未達 100% 嚴禁劇透）：{f.get('truth')}\n----------------------------------------\n" for f in app_data.get("foreshadowing_list", [])])

we_info = app_data["world_event"]
world_event_context = f"""
【🌪️ 當前觸發的世界線大事件（最高優先級背景）】
• 事件名稱：{we_info.get('title')}
• 波及範圍：{we_info.get('scope')}
• 狀況描述：{we_info.get('description')}
• 對主角（蘇默）的決策影響：{we_info.get('impact_hero')}
• 對配角/盟友的心理波動影響：{we_info.get('impact_allies')}
• 對反派/高維存在的波及：{we_info.get('impact_villains')}
* 寫作特別指令：本章情節與角色的心理反應【必須高度受此大事件牽引與逼迫】！
"""

enable_f = app_data.get("enable_new_foreshadow", True)
f_count = int(app_data.get("new_foreshadow_count", 1))
f_blacklist = app_data.get("foreshadow_black_list", "")
foreshadow_instruction = f"請撰寫本章內文，同時在 new_foreshadowing 中精準列出 {f_count} 個全新伏筆細節。絕對禁止與既有伏筆同質化，避開黑名單：\n{f_blacklist}" if (enable_f and f_count > 0) else "本章專注於推進劇情，嚴禁埋下新伏筆！請將 new_foreshadowing 設為 []。"

# API 邏輯 0：推演大事件連鎖衝擊
if btn_sim_event:
    if not active_api_key: st.error("❌ 請先輸入 Gemini API Key！")
    else:
        with st.spinner("🎲 AI 正在進行世界大事件對全場角色的連鎖衝擊推演..."):
            try:
                genai.configure(api_key=active_api_key)
                sim_prompt = f"你是一位頂級小說執行導演。請根據當前爆發的世界大事件【{we_info.get('title')}】，自動推演對『主角衝擊』、『配角心態與背叛概率』與『反派反應』的連鎖動態：\n\n【大事件內容】\n{we_info.get('description')}"
                sim_schema = {"type": "OBJECT", "properties": {"impact_hero": {"type": "STRING"}, "impact_allies": {"type": "STRING"}, "impact_villains": {"type": "STRING"}}, "required": ["impact_hero", "impact_allies", "impact_villains"]}
                sim_model = genai.GenerativeModel("gemini-flash-latest")
                sim_res = json.loads(sim_model.generate_content(sim_prompt, generation_config={"response_mime_type": "application/json", "response_schema": sim_schema}).text)
                we["impact_hero"] = sim_res.get("impact_hero", "")
                we["impact_allies"] = sim_res.get("impact_allies", "")
                we["impact_villains"] = sim_res.get("impact_villains", "")
                st.success("🎉 大事件連鎖推演完成！已自動填入各陣營影響欄位中！"); st.rerun()
            except Exception as e: st.error(f"推演失敗: {str(e)}")

# API 邏輯 1：導演腳本
if btn_director:
    if not active_api_key: st.error("❌ 請先輸入 Gemini API Key！")
    else:
        with st.spinner("🎬 AI 導演進行大綱檢查與分鏡拆解中..."):
            try:
                genai.configure(api_key=active_api_key)
                dir_prompt = f"你是一位極度嚴苛的懸疑小說執行導演。請針對【{app_data.get('book_title')}】第 {app_data.get('current_chap')} 章大綱與世界大事件【{we_info.get('title')}】，進行『無聲鐵律檢查』並拆解出『4 個具體鏡頭腳本』。\n\n{world_event_context}\n【鐵律】\n{rules_text}\n【大綱】\n{app_data.get('chapter_outline')}"
                d_model = genai.GenerativeModel("gemini-flash-latest")
                st.session_state["director_script"] = d_model.generate_content(dir_prompt).text
                st.success("🎉 分鏡腳本拆解完成！"); st.rerun()
            except Exception as e: st.error(f"拆解失敗: {str(e)}")

# API 邏輯 2：定向發想伏筆
if btn_ai_f:
    if not active_api_key: st.error("❌ 請先輸入 Gemini API Key！")
    else:
        with st.spinner("✨ Gemini 正在依指定方向發想新伏筆..."):
            try:
                genai.configure(api_key=active_api_key)
                ai_f_prompt = f"你是一位頂級小說架構師。請遵循作者要求的方向【{f_type_selected} | 關鍵字: {f_custom_prompt}】，為【{app_data.get('book_title')}】發想 1 個全新長線伏筆。絕不侷限於物理特性，可為感官錯覺或記憶污染。\n\n既有伏筆：\n{foreshadowing_context}\n黑名單：\n{f_blacklist}"
                f_schema = {"type": "OBJECT", "properties": {"content": {"type": "STRING"}, "progress": {"type": "STRING"}, "status": {"type": "STRING"}, "current_stage_goal": {"type": "STRING"}, "truth": {"type": "STRING"}}, "required": ["content", "progress", "status", "current_stage_goal", "truth"]}
                f_model = genai.GenerativeModel("gemini-flash-latest")
                new_f_data = json.loads(f_model.generate_content(ai_f_prompt, generation_config={"response_mime_type": "application/json", "response_schema": f_schema}).text)
                app_data.setdefault("foreshadowing_list", []).append({"id": f"f_{datetime.now().strftime('%M%S%f')}", "content": new_f_data.get("content", ""), "progress": new_f_data.get("progress", "0% (剛埋下/僅現象)"), "status": new_f_data.get("status", "待解答"), "current_stage_goal": new_f_data.get("current_stage_goal", "僅維持現象描寫！"), "truth": new_f_data.get("truth", "")})
                st.success("🎉 定向伏筆發想完畢！已加入智庫！"); st.rerun()
            except Exception as e: st.error(f"發想伏筆失敗: {str(e)}")

# API 邏輯 3：生成正文 (嚴格負向語氣限制)
if generate_btn:
    if not active_api_key: st.error("❌ 找不到 Gemini API Key！")
    else:
        pov_type = app_data.get("pov_type", "第一人稱")
        pov_character = app_data.get("pov_character", "蘇默")
        perspective_instruction = f"• 描寫視角：【{pov_type}】(主角：{pov_character})，全程以其體感與思考展開，嚴禁出現遊戲數據或旁白感。"
        director_script_context = f"\n【🎬 導演分鏡腳本參考】\n{st.session_state['director_script']}\n" if st.session_state.get("director_script") else ""

        prompt = f"""
你是一位頂級懸疑/規則怪談小說家。請根據以下風格、世界大事件與指令撰寫最新一章純內文。

{world_event_context}

【🔥 最高優先級風格要求】
1. 🌊 懸疑氛圍：{app_data.get('style_suspense')}
2. ⚔️ 戰鬥博弈：{app_data.get('style_battle')}

【🚫 絕對禁止語詞與風格（Negative Prompt - 違者重寫）】
1. 嚴禁出現任何物理公式、定理名稱、常數單位（如分貝、阻尼係數、熱力學熵、向量等物理名詞）。
2. 主角解謎必須依賴【對規則的洞察、感官體感、心理博弈與邏輯推理】，絕對不可進行物理/化學實驗式的推導！

【全書與區域】
• 書名：{app_data.get('book_title')} ({app_data.get('book_theme')}) | 真相：{app_data.get('book_overall_secret')}
{locations_text}
• 已驗證鐵律：\n{rules_text}
• 道具庫：\n{items_text}

【長線伏筆與進度鎖 (嚴禁提前解開未達100%的真相)】
{foreshadowing_context}

【登場角色】
{updated_characters_text}

【銜接與大綱】
• 上一章銜接：{app_data.get('previous_summary')}
{director_script_context}
• 本章大綱 (第 {app_data.get('current_chap')} 章)：{app_data.get('chapter_outline')}
• 目標字數：約 {app_data.get('target_chapter_words')} 字
{perspective_instruction}
• 寫作禁忌：\n{app_data.get('writing_taboos')}

【伏筆任務】
{foreshadow_instruction}

同時，請在 next_chapter_summary 提供 150 字結尾摘要以自動預填為下一章銜接點。
"""
        try:
            genai.configure(api_key=active_api_key)
            response_schema = {"type": "OBJECT", "properties": {"novel_text": {"type": "STRING"}, "next_chapter_summary": {"type": "STRING"}, "new_foreshadowing": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"content": {"type": "STRING"}, "progress": {"type": "STRING"}, "status": {"type": "STRING"}, "current_stage_goal": {"type": "STRING"}, "truth": {"type": "STRING"}}, "required": ["content", "status", "truth"]}}}, "required": ["novel_text", "next_chapter_summary", "new_foreshadowing"]}
            model = genai.GenerativeModel("gemini-flash-latest")
            
            with st.spinner("✨ 正在撰寫小說內文並同步生成銜接點..."):
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "response_schema": response_schema})
            
            result_json = json.loads(response.text)
            app_data["generated_content"] = result_json.get("novel_text", "")
            if result_json.get("next_chapter_summary"): app_data["previous_summary"] = result_json.get("next_chapter_summary")

            if enable_f and f_count > 0:
                for nf in result_json.get("new_foreshadowing", []):
                    if nf.get("content"):
                        app_data.setdefault("foreshadowing_list", []).append({"id": f"f_{datetime.now().strftime('%M%S%f')}", "content": nf.get("content", ""), "progress": nf.get("progress", "0% (剛埋下/僅現象)"), "status": nf.get("status", "待解答"), "current_stage_goal": nf.get("current_stage_goal", "僅維持現象描寫！"), "truth": nf.get("truth", "")})

            st.session_state["just_generated"] = True
            st.session_state["gen_time_key"] = datetime.now().strftime('%M%S%f')
            st.rerun()

        except Exception as e: st.error(f"Gemini API 呼叫失敗：{str(e)}")
