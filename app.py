import streamlit as st
import requests

# 頁面基本設定
st.set_page_config(page_title="專業小說家 AI 寫作工作站", page_icon="✍️", layout="wide")

st.title("✍️ 專業小說家 AI 寫作工作站")
st.caption("具備長篇結構控管、單章字數預算、伏筆錨點與風格禁忌的深度創作介面")

# 設定 Render API 網址
API_URL = "https://novel-ai-api-himy.onrender.com/v1/chapter/stream"

# ================= 側邊欄：宏觀架構與世界觀設定 =================
with st.sidebar:
    st.header("📚 1. 宏觀架構 (本冊/全書設定)")
    volume_title = st.text_input("本冊/本集名稱", value="第一集：失聲火車")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        target_volume_words = st.number_input("本集目標總字數", value=100000, step=10000)
        current_chap = st.number_input("目前撰寫章節", value=6, min_value=1)
    with col_v2:
        total_chaps = st.number_input("預估本集總章數", value=30, min_value=1)
        # 自動計算單章建議字數
        suggested_words = int(target_volume_words / total_chaps)
        st.info(f"💡 建議單章字數：約 {suggested_words} 字")
        
    st.divider()
    
    volume_overall_outline = st.text_area(
        "🗺️ 本集整體大綱與核心主線",
        value="""【失聲火車主線】
主角蘇默在陷入時間停滯與無聲鐵律的列車中醒來，必須利用理工物理知識推演規則邊界，與夥伴林欣合作，並透過 13 車車票與 1% 電量手機，在必死事故中尋找逆向解謎的唯一生路。""",
        height=150
    )
    
    previous_volumes_summary = st.text_area(
        "📜 既定歷史與前情總結 (AI 不可違背)",
        value="""1. 蘇默與林欣確認了「無聲鐵律」存在，全車均持 13 車車票。
2. 阿豪已發聲陣亡（已死）；西裝男半身麻痺昏迷。
3. 蘇默的手機電量鎖定在 1%，為永久規則標記。""",
        height=150
    )
    
    story_bg = st.text_area("🌌 世界觀與運作鐵律", value="列車陷入絕對死寂，時間停滯，手機電量是唯一的生命線。", height=100)
    character_cards = st.text_area("👤 登場角色卡", value="蘇默（冷靜理工男，手機常駐 1%）、林欣（求生夥伴）", height=100)

# ================= 主畫面：微觀單章寫作與控管 =================
st.subheader(f"📖 2. 微觀寫作：{volume_title} — 第 {current_chap} 章 / 共 {total_chaps} 章")

# 第一排：單章目標字數與視角設定
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    target_chapter_words = st.number_input("🎯 本章目標字數", value=suggested_words, step=500)
with col_m2:
    pov_setting = st.selectbox("👁️ 寫作視角", ["第一人稱 (蘇默視角)", "第三人稱限制視角", "第三人稱全知視角"])
with col_m3:
    tone_setting = st.text_input("🎭 本章情緒基調", value="極度壓抑、懸疑冷酷、理性推算")

st.divider()

# 第二排：上一章銜接點與本章大綱
col_l, col_r = st.columns(2)
with col_l:
    previous_summary = st.text_area(
        "📌 上一章結尾錨點 (畫面/局勢銜接點)",
        value="上一章（第 5 章）結尾：蘇默盯著手機螢幕上常駐的 1% 電量，突然發現畫面上閃爍出一條未知微波訊號，前方鐵門傳來輕微扣擊聲...",
        height=130
    )
    must_include = st.text_area(
        "🔑 本章必須出現的伏筆/關鍵道具",
        value="• 手機 1% 電量接收到的神祕微波數據\n• 車廂鐵門上的刺鼻金屬鏽蝕味",
        height=100
    )

with col_r:
    chapter_outline = st.text_area(
        "🎯 本章具體大綱與情節推進",
        value="第六章：蘇默與林欣戒備地靠近鐵門，透過門縫觀察前方車廂，同時蘇默嘗試解析手機接收到的神秘訊號。",
        height=130
    )
    writing_taboos = st.text_area(
        "🚫 寫作禁忌與風格避雷 (Negative Prompt)",
        value="• 禁止出現感性說教台詞\n• 禁止主角無故陷入驚慌失措\n• 對話需簡短、注重環境物理描寫",
        height=100
    )

generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

# ================= 生成與成果展示 =================
if generate_btn:
    st.markdown("---")
    st.subheader("📝 本章生成成果：")
    
    # 組合完整的提示詞發給後端 API
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
        "character_profiles": character_cards,
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
        else:
            st.error(f"生成失敗，伺服器回應狀態碼：{response.status_code}")
    except Exception as e:
        st.error(f"連線發生錯誤：{str(e)}")
