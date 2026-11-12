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
    timeout=65.0
)

def extract_clean_text(message) -> str:
    """Extrae el texto limpio eliminando bloques <think> incluso si falta la etiqueta de apertura."""
    content = getattr(message, "content", None)
    if not content:
        content = getattr(message, "reasoning_content", "") or ""
    
    text = str(content)
    # 1. Si el modelo cerró con </think>, descartar todo lo anterior
    if "</think>" in text:
        text = text.split("</think>")[-1]
    
    # 2. Eliminar cualquier bloque <think>...</think> restante
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text

def clean_vision_diagnosis(text: str) -> str:
    """Se queda únicamente con la última línea limpia del diagnóstico visual."""
    if not text:
        return "IMAGEN_NO_RECONOCIDA"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1].strip("*_ \"'") if lines else "IMAGEN_NO_RECONOCIDA"

def clean_final_report(text: str) -> str:
    """Elimina cualquier borrador en inglés previo al primer encabezado Markdown (### o ##)."""
    if not text:
        return ""
    # Busca el primer encabezado Markdown (## o ###) y corta todo el borrador previo
    match = re.search(r"(^|\n)(#{1,3}\s+)", text)
    if match:
        return text[match.start(2):].strip()
    
    # Respaldo por si el modelo escribió "Let's draft:" sin usar ###
    if "Let's draft:" in text:
        return text.split("Let's draft:")[-1].strip()
    return text.strip()

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
    """Core AI Agent workflow optimized for low latency and clean output."""
    
    # 1. Process image file into Base64 format in memory
    try:
        image_bytes = await file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data = f"data:{file.content_type};base64,{encoded_image}"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to process the uploaded image.")

    # 2. Fast Vision Processing
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
            max_tokens=250
        )
        raw_text = extract_clean_text(vision_response.choices[0].message)
        raw_diagnosis = clean_vision_diagnosis(raw_text)
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

    # 4. Fast LLM Synthesis
    mode_prompts = {
        "educativo": (
            "detailed thinking off\n"
            "Eres un científico y educador conciso. Empieza tu respuesta DIRECTAMENTE con un título ### sin introducción. "
            "Usa viñetas cortas, datos precisos sobre taxonomía o historia, y emojis científicos (🔬, 🧬, 📊)."
        ),
        "turistico": (
            "detailed thinking off\n"
            "Eres un guía turístico carismático y directo. Empieza tu respuesta DIRECTAMENTE con un título ### sin introducción. "
            "Cuenta datos curiosos e historia local en viñetas cortas con emojis de viaje (✈️, 🗺️, 📸)."
        ),
        "explorador": (
            "detailed thinking off\n"
            "Eres un aventurero experto en geografía. Empieza tu respuesta DIRECTAMENTE con un título ### sin introducción. "
            "Conecta el sujeto con su entorno e importancia cultural en viñetas cortas con emojis de aventura (🧭, 🌍, 🏕️)."
        )
    }
    agent_persona = mode_prompts.get(modo, mode_prompts["explorador"])

    final_prompt = (
        f"UBICACIÓN: {ubicacion}\n"
        f"SUJETO IDENTIFICADO: {raw_diagnosis}\n"
        f"CONTEXTO WEB: {web_context}\n\n"
        f"INSTRUCCIÓN:\n"
        f"1. Empieza DIRECTAMENTE con el primer encabezado '### '. Prohibido incluir borradores o introducciones.\n"
        f"2. Redacta un reporte ágil dividido en 3 secciones breves con Markdown (###).\n"
        f"3. LÍMITE DE LONGITUD: Máximo 180 palabras en total.\n"
        f"4. IDIOMA OBLIGATORIO: Responde estrictamente en '{idioma}'."
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
                max_tokens=850
            )
        except Exception:
            text_response = nebius_client.chat.completions.create(
                model="nvidia/Nemotron-3.5-Super-VL",
                messages=[
                    {"role": "system", "content": agent_persona},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.3,
                max_tokens=850
            )
        raw_report = extract_clean_text(text_response.choices[0].message)
        final_report = clean_final_report(raw_report)
    except Exception as e:
        print(f"\n🚨 ERROR REAL DEL MODELO DE TEXTO: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Error de API Texto: {str(e)}")

    # 5. Return final payload
    return {
        "diagnostico_interno": raw_diagnosis,
        "ficha_final": final_report
    }
