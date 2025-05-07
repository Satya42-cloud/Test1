import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import whisper
import numpy as np
import tempfile
import os
from fpdf import FPDF
import soundfile as sf

# Title
st.set_page_config(page_title="Scribe AI", layout="centered")
st.title("🎤 Scribe AI - Voice to Text Transcription")

# Load Whisper model only once
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# Custom audio processor
class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray().flatten().astype(np.float32) / 32768.0
        self.audio_frames.append(audio)
        return frame

# WebRTC audio streamer
ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,  # ✅ Correct enum usage
    audio_receiver_size=256,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioRecorder,
    async_processing=True,
)

# Transcription logic
if ctx.audio_processor:
    if st.button("🛑 Transcribe"):
        with st.spinner("Transcribing audio..."):
            audio_data = np.concatenate(ctx.audio_processor.audio_frames, axis=0)

            # Save to temp WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, 16000, format='WAV')
                tmp_path = tmp_file.name

            # Transcribe
            result = model.transcribe(tmp_path)
            transcript = result["text"]

            # Display transcript
            st.subheader("📝 Transcription:")
            st.text_area("Transcript", transcript, height=300)

            # PDF Report
            if st.button("📄 Generate PDF Report"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, "Scribe AI - Transcription Report", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, transcript)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
                    pdf.output(pdf_file.name)
                    st.download_button("⬇️ Download Report", open(pdf_file.name, "rb"), file_name="ScribeAI_Report.pdf")

            os.remove(tmp_path)
