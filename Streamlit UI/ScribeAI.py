import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
import google.generativeai as genai
from io import BytesIO
from pydub import AudioSegment
import os

# Set up Google Generative AI API key
genai.configure(api_key="YOUR_GOOGLE_API_KEY")  # Replace with your API key

# Global variables to hold the audio recording data and control flags
audio_data = None
is_recording = False
filename = "/content/audio_recording.wav"

# Function to record audio
def record_audio(duration=10, samplerate=44100):
    global audio_data
    print("Recording Started...")

    # Record audio from the microphone
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished

    # Save audio to a file
    wav.write(filename, samplerate, audio_data)  # Save as .wav file
    print(f"Recording saved as {filename}")

# Function to stop recording manually
def stop_recording():
    global is_recording
    print("Recording Stopped")
    sd.stop()
    is_recording = False

# Function to transcribe audio using Google Generative AI
def transcribe_audio(filename):
    print("Transcribing the audio...")
    
    # Read the audio file and convert it to text
    try:
        with open(filename, 'rb') as audio_file:
            audio_content = audio_file.read()
        
        # Call the generative model to transcribe (replace this with actual speech-to-text logic)
        response = genai.GenerativeModel("gemma-3-27b-it").generate(
            prompt=f"Please transcribe the following audio: {audio_content}",
            max_output_tokens=1000
        )
        
        transcription = response.result['text']
        print(f"Transcription: {transcription}")
        return transcription
    
    except Exception as e:
        print(f"Error in transcription: {e}")
        return None

# Function to generate the report based on transcription
def generate_report(transcription):
    print("Generating Medical Report...")
    
    # Create a simple medical report structure
    report = f"""
    Medical Report:
    ----------------------
    Doctor's Notes:
    {transcription}
    ----------------------
    """
    return report

# UI Functions for Colab
def start_recording(duration=10):
    print("Starting recording...")
    record_audio(duration=duration)
    print("Recording complete.")

def stop_and_transcribe():
    stop_recording()
    transcription = transcribe_audio(filename)
    
    if transcription:
        report = generate_report(transcription)
        print(report)
        
        # Save report to a text file
        with open("/content/medical_report.txt", 'w') as report_file:
            report_file.write(report)
        
        print("Medical Report generated and saved as medical_report.txt.")
        return report
    else:
        print("Transcription failed.")
        return None

# Example Usage in Colab
# 1. Start recording
start_recording(duration=10)

# 2. Stop recording and transcribe
report = stop_and_transcribe()

# 3. Provide download link for the report
if report:
    from google.colab import files
    files.download("/content/medical_report.txt")  # Download the report
