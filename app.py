import streamlit as st
import json
import os
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 1. Streamlit 頁面基礎設定
# ==========================================
st.set_page_config(
    page_title="克蘇魯小說創作工作站",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 載入 API KEY (優先讀取環境變數，或從 sidebar 手動輸入)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

st.sidebar.title("⚙️ 系統設定")
api_key_input = st.sidebar.text_input("Gemini API Key", value=GEMINI_API_KEY, type="password")

if api_key_input:
    genai.configure(api_key=api_key_input)

# 模型選擇
selected_model = st.sidebar.selectbox(
    "優先模型選擇",
    ["gemini-1.5-pro", "gemini-1.5-flash"],
    index=0
)

# ==========================================
# 2. JSON 資料管理與載入
# ==========================================
DEFAULT_JSON_FILE = "novel_state.json"

def get_empty_schema():
    """返回符合小說設定的完整 Schema"""
    return {
        "book_title": "",
        "book_theme": "",
        "book_overall_secret": "",
        "confirmed_rules_list": [],
        "hypotheses_list": [],
        "clues_list": [],
        "items_inventory": [],
        "location_list": [],
        "volumes_list": [],
        "character_list": [],
        "chapters_list": [],
        "current_vol_title": "",
        "current_chap": 1,
        "target_chapter_words": 4000,
        "time_and_environment": "",
        "pacing_setting": "",
        "sensory_details": "",
        "pov_type": "第一人稱",
        "pov_character": "",
        "tone_setting": "",
        "previous_summary": "",
        "scene_conflict": "",
        "scene_turn": "",
        "reveal_and_mystery": "",
        "must_include": "",
        "chapter_outline": "",
        "writing_taboos": "",
        "generated_content": "",
        "saved_at": "",
        "enable_new_foreshadow": False,
        "new_foreshadow_count": 1,
        "foreshadow_black_list": "",
        "foreshadowing_list": []
    }

if 'app_data' not in st.session_state:
    st.session_state['app_data'] = get_empty_schema()

# 檔案上傳與載入
st.sidebar.markdown("---")
st.sidebar.subheader("📁 JSON 檔案讀寫")
uploaded_file = st.sidebar.file_uploader("上傳小說設定 JSON", type=["json"])

if uploaded_file is not None:
    try:
        loaded_data = json.load(uploaded_file)
        # 合併載入的資料，確保缺失欄位能被預設值補齊
        schema = get_empty_schema()
        schema.update(loaded_data)
        st.session_state['app_data'] = schema
        st.sidebar.success("✅ JSON 設定成功載入！")
    except Exception as e:
        st.sidebar.error(f"❌ JSON 載入失敗: {e}")

# 下載當前 JSON 按鈕
json_string = json.dumps(st.session_state['app_data'], ensure_ascii=False, indent=2)
st.sidebar.download_button(
    label="💾 下載當前 JSON 設定檔",
    data=json_string,
    file_name=f"{st.session_state['app_data'].get('book_title', 'novel')}_第{st.session_state['app_data'].get('current_chap', 1)}章.json",
    mime="application/json"
)

# ==========================================
# 3. 主 UI 分頁結構
# ==========================================
app_data = st.session_state['app_data']

st.title(f"📖 小說創作工作站：{app_data.get('book_title', '未命名作品')}")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✍️ 本章寫作控制台",
    "🔮 長線伏筆與進度鎖",
    "👥 角色與登場卡片",
    "🌍 世界觀與物品庫",
    "📜 章節大綱與歷史",
    "🛠️ 寫作禁忌與風格"
])

