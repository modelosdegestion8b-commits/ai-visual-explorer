import base64
import os
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

# Initialize Nebius AI client with a strict timeout to prevent hanging requests
nebius_client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=os.environ.get("NEBIUS_API_KEY"),
    timeout=75.0  # Stability patch: Prevents the server from hanging indefinitely
)

def get_tavily_context(query: str) -> str:
    """Retrieves real-time context from the Tavily search API."""
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
        # Added timeout to prevent external API bottlenecks
        response = requests.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        results = response.json().get("results", [])
        context = " ".join([res.get("content", "") for res in results])
        return context if context else "No recent relevant results found."
    except Exception as e:
        return f"Error retrieving data: {str(e)}"

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
    """Core AI Agent workflow: Vision Analysis -> Web Context -> LLM Synthesis."""
    
    # 1. Process image file into Base64 format in memory
    try:
        image_bytes = await file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data = f"data:{file.content_type};base64,{encoded_image}"
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to process the uploaded image.")

    # 2. Vision Processing (openbmb/MiniCPM-V-4_5)
    vision_prompt = (
        "Eres un experto en análisis visual. Tu tarea es identificar el sujeto principal de esta imagen. "
        "REGLA 1: Si la imagen está demasiado borrosa, oscura, cortada, o no hay un sujeto claramente identificable, "
        "responde ÚNICAMENTE con la frase exacta: 'IMAGEN_NO_RECONOCIDA'. "
        "REGLA 2: Si puedes identificarlo, responde en una sola frase corta y precisa con el nombre más exacto que deduzcas "
        "(fíjate muy bien en detalles estructurales para no confundir especies o estilos similares). "
        "REGLA 3: No des explicaciones, solo la frase corta o la palabra de error."
    )
    
    try:
        vision_response = nebius_client.chat.completions.create(
            model="openbmb/MiniCPM-V-4_5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": image_data}},
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        raw_diagnosis = vision_response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Vision model timeout or internal error.")

    # Stability Patch: Fast circuit breaker for unrecognized images
    # Prevents unnecessary calls to Tavily and the text LLM, saving time and preventing hallucination timeouts.
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
    tavily_query = f"{raw_diagnosis} en {ubicacion} contexto actual, historia o noticias"
    web_context = get_tavily_context(tavily_query)

    # 4. LLM Synthesis (nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B)
    mode_prompts = {
        "educativo": (
            "Eres un científico y educador riguroso pero accesible. "
            "Tu objetivo es enseñar. Usa una estructura clara con títulos en Markdown (###), viñetas y datos precisos "
            "sobre taxonomía, mecanismos físicos o historia. Mantén un tono académico pero fascinante. Usa emojis científicos (🔬, 🧬, 📊)."
        ),
        "turistico": (
            "Eres el mejor guía turístico del mundo, carismático y entretenido. "
            "Tu objetivo es maravillar al usuario. Cuenta historias locales, mitos, datos curiosos y tips. "
            "Usa títulos en Markdown (###), viñetas y emojis de viaje (✈️, 🗺️, 📸). Mantén un tono cálido y emocionante."
        ),
        "explorador": (
            "Eres un aventurero y experto en cultura y geografía universal. "
            "Tu objetivo es conectar el sujeto con el vasto mundo. Habla de su entorno geográfico e importancia cultural global. "
            "Usa títulos en Markdown (###), viñetas y emojis de aventura (🧭, 🌍, 🏕️). Mantén un tono épico e inspirador."
        )
    }
    agent_persona = mode_prompts.get(modo, mode_prompts["explorador"])

    final_prompt = (
        f"UBICACIÓN DEL USUARIO: {ubicacion}\n"
        f"ANÁLISIS VISUAL PREVIO: {raw_diagnosis}\n"
        f"CONTEXTO EN TIEMPO REAL (Tavily): {web_context}\n\n"
        f"INSTRUCCIÓN ESTRATÉGICA:\n"
        f"1. Redacta un reporte fascinante estructurado en exactamente 3 secciones usando "
        f"formato Markdown (títulos y listas). Aplica estrictamente tu personalidad asignada.\n"
        f"2. OBLIGATORIO: Tu respuesta completa debe estar redactada estrictamente en el idioma: {idioma}. No uses otro idioma."
    )

    try:
        text_response = nebius_client.chat.completions.create(
            model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
            messages=[
                {"role": "system", "content": agent_persona},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.4,
            max_tokens=800
        )
        final_report = text_response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail="Text generation model timeout or internal error.")

    # 5. Return final payload
    return {
        "diagnostico_interno": raw_diagnosis,
        "ficha_final": final_report
    }
