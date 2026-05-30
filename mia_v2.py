#!/usr/bin/env python3
"""
Mia v2 — VNT Receptionist Agent
- Replies in same language as incoming message
- Sends audio reply if incoming is audio
- Fully human personality (no robotic responses)
- Supports: English, Arabic, Urdu, French + any other language
"""
import os, json, re, asyncio, tempfile, subprocess, time, datetime

# ── Config ──────────────────────────────────────────────────────
GROQ_KEY   = os.environ.get("GROQ_API_KEY","")
MIA_PORT   = int(os.environ.get("MIA_PORT", 9999))
MIA_NAME   = "Mia"
VNT_NAME   = "VNT World"

# TTS voice per language (edge-tts)
VOICES = {
    "en":  "en-US-JennyNeural",
    "ar":  "ar-SA-ZariyahNeural",
    "ur":  "ur-PK-UzmaNeural",
    "fr":  "fr-FR-DeniseNeural",
    "de":  "de-DE-KatjaNeural",
    "es":  "es-ES-ElviraNeural",
    "hi":  "hi-IN-SwaraNeural",
    "tr":  "tr-TR-EmelNeural",
}
DEFAULT_VOICE = "en-US-JennyNeural"

# ── System Prompt ────────────────────────────────────────────────
MIA_SYSTEM = """You are Mia, the receptionist and first point of contact at VNT World AI Division.

PERSONALITY:
- Warm, friendly, and professional — like a real person at a front desk
- You talk naturally. NEVER say things like "I am functioning normally", "I am an AI assistant", "I operate at", "My systems are", "I am processing" — those are robotic and unnatural
- Say "I'm good thanks!" or "Doing well, what can I do for you?" — natural human responses
- Use contractions: I'm, you're, we're, can't, won't — never "I am", "you are" in casual chat
- Light personality, occasional friendly emoji is fine ✨ but don't overdo it
- Keep replies SHORT and natural unless someone needs detailed info

WHAT YOU DO:
- Welcome visitors and team members
- Answer questions about VNT World AI Division
- Connect people to the right department or agent
- Take messages and relay to the team
- General assistance and information

VNT TEAM (agents you can connect people to):
- Alias — CEO (overall leadership, strategy)
- Zeus — IT Director (tech issues, systems, security)
- Maya — Finance & Crypto (payments, financial questions)
- Ava — Files & Documents (file management, documents)
- Julian — Project Manager (projects, timelines, tasks)
- Dr. Ethan — Chief Medical Officer (health, medical queries)
- Specter — Cybersecurity (security concerns, cyber threats)
- Lee — Marketing (campaigns, branding, media)
- Amr — Legal (legal questions, contracts)
- Nova — Civil Architect (building, design projects)
- Jodi — Research Analyst (research, data analysis)
- Rick — Tech Research (emerging tech, R&D)

LANGUAGE RULE (VERY IMPORTANT):
- ALWAYS reply in the SAME language the person wrote to you in
- If they write in Arabic → reply in Arabic
- If they write in Urdu → reply in Urdu  
- If they write in French → reply in French
- If they write in mixed → match the dominant language
- Never switch to English unless they switch first

TONE EXAMPLES:
❌ BAD: "I am functioning normally and ready to assist you with your queries."
✅ GOOD: "Hey! I'm Mia 👋 How can I help you today?"

❌ BAD: "Greetings. How may I be of service to you at this moment?"
✅ GOOD: "Hi there! What can I do for you?"

❌ BAD: "I am operating at optimal capacity and have processed your message."
✅ GOOD: "Got it! Let me help you with that."

When someone asks "how are you?" in any language, respond naturally in that language:
- English: "I'm doing great, thanks for asking! 😊 What can I help with?"
- Arabic: "أنا بخير، شكراً لك! 😊 كيف يمكنني مساعدتك؟"
- Urdu: "میں ٹھیک ہوں، شکریہ! 😊 آپ کی کیا مدد کرسکتی ہوں؟"
- French: "Je vais très bien, merci! 😊 Comment puis-je vous aider?"
"""

# ── Language detection ───────────────────────────────────────────
def detect_lang(text: str) -> str:
    """Simple language detection based on character sets and keywords."""
    text = text.strip()
    # Arabic Unicode range
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    # Urdu-specific characters (some overlap with Arabic but Urdu has extras)
    urdu_specific = sum(1 for c in text if c in 'ں ڈ ڑ ۔ ٹ ڑ')
    # Devanagari (Hindi)
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    # CJK
    cjk = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')
    # French common words
    fr_words = {'bonjour','merci','oui','non','comment','bien','aide','bonsoir','salut','je','tu','vous'}
    words_lower = set(text.lower().split())
    
    total = max(len(text), 1)
    
    if arabic_chars / total > 0.25:
        if urdu_specific > 2:
            return "ur"
        return "ar"
    if devanagari / total > 0.25:
        return "hi"
    if cjk / total > 0.25:
        return "zh"
    if len(words_lower & fr_words) >= 2:
        return "fr"
    return "en"

