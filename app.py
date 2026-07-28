# 🎯 嚴格遵循模型調用指令：優先 gemini-flash-latest，備選 gemini-3.5-flash
target_model = "gemini-flash-latest"
try:
    model = genai.GenerativeModel(target_model)
except Exception:
    target_model = "gemini-3.5-flash"
    model = genai.GenerativeModel(target_model)
