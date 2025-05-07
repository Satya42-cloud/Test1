import os
import time
import wave
import numpy as np
import sounddevice as sd
import google.generativeai as genai
import streamlit as st

# Step 1: Setup the Google Gemini LLM model API
genai.configure(api_key="AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA")  # Replace with your actual API key
model = genai.GenerativeModel("gemma-3-27b-it")  # Replace with the appropriate model

# Step 2: Function to record audio
def record_audio(duration=10, fs=16000):
    """Record audio from the microphone"""
    st.write("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    st.write("Recording finished.")
    return audio

# Step 3: Function to save recorded audio to a .wav file
def save_audio(audio, fs, filename="recording.wav"):
    """Save audio to a wav file"""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(np.int16().itemsize)
        wf.setframerate(fs)
        wf.writeframes(audio.tobytes())
    return filename

# Step 4: Transcribe audio using the model
def transcribe_audio(filename="recording.wav"):
    """Transcribe the audio into text using LLM"""
    with open(filename, 'rb') as audio_file:
        audio_data = audio_file.read()

    prompt = f"""
    You are a medical assistant. Transcribe the following conversation between a doctor and a patient into a detailed medical report.
    The doctor and patient conversation is as follows:

    Audio: {audio_data}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Step 5: Generate the medical report from the transcription
def generate_medical_report(transcription):
    """Generate a report from the transcription"""
    prompt = f"""
    Using the transcribed conversation, generate a well-defined medical report for the patient. Include the following sections:
    - Patient's Symptoms
    - Diagnosis
    - Recommended Treatment
    - Follow-up Instructions

    Transcription: {transcription}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Step 6: Streamlit UI for interacting with the app
st.title("Scribe AI - Medical Transcription")

# Setup buttons for user interaction
if 'audio_recorded' not in st.session_state:
    st.session_state.audio_recorded = False
    st.session_state.audio_file = None

# Button to start recording
if st.button("Start Recording"):
    st.session_state.audio_recorded = False
    st.session_state.audio_file = None
    audio_data = record_audio(duration=10)  # Record for 10 seconds (adjust as needed)
    filename = save_audio(audio_data, fs=16000)
    st.session_state.audio_file = filename
    st.session_state.audio_recorded = True
    st.write(f"Audio saved to {filename}")

# Button to transcribe the recorded audio
if st.session_state.audio_recorded and st.button("Transcribe Audio"):
    transcription = transcribe_audio(filename=st.session_state.audio_file)
    st.session_state.transcription = transcription
    st.write("Transcription:")
    st.text_area("Transcription", transcription, height=200)

# Button to generate medical report
if 'transcription' in st.session_state and st.session_state.transcription:
    if st.button("Generate Medical Report"):
        report = generate_medical_report(st.session_state.transcription)
        st.session_state.medical_report = report
        st.write("Generated Medical Report:")
        st.text_area("Medical Report", report, height=300)

# Button to download the report
if 'medical_report' in st.session_state:
    if st.button("Download Report"):
        report_file_name = "medical_report.txt"
        with open(report_file_name, "w") as file:
            file.write(st.session_state.medical_report)
        
        with open(report_file_name, "rb") as file:
            st.download_button(label="Download the report", data=file, file_name=report_file_name, mime="text/plain")
