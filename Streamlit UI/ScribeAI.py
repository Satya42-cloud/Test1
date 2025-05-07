# scribe_ai_app.py

import streamlit as st
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import tempfile
import os
import whisper
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key="AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA")  # 🔁 Replace with your key

st.title("🩺 Scribe AI – Clinical Note Generator")

# Record audio
duration = st.slider("🎙️ Recording duration (seconds)", 3, 30, 10)
fs = 44100

if st.button("Start Recording"):
    st.info("Recording in progress...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    st.success("Recording complete!")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        write(f.name, fs, audio)
        st.audio(f.name, format="audio/wav")

        st.session_state.audio_path = f.name

# Transcribe audio with Whisper
if "audio_path" in st.session_state and st.button("Transcribe Audio"):
    with st.spinner("Transcribing with Whisper..."):
        model = whisper.load_model("base")
        result = model.transcribe(st.session_state.audio_path)
        transcript = result["text"]
        st.session_state.transcript = transcript
        st.text_area("📝 Transcript", transcript, height=200)

# Generate Clinical Note with Gemini
if "transcript" in st.session_state and st.button("Generate Clinical Note"):
    with st.spinner("Generating SOAP note..."):
        prompt = f"""
        You are a medical scribe. Based on this doctor-patient conversation transcript, generate a clinical SOAP note:

        Transcript:
        {st.session_state.transcript}

        Format:
        S: [Subjective - patient's complaints]
        O: [Objective - doctor's observations]
        A: [Assessment - diagnosis]
        P: [Plan - treatment plan]

        Structured SOAP Note:
        """

        gemini_model = genai.GenerativeModel("gemini-pro")
        response = gemini_model.generate_content(prompt)
        st.text_area("🧾 Clinical Note (SOAP Format)", response.text, height=300)
