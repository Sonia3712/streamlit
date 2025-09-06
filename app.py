import streamlit as st
import pdfplumber
import os
import re
import torch
from pydub import AudioSegment
from TTS.api import TTS
from scipy.io import wavfile
import numpy as np
from librosa import resample
from deepgram import DeepgramClient, SpeakOptions
from datetime import datetime
import glob
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.title("📖 Life 3.0 Audiobook Generator")
st.write("Upload a PDF and your voice to create an audiobook!")

# Uploads
pdf_file = st.file_uploader("Upload PDF", type="pdf")
voice_file = st.file_uploader("Upload Voice Sample (.wav or .mp3)", type=["wav", "mp3"])
page_range = st.text_input("Page Range (e.g., 1-10)", "")
DEEPGRAM_API_KEY = st.text_input("Enter Deepgram API Key", type="password")
use_existing = st.checkbox("Reuse previously generated files", value=True)

if st.button("Generate Audiobook"):
    if not pdf_file or not voice_file or not DEEPGRAM_API_KEY:
        st.error("❌ Please upload PDF, voice, and API key")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        pdf_path = os.path.join(base_dir, "book.pdf")
        voice_path = os.path.join(base_dir, "voice.wav")
        deepgram_wav = os.path.join(output_dir, f"deepgram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        mp3_path = os.path.join(output_dir, f"yourtts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")

        # Save PDF
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        # Save and convert voice
        raw_voice = os.path.join(base_dir, "uploaded_voice")
        with open(raw_voice, "wb") as f:
            f.write(voice_file.read())
        try:
            if voice_file.name.endswith(".mp3"):
                audio = AudioSegment.from_mp3(raw_voice)
            else:
                audio = AudioSegment.from_wav(raw_voice)
            audio = audio.set_channels(1).set_frame_rate(22050)
            audio.export(voice_path, format="wav")
        except Exception as e:
            st.error(f"Voice conversion error: {e}")
            st.stop()

        # Extract text
        def extract_text(path, page_range=None):
            text = ""
            with pdfplumber.open(path) as pdf:
                start, end = 0, len(pdf.pages)
                if page_range and "-" in page_range:
                    s, e = page_range.split("-")
                    start, end = int(s) - 1, int(e)
                for page in pdf.pages[start:end]:
                    txt = page.extract_text()
                    if txt:
                        text += txt + "\n"
            return re.sub(r'[^a-zA-Z0-9\s.,!?\'"-]', '', text)

        book_text = extract_text(pdf_path, page_range)
        st.write(f"✅ Extracted {len(book_text)} characters")

        # --- Deepgram TTS ---
        existing = glob.glob(os.path.join(output_dir, "deepgram_*.wav"))
        if use_existing and existing:
            deepgram_wav = max(existing, key=os.path.getmtime)
            st.info("Using existing Deepgram file")
        else:
            dg = DeepgramClient(DEEPGRAM_API_KEY)
            chunks = [book_text[i:i+2000] for i in range(0, len(book_text), 2000)]
            combined = AudioSegment.empty()
            for i, chunk in enumerate(chunks):
                st.write(f"Deepgram chunk {i+1}/{len(chunks)}")
                temp = os.path.join(base_dir, f"dg_{i}.wav")
                dg.speak.v("1").save(temp, {"text": chunk}, SpeakOptions(model="aura-luna-en", encoding="linear16", container="wav"))
                combined += AudioSegment.from_wav(temp)
                os.remove(temp)
            combined.export(deepgram_wav, format="wav")
        st.audio(deepgram_wav)

        # --- YourTTS Cloning ---
        existing = glob.glob(os.path.join(output_dir, "yourtts_*.mp3"))
        if use_existing and existing:
            mp3_path = max(existing, key=os.path.getmtime)
            st.info("Using existing YourTTS file")
        else:
            tts = TTS("tts_models/multilingual/multi-dataset/your_tts")
            chunks = [book_text[i:i+2000] for i in range(0, len(book_text), 2000)]
            combined = AudioSegment.empty()
            for i, chunk in enumerate(chunks):
                st.write(f"YourTTS chunk {i+1}/{len(chunks)}")
                out = os.path.join(base_dir, f"tts_{i}.wav")
                tts.tts_to_file(chunk, file_path=out, speaker_wav=voice_path, language="en")
                combined += AudioSegment.from_wav(out)
                os.remove(out)
            combined.export(mp3_path, format="mp3")
        st.audio(mp3_path)
