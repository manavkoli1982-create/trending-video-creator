import os
import re
import io
import textwrap
import tempfile
import urllib.parse
from datetime import datetime, timezone

import feedparser
import requests
import streamlit as st
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

APP_TITLE = "Trend-to-Video Creator"
RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide")
st.title("🌍 Trend-to-Video Creator")
st.caption("Find worldwide news topics, write a short script, add AI narration, and render a vertical MP4.")

with st.sidebar:
    st.header("Settings")
    duration = st.selectbox("Video length", ["30 seconds", "45 seconds", "60 seconds"], index=1)
    voice_lang = st.selectbox("Voice language", ["English", "Hindi"], index=0)
    use_claude = st.checkbox("Use Claude to write the script", value=bool(os.getenv("ANTHROPIC_API_KEY")))
    api_key = st.text_input("Anthropic API key (optional)", type="password",
                            value=os.getenv("ANTHROPIC_API_KEY", ""))
    model = st.text_input("Claude model", value="claude-haiku-4-5-20251001")
    st.caption("Without a Claude key, the app uses a basic script template. Never share your API key.")

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fetch_trends(category):
    query_map = {
        "All worldwide headlines": "world OR technology OR business OR science OR entertainment OR sports",
        "World news": "world news",
        "Technology & AI": "artificial intelligence OR technology",
        "Business & economy": "business OR economy OR markets",
        "Science & unusual discoveries": "science OR discovery",
        "Entertainment": "entertainment OR celebrity",
        "Sports": "sports"
    }
    query = query_map.get(category, "world news")
    url = RSS_URL.format(query=urllib.parse.quote(query))
    response = requests.get(url, timeout=20, headers={"User-Agent": "TrendToVideoCreator/1.0"})
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    items = []
    seen = set()
    for entry in feed.entries:
        title = re.sub(r"\s+-\s+[^-]+$", "", entry.get("title", "")).strip()
        link = entry.get("link", "")
        if title and title.lower() not in seen:
            seen.add(title.lower())
            items.append({
                "title": title,
                "link": link,
                "source": entry.get("source", {}).get("title", "Google News"),
                "published": entry.get("published", "Publication time not supplied"),
                "summary": re.sub("<[^<]+?>", "", entry.get("summary", ""))[:500]
            })
        if len(items) >= 15:
            break
    return items

def make_script(topic, details, seconds, api_key, model, use_claude):
    target_words = {"30 seconds": 75, "45 seconds": 110, "60 seconds": 145}[seconds]
    if use_claude and api_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            prompt = f"""Write a factual short-form video voiceover about this news topic.
Topic: {topic}
Context from a news feed (may be incomplete): {details}
Target length: about {target_words} words.
Use a strong but not misleading opening, simple natural English, clear context, why it matters, and a careful ending.
Do not invent facts, figures, quotes, motives, or claims not supported by the context. If details are uncertain, say so.
Return only the narration, no scene directions, no markdown."""
            msg = client.messages.create(
                model=model.strip(),
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text").strip()
        except Exception as e:
            st.warning(f"Claude request failed; using a basic script instead. Details: {e}")
    detail = re.sub(r"\s+", " ", details or "").strip()
    if len(detail) > 260:
        detail = detail[:257].rsplit(" ", 1)[0] + "..."
    if not detail:
        detail = "A headline is attracting attention, but the available feed does not provide enough detail to verify the full story."
    return (
        f"Here is a story getting attention: {topic}. "
        f"Here is what the available report says. {detail} "
        "Keep in mind that headlines can leave out important context, and early reports may change as more information becomes available. "
        "Check the linked source for the latest details before sharing this story. "
        "Follow for more updates explained clearly, without the noise."
    )

def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]

def draw_card(topic, caption, index, total, out_path):
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (12, 22, 42))
    draw = ImageDraw.Draw(img)
    # Simple dark editorial gradient
    for y in range(H):
        ratio = y / H
        color = (int(12 + 10*ratio), int(22 + 12*ratio), int(42 + 22*ratio))
        draw.line((0, y, W, y), fill=color)
    draw.rounded_rectangle((64, 70, 360, 145), radius=26, fill=(20, 105, 130))
    draw.text((88, 88), "WORLD TREND", font=get_font(30, True), fill="white")
    draw.text((65, 205), f"STORY {index+1}/{total}", font=get_font(28, True), fill=(104, 220, 231))
    title_lines = textwrap.wrap(topic, width=24)
    y = 300
    for line in title_lines[:5]:
        draw.text((65, y), line, font=get_font(60, True), fill="white", stroke_width=1)
        y += 78
    draw.rounded_rectangle((58, 850, 1022, 1510), radius=35, fill=(23, 40, 65), outline=(62, 99, 127), width=3)
    lines = textwrap.wrap(caption, width=29)
    y = 915
    for line in lines[:10]:
        draw.text((95, y), line, font=get_font(42), fill=(232, 239, 246))
        y += 57
    draw.text((65, 1660), "VERIFY THE STORY • READ SOURCES", font=get_font(28, True), fill=(104, 220, 231))
    draw.text((65, 1740), "AI-assisted explainer • Check the source before sharing", font=get_font(24), fill=(180, 195, 210))
    img.save(out_path, quality=92)