# ------------------------------------------
# TAB 1: 本章寫作控制台
# ------------------------------------------
with tab1:
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c1:
        app_data['current_vol_title'] = st.text_input("卷名/集名", value=app_data.get('current_vol_title', ''))
    with col_c2:
        app_data['current_chap'] = st.number_input("當前寫作章節 (第幾章)", value=int(app_data.get('current_chap', 1)), step=1)
    with col_c3:
        app_data['target_chapter_words'] = st.number_input("目標字數", value=int(app_data.get('target_chapter_words', 4000)), step=500)

    st.markdown("---")
    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
        app_data['time_and_environment'] = st.text_input("時間與環境描寫", value=app_data.get('time_and_environment', ''))
        app_data['chapter_outline'] = st.text_area("🎯 本章具體大綱與情節推進 (可下達伏筆回收指令)", value=app_data.get('chapter_outline', ''), height=120)
        app_data['must_include'] = st.text_area("📌 本章必須包含要素", value=app_data.get('must_include', ''), height=70)
    with col_e2:
        app_data['pacing_setting'] = st.text_input("節奏基調", value=app_data.get('pacing_setting', ''))
        app_data['pov_type'] = st.selectbox("視角類型", ["第一人稱", "第三人稱有限視角", "第三人稱全知視角"], index=0)
        app_data['pov_character'] = st.text_input("視角角色", value=app_data.get('pov_character', ''))

    st.markdown("---")
    st.subheader("前文提要 (Previous Summary)")
    app_data['previous_summary'] = st.text_area("上一章結尾/前文摘錄", value=app_data.get('previous_summary', ''), height=150)

    # API 生成邏輯按鈕
    st.markdown("---")
    if st.button("🚀 呼叫 Gemini API 開始生成本章內文", type="primary"):
        if not api_key_input:
            st.error("請先在左側邊欄輸入有效的 Gemini API Key！")
        else:
            with st.spinner("Gemini 正在撰寫中，請稍候..."):
                try:
                    # 1. 構建伏筆與進度鎖 Context
                    foreshadowing_context = "".join([
                        f"• [伏筆 ID: {f.get('id')}] 表面現象描寫：{f.get('content')}\n"
                        f"  - 📍 當前解開進度限制：【{f.get('progress', f.get('status', '0%'))}】\n"
                        f"  - 🎯 本章允許揭露的邊界/目標：{f.get('current_stage_goal', '僅維持現象描寫，絕對不可解開或劇透！')}\n"
                        f"  - 🔒 終極隱藏真相（⚠️ 未達 100% 前嚴禁在內文中透露以下任何字眼）：\n"
                        f"    {f.get('truth')}\n"
                        f"----------------------------------------\n"
                        for f in app_data.get("foreshadowing_list", [])
                    ])

                    # 2. 構建角色與環境 Context
                    character_context = "".join([
                        f"• {c.get('name')}（{c.get('category')}）：{c.get('summary')} | 生理與理智狀態：{c.get('status')} (San: {c.get('sanity')})\n"
                        for c in app_data.get("character_list", [])
                    ])

                    rules_context = "\n".join([f"• {r.get('content')}" for r in app_data.get("confirmed_rules_list", [])])

                    # 3. 組合 Prompt
                    prompt = f"""你是一位擅長克蘇魯懸疑、規則怪談與高智商解謎的頂級小說家。
請根據以下提供的完整背景設定、伏筆進度鎖以及本章大綱，撰寫【{app_data.get('book_title')}】{app_data.get('current_vol_title')} 第 {app_data.get('current_chap')} 章。

【作品基本資訊】
• 主題風格：{app_data.get('book_theme')}
• 敘事視角：{app_data.get('pov_type')}（視角角色：{app_data.get('pov_character')}）
• 語氣基調：{app_data.get('tone_setting')}
• 本章環境與時間：{app_data.get('time_and_environment')}
• 節奏設定：{app_data.get('pacing_setting')}

【既有確認規則】
{rules_context}

【登場角色狀態】
{character_context}

【關鍵伏筆控線與進度鎖定指令（極重要）】
{foreshadowing_context}
* 寫作特別規範：請嚴格審視上方伏筆的『當前解開進度限制』與『本章允許揭露的邊界』。當前寫作進度只能精準停留在該百分比！嚴禁提前洩漏『終極隱藏真相』中的任何底層原理、名詞或答案！

【本章寫作大綱與任務】
{app_data.get('chapter_outline')}

【必須包含要素】
{app_data.get('must_include')}

【前文提要】
{app_data.get('previous_summary')}

【寫作禁忌 Negative Prompt（違者重寫）】
{app_data.get('writing_taboos')}

【字數要求】
請詳細描寫白描細節、心理體感與環境氛圍，目標字數約 {app_data.get('target_chapter_words')} 字。請直接開始寫小說正文："""

                    # 呼叫 Gemini API
                    model = genai.GenerativeModel(selected_model)
                    response = model.generate_content(prompt)
                    
                    app_data['generated_content'] = response.text
                    app_data['saved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("🎉 小說章節生成完畢！")

                except Exception as e:
                    st.error(f"生成過程發生錯誤: {e}")

    # 顯示生成的文章內容
    if app_data.get('generated_content'):
        st.subheader("📝 生成內容預覽")
        st.caption(f"最後生成時間：{app_data.get('saved_at')}")
        app_data['generated_content'] = st.text_area("正文內容", value=app_data.get('generated_content'), height=400)


# ------------------------------------------
# TAB 2: 長線伏筆與進度鎖
# ------------------------------------------
with tab2:
    st.subheader("🔮 長線伏筆與進度百分比控制")
    st.info("💡 你可以在此設定每個伏筆的揭開進度（0%~100%）與本章允許揭露的邊界，API 會嚴格遵循進度鎖定，防止提前劇透。")

    if st.button("➕ 新增伏筆項目"):
        new_f_id = f"f_{hash(datetime.now()) % 1000000000}"
        app_data['foreshadowing_list'].append({
            "id": new_f_id,
            "content": "",
            "progress": "0% (剛埋下/僅現象)",
            "status": "未解鎖",
            "current_stage_goal": "僅維持現象描寫，絕對不可解開或劇透！",
            "truth": ""
        })

    delete_target_id = None
    for idx, f_item in enumerate(app_data.get('foreshadowing_list', [])):
        f_id = f_item.get('id', f'f_{idx}')
        title_preview = f_item.get('content', '未命名伏筆')
        if len(title_preview) > 30: title_preview = title_preview[:30] + "..."
        
        with st.expander(f"📌 伏筆 [{f_id}]：{title_preview} 【當前進度：{f_item.get('progress', f_item.get('status', '0%'))}】", expanded=True):
            f_item['content'] = st.text_area("📍 伏筆表面現象/道具描寫", value=f_item.get('content', ''), height=70, key=f"fc_{f_id}")
            
            col_fs1, col_fs2 = st.columns([1, 2])
            with col_fs1:
                progress_opts = ["0% (剛埋下/僅現象)", "20% (發現甜頭/微小異常)", "50% (產生第一層誤解/疑心)", "80% (假真相/第一重反轉)", "100% (完全回收/終極真相)"]
                cur_p = f_item.get('progress', "0% (剛埋下/僅現象)")
                p_idx = progress_opts.index(cur_p) if cur_p in progress_opts else 0
                f_item['progress'] = st.selectbox("📊 解開進度鎖", progress_opts, index=p_idx, key=f"fp_{f_id}")
            
            with col_fs2:
                f_item['status'] = st.text_input("⏱️ 當前狀態簡述/預計解答章節", value=f_item.get('status', ''), key=f"fs_{f_id}")

            f_item['current_stage_goal'] = st.text_area(
                "🎯 本章允許揭露的邊界 (告訴 AI 本章只能寫到哪)", 
                value=f_item.get('current_stage_goal', '僅維持現象描寫，絕對不可解開或劇透！'), 
                height=70, 
                key=f"fcg_{f_id}"
            )

            f_item['truth'] = st.text_area("🔒 終極隱藏真相 (未達 100% 前嚴禁在文中透露)", value=f_item.get('truth', ''), height=100, key=f"ft_{f_id}")
            
            if st.button(f"🗑️ 刪除伏筆 {f_id}", key=f"fd_{f_id}"):
                delete_target_id = idx

    if delete_target_id is not None:
        app_data['foreshadowing_list'].pop(delete_target_id)
        st.rerun()


# ------------------------------------------
# TAB 3: 角色與登場卡片
# ------------------------------------------
with tab3:
    st.subheader("👥 登場角色卡片管理")
    
    if st.button("➕ 新增角色"):
        new_c_id = f"c{len(app_data['character_list']) + 1}"
        app_data['character_list'].append({
            "id": new_c_id,
            "name": "新角色",
            "category": "當前在場/主要角色",
            "faction": "",
            "public_relation": "",
            "hidden_motive": "",
            "summary": "",
            "personality": "",
            "status": "健康",
            "sanity": "100%",
            "speech_style": "",
            "dialogue_example": ""
        })

    del_c_idx = None
    for idx, c in enumerate(app_data.get('character_list', [])):
        with st.expander(f"👤 [{c.get('id')}] {c.get('name')} - {c.get('category')}", expanded=False):
            col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
            with col_c1:
                c['name'] = st.text_input("姓名", value=c.get('name', ''), key=f"cn_{idx}")
                c['category'] = st.text_input("分類", value=c.get('category', ''), key=f"cc_{idx}")
            with col_c2:
                c['status'] = st.text_input("生理狀態", value=c.get('status', ''), key=f"cs_{idx}")
                c['sanity'] = st.text_input("San理智值", value=c.get('sanity', ''), key=f"csan_{idx}")
            with col_c3:
                c['faction'] = st.text_input("陣營/身分", value=c.get('faction', ''), key=f"cf_{idx}")

            c['summary'] = st.text_area("簡介", value=c.get('summary', ''), key=f"csum_{idx}")
            c['personality'] = st.text_input("性格特質", value=c.get('personality', ''), key=f"cp_{idx}")
            c['hidden_motive'] = st.text_input("隱藏動機", value=c.get('hidden_motive', ''), key=f"chm_{idx}")
            c['speech_style'] = st.text_input("說話/交流風格", value=c.get('speech_style', ''), key=f"css_{idx}")
            
            if st.button(f"🗑️ 刪除角色 {c.get('name')}", key=f"cdel_{idx}"):
                del_c_idx = idx

    if del_c_idx is not None:
        app_data['character_list'].pop(del_c_idx)
        st.rerun()


# ------------------------------------------
# TAB 4: 世界觀與物品庫
# ------------------------------------------
with tab4:
    st.subheader("🌌 世界觀與核心祕密")
    app_data['book_title'] = st.text_input("書名", value=app_data.get('book_title', ''))
    app_data['book_theme'] = st.text_input("主題風格", value=app_data.get('book_theme', ''))
    app_data['book_overall_secret'] = st.text_area("🔒 全書終局世界觀真相 (全書最高機密)", value=app_data.get('book_overall_secret', ''), height=100)

    st.markdown("---")
    st.subheader("📋 確認規則列表 (Confirmed Rules)")
    for idx, r in enumerate(app_data.get('confirmed_rules_list', [])):
        r['content'] = st.text_input(f"規則 {r.get('id')}", value=r.get('content', ''), key=f"rule_{idx}")

    st.markdown("---")
    st.subheader("🎒 物品與道具庫 (Items Inventory)")
    for idx, item in enumerate(app_data.get('items_inventory', [])):
        col_i1, col_i2, col_i3 = st.columns([1, 2, 1])
        with col_i1:
            item['name'] = st.text_input("物品名稱", value=item.get('name', ''), key=f"itn_{idx}")
        with col_i2:
            item['status'] = st.text_input("狀態/細節", value=item.get('status', ''), key=f"its_{idx}")
        with col_i3:
            item['owner'] = st.text_input("持有者", value=item.get('owner', ''), key=f"ito_{idx}")

    st.markdown("---")
    st.subheader("📍 地點與地圖庫 (Location List)")
    for idx, loc in enumerate(app_data.get('location_list', [])):
        with st.expander(f"📍 地點：{loc.get('name')}"):
            loc['name'] = st.text_input("地點名稱", value=loc.get('name', ''), key=f"locn_{idx}")
            loc['visual_style'] = st.text_input("視覺風格", value=loc.get('visual_style', ''), key=f"locv_{idx}")
            loc['physics_detail'] = st.text_area("物理細節與規則", value=loc.get('physics_detail', ''), key=f"locp_{idx}")


# ------------------------------------------
# TAB 5: 章節大綱與歷史
# ------------------------------------------
with tab5:
    st.subheader("📚 卷目錄 (Volumes List)")
    for idx, v in enumerate(app_data.get('volumes_list', [])):
        v['title'] = st.text_input("卷名", value=v.get('title', ''), key=f"vt_{idx}")
        v['summary'] = st.text_area("卷大綱", value=v.get('summary', ''), key=f"vs_{idx}")

    st.markdown("---")
    st.subheader("📜 章節歷史列表 (Chapters List)")
    for idx, ch in enumerate(app_data.get('chapters_list', [])):
        col_ch1, col_ch2 = st.columns([1, 3])
        with col_ch1:
            st.markdown(f"**第 {ch.get('num')} 章**")
            ch['title'] = st.text_input("章節標題", value=ch.get('title', ''), key=f"cht_{idx}")
        with col_ch2:
            ch['summary'] = st.text_area("章節概要", value=ch.get('summary', ''), key=f"chs_{idx}")


# ------------------------------------------
# TAB 6: 寫作禁忌與風格
# ------------------------------------------
with tab6:
    st.subheader("🛠️ 寫作禁忌 (Negative Prompt)")
    app_data['writing_taboos'] = st.text_area("嚴格寫作禁忌與 Prompt 規範", value=app_data.get('writing_taboos', ''), height=250)

    st.subheader("🎭 語氣與文風設定")
    app_data['tone_setting'] = st.text_area("文風描寫參考 (如遠瞳、那一只蚊子)", value=app_data.get('tone_setting', ''), height=100)

