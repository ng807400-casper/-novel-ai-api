import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai

app = FastAPI(
    title="AI 小說創作助手 API",
    description="專為長篇小說生成大綱、角色與章節內容的 API",
    version="1.0.0"
)

# 從系統環境變數獲取 API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # 提醒：可以在 Render 的 Environment 頁面設定此變數
    pass

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 資料結構定義
class ChapterRequest(BaseModel):
    story_background: str  # 世界觀/故事背景
    character_profiles: str # 登場角色設定
    chapter_outline: str   # 本章大綱
    previous_summary: str = "" # 前情提要 (可選)

class OutlineRequest(BaseModel):
    genre: str             # 小說類型 (例如：科幻、玄幻、職場)
    core_concept: str      # 故事核心概念/靈感

@app.get("/")
def read_root():
    return {"status": "ok", "message": "小說寫作 API 正常運作中！"}

@app.post("/v1/outline")
async def generate_outline(req: OutlineRequest):
    """生成故事大綱與三幕劇結構"""
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 未設定")
    
    prompt = f"請為一部【{req.genre}】類型的小說設計詳細的故事大綱與核心衝突。\n靈感概念：{req.core_concept}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"outline": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chapter/stream")
async def generate_chapter_stream(req: ChapterRequest):
    """串流生成小說章節內容 (適合長文本，避免 Timeout)"""
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 未設定")

    prompt = f"""
    你是一位專業的小說家。請根據以下設定，撰寫流暢且富有畫面感的章節內容，注重動作與對話描寫：

    【世界觀與背景】
    {req.story_background}

    【登場角色】
    {req.character_profiles}

    【前情提要】
    {req.previous_summary}

    【本章大綱】
    {req.chapter_outline}

    請開始撰寫本章內文：
    """

    def text_generator():
        response = client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=prompt
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    return StreamingResponse(text_generator(), media_type="text/plain")
