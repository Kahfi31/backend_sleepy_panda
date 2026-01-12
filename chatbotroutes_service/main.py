from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
from langdetect import detect, DetectorFactory
import time
import logging

# Agar deteksi bahasa konsisten
DetectorFactory.seed = 0

load_dotenv()
app = FastAPI()
logger = logging.getLogger("chatbot")

# ============================================================
# DATA MODELS (PENGGANTI SCHEMAS.PY)
# ============================================================
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    response_time_ms: float

# ============================================================
# MIDDLEWARE RESPONSE TIME
# ============================================================
@app.middleware("http")
async def add_response_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
    "Request %s %s completed in %.2f ms",
    request.method,
    request.url.path,
    process_time_ms
    )

    response.headers["X-Response-Time-ms"] = str(process_time_ms)
    return response


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = os.getenv("GEMINI_URL")

# Prompt template per bahasa
STYLE_PROMPTS = {
    "id": """
Kamu adalah teman yang ngobrol santai, bukan AI. 
Gaya bicaramu:
- pake bahasa sehari-hari
- intonasinya lembut dan empatik
- jangan pakai format markdown
- jawab natural, kayak manusia
- tanya balik kalau konteks belum jelas
- boleh pakai emoji tapi jangan berlebihan
- fokus pada konteks tidur/insomnia/kecemasan
""",
    "jv": """
Kowe kuwi kancane ngobrol santai, dudu AI.
Gaya omonganmu:
- nganggo basa Jawa ngoko sing alus
- omongane empatik lan nenangake
- aja nganggo markdown utawa format khusus
- wangsulana kanthi alami kaya wong tenan
- takon maneh yen konteks durung cetha
- oleh nganggo emoji, nanging ojo kakehan
- fokus marang turu, ora isa turu, lan rasa kuatir
""",
   "en": """
You are a friendly conversational partner, not an AI.
Style:
- casual everyday English
- empathetic and soft tone
- do NOT use markdown
- do NOT use **bold**, *italic*, underscores, or bullet formatting
- respond naturally, like a human texting
- ask clarifying questions if context is unclear
- emojis allowed but not excessive
- focus on sleep/insomnia/anxiety topics
""",
    "es": """
Eres un amigo con quien hablar de manera casual, no una IA.
Estilo:
- usa lenguaje cotidiano
- habla con suavidad y empatía
- no uses markdown
- responde naturalmente
- pregunta si no entiendes el contexto
- emojis permitidos pero moderados
- enfócate en sueño, insomnio o ansiedad
""",
    "fr": """
Tu es un ami avec qui on discute de façon décontractée, pas une IA.
Style:
- utilise un langage quotidien
- parle doucement et avec empathie
- pas de markdown
- réponds naturellement
- pose des questions si le contexte n'est pas clair
- emojis autorisés mais modérés
- concentre-toi sur le sommeil, l’insomnie ou l’anxiété
""",
    "ja": """
あなたはカジュアルに話す友達で、AIではありません。
スタイル:
- 日常的な言葉を使う
- 優しく共感的に話す
- マークダウンは使わない
- 人間のように自然に答える
- 文脈が不明なら質問する
- 絵文字は少しだけ使用可
- 睡眠、不眠、または不安に集中
"""
}

# ============================================================
# PARSER GEMINI (UNIVERSAL)
# ============================================================
def extract_text_from_gemini(data: dict) -> str:
    candidates = data.get("candidates")
    if not candidates:
        raise Exception("Gemini returned no candidates")
    
    candidate = candidates[0]

    if candidate.get("text"):
        return candidate["text"]

    content = candidate.get("content")
    collected_texts = []

    if isinstance(content, dict):
        for p in content.get("parts", []):
            if p.get("text", "").strip():
                collected_texts.append(p["text"])
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            for p in block.get("parts", []):
                if p.get("text", "").strip():
                    collected_texts.append(p["text"])

    if collected_texts:
        return "\n".join(collected_texts)

    pf = data.get("promptFeedback")
    if pf and pf.get("blockReason"):
        return f"[Model memblokir respons: {pf['blockReason']}]"

    raise Exception("Gemini returned no usable text")

# ============================================================
# CHAT ENDPOINT (STATELESS)
# ============================================================
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        lang_code = detect(req.message)
    except:
        lang_code = "id"

    # Override deteksi bahasa untuk kata kunci Jawa spesifik
    if any(word in req.message.lower() for word in ["ora", "merga", "turu", "atiku"]):
        lang_code = "jv"

    prompt_style = STYLE_PROMPTS.get(lang_code, STYLE_PROMPTS["id"])
    prompt = f"{prompt_style}\nUser: {req.message}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.95,
            "topK": 60,
            "topP": 0.99,
            "maxOutputTokens": 300
        }
    }

    try:
        start_time = time.perf_counter()

        response = requests.post(
            f"{GEMINI_URL}:generateContent?key={GEMINI_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        response.raise_for_status()

        text = extract_text_from_gemini(response.json())

        response_time_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )

        return ChatResponse(
            response=text,
            response_time_ms=response_time_ms
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error connecting to Gemini API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))