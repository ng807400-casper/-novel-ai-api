import streamlit as st
import requests

# 頁面基本設定
st.set_page_config(page_title="AI 小說家創作工作站", page_icon="✍️", layout="wide")

st.title("✍️ 長篇小說創作工作站")
st.caption("專為小說家設計的無程式感寫作介面")

# 設定你的 Render API 網址 (本地或線上)
API_URL = "https://novel-ai-api-himy.onrender.com/v1/chapter/stream"

# 側邊欄：小說核心設定檔 (Lorebook)
with st.sidebar:
    st.header("📚 本冊設定與記憶")
    volume_title = st.text_input("本冊名稱", value="第一集：失聲火車")
    
    col1, col2 = st.columns(2)
    with col1:
        target_words = st.number_input("本冊目標字數", value=100000, step=10000)
        current_chap = st.number_input("目前撰寫章節", value=6, min_value=1)
    with col2:
        total_chaps = st.number_input("預估總章節數", value=30, min_value=1)
        
    st.divider()
    
    previous_volumes_summary = st.text_area(
        "📜 跨集/前情歷史既定事實 (AI 不會違背此紀錄)",
        value="""1. 蘇默與林欣確認了「無聲鐵律」存在，並發現全車持 13 車車票。
2. 阿豪已發聲陣亡；西裝男半身麻痺昏迷。
3. 蘇默的手機電量鎖定在 1%，為永久規則標記。""",
        height=200
    )
    
    story_bg = st.text_area("🌌 本集世界觀與運作鐵律", value="列車陷入絕對死寂，時間停滯，手機電量是唯一的生命線。", height=100)
    character_cards = st.text_area("👤 登場角色卡", value="蘇默（冷靜理工男，手機常駐 1%）、林欣（求生夥伴）", height=100)

# 主畫面：章節寫作區
st.subheader(f"📖 正在撰寫：{volume_title} — 第 {current_chap} 章")

col_left, col_right = st.columns(2)

with col_left:
    previous_summary = st.text_area(
        "📌 上一章結尾錨點 (接續點)",
        value="上一章（第 5 章）結尾：蘇默盯著手機螢幕上常駐的 1% 電量，突然發現畫面上閃爍出一條未知微波訊號，前方鐵門傳來輕微扣擊聲...",
        height=120
    )

with col_right:
    chapter_outline = st.text_area(
        "🎯 本章具體大綱與情節構想",
        value="第六章：蘇默與林欣戒備地靠近鐵門，透過門縫觀察前方車廂，同時蘇默嘗試解析手機接收到的神秘訊號。",
        height=120
    )

generate_btn = st.button("✨ 開始生成本章小說內文", type="primary", use_container_width=True)

# 顯示生成的文章內容
if generate_btn:
    st.markdown("---")
    st.subheader("📝 生成內文成果：")
    
    payload = {
        "volume_title": volume_title,
        "target_volume_words": target_words,
        "current_chapter": current_chap,
        "total_chapters": total_chaps,
        "previous_volumes_summary": previous_volumes_summary,
        "story_background": story_bg,
        "character_profiles": character_cards,
        "chapter_outline": chapter_outline,
        "previous_summary": previous_summary
    }
    
    try:
        # 呼叫你背後建好的 API
        response = requests.post(API_URL, json=payload, stream=True)
        
        if response.status_code == 200:
            # 即時打字機效果輸出
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
