# 🌿 AI Visual Explorer

An intelligent, multilingual botanical and environmental guide powered by Nebius AI Cloud and NVIDIA LLMs. Built for the **Nebius x NVIDIA Global AI Hackathon**.

## 🚀 Project Overview

AI Visual Explorer is a web-based application designed to bridge the gap between advanced artificial intelligence and real-world environmental education. Conceived from practical experience in national tour guiding and botanical interpretation in Ecuador, this tool transforms any smartphone into an expert pocket guide.

Users can snap or upload photos of plants, landscapes, or landmarks, and receive immediate, context-aware analysis in their native language.

### 🔗 Links
- **Live Demo**: https://ai-visual-explorer.onrender.com
- **Video Pitch**: (https://youtu.be/ei9oo46DSNw)

## 🧠 Nebius & NVIDIA Integration (Hackathon Requirement)

This project heavily leverages the **Nebius Token Factory** serverless infrastructure to orchestrate multiple AI models seamlessly:

1. **Vision Filter (`openbmb/MiniCPM-V-4_5`)**: Acts as the first line of defense. It analyzes the uploaded image to identify the main subject or immediately halts the process if the image is blurry or unrecognized, saving compute time and preventing AI hallucinations.
2. **Multilingual Synthesis (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`)**: The core reasoning engine. It takes the visual diagnosis, cross-references it with live data from the Tavily API, and generates a structured, engaging report matching the user's selected persona (Educational, Touristic, or Explorer) and language.

## ✨ Key Features
- **Dynamic Personas**: Choose how you want to learn (Academic Scientist, Charismatic Tour Guide, or Epic Explorer).
- **Live Context**: Integrates Tavily Search API to pull real-time location data and environmental history.
- **Discovery Passport**: Saves your findings locally, creating a personalized journal of your explorations.
- **Multilingual UI**: Fully translated interface and AI responses (English, Spanish, French, German, Chinese) adapting in real-time.

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla, no heavy frameworks)
- **AI API**: Nebius Token Factory (OpenAI Python SDK)
- **Deployment**: Render (Web Service)

## 💻 Local Setup
1. Clone the repository: `git clone https://github.com/modelosdegestion8b-commits/ai-visual-explorer.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file and add your keys:
   ```text
   NEBIUS_API_KEY=your_key_here
   TAVILY_API_KEY=your_key_here

Run the server: uvicorn main:app --host 0.0.0.0 --port 8000

📜 License
This project is licensed under the MIT License.

Author: Daniel Pacheco
