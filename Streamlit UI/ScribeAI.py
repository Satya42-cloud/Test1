import streamlit as st
import whisper
import google.generativeai as genai
import tempfile
import os
import wave
import numpy as np
import sounddevice as sd

# Initialize Whisper model for transcription
whisper_model = whisper.load_model("base")

# Set up the Google Generative AI model (replace 'your-api-key' with your actual key)
genai.api_key = 'AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA'  # Make sure to replace with your actual API key

# Function to record audio
def record_audio():
    st.write("Recording... Please speak into the microphone.")
    samplerate = 44100  # Sampling rate (samples per second)
    duration = 30  # Duration of the recording in seconds
    recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=2, dtype='int16')
    sd.wait()  # Wait until recording is finished
    return recording, samplerate

# Function to save the recorded audio to a temporary file
def save_audio(recording, samplerate):
    temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_wav_file.name, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)  # 2 bytes per sample
        wf.setframerate(samplerate)
        wf.writeframes(recording)
    return temp_wav_file.name

# Function to transcribe audio
def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result['text']

# Function to generate medical report using LLM (Google AI Model)
def generate_medical_report(transcript):
    response = genai.GenerativeModel("gemma-3-27b-it").predict(
        f"Generate a structured medical report based on the following conversation:\n\n{transcript}"
    )
    return response.result

# Streamlit interface
st.title("🩺 Scribe AI - Doctor-Patient Conversation Recorder")

# Button to start recording
if st.button("Start Recording"):
    recording, samplerate = record_audio()
    audio_path = save_audio(recording, samplerate)
    st.audio(audio_path)  # Play the recorded audio for confirmation
    st.success("Recording finished!")

    # Transcribe the audio and generate report
    transcript = transcribe_audio(audio_path)
    st.subheader("📜 Transcript")
    st.write(transcript)

    # Generate medical report from the transcription
    st.subheader("📄 Generated Medical Report")
    report = generate_medical_report(transcript)
    st.write(report)

    # Option to download the transcript and report
    st.download_button("Download Transcript", transcript, file_name="transcript.txt")
    st.download_button("Download Medical Report", report, file_name="medical_report.txt")
