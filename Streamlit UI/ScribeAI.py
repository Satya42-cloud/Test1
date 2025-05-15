import streamlit as st
import os
import tempfile
import shutil
import whisper
import subprocess
import google.generativeai as genai
from azure.storage.filedatalake import DataLakeServiceClient
from fpdf import FPDF

# ----------------------------
# HARD-CODED CONFIGURATION
# ----------------------------

GOOGLE_API_KEY = "AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA"
AZURE_STORAGE_ACCOUNT_NAME = "aitoolschatbotssa"
AZURE_STORAGE_ACCOUNT_KEY = "81nZ6FOa+hiXdkA8pEHb7MHJNF5Go4YamjNZweJloFIAMIz7qeIhXVYBrFwvcGR54iZoqKVKXmPe+AStkYbedA=="
AZURE_FILESYSTEM_NAME = "insurance"
AZURE_DIRECTORY = "audio_uploads"

# ----------------------------
# INITIALIZE GOOGLE API
# ----------------------------
genai.configure(api_key=GOOGLE_API_KEY)

# ----------------------------
# Utility: Check if ffmpeg is installed
# ----------------------------
def is_ffmpeg_installed():
    return shutil.which("ffmpeg") is not None

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
            file_contents = f.read()
        file_client.append_data(data=file_contents, offset=0, length=len(file_contents))
        file_client.flush_data(len(file_contents))
        st.success("✅ Uploaded to Azure Data Lake.")
    except Exception as e:
        st.error(f"❌ Azure upload failed: {e}")

# ----------------------------
# Transcribe Audio using Whisper
# ----------------------------
def transcribe_audio(audio_path):
    if not is_ffmpeg_installed():
        st.error("❌ FFmpeg is not installed. Please install it to enable transcription.")
        return ""

    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result['text']
    except Exception as e:
        st.error(f"❌ Transcription failed: {e}")
        return ""

# ----------------------------
# Generate Medical Report using Gemini
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
    pdf_output_path = os.path.join(tempfile.gettempdir(), "medical_report.pdf")
    pdf.output(pdf_output_path)
    return pdf_output_path

# ----------------------------
# STREAMLIT APP
# ----------------------------
st.set_page_config(page_title="Medical Audio Assistant", page_icon="🩺")
st.title("🩺 Medical Audio Assistant")

uploaded_file = st.file_uploader("📤 Upload an audio file", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
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
