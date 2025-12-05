import streamlit as st
from PIL import Image, ImageDraw, ImageFilter
from collections import Counter
import random, math, io

st.set_page_config(page_title="Data-Driven Emotion Art Generator", layout="wide")

st.title("🎨 Data-Driven Emotion Art Generator")
st.write(
    "Paste any text (English works best). The app infers emotions with a small lexicon "
    "and turns them into abstract generative art using emotion-specific colors and shapes."
)

# ---------- Minimal emotion lexicon (subset; extend as needed) ----------
# Each word maps to one or more emotions
EMOTION_LEXICON = {
    # joy
    "happy": ["joy", "trust"],
    "joy": ["joy"],
    "love": ["joy", "trust"],
    "smile": ["joy"],
    "delight": ["joy"],
    "peace": ["joy", "trust"],
    "confidence": ["trust", "joy"],
    "proud": ["joy"],
    "grateful": ["joy", "trust"],
    "excited": ["joy", "surprise"],

    # sadness
    "sad": ["sadness"],
    "lonely": ["sadness"],
    "cry": ["sadness"],
    "loss": ["sadness"],
    "regret": ["sadness"],
    "tired": ["sadness"],
    "hurt": ["sadness"],
    "blue": ["sadness"],

    # anger
    "angry": ["anger"],
    "rage": ["anger"],
    "hate": ["anger"],
    "annoyed": ["anger"],
    "furious": ["anger"],
    "upset": ["anger", "sadness"],

    # fear
    "fear": ["fear"],
    "afraid": ["fear"],
    "worry": ["fear"],
    "anxious": ["fear"],
    "scared": ["fear"],
    "panic": ["fear"],

    # surprise
    "surprise": ["surprise"],
    "wow": ["surprise", "joy"],
    "shocked": ["surprise", "fear"],
    "unexpected": ["surprise"],

    # trust
    "trust": ["trust"],
    "reliable": ["trust"],
    "honest": ["trust"],
    "secure": ["trust"],
    "safe": ["trust"],
    "faith": ["trust"],

    # disgust
    "disgust": ["disgust"],
    "gross": ["disgust"],
    "nasty": ["disgust"],
    "dirty": ["disgust"],
    "toxic": ["disgust", "anger"],
}

PALETTES = {
    "joy": [(255, 214, 102), (255, 159, 28), (255, 111, 105)],
    "sadness": [(102, 153, 255), (64, 105, 225), (35, 62, 140)],
    "anger": [(255, 71, 87), (255, 99, 72), (199, 0, 57)],
    "fear": [(155, 89, 182), (52, 31, 151), (41, 128, 185)],
    "surprise": [(255, 221, 89), (255, 195, 0), (255, 87, 51)],
    "trust": [(46, 204, 113), (39, 174, 96), (23, 165, 137)],
    "disgust": [(143, 188, 143), (85, 107, 47), (0, 128, 0)],
    "neutral": [(220, 220, 220), (200, 200, 200), (180, 180, 180)],
}
EMOTIONS = ["joy", "sadness", "anger", "fear", "surprise", "trust", "disgust"]

def score_emotions(text: str):
    tokens = [t.strip(".,!?;:()[]\"'").lower() for t in text.split()]
    counts = Counter()
    total_hits = 0
    for tok in tokens:
        if tok in EMOTION_LEXICON:
            for e in EMOTION_LEXICON[tok]:
                counts[e] += 1
                total_hits += 1
    scores = {e: (counts[e] / max(1, total_hits)) for e in EMOTIONS}
    if total_hits == 0:
        scores = {e: 0.0 for e in EMOTIONS}
    return scores, total_hits

def lerp(a, b, t): 
    return a + (b - a) * t

def pick_color(emotion, intensity):
    palette = PALETTES.get(emotion, PALETTES["neutral"])
    c1, c2, c3 = palette
    if intensity < 0.33:
        return c1
    elif intensity < 0.66:
        return c2
    return c3

def generate_art(width, height, emotion_scores, seed=42, density=400, blur=1):
    random.seed(seed)
    img = Image.new("RGB", (width, height), (250, 250, 250))
    draw = ImageDraw.Draw(img, "RGBA")

    total = sum(emotion_scores.values())
    if total == 0:
        # neutral composition
        for _ in range(max(80, density // 4)):
            x, y = random.randint(0, width), random.randint(0, height)
            r = random.randint(6, 40)
            col = PALETTES["neutral"][random.randint(0, 2)] + (110,)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=col)
        return img.filter(ImageFilter.GaussianBlur(radius=blur)) if blur > 0 else img

    norm = {e: (emotion_scores[e] / total if total > 0 else 0.0) for e in EMOTIONS}

    for e, frac in norm.items():
        count = max(1, int(density * frac))
        for _ in range(count):
            cx, cy = random.randint(0, width), random.randint(0, height)
            size = int(lerp(8, 120, frac) * random.uniform(0.6, 1.4))
            color = pick_color(e, random.random())
            alpha = int(lerp(60, 185, frac))

            if e in ["joy", "trust", "surprise"]:
                # round / soft
                draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=color + (alpha,))
            elif e in ["anger", "disgust"]:
                # sharp polygons
                pts = [(cx + int(size * math.cos(t)), cy + int(size * math.sin(t))) for t in [0, 2.1, 4.2]]
                draw.polygon(pts, fill=color + (alpha,))
            elif e in ["sadness", "fear"]:
                # strokes
                x2 = cx + random.randint(-size * 2, size * 2)
                y2 = cy + random.randint(-size * 2, size * 2)
                draw.line((cx, cy, x2, y2), fill=color + (alpha,), width=max(1, size // 10))

    return img.filter(ImageFilter.GaussianBlur(radius=blur)) if blur > 0 else img

# ---------------- UI ----------------
with st.sidebar:
    st.header("⚙️ Controls")
    seed = st.number_input("Random Seed", value=42, step=1)
    density = st.slider("Shape Density", 100, 1500, 450, step=50)
    blur = st.slider("Gaussian Blur", 0, 10, 1)

    st.markdown("---")
    st.caption("Canvas Size")
    w = st.slider("Width", 640, 1920, 1200, step=10)
    h = st.slider("Height", 480, 1200, 800, step=10)

demo_text = (
    "We feel happy and excited to start a new creative journey. "
    "Sometimes we are anxious and worried about results, but we trust the process "
    "and keep going with confidence and love. Wow, this is surprising and delightful!"
)

mode = st.radio("Input Mode", ["Type / Paste Text", "Demo Text"], horizontal=True)
if mode == "Type / Paste Text":
    text = st.text_area(
        "Paste your text here (English preferred):",
        height=180,
        placeholder="Type feelings, lyrics, diary, or any text..."
    )
else:
    text = st.text_area("Demo Text:", value=demo_text, height=180)

if st.button("Generate Art", type="primary"):
    scores, hits = score_emotions(text)
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Emotion Scores")
        if hits == 0:
            st.info("No emotion words found in the text. Generated a neutral composition.")
        st.json(scores)

    with col2:
        img = generate_art(w, h, scores, seed=seed, density=density, blur=blur)
        st.image(img, caption="Generated Artwork", use_column_width=True)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.download_button(
            "Download PNG",
            data=buf.getvalue(),
            file_name="emotion_art.png",
            mime="image/png",
        )

st.markdown("---")
st.markdown(
    "**How it works**: The app maps detected emotion words to seven emotions "
    "(joy, sadness, anger, fear, surprise, trust, disgust). Intensities control "
    "colors, shapes, and densities to compose an abstract image."
)
st.caption("No external API or keys required. You can extend to transformer-based emotion models if needed.")

