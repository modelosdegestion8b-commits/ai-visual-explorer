# 🌍 AI Visual Explorer — Multimodal RAG Agent

[![Live Demo](https://img.shields.io/badge/Live_Demo-Render-46E3B7?style=for-the-badge&logo=render)](https://ai-visual-explorer.onrender.com)
[![Nebius Token Factory](https://img.shields.io/badge/AI_Engine-Nebius_Token_Factory-76B900?style=for-the-badge&logo=nvidia)](https://tokenfactory.nebius.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> ### 🛠️ Production Maintenance Notice (November 2026)
> Following the official **Nebius Token Factory Serverless Deprecation** on November 9, 2026, this repository received an infrastructure maintenance patch to guarantee 100% uptime during the judging period:
> * **Vision Pipeline Migration:** Replaced the retired `openbmb/MiniCPM-V-4_5` endpoint with **`nvidia/Nemotron-3.5-Super-VL`** (121B parameters, BF16).
> * **Synthesis LLM Migration:** Replaced the retired `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` endpoint with **`nvidia/Nemotron-3.5-Lightning`** (30B parameters, BF16), backed by an automatic failover to **`nvidia/Nemotron-3.5-Super-VL`**.
> * **Latency & Output Sanitization:** Implemented system-level reasoning controls (`detailed thinking off`) and regex sanitization (`extract_clean_text` & `clean_final_report`) to strip internal `<think>` draft traces, preserving fast response times and clean Markdown rendering.
> * *Note: No core application features, UI components, or user workflows were altered after the submission deadline.*

---

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
