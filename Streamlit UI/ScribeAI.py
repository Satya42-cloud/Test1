import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import whisper
import os
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")  # Replace with your actual key

# Load Whisper model
whisper_model = whisper.load_model("base")

# Audio Processor Class
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.audio_frames.append(audio)
        return frame

# Title
st.title("🎤 Scribe AI - Record, Transcribe & Generate Report")

# WebRTC streaming for audio capture
ctx = webrtc_streamer(
    key="audio",
    mode="sendonly",
    in_audio=True,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

# Store audio after recording stops
if ctx.audio_processor and ctx.audio_processor.audio_frames:
    st.session_state.audio_data = np.concatenate(ctx.audio_processor.audio_frames, axis=0)

# Transcription
if "audio_data" in st.session_state:
    if st.button("📝 Transcribe"):
        with st.spinner("Transcribing audio..."):
            audio = st.session_state.audio_data.astype(np.float32)
            temp_audio_path = tempfile.mktemp(suffix=".wav")
            import soundfile as sf
            sf.write(temp_audio_path, audio, 16000)
            result = whisper_model.transcribe(temp_audio_path)
            st.session_state.transcript = result["text"]
            st.success("Transcription complete!")

# Show transcript
if "transcript" in st.session_state:
    st.subheader("🧾 Transcription")
    st.text_area("Transcript", st.session_state.transcript, height=200)

    if st.button("📄 Generate Report"):
        with st.spinner("Generating report using Gemini..."):
            prompt = f"""
            You are a professional note-taking assistant. Convert the following transcript into a well-organized summary:
            ---
            {st.session_state.transcript}
            ---
            Format it in bullet points or structured paragraphs.
            """
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            st.session_state.report = response.text.strip()
            st.success("Report generated!")

# Show Report
if "report" in st.session_state:
    st.subheader("📝 Final Report")
    st.text_area("Report", st.session_state.report, height=300)

    st.download_button(
        label="📥 Download Report",
        data=st.session_state.report,
        file_name="scribe_ai_report.txt",
        mime="text/plain"
    )
