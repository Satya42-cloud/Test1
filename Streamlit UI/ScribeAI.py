import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import tempfile
import os
import google.generativeai as genai

# Google Gemini API key setup (replace with your own)
genai.configure(api_key="YOUR_GOOGLE_API_KEY")

# Streamlit UI setup
st.title("Scribe AI - Doctor-Patient Conversation Recorder")

# Placeholder for audio recording
class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_path = None

    def start_recording(self):
        self.is_recording = True
        st.write("Recording started...")

    def stop_recording(self, audio_data):
        self.is_recording = False
        st.write("Recording stopped.")
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(audio_data)
            self.audio_path = tmp_file.name
            st.audio(self.audio_path)  # Play the recorded audio

    def transcribe_audio(self):
        if not self.audio_path:
            return "No audio recorded."
        
        # Use Google Gemini API for transcription
        try:
            transcription = self.transcribe_with_gemini(self.audio_path)
            return transcription
        except Exception as e:
            st.error(f"Error during transcription: {e}")
            return "Transcription failed."

    def transcribe_with_gemini(self, audio_path):
        # Here you would send the audio data to Google Gemini for transcription
        # For now, it is a mock transcription. Replace this with the actual API call.
        
        # Mock transcription:
        prompt = f"Transcribe the following doctor-patient conversation from the audio at {audio_path}. Provide a detailed report."
        
        response = genai.GenerativeModel("gemma-3-27b-it").generate(prompt=prompt)
        return response.result


    def generate_report(self, transcription):
        # Here you would generate a detailed report based on the transcription.
        # This could be a simple text-based report.
        report = f"""
        **Doctor-Patient Conversation Report**
        
        **Transcription:**
        {transcription}
        
        **Summary:**
        The conversation between the doctor and patient focuses on identifying symptoms, diagnosing potential conditions, and outlining treatment plans.
        
        **Next Steps:**
        - Further diagnostic tests
        - Follow-up consultation
        - Medication prescribed
        """
        return report

# UI for Start and Stop recording
recorder = AudioRecorder()

# Button for starting the recording
if st.button("Start Recording"):
    recorder.start_recording()

# Button for stopping the recording
if st.button("Stop Recording"):
    if recorder.is_recording:
        # Use the WebRTC stream for recording
        webrtc_streamer(key="audio-recorder", mode=WebRtcMode.SENDRECV, client_settings=ClientSettings(
            video=False, audio=True, media_stream_constraints={"audio": True}))
        # Stop the recording and save the audio (mock behavior here, you can replace with actual audio data)
        audio_data = b"fake_audio_data"  # Replace this with actual recorded audio data
        recorder.stop_recording(audio_data)

# Button for transcribing audio
if st.button("Transcribe Audio"):
    transcription = recorder.transcribe_audio()
    st.write(transcription)

# Display transcription (mock implementation)
if transcription and transcription != "No audio recorded.":
    st.write("Transcription:")
    st.write(transcription)

    # Button for generating the report
    if st.button("Generate Report"):
        report = recorder.generate_report(transcription)
        st.write(report)

        # Provide an option to download the report as a file
        report_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8')
        report_file.write(report)
        report_file.close()

        with open(report_file.name, "rb") as f:
            st.download_button(
                label="Download Report",
                data=f,
                file_name="doctor_patient_report.txt",
                mime="text/plain"
            )
