import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from google import genai

app = FastAPI(
    title="長篇連載小說創作助手 API",
    description="具備跨集歷史記憶、篇幅節奏控管與字數預算的長篇小說專用 API",
    version="2.1.0"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ChapterRequest(BaseModel):
    # 1. 本集與進度資訊
    volume_title: str = Field(default="第二集：深淵迴響", description="本冊/本集名稱")
    target_volume_words: int = Field(default=100000, description="本集目標總字數 (如 100000 字)")
    current_chapter: int = Field(default=1, description="目前章節數")
    total_chapters: int = Field(default=30, description="預估本集總章節數")
    
    # 2. 跨集歷史記憶 (解決第二集延續第一集設定的核心機制)
    previous_volumes_summary: str = Field(
        default="""
        【前情歷程與第一集《失聲火車》既定事實】：
        1. 蘇默與林欣利用 13 車車票的逆向解謎機制，暫時破解了第一階段的死寂異變。
        2. 阿豪在第一集第 12 章不幸遭到無聲鐵律吞噬身亡（已陣亡）。
        3. 西裝男半身異變後獲得感應死寂頻率的能力，目前仍處於極度虛弱狀態。
        4. 蘇默的手機電量在第一集結尾被鎖定在 1%，成為永久性的規則標記與生命線。
        """,
        description="前幾集的重大既定歷史、生死狀態與獲得的關鍵標記"
    )
    
    # 3. 本集背景與角色設定
    story_background: str = Field(
        default="列車駛入第二階段異變區域，無聲鐵律出現衍生規則，手機電量 1% 成為觸發特殊感應的介面。",
        description="本集世界觀與運作鐵律"
    )
    character_profiles: str = Field(
        default="蘇默（主角，冷靜理工男，手機常駐 1% 電量）、林欣（求生夥伴，負責心理與物資調配）、西裝男（半身異變感應者）",
        description="主要登場角色卡"
    )
    
    # 4. 本章大綱與前情提要
    chapter_outline: str = Field(
        default="第二集第一章：列車進入全新暗黑隧道，蘇默發現常駐 1% 電量的手機開始接收到不屬於本車廂的未知微波訊號。",
        description="本章具體大綱"
    )
    previous_summary: str = Field(
        default="上一章（第一集結尾）：眾人從 13 車險勝，列車發出劇烈震撼，駛入未知的第二階段區域。",
        description="上一章的前情提要"
    )

def calculate_pacing_instruction(current: int, total: int) -> str:
    """根據章節進度百分比，自動產生三幕劇節奏提示"""
    progress = (current / total) * 100
    
    if progress <= 15:
        return f"【進度：{progress:.1f}% - 開場鋪陳期】節奏應偏向懸疑與環境壓迫感。著重建立新階段規則、展現前集過渡後的心理陰影與新危機，不要過早揭露核心大謎底。"
    elif progress <= 40:
        return f"【進度：{progress:.1f}% - 上昇動作期】危機開始升級。角色嘗試破解新規則但遇到阻礙，衝突逐步升溫，累積心理壓力。"
    elif progress <= 60:
        return f"【進度：{progress:.1f}% - 中點大轉折 (Midpoint)】爆發重大轉折！揭露關於列車或前集伏筆的關鍵真相，徹底改變本集的走向與目標。"
    elif progress <= 85:
        return f"【進度：{progress:.1f}% - 黎明前的黑暗】局勢嚴峻惡化，資源即將耗盡，角色的信念與生理極限受重大考驗。"
    elif progress <= 95:
        return f"【進度：{progress:.1f}% - 核心大高潮 (Climax)】所有線索與張力集中爆發！主角必須結合第一集獲得的經驗與本集的推演進行最終決斷。"
    else:
        return f"【進度：{progress:.1f}% - 尾聲收束】高潮過後的餘波、解謎回應與本集收尾，同時留下引向下一集的隱晦伏筆。"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "長篇連載小說創作 API (含跨集記憶) 正常運作中！"}

@app.post("/v1/chapter/stream")
async def generate_chapter_stream(req: ChapterRequest):
    """根據總篇幅進度、跨集歷史記憶與節奏引導，串流生成章節內文"""
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 未設定")

    pacing_guide = calculate_pacing_instruction(req.current_chapter, req.total_chapters)
    approx_chapter_words = int(req.target_volume_words / req.total_chapters)

    prompt = f"""
    你是一位精通長篇連載小說架構與懸疑節奏的職業小說家。
    目前正在撰寫《{req.volume_title}》，本冊目標總篇幅為 {req.target_volume_words} 字。
    當前進度：第 {req.current_chapter} 章 / 共 {req.total_chapters} 章（本章目標字數約 {approx_chapter_words} 字）。

    【前集歷程與既定歷史 (跨集記憶 constraint)】
    {req.previous_volumes_summary}
    *(特別注意：必須絕對遵循上述前集歷史！已陣亡角色不可無故復活，已獲得的標記/能力需保持一致)*

    【當前劇情節奏指導】
    {pacing_guide}

    【本集世界觀與無聲鐵律】
    {req.story_background}

    【登場角色】
    {req.character_profiles}

    【上一章前情提要】
    {req.previous_summary}

    【本章大綱需求】
    {req.chapter_outline}

    請務必遵循【跨集記憶】與【節奏指導】，掌控場景描寫、懸疑張力與角色對話，開始撰寫本章內文：
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
