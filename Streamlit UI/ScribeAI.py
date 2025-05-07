import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import whisper
import numpy as np
import tempfile
import os
from fpdf import FPDF

# Title
st.title("🎤 Scribe AI - Voice to Text Transcription")

# Initialize Whisper model
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# AudioProcessor for webrtc_streamer
class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray().flatten().astype(np.float32) / 32768.0  # Convert to float32
        self.audio_frames.append(audio)
        return frame

# Start the WebRTC audio streamer
ctx = webrtc_streamer(
    key="audio",
    mode="sendonly",
    audio_receiver_size=256,
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioRecorder,
    async_processing=True,
)

# Process recorded audio
if ctx.audio_processor:
    if st.button("🛑 Transcribe"):
        with st.spinner("Transcribing audio..."):
            # Concatenate audio frames
            audio_data = np.concatenate(ctx.audio_processor.audio_frames, axis=0)

            # Save to WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                import soundfile as sf
                sf.write(tmp_file.name, audio_data, 16000, format='WAV')
                tmp_path = tmp_file.name

            # Transcribe using Whisper
            result = model.transcribe(tmp_path)
            transcript = result["text"]

            # Show transcript
            st.subheader("📝 Transcription:")
            st.text_area("Transcript", transcript, height=300)

            # Generate report
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

            # Clean up
            os.remove(tmp_path)
