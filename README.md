# Data-Driven Emotion Art Generator 🎨

Turn text into abstract emotion-driven art. This Streamlit app detects a small set of emotion keywords and generates visuals (colors, shapes, density) for seven emotions: **joy, sadness, anger, fear, surprise, trust, disgust**.

## Demo (How to use)
1. Paste any English text (diary, lyrics, notes).  
2. Click **Generate Art**.  
3. Download the PNG or tweak **seed / density / blur** in the sidebar.

## Tech Stack
- **Streamlit** for the web UI  
- **Pillow (PIL)** for image generation and compositing  
- **Python** (no API keys required)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
