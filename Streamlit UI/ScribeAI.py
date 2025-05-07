import streamlit as st
from audiorecorder import audiorecorder
import whisper
import tempfile
import google.generativeai as genai

# Set Gemini API key
genai.configure(api_key="AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA")  # Replace with your actual Gemini API key

# Load Whisper model
whisper_model = whisper.load_model("base")

st.title("🎤 Scribe AI - Record, Transcribe, and Report")

# Record audio
st.header("🎙️ Step 1: Record Your Voice")
audio = audiorecorder("Start Recording", "Stop Recording")

if len(audio) > 0:
    st.audio(audio.tobytes(), format="audio/wav")

    # Save audio to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio.tobytes())
        audio_path = f.name

    # Transcribe button
    if st.button("📝 Transcribe"):
        with st.spinner("Transcribing..."):
            result = whisper_model.transcribe(audio_path)
            transcript = result["text"]
            st.session_state.transcript = transcript
            st.success("✅ Transcription Complete")
            st.text_area("🧾 Transcript", transcript, height=200)

# Report generation
if "transcript" in st.session_state:
    st.header("📄 Step 2: Generate Report")
    if st.button("Generate Report"):
        with st.spinner("Generating report using Gemini..."):
            prompt = f"""
            Summarize this patient-doctor audio conversation into a clean, professional medical report:
            {st.session_state.transcript}
            """
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            report = response.text.strip()
            st.session_state.report = report
            st.success("✅ Report Generated")
            st.text_area("📋 Final Report", report, height=300)
            st.download_button("📥 Download Report", data=report, file_name="Scribe_Report.txt", mime="text/plain")
