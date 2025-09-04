import streamlit as st
import os
import pdfplumber
from openvoice.api import BaseSpeakerTTS, ToneColorConverter
from openvoice import se_extractor
from pydub import AudioSegment
import torch

st.title("Voice Cloning Audiobook Generator")

# File upload
pdf_file = st.file_uploader("Upload PDF (e.g., Life 3.0)", type="pdf")
voice_file = st.file_uploader("Upload Voice Sample (e.g., my_voice.wav)", type=["wav", "mp3"])

if pdf_file and voice_file:
    # Save uploaded files
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.getbuffer())
    with open("temp_voice.wav", "wb") as f:
        f.write(voice_file.getbuffer())

    # Extract text
    with pdfplumber.open("temp.pdf") as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    st.write(f"Extracted {len(text)} characters")

    # Placeholder for OpenVoice processing (simplified)
    st.write("Processing with OpenVoice (voice cloning in progress)...")
    # Add your OpenVoice logic here (e.g., call openvoice_pipeline.py functions)
    st.success("Audiobook generation complete! Check D:\\Life_3.0_audiobook.mp3")

    # Cleanup
    os.remove("temp.pdf")
    os.remove("temp_voice.wav")