import streamlit as st
import os
import tempfile
import whisper
import google.generativeai as genai
from azure.storage.filedatalake import DataLakeServiceClient
from fpdf import FPDF

# ----------------------------
# CONFIG
# ----------------------------

GOOGLE_API_KEY = "AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA"
AZURE_STORAGE_ACCOUNT_NAME = "aitoolschatbotssa"
AZURE_STORAGE_ACCOUNT_KEY = "81nZ6FOa+hiXdkA8pEHb7MHJNF5Go4YamjNZweJloFIAMIz7qeIhXVYBrFwvcGR54iZoqKVKXmPe+AStkYbedA=="
AZURE_FILESYSTEM_NAME = "insurance"
AZURE_DIRECTORY = "audio_uploads"

genai.configure(api_key=GOOGLE_API_KEY)

# ----------------------------
# Upload to Azure ADLS
# ----------------------------

def upload_to_adls(file_path, file_name):
    try:
        service_client = DataLakeServiceClient(
            account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.dfs.core.windows.net",
            credential=AZURE_STORAGE_ACCOUNT_KEY,
        )
        file_system_client = service_client.get_file_system_client(file_system=AZURE_FILESYSTEM_NAME)
        directory_client = file_system_client.get_directory_client(AZURE_DIRECTORY)
        file_client = directory_client.create_file(file_name)

        with open(file_path, "rb") as f:
            data = f.read()
        file_client.append_data(data=data, offset=0, length=len(data))
        file_client.flush_data(len(data))
        st.success("✅ Uploaded to Azure Data Lake.")
    except Exception as e:
        st.error(f"❌ Azure upload failed: {e}")

# ----------------------------
# Transcribe WAV Audio (No ffmpeg)
# ----------------------------

import whisper
import soundfile as sf

def transcribe_without_ffmpeg(wav_path):
    model = whisper.load_model("base")
    audio, sr = sf.read(wav_path)
    # Whisper expects 16kHz audio
    if sr != 16000:
        import numpy as np
        from scipy.signal import resample
        audio = resample(audio, int(len(audio) * 16000 / sr))
    result = model.transcribe(audio, language='en', fp16=False)  # pass np array directly
    return result["text"]


# ----------------------------
# Generate Medical Report
# ----------------------------

def generate_report(transcription):
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        You are a clinical documentation assistant. Convert the following doctor-patient conversation
        into a structured medical report with the following sections:

        - Chief Complaint
        - History of Present Illness
        - Past Medical History
        - Medications
        - Allergies
        - Family History
        - Social History
        - Review of Systems
        - Physical Exam Plan
        - Impression / Next Steps

        Conversation:
        \"\"\"{transcription}\"\"\"
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ Report generation failed: {e}")
        return ""

# ----------------------------
# Generate PDF from Report
# ----------------------------

def generate_pdf(report_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in report_text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf_path = os.path.join(tempfile.gettempdir(), "medical_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title="Medical Audio Assistant", page_icon="🩺")
st.title("🩺 Medical Audio Assistant")

uploaded_file = st.file_uploader("📤 Upload a WAV audio file (PCM 16-bit format)", type=["wav"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    upload_to_adls(audio_path, uploaded_file.name)

    user_prompt = st.text_input("💬 What do you want me to do?")

    if user_prompt:
        if "text" in user_prompt.lower():
            with st.spinner("🧠 Transcribing audio..."):
                transcript = transcribe_audio(audio_path)
                if transcript:
                    st.subheader("📝 Transcript")
                    st.write(transcript)
                    st.session_state.transcript = transcript

        elif "report" in user_prompt.lower():
            if "transcript" not in st.session_state:
                st.warning("Please transcribe the audio first.")
            else:
                with st.spinner("📄 Generating medical report..."):
                    report = generate_report(st.session_state.transcript)
                    if report:
                        st.subheader("🧾 Medical Report")
                        st.text_area("Generated Report", report, height=300)
                        st.session_state.report = report

        elif "pdf" in user_prompt.lower():
            if "report" not in st.session_state:
                st.warning("Please generate the report first.")
            else:
                with st.spinner("📄 Creating PDF..."):
                    pdf_path = generate_pdf(st.session_state.report)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF",
                            data=f,
                            file_name="medical_report.pdf",
                            mime="application/pdf"
                        )
        else:
            st.info("Try commands like: 'convert to text', 'generate report', or 'give me PDF'.")