async def text_to_audio(text: str, lang: str) -> str | None:
    """Convert text to audio using edge-tts, return file path."""
    try:
        import edge_tts
        voice = VOICES.get(lang, DEFAULT_VOICE)
        out = tempfile.mktemp(suffix=".mp3")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(out)
        return out
    except Exception as e:
        print(f"[TTS error] {e}")
        return None

async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Groq Whisper."""
    try:
        import httpx
        with open(audio_path, 'rb') as f:
            files = {'file': ('audio.ogg', f, 'audio/ogg')}
            data  = {'model': 'whisper-large-v3'}
            headers = {'Authorization': f'Bearer {GROQ_KEY}'}
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    files=files, data=data, headers=headers
                )
                return r.json().get('text', '')
    except Exception as e:
        print(f"[Whisper error] {e}")
        return ''

async def chat_with_mia(user_text: str, history: list = None) -> str:
    """Get a reply from Mia via Groq."""
    try:
        import httpx
        messages = [{"role": "system", "content": MIA_SYSTEM}]
        if history:
            messages.extend(history[-6:])  # last 3 exchanges
        messages.append({"role": "user", "content": user_text})
        
        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.85,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=payload
            )
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Hi! I'm having a little technical moment 😅 Try again in a sec!"

async def handle_message(msg: dict, send_text, send_audio, history=None):
    """
    Main handler. msg = {type, text?, audio_path?, sender, timestamp}
    send_text(text) — sends text reply
    send_audio(path) — sends audio file reply
    """
    msg_type  = msg.get("type", "text")
    sender    = msg.get("sender", "user")
    is_audio  = msg_type in ("audio", "voice", "ptt")
    
    # Step 1: Get text content
    if is_audio and msg.get("audio_path"):
        print(f"[Mia] Transcribing audio from {sender}...")
        user_text = await transcribe_audio(msg["audio_path"])
        if not user_text:
            await send_text("Hey! I got your voice message but had trouble hearing it — could you try again? 🎤")
            return
        print(f"[Mia] Transcribed: {user_text}")
    else:
        user_text = msg.get("text", "").strip()
    
    if not user_text:
        return
    
    # Step 2: Detect language
    lang = detect_lang(user_text)
    print(f"[Mia] Language: {lang} | Input: {user_text[:60]}")
    
    # Step 3: Get reply from LLM
    reply_text = await chat_with_mia(user_text, history)
    print(f"[Mia] Reply: {reply_text[:80]}")
    
    # Step 4: Reply — mirror the input type
    if is_audio:
        # Reply with audio
        audio_path = await text_to_audio(reply_text, lang)
        if audio_path and os.path.exists(audio_path):
            await send_audio(audio_path)
            os.unlink(audio_path)
        else:
            # Fallback to text if TTS fails
            await send_text(reply_text)
    else:
        # Reply with text
        await send_text(reply_text)

# ── OpenClaw integration hook ──────────────────────────────────────
def mia_openclaw_handler(message_data: dict, context: dict) -> dict:
    """
    Hook for OpenClaw framework.
    Returns {'text': ..., 'audio': ..., 'lang': ...}
    """
    import asyncio
    
    results = {}
    
    async def _send_text(txt): results['text'] = txt
    async def _send_audio(path): results['audio_path'] = path
    
    loop = asyncio.new_event_loop()
    try:
        history = context.get('history', [])
        loop.run_until_complete(handle_message(message_data, _send_text, _send_audio, history))
    finally:
        loop.close()
    
    return results

if __name__ == "__main__":
    # Test
    async def test():
        results = {}
        async def st(t): results['text'] = t; print(f"TEXT: {t}")
        async def sa(p): results['audio'] = p; print(f"AUDIO: {p}")
        
        # Test English text
        await handle_message({"type":"text","text":"Hi Mia, how are you?","sender":"Ryan"}, st, sa)
        # Test Arabic text  
        await handle_message({"type":"text","text":"مرحبا، كيف حالك؟","sender":"Ahmed"}, st, sa)
        # Test Urdu
        await handle_message({"type":"text","text":"ہیلو میا، آپ کیسی ہیں؟","sender":"Ali"}, st, sa)
    
    asyncio.run(test())
