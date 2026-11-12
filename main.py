import base64
import os
import re
import requests
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Visual Explorer - Nebius Hackathon")

# Configure static files directory for frontend assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Nebius AI client
nebius_client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=os.environ.get("NEBIUS_API_KEY"),
    timeout=60.0
)

def extract_clean_text(message) -> str:
    """Safely extracts text from reasoning models, removing <think> tags."""
    content = getattr(message, "content", None)
    if not content:
        content = getattr(message, "reasoning_content", "") or ""
    
    cleaned = re.sub(r"<think>.*?</think>", "", str(content), flags=re.DOTALL).strip()
    return cleaned if cleaned else str(content).strip()

def get_tavily_context(query: str) -> str:
    """Retrieves real-time context from the Tavily search API with fast timeout."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "No real-time internet connection available."
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 1
    }
    try:
        # Fast 5-second timeout so web search never bottlenecks the LLM
        response = requests.post(url, json=payload, timeout=5.0)
        response.raise_for_status()
        results = response.json().get("results", [])
        context = " ".join([res.get("content", "") for res in results])
        return context[:800] if context else "No recent relevant results found."
    except Exception as e:
        return f"Context unavailable: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the main frontend interface."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Missing index.html</h1><p>Please ensure the 'static' folder exists and contains index.html.</p>"

@app.post("/api/analizar")
async def analyze_environment(
    file: UploadFile = File(...),
    modo: str = Form(...),
    idioma: str = Form(...),
    ubicacion: str = Form(default="Ubicación desconocida")
):
    """Core AI Agent workflow optimized for low latency."""
    
    # 1. Process image file into Base64 format in memory
    try:
        image_bytes = await file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data = f"data:{file.content_type};base64,{encoded_image}"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to process the uploaded image.")

    # 2. Fast Vision Processing (detailed thinking off)
    vision_prompt = (
        "Identifica el sujeto principal de esta imagen. "
        "REGLA 1: Si está borrosa, oscura o no hay sujeto claro, responde SOLO: 'IMAGEN_NO_RECONOCIDA'. "
        "REGLA 2: Si lo identificas, responde ÚNICAMENTE con el nombre común y científico en máximo 8 palabras. "
        "REGLA 3: Cero explicaciones adicionales."
    )
    
    try:
        vision_response = nebius_client.chat.completions.create(
            model="nvidia/Nemotron-3.5-Super-VL",
            messages=[
                {"role": "system", "content": "detailed thinking off"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": image_data}},
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=200
        )
        raw_diagnosis = extract_clean_text(vision_response.choices[0].message)
        if not raw_diagnosis:
            raw_diagnosis = "IMAGEN_NO_RECONOCIDA"
    except Exception as e:
        print(f"\n🚨 ERROR REAL DEL MODELO VISUAL: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Error de API Visual: {str(e)}")

    # Fast circuit breaker for unrecognized images
    if "IMAGEN_NO_RECONOCIDA" in raw_diagnosis or "no reconocida" in raw_diagnosis.lower():
        fallback_messages = {
            "es": "¡Vaya! 😅 No logro distinguir bien el sujeto principal. ¿Podrías intentar con una foto más clara?",
            "en": "Oops! 😅 I can't clearly distinguish the main subject. Could you try a clearer photo?",
            "fr": "Oups ! 😅 Je n'arrive pas à bien distinguer le sujet principal. Pourriez-vous essayer avec une photo plus claire ?",
            "de": "Hoppla! 😅 Ich kann das Hauptmotiv nicht klar erkennen. Könnten Sie ein klareres Foto versuchen?",
            "zh": "哎呀！😅 我无法清楚地分辨出主要目标。您能尝试拍一张更清晰的照片吗？"
        }
        return {
            "diagnostico_interno": "Unrecognized Image",
            "ficha_final": fallback_messages.get(idioma, fallback_messages["en"])
        }

    # 3. Context Retrieval (Tavily Agent)
    tavily_query = f"{raw_diagnosis} {ubicacion}"
    web_context = get_tavily_context(tavily_query)

    # 4. Fast LLM Synthesis (detailed thinking off + strict length cap)
    mode_prompts = {
        "educativo": (
            "detailed thinking off\n"
            "Eres un científico y educador conciso. Usa títulos en Markdown (###), viñetas cortas y datos precisos "
            "sobre taxonomía o historia. Usa emojis científicos (🔬, 🧬, 📊)."
        ),
        "turistico": (
            "detailed thinking off\n"
            "Eres un guía turístico carismático y directo. Cuenta datos curiosos e historia local en viñetas cortas. "
            "Usa títulos en Markdown (###) y emojis de viaje (✈️, 🗺️, 📸)."
        ),
        "explorador": (
            "detailed thinking off\n"
            "Eres un aventurero experto en geografía. Conecta el sujeto con su entorno e importancia cultural en viñetas cortas. "
            "Usa títulos en Markdown (###) y emojis de aventura (🧭, 🌍, 🏕️)."
        )
    }
    agent_persona = mode_prompts.get(modo, mode_prompts["explorador"])

    final_prompt = (
        f"UBICACIÓN: {ubicacion}\n"
        f"SUJETO IDENTIFICADO: {raw_diagnosis}\n"
        f"CONTEXTO WEB: {web_context}\n\n"
        f"INSTRUCCIÓN:\n"
        f"1. Redacta un reporte ágil dividido en 3 secciones breves con Markdown (###).\n"
        f"2. LÍMITE DE LONGITUD: Máximo 180 palabras en total. Ve directo al grano sin introducciones largas.\n"
        f"3. IDIOMA OBLIGATORIO: Responde estrictamente en '{idioma}'."
    )

    try:
        try:
            text_response = nebius_client.chat.completions.create(
                model="nvidia/Nemotron-3.5-Lightning",
                messages=[
                    {"role": "system", "content": agent_persona},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
        except Exception as e_light:
            print(f"⚠️ Aviso: Lightning falló ({e_light}), usando Super-VL como respaldo.")
            text_response = nebius_client.chat.completions.create(
                model="nvidia/Nemotron-3.5-Super-VL",
                messages=[
                    {"role": "system", "content": agent_persona},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
        final_report = extract_clean_text(text_response.choices[0].message)
    except Exception as e:
        print(f"\n🚨 ERROR REAL DEL MODELO DE TEXTO: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Error de API Texto: {str(e)}")

    # 5. Return final payload
    return {
        "diagnostico_interno": raw_diagnosis,
        "ficha_final": final_report
    }