def render_video(topic, script, seconds, language):
    sentences = split_sentences(script)
    if not sentences:
        raise ValueError("The script is empty.")
    # Build narration audio
    audio_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    lang = "hi" if language == "Hindi" else "en"
    gTTS(text=script, lang=lang, slow=False).save(audio_file)
    audio = AudioFileClip(audio_file)
    total_duration = audio.duration
    # One card per sentence, capped for legibility
    captions = sentences[:8]
    if len(sentences) > 8:
        captions = sentences[:7] + [" ".join(sentences[7:])]
    per_scene = total_duration / len(captions)
    clips = []
    image_files = []
    for i, sentence in enumerate(captions):
        path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
        image_files.append(path)
        draw_card(topic, sentence, i, len(captions), path)
        clips.append(ImageClip(path).with_duration(per_scene))
    video = concatenate_videoclips(clips, method="compose").with_audio(audio)
    out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    video.write_videofile(out, fps=24, codec="libx264", audio_codec="aac",
                          preset="ultrafast", threads=2, logger=None)
    video.close()
    audio.close()
    for c in clips:
        c.close()
    try:
        os.unlink(audio_file)
        for f in image_files:
            os.unlink(f)
    except OSError:
        pass
    return out

category = st.selectbox("Choose a topic area", [
    "All worldwide headlines", "World news", "Technology & AI",
    "Business & economy", "Science & unusual discoveries", "Entertainment", "Sports"
])

if "trends" not in st.session_state:
    st.session_state.trends = []
if "script" not in st.session_state:
    st.session_state.script = ""
if "selected" not in st.session_state:
    st.session_state.selected = None

if st.button("🔎 Find current headlines", type="primary"):
    try:
        with st.spinner("Loading headlines from Google News RSS…"):
            st.session_state.trends = fetch_trends(category)
        st.session_state.selected = None
        st.session_state.script = ""
        if not st.session_state.trends:
            st.info("No headlines were returned. Try another category.")
    except Exception as e:
        st.error(f"Could not load headlines: {e}")

if st.session_state.trends:
    st.subheader("Headline ideas")
    options = [f"{i+1}. {x['title']} — {x['source']}" for i, x in enumerate(st.session_state.trends)]
    choice = st.radio("Choose a story", options, index=0)
    idx = options.index(choice)
    selected = st.session_state.trends[idx]
    st.session_state.selected = selected
    st.markdown(f"**Source:** {selected['source']}  \n**Published:** {selected['published']}  \n[Open original story]({selected['link']})")
    if selected.get("summary"):
        st.write(selected["summary"])

    if st.button("✍️ Generate narration script"):
        with st.spinner("Writing script…"):
            st.session_state.script = make_script(
                selected["title"], selected.get("summary", ""), duration,
                api_key, model, use_claude
            )
    if st.session_state.script:
        st.subheader("Editable narration")
        edited = st.text_area("Review and edit before rendering", value=st.session_state.script, height=220)
        st.session_state.script = edited
        st.caption("The generated cards are text-based. This starter does not create cinematic AI footage.")
        if st.button("🎬 Render vertical MP4", type="primary"):
            try:
                with st.spinner("Generating voiceover and rendering video. This may take a few minutes…"):
                    path = render_video(selected["title"], st.session_state.script, duration, voice_lang)
                with open(path, "rb") as f:
                    video_bytes = f.read()
                st.success("Video rendered.")
                st.video(video_bytes)
                st.download_button("⬇️ Download MP4", data=video_bytes,
                                   file_name="trending_story_video.mp4", mime="video/mp4")
                try:
                    os.unlink(path)
                except OSError:
                    pass
            except Exception as e:
                st.error(f"Video rendering failed: {e}")
                st.info("If this is a memory/FFmpeg issue, try a 30-second video or run the app on a cloud runtime with more memory.")

st.divider()
st.caption("Use this as a starter tool, not an automatic truth engine. Check source links and facts before publishing. Google News RSS is a headline discovery feed, not a definitive measure of global social-media virality.")
