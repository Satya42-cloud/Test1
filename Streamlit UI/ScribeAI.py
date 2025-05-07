import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import av
import numpy as np
import tempfile
import whisper
import os
import soundfile as sf
import google.generativeai as genai

# 👉 Configure your Gemini API key
genai.configure(api_key="AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA")  # Replace this with your actual Gemini API key

# Load Whisper model
whisper_model = whisper.load_model("base")

# Audio Processor for recording
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.frames.append(audio)
        return frame

# Streamlit UI
st.title("🎤 Scribe AI - Record, Transcribe & Report")

ctx = webrtc_streamer(
    key="scribe",
    mode=WebRtcMode.SENDONLY,
    in_audio=True,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

# Capture and store audio after stopping
if ctx.state.playing:
    st.info("🎙️ Recording... Speak now.")
elif ctx.audio_processor and ctx.audio_processor.frames:
    audio_data = np.concatenate(ctx.audio_processor.frames, axis=0)
    temp_audio_path = tempfile.mktemp(suffix=".wav")
    sf.write(temp_audio_path, audio_data, 16000)
    st.success("✅ Audio recording captured!")

    if st.button("📝 Transcribe"):
        with st.spinner("Transcribing audio..."):
            result = whisper_model.transcribe(temp_audio_path)
            transcript = result["text"]
            st.session_state.transcript = transcript
            st.success("Transcription complete!")
            st.text_area("🧾 Transcript", transcript, height=200)

# Generate report
if "transcript" in st.session_state:
    if st.button("📄 Generate Report"):
        with st.spinner("Generating report with Gemini..."):
            prompt = f"""
            Summarize the following transcription in a professional report format:
            {st.session_state.transcript}
            """
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            report = response.text.strip()
            st.session_state.report = report
            st.success("Report generated!")
            st.text_area("📝 Final Report", report, height=300)

            st.download_button("📥 Download Report", data=report, file_name="scribe_report.txt", mime="text/plain")
