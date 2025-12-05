import streamlit as st
from PIL import Image, ImageDraw
import hashlib, math, random, io

st.set_page_config(page_title="Hash-Palette Flowfield Generator", layout="wide")

st.title("🌀 Hash-Palette Flowfield Generator")
st.write(
    "Turn any text prompt into a **deterministic color palette** "
    "and generate flowfield line art. Great for creative posters and data-driven generative design demos."
)

# -------- Palette hashing --------
def hash_to_palette(s: str, n: int = 5):
    """
    Deterministically map input string -> n RGB colors in [0..255].
    Uses SHA-256 and slices it into triplets.
    """
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    cols = []
    for i in range(n):
        # take 2 hex chars per channel (6 total per color)
        r = int(h[(i * 6) % 64 : (i * 6) % 64 + 2], 16)
        g = int(h[(i * 6 + 2) % 64 : (i * 6 + 2) % 64 + 2], 16)
        b = int(h[(i * 6 + 4) % 64 : (i * 6 + 4) % 64 + 2], 16)
        cols.append((r, g, b))
    return cols

# -------- Flow field --------
def flow_angle(x: float, y: float, scale: float, twist: float) -> float:
    """A dependency-free pseudo-noise angle field using sines/cosines."""
    return math.sin(x / scale + twist * math.sin(y / scale)) + math.cos(
        y / scale + twist * math.cos(x / scale)
    )

def generate_image(
    prompt: str,
    seed: int,
    w: int,
    h: int,
    steps: int,
    n_particles: int,
    step_len: float,
    stroke_w: int,
    bg_mode: str,
    palette_size: int,
    scale: float,
    twist: float,
    alpha: int,
):
    random.seed(seed)
    # palette from prompt (deterministic)
    palette = hash_to_palette(prompt if prompt.strip() else "flowfield", n=palette_size)

    # background
    if bg_mode == "Dark":
        bg = (12, 12, 16)
    elif bg_mode == "Light":
        bg = (245, 245, 245)
    else:
        # use first palette color
        bg = palette[0]

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img, "RGBA")

    # seed particles randomly over the canvas
    particles = [(random.randint(0, w - 1), random.randint(0, h - 1)) for _ in range(n_particles)]

    for (x0, y0) in particles:
        x, y = float(x0), float(y0)
        color = random.choice(palette)
        rgba = color + (alpha,)
        for _ in range(steps):
            ang = flow_angle(x, y, scale, twist)
            dx, dy = math.cos(ang), math.sin(ang)
            x2, y2 = x + dx * step_len, y + dy * step_len
            draw.line((x, y, x2, y2), fill=rgba, width=stroke_w)
            x, y = x2, y2
            # toroidal wrap for continuous paths
            if x < 0:
                x += w
            if x >= w:
                x -= w
            if y < 0:
                y += h
            if y >= h:
                y -= h

    return img, palette

# -------------------- UI --------------------
with st.sidebar:
    st.header("⚙️ Controls")
    prompt = st.text_input("Text to Palette (deterministic)", "dance emotion k-pop freedom")
    seed = st.number_input("Random Seed", value=123, step=1)
    w = st.slider("Width", 640, 1920, 1400, step=10)
    h = st.slider("Height", 480, 1400, 900, step=10)

    st.markdown("---")
    steps = st.slider("Steps per Particle", 50, 1200, 450, step=10)
    n_particles = st.slider("Particles", 100, 4000, 1200, step=100)
    step_len = st.slider("Step Length", 0.5, 6.0, 2.2, step=0.1)
    stroke_w = st.slider("Stroke Width", 1, 6, 2, step=1)
    alpha = st.slider("Stroke Alpha", 30, 255, 110, step=5)

    st.markdown("---")
    palette_size = st.slider("Palette Size", 3, 7, 5, step=1)
    scale = st.slider("Field Scale", 30.0, 200.0, 80.0, step=1.0)
    twist = st.slider("Field Twist", 0.0, 3.0, 1.3, step=0.05)
    bg_mode = st.selectbox("Background", ["Dark", "Light", "Use 1st Palette Color"])

col1, col2 = st.columns([1, 1])

if st.button("Generate Poster", type="primary"):
    img, palette = generate_image(
        prompt,
        seed,
        w,
        h,
        steps,
        n_particles,
        step_len,
        stroke_w,
        bg_mode,
        palette_size,
        scale,
        twist,
        alpha,
    )
    with col1:
        st.subheader("Generated Poster")
        st.image(img, use_column_width=True)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.download_button(
            "Download PNG",
            data=buf.getvalue(),
            file_name="flowfield_poster.png",
            mime="image/png",
        )

    with col2:
        st.subheader("Palette (from text hash)")
        # simple palette strip preview
        sw = 80
        ph = 60
        from PIL import Image as PImage, ImageDraw as PDraw

        pal_img = PImage.new("RGB", (sw * len(palette), ph), (255, 255, 255))
        pdraw = PDraw.Draw(pal_img)
        for i, c in enumerate(palette):
            pdraw.rectangle((i * sw, 0, (i + 1) * sw, ph), fill=c)
        st.image(pal_img, caption=str(palette), use_column_width=False)

st.caption(
    "Deterministic mapping: same text → same palette. "
    "Play with field scale/twist and particle counts for different vibes. No external APIs required."
)
