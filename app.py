import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import tempfile
import speech_recognition as sr
import os
import wave

st.set_page_config(page_title="Reconnaissance Vocale", layout="centered")

st.title("🎙️ Application de Reconnaissance Vocale")
st.markdown("Enregistrez votre voix, puis obtenez la transcription.")

# Langue de transcription
language = st.selectbox("Choisissez la langue :", [
    ("fr-FR", "Français"),
    ("en-US", "Anglais (US)"),
    ("es-ES", "Espagnol"),
    ("de-DE", "Allemand")
], format_func=lambda x: x[1])[0]

# État de session pour stocker l’audio
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "transcription" not in st.session_state:
    st.session_state.transcription = ""

# Configuration WebRTC
client_settings = ClientSettings(
    media_stream_constraints={"audio": True, "video": False},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Enregistre l'audio capté
class AudioProcessor:
    def __init__(self):
        self.frames = []

    def recv(self, frame):
        audio = frame.to_ndarray()
        self.frames.append(audio)
        return av.AudioFrame.from_ndarray(audio, layout="mono")

processor = AudioProcessor()

webrtc_ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDRECV,
    in_audio=True,
    client_settings=client_settings,
    audio_processor_factory=lambda: processor,
)

# Bouton pour arrêter l'enregistrement et sauvegarder l'audio
if st.button("🛑 Arrêter et transcrire"):
    if not processor.frames:
        st.warning("Aucun audio détecté.")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            wf = wave.open(tmpfile.name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16 bits
            wf.setframerate(16000)
            import numpy as np
            audio_data = np.concatenate(processor.frames).astype(np.int16).tobytes()
            wf.writeframes(audio_data)
            wf.close()
            st.session_state.audio_file = tmpfile.name

        # Transcription
        r = sr.Recognizer()
        with sr.AudioFile(st.session_state.audio_file) as source:
            audio = r.record(source)
            try:
                text = r.recognize_google(audio, language=language)
                st.success("Transcription réussie :")
                st.write(text)
                st.session_state.transcription = text
            except sr.UnknownValueError:
                st.error("Impossible de comprendre l'audio.")
            except sr.RequestError as e:
                st.error(f"Erreur de service : {e}")

# Télécharger le fichier texte
if st.session_state.transcription:
    st.download_button(
        label="💾 Télécharger la transcription",
        data=st.session_state.transcription,
        file_name="transcription.txt"
    )

# Nettoyage
if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
    os.remove(st.session_state.audio_file)
