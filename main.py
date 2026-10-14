import base64
import os
import requests
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="AI Visual Explorer - Nebius Hackathon")

# Configurar el directorio para los archivos web (HTML, JS, CSS)
# Si la carpeta 'static' no existe, asegúrate de crearla.
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cliente configurado para Nebius Token Factory
nebius_client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=os.environ.get("NEBIUS_API_KEY"),
)

def buscar_en_tavily(query: str) -> str:
    """Consulta a la API de Tavily para buscar información en tiempo real."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "No hay conexión a internet en tiempo real."
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 3
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        resultados = response.json().get("results", [])
        # Juntar el contenido de los resultados
        contexto = " ".join([res.get("content", "") for res in resultados])
        return contexto if contexto else "Sin resultados relevantes recientes."
    except Exception as e:
        return f"Error al buscar datos: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def servir_web():
    """Esta ruta sirve tu página web (frontend) cuando abres la URL."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Falta el archivo index.html</h1><p>Crea la carpeta 'static' y coloca index.html dentro.</p>"


@app.post("/api/analizar")
async def analizar_entorno(
    file: UploadFile = File(...),
    modo: str = Form(...),
    idioma: str = Form(...),
    ubicacion: str = Form(default="Ubicación desconocida")
):
    """El núcleo del Agente de IA: Visión -> Tavily -> Redacción"""
    
    # 0. Convertir imagen a Base64 en Memoria RAM
    try:
        image_bytes = await file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        imagen_data = f"data:{file.content_type};base64,{encoded_image}"
    except Exception:
        raise HTTPException(status_code=400, detail="Error al procesar la imagen.")

    # ==========================================
    # PASO 1: VISIÓN CON OPEN-BMB (Cosmos3)
    # ==========================================
    prompt_vision = (
        "Eres un experto en análisis visual. Tu tarea es identificar el sujeto principal de esta imagen. "
        "REGLA 1: Si la imagen está demasiado borrosa, oscura, cortada, o no hay un sujeto claramente identificable, "
        "responde ÚNICAMENTE con la frase exacta: 'IMAGEN_NO_RECONOCIDA'. "
        "REGLA 2: Si puedes identificarlo, responde en una sola frase corta y precisa con el nombre más exacto que deduzcas "
        "(fíjate muy bien en detalles estructurales para no confundir especies o estilos similares). "
        "REGLA 3: No des explicaciones, solo la frase corta o la palabra de error."
    )
    
    try:
        res_vision = nebius_client.chat.completions.create(
            model="openbmb/MiniCPM-V-4_5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_vision},
                        {"type": "image_url", "image_url": {"url": imagen_data}},
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=60
        )
        diagnostico_crudo = res_vision.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en el modelo de visión: {str(e)}")

    # ==========================================
    # PASO 2: AGENTE TAVILY (Búsqueda Viva)
    # ==========================================
    # Cruzamos lo que vio el modelo con la ubicación actual del usuario
    query_tavily = f"{diagnostico_crudo} en {ubicacion} contexto actual, historia o noticias"
    contexto_web = buscar_en_tavily(query_tavily)

    # ==========================================
    # PASO 3: RAZONAMIENTO Y REDACCIÓN MULTILINGÜE (Nemotron)
    # ==========================================
    prompts_modo = {
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
    personalidad = prompts_modo.get(modo, prompts_modo["explorador"])

    prompt_final = (
        f"UBICACIÓN DEL USUARIO: {ubicacion}\n"
        f"ANÁLISIS VISUAL PREVIO: {diagnostico_crudo}\n"
        f"CONTEXTO EN TIEMPO REAL (Tavily): {contexto_web}\n\n"
        f"INSTRUCCIÓN ESTRATÉGICA:\n"
        f"1. Si el ANÁLISIS VISUAL dice 'IMAGEN_NO_RECONOCIDA', ignora por completo el contexto de Tavily. En su lugar, "
        f"redacta un mensaje muy amable y con un toque de humor indicando que la foto está borrosa o no se distingue nada, "
        f"y pídele al usuario que intente tomar una foto más clara o más cerca.\n"
        f"2. Si hay un sujeto identificado, redacta un reporte fascinante estructurado en exactamente 3 secciones usando "
        f"formato Markdown (títulos y listas). Aplica estrictamente tu personalidad asignada.\n"
        f"3. OBLIGATORIO: Tu respuesta completa debe estar redactada estrictamente en el idioma: {idioma}. No uses otro idioma."
    )

    try:
        res_texto = nebius_client.chat.completions.create(
            model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
            messages=[
                {"role": "system", "content": personalidad},
                {"role": "user", "content": prompt_final}
            ],
            temperature=0.4,
            max_tokens=800
        )
        ficha_final = res_texto.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en Nemotron Ultra: {str(e)}")

    # 4. Devolver resultado (La imagen se elimina de la RAM al terminar la función)
    return {
        "diagnostico_interno": diagnostico_crudo,
        "ficha_final": ficha_final
    }

