# Trend-to-Video Creator

A beginner-friendly Streamlit starter app that:
- pulls worldwide/current headline ideas from Google News RSS;
- optionally uses the Anthropic Claude API to draft narration;
- creates narration audio using gTTS;
- renders a 9:16 MP4 slideshow with large text cards and narration;
- lets you preview and download the MP4.

## Important limitations
- Google News RSS is a news-headline feed, not a definitive ranking of what is trending on every social network.
- Free GNews/Google News data can have delays and limits; this app uses Google News RSS directly and does not need a news API key.
- Without an Anthropic API key, the app uses a basic template, not Claude.
- gTTS uses an online text-to-speech service and is not a guaranteed commercial-use voice API. Check current terms before monetizing.
- This starter renders text-based visual cards, not AI-generated cinematic footage.
- Always review factual claims and source links before publishing.

## Run locally or in a cloud IDE
1. Create a folder and add `app.py` and `requirements.txt`.
2. Install Python 3.10+ and run:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Open the local URL shown by Streamlit.
4. Optional Claude integration:
   - Get an API key at https://console.anthropic.com/
   - Add it in the sidebar, or set `ANTHROPIC_API_KEY` as an environment variable.
   - API usage is billed separately from a Claude chat subscription.

## Phone-first option
You can create a GitHub repository from your phone, upload these files, then deploy the repository using Streamlit Community Cloud. The free hosting tier and its availability/limits may change. Rendering videos can use memory and may be slow on free instances.

## Cost estimate
- App code / Google News RSS: $0 to start (RSS is not a paid API, but availability/terms can change).
- Streamlit Community Cloud: a free tier may be available; check its current limits.
- Claude API: optional and pay-as-you-go; check official pricing before using it. A Claude chat subscription does not automatically include API credits.
- gTTS: no separate API key, but it relies on an online service and should not be treated as a guaranteed commercial production service.
- AI-generated footage: not included; image/video generation APIs can add costs.
- Practical prototype: potentially $0 if you skip Claude and use the available free hosting/voice service. Actual costs and availability depend on current provider terms.

## Safety and publishing
Do not expose API keys in public code. Keep them in environment variables or a private secrets panel. Attribute and link to original reporting; do not copy entire articles. Verify sensitive or breaking news from multiple reputable sources.
