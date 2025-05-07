import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import numpy as np
import whisper
import tempfile
from fpdf import FPDF
import genai  # Import GenAI library
import os

# Set up GenAI API key (replace with your key)
genai.api_key = "your_genai_api_key_here"

st.set_page_config(page_title="Scribe AI", layout="centered")
st.title("🩺 Scribe AI - Doctor-Patient Transcription")

# Load Whisper model once
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# Audio frame processor
class AudioProcessor:
    def __init__(self):
        self.recording = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.recording.append(audio)
        return frame

# Session state variables
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "report" not in st.session_state:
    st.session_state.report = None

# Recording section
st.header("🎤 Record Doctor-Patient Conversation")
ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,
    in_audio=True,
    client_settings=ClientSettings(
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    ),
    audio_processor_factory=AudioProcessor,
)

# Save and process after recording ends
if ctx and ctx.state.playing is False and ctx.audio_processor:
    audio = np.concatenate(ctx.audio_processor.recording, axis=1)[0]  # Mono
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        import soundfile as sf
        sf.write(f.name, audio.T, 48000)
        st.session_state.audio_data = f.name
        st.success("✅ Recording saved. Ready to transcribe.")

# Transcription section
if st.session_state.audio_data:
    if st.button("📝 Transcribe Audio"):
        with st.spinner("Transcribing..."):
            result = model.transcribe(st.session_state.audio_data)
            st.session_state.transcript = result["text"]
        st.success("✅ Transcription Complete")
        st.text_area("📄 Transcript", st.session_state.transcript, height=200)

# GenAI-based Report Generation using Gemma-3-27B
def generate_report_with_genai(transcript):
    prompt = f"""
    You are a medical transcriptionist. Based on the following conversation between a doctor and a patient, create a well-structured medical report.
    The report should include:
    - A consultation summary.
    - Doctor's notes (diagnosis, treatment, and follow-up).
    - Any relevant medical instructions.
    
    Conversation:
    {transcript}

    Medical Report:
    """

    try:
        # Use GenAI's gemma-3-27b-it model to generate the report
        model = genai.GenerativeModel("gemma-3-27b-it")
        response = model.generate_content(prompt, max_tokens=1000, temperature=0.7)
        report = response['content']
        return report
    except Exception as e:
        return f"Error generating report: {e}"

# Report generation using GenAI's Gemma-3-27B model
if st.session_state.transcript:
    if st.button("📄 Generate Medical Report"):
        report_text = generate_report_with_genai(st.session_state.transcript)
        st.session_state.report = report_text
        st.text_area("📝 Medical Report", report_text, height=300)

    if st.session_state.report:
        # Save the report as a PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in st.session_state.report.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf_path = "report.pdf"
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download Report", f, file_name="medical_report.pdf")
