import streamlit as st
from transformers import pipeline
import librosa
import numpy as np
import tempfile
import os
from datetime import datetime
import io
import wave
import pyaudio
import threading
import time

# Configure page
st.set_page_config(
    page_title="🎙️ Speech-to-Text Transcription",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .timestamp-box {
        background: #e3f2fd;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        border-left: 3px solid #2196f3;
    }
    .recording-indicator {
        background: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #f44336;
        text-align: center;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'transcription_history' not in st.session_state:
    st.session_state.transcription_history = []

@st.cache_resource
def load_asr_model(model_name):
    """Load and cache the ASR model"""
    try:
        return pipeline("automatic-speech-recognition", model=model_name)
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

def transcribe_audio(audio_file, model_pipeline):
    """Transcribe audio file using the loaded model"""
    try:
        # Load audio as numpy array (forces mono, resample to 16kHz)
        audio, sr = librosa.load(audio_file, sr=16000)
        
        # Run the ASR pipeline with timestamps
        result = model_pipeline(audio, return_timestamps=True)
        return result
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None

def record_audio(duration, sample_rate=16000):
    """Record audio from microphone"""
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    
    try:
        p = pyaudio.PyAudio()
        
        stream = p.open(format=format,
                       channels=channels,
                       rate=sample_rate,
                       input=True,
                       frames_per_buffer=chunk)
        
        frames = []
        
        for i in range(0, int(sample_rate / chunk * duration)):
            if not st.session_state.recording:
                break
            data = stream.read(chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Convert to numpy array
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize
        
        return audio_data, sample_rate
    except Exception as e:
        st.error(f"Error recording audio: {str(e)}")
        return None, None

def save_transcription_history(text, timestamp, method):
    """Save transcription to history"""
    st.session_state.transcription_history.append({
        'text': text,
        'timestamp': timestamp,
        'method': method
    })

def export_transcriptions():
    """Export transcription history as text file"""
    if not st.session_state.transcription_history:
        return None
    
    content = "Speech-to-Text Transcription History\n"
    content += "=" * 50 + "\n\n"
    
    for i, item in enumerate(st.session_state.transcription_history, 1):
        content += f"Transcription #{i}\n"
        content += f"Method: {item['method']}\n"
        content += f"Timestamp: {item['timestamp']}\n"
        content += f"Text: {item['text']}\n"
        content += "-" * 30 + "\n\n"
    
    return content

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎙️ Advanced Speech-to-Text Transcription</h1>
        <p>Powered by OpenAI Whisper | Upload files or record live audio</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        model_options = {
            "Whisper Tiny (Fast)": "openai/whisper-tiny",
            "Whisper Base (Balanced)": "openai/whisper-base",
            "Whisper Small (Better Quality)": "openai/whisper-small"
        }
        
        selected_model = st.selectbox(
            "Choose Model",
            options=list(model_options.keys()),
            help="Larger models provide better accuracy but are slower"
        )
        
        model_name = model_options[selected_model]
        
        # Load model
        with st.spinner(f"Loading {selected_model}..."):
            asr_pipeline = load_asr_model(model_name)
        
        if asr_pipeline:
            st.success("✅ Model loaded successfully!")
        else:
            st.error("❌ Failed to load model")
            return
        
        st.divider()
        
        # Recording settings
        st.subheader("🎤 Recording Settings")
        recording_duration = st.slider("Recording Duration (seconds)", 5, 60, 10)
        
        st.divider()
        
        # History management
        st.subheader("📝 Transcription History")
        if st.session_state.transcription_history:
            st.write(f"Total transcriptions: {len(st.session_state.transcription_history)}")
            
            if st.button("📥 Export History"):
                export_content = export_transcriptions()
                if export_content:
                    st.download_button(
                        label="Download Transcriptions",
                        data=export_content,
                        file_name=f"transcriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            
            if st.button("🗑️ Clear History"):
                st.session_state.transcription_history = []
                st.rerun()
        else:
            st.write("No transcriptions yet")
    
    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3>📁 File Upload Transcription</h3>
            <p>Upload audio files for transcription</p>
        </div>
        """, unsafe_allow_html=True)
        
        audio_file = st.file_uploader(
            "Upload an audio file",
            type=["mp3", "wav", "flac", "m4a", "ogg"],
            help="Supported formats: MP3, WAV, FLAC, M4A, OGG"
        )
        
        if audio_file is not None:
            st.audio(audio_file)
            
            col1a, col1b = st.columns(2)
            with col1a:
                if st.button("🚀 Transcribe File", type="primary"):
                    with st.spinner("Transcribing... Please wait ⏳"):
                        result = transcribe_audio(audio_file, asr_pipeline)
                        
                        if result:
                            st.success("✅ Transcription complete!")
                            
                            # Save to history
                            save_transcription_history(
                                result["text"],
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "File Upload"
                            )
                            
                            # Display results
                            st.subheader("📝 Full Transcript:")
                            st.text_area("Transcript", result["text"], height=150)
                            
                            # Download transcript
                            st.download_button(
                                label="📥 Download Transcript",
                                data=result["text"],
                                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                            
                            # Timestamps
                            if "chunks" in result and result["chunks"]:
                                st.subheader("🕑 Detailed Timestamps:")
                                for chunk in result["chunks"]:
                                    start = chunk.get('timestamp', [None, None])[0]
                                    end = chunk.get('timestamp', [None, None])[1]
                                    text = chunk.get('text', "")
                                    
                                    if start is not None and end is not None:
                                        st.markdown(f"""
                                        <div class="timestamp-box">
                                            <strong>{start:.2f}s - {end:.2f}s</strong> → {text}
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div class="timestamp-box">
                                            <strong>No timestamp</strong> → {text}
                                        </div>
                                        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3>🎤 Live Audio Recording</h3>
            <p>Record audio directly from your microphone</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recording interface
        if not st.session_state.recording:
            if st.button("🔴 Start Recording", type="primary"):
                st.session_state.recording = True
                st.rerun()
        else:
            st.markdown("""
            <div class="recording-indicator">
                <h4>🔴 RECORDING IN PROGRESS</h4>
                <p>Speak clearly into your microphone...</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⏹️ Stop Recording"):
                st.session_state.recording = False
                st.rerun()
        
        # Handle recording
        if st.session_state.recording:
            with st.spinner(f"Recording for {recording_duration} seconds..."):
                audio_data, sample_rate = record_audio(recording_duration)
                st.session_state.recording = False
                
                if audio_data is not None:
                    st.success("✅ Recording completed!")
                    
                    # Save audio to temporary file for transcription
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                        # Convert numpy array to wav file
                        with wave.open(tmp_file.name, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(sample_rate)
                            wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
                        
                        # Play recorded audio
                        st.audio(tmp_file.name)
                        
                        # Transcribe
                        with st.spinner("Transcribing recorded audio..."):
                            result = transcribe_audio(tmp_file.name, asr_pipeline)
                            
                            if result:
                                st.success("✅ Live transcription complete!")
                                
                                # Save to history
                                save_transcription_history(
                                    result["text"],
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "Live Recording"
                                )
                                
                                # Display results
                                st.subheader("📝 Live Transcript:")
                                st.text_area("Live Transcript", result["text"], height=150)
                                
                                # Download transcript
                                st.download_button(
                                    label="📥 Download Live Transcript",
                                    data=result["text"],
                                    file_name=f"live_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain"
                                )
                        
                        # Clean up temporary file
                        os.unlink(tmp_file.name)
    
    # Recent transcriptions
    if st.session_state.transcription_history:
        st.divider()
        st.subheader("📋 Recent Transcriptions")
        
        # Show last 3 transcriptions
        recent_transcriptions = st.session_state.transcription_history[-3:]
        
        for i, item in enumerate(reversed(recent_transcriptions)):
            with st.expander(f"🎯 {item['method']} - {item['timestamp']}"):
                st.write(item['text'])
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎙️ Advanced Speech-to-Text Application | Powered by OpenAI Whisper</p>
        <p>💡 Tip: Use headphones for better recording quality</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
