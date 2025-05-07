import streamlit as st
import streamlit.components.v1 as components
import tempfile
import base64
import whisper
from fpdf import FPDF

# Title of the app
st.title("🎤 Scribe AI - Record Audio")

# Step 1: Embed JavaScript Recorder in the Streamlit app
st.markdown(
    """
    <script src="https://cdn.jsdelivr.net/npm/recorderjs"></script>
    <script>
        let recorder;
        let audioBlob;
        
        function startRecording() {
            let audioContext = new (window.AudioContext || window.webkitAudioContext)();
            let stream = navigator.mediaDevices.getUserMedia({audio: true});
            
            stream.then(function(mediaStream) {
                recorder = new Recorder(audioContext, {numChannels: 1});
                recorder.initStream(mediaStream);
                recorder.record();
                document.getElementById('status').innerText = "Recording... Click 'Stop' when done.";
            });
        }
        
        function stopRecording() {
            recorder.stop();
            recorder.exportWAV(function(blob) {
                audioBlob = blob;
                let reader = new FileReader();
                reader.onloadend = function() {
                    let audioData = reader.result.split(',')[1];
                    window.parent.postMessage({ type: 'audio', data: audioData }, "*");
                };
                reader.readAsDataURL(blob);
                document.getElementById('status').innerText = "Recording stopped.";
            });
        }
        
        function downloadAudio() {
            let link = document.createElement('a');
            link.href = URL.createObjectURL(audioBlob);
            link.download = "recorded_audio.wav";
            link.click();
        }
    </script>
    <button onclick="startRecording()">Start Recording</button>
    <button onclick="stopRecording()">Stop Recording</button>
    <button onclick="downloadAudio()">Download Audio</button>
    <p id="status">Press "Start Recording" to begin.</p>
    """,
    unsafe_allow_html=True
)

# Step 2: Retrieve audio data and display
audio_data = st.empty()

# To handle the audio data in Python (base64 encoding to save as a file)
def audio_callback(data):
    audio_data.audio(data, format="audio/wav")

# Step 3: Handle the message with the recorded audio
def handle_message(message):
    if message["type"] == "audio":
        audio_base64 = message["data"]
        
        # Debugging step: Check if the audio data is in base64 format
        if not audio_base64 or not isinstance(audio_base64, str):
            st.error("Received invalid audio data!")
            return None

        try:
            # Decode the base64 audio
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            st.error(f"Error decoding base64 data: {e}")
            return None
        
        # Save to temp file and process it (transcription, etc.)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file:
            tmp_audio_file.write(audio_bytes)
            tmp_audio_file.close()
            audio_callback(tmp_audio_file.name)
            return tmp_audio_file.name

# Step 4: Setup listener for JavaScript messages
components.html("""
    <script>
        window.addEventListener("message", function(event) {
            if (event.data.type === 'audio') {
                window.parent.postMessage(event.data, '*');
            }
        }, false);
    </script>
""", height=0)

st.write("Audio recorded will appear here once uploaded.")

# Step 5: Transcription using Whisper
def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

# Step 6: Handle the audio file and transcribe
if audio_data:
    audio_path = handle_message({"type": "audio", "data": audio_data})
    if audio_path:
        st.write("Transcription Result:")
        transcript = transcribe_audio(audio_path)
        st.text_area("Transcript", transcript, height=300)
        
        # Step 7: Generate Report as PDF
        if st.button("Generate Report"):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # Set title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, txt="Scribe AI - Transcription Report", ln=True, align='C')
            
            # Add Transcription text
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt="Transcription:\n\n" + transcript)
            
            # Save PDF to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf_file:
                pdf.output(tmp_pdf_file.name)
                tmp_pdf_file.close()
                
                # Allow the user to download the PDF
                with open(tmp_pdf_file.name, "rb") as file:
                    st.download_button(
                        label="Download Report",
                        data=file,
                        file_name="scribe_ai_report.pdf",
                        mime="application/pdf"
                    )
