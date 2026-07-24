# ================= 動態視角指令生成 =================
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

# ================= 最終傳給 Gemini 的 Prompt =================
prompt = f"""
你是一位頂級的懸疑 / 克蘇魯 / 規則怪談小說作家。請根據以下完整的全書世界觀、區域設定與本章微調指令，為我撰寫小說最新一章的純內文。

【全書背景】
• 書名：{book_title} ({book_theme})
• 全書終局真相：{book_overall_secret}

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
{previous_summary}

【本章撰寫精準指令】
• 當前章節：{current_vol_title} 第 {current_chap} 章
• 本章大綱：{chapter_outline}
• 目標字數：約 {target_chapter_words} 字
{perspective_instruction}
• 時間與環境：{time_and_environment}
• 五感描寫重點：\n{sensory_details}
• 核心衝突：{scene_conflict}
• 認知大翻轉：{scene_turn}
• 必須包含元素：\n{must_include}
• 寫作禁忌 (Negative Prompt)：\n{writing_taboos}

【寫作與格式極嚴格要求】
1. **直接輸出純小說內文**，不要帶有任何開場白、結語、分析文字或系統日誌標籤（如：【監控端日誌】等）。
2. 保持極度壓抑、嚴密符合規則怪談的氣氛。
3. 嚴格遵守寫作禁忌的設定
"""
