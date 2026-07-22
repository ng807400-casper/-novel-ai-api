import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from google import genai

app = FastAPI(
    title="長篇小說創作助手 API",
    description="具備長篇節奏控制、字數預算與大綱生成的專用 API",
    version="2.0.0"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ChapterRequest(BaseModel):
    volume_title: str = Field(default="第一集：失聲火車", description="本冊/本集名稱")
    target_volume_words: int = Field(default=100000, description="本集目標總字數 (例如 100000 字)")
    current_chapter: int = Field(default=3, description="目前章節數")
    total_chapters: int = Field(default=30, description="預估總章節數 (若一章 3000~4000 字，10 萬字約 30 章)")
    
    story_background: str = Field(
        default="列車陷入絕對死寂，時間停滯，手機電量是唯一的生命線與壓迫機制。全車乘客均持有 13 車車票。",
        description="世界觀與鐵律設定"
    )
    character_profiles: str = Field(
        default="蘇默（主角，冷靜理工男）、林欣（夥伴）、西裝男（半身麻痺異變者）、阿豪（驚恐乘客）",
        description="主要登場角色"
    )
    chapter_outline: str = Field(
        default="蘇默嘗試利用手機剩餘電量與車廂內的物理現象，推導無聲鐵律的觸發邊界。",
        description="本章具體大綱"
    )
    previous_summary: str = Field(
        default="前情提要：蘇默與林欣在 13 車會合，發現西裝男異變，手機電量降至 18%。",
        description="前情提要"
    )

def calculate_pacing_instruction(current: int, total: int) -> str:
    """根據章節進度百分比，自動產生給 AI 的節奏提示"""
    progress = (current / total) * 100
    
    if progress <= 15:
        return f"【進度：{progress:.1f}% - 開場鋪陳期】節奏應偏向懸疑與環境壓迫感。著重建立規則、展現危機與角色性格，不要過早揭露核心謎底。"
    elif progress <= 40:
        return f"【進度：{progress:.1f}% - 上昇動作期】危機開始升級。角色嘗試破解規則但遇到阻礙，小衝突不斷爆發，逐步累積心理壓力與懸念。"
    elif progress <= 60:
        return f"【進度：{progress:.1f}% - 中點大轉折 (Midpoint)】爆發重大轉折或偽勝利/偽失敗！揭露關鍵線索（如 13 車車票的隱藏秘密），徹底改變故事走向。"
    elif progress <= 85:
        return f"【進度：{progress:.1f}% - 黎明前的黑暗】局勢惡化，資源（電量/時間）即將耗盡。角色的信念受考驗，陷入極度絕望與最後的備戰準備。"
    elif progress <= 95:
        return f"【進度：{progress:.1f}% - 核心大高潮 (Climax)】所有線索與張力集中爆發！主角必須做出重大抉擇，利用前期累積的知識/規則進行最終搏鬥。"
    else:
        return f"【進度：{progress:.1f}% - 尾聲收束】高潮過後的餘波、解謎回應與本集收尾，同時留下引向下一集的隱晦伏筆。"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "長篇小說節奏控管 API 正常運作中！"}

@app.post("/v1/chapter/stream")
async def generate_chapter_stream(req: ChapterRequest):
    """根據總篇幅進度與節奏引導，串流生成章節內文"""
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 未設定")

    pacing_guide = calculate_pacing_instruction(req.current_chapter, req.total_chapters)
    approx_chapter_words = int(req.target_volume_words / req.total_chapters)

    prompt = f"""
    你是一位精通故事結構與節奏控制的職業長篇小說家。
    目前正在撰寫《{req.volume_title}》，本冊目標總篇幅為 {req.target_volume_words} 字。
    當前為第 {req.current_chapter} 章 / 共 {req.total_chapters} 章。
    本章預計篇幅約：{approx_chapter_words} 字。

    【當前劇情節奏指導】
    {pacing_guide}

    【世界觀與無聲鐵律】
    {req.story_background}

    【登場角色】
    {req.character_profiles}

    【前情提要】
    {req.previous_summary}

    【本章大綱需求】
    {req.chapter_outline}

    請務必遵循上述【節奏指導】，掌控場景描寫與張力推移，開始撰寫本章內文：
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
