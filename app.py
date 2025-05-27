import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os

st.set_page_config(page_title="Transcription Locale", layout="centered")
st.title("🎙️ Transcription audio locale")
st.markdown("Téléversez un fichier audio (.mp3, .wav, .m4a, .ogg...) et obtenez une transcription sans connexion internet via Google Speech Recognition locale.")

# Choix de la langue
langue = st.selectbox("Langue de l'audio :", [
    ("fr-FR", "Français"),
    ("en-US", "Anglais (US)"),
    ("es-ES", "Espagnol"),
    ("de-DE", "Allemand"),
], format_func=lambda x: x[1])[0]

uploaded_file = st.file_uploader("📤 Téléversez un fichier audio", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file:
    st.audio(uploaded_file, format="audio")

    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_input:
        tmp_input.write(uploaded_file.read())
        tmp_input.flush()

        # 🔄 Conversion automatique en WAV mono 16kHz
        try:
            audio = AudioSegment.from_file(tmp_input.name)
            audio = audio.set_channels(1).set_frame_rate(16000)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                audio.export(tmp_wav.name, format="wav")
                wav_path = tmp_wav.name
        except Exception as e:
            st.error(f"❌ Erreur lors de la conversion audio : {e}")
            os.remove(tmp_input.name)
            st.stop()

        if st.button("🎧 Transcrire"):
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data, language=langue)
                st.success("✅ Transcription réussie :")
                st.write(text)
                st.download_button("💾 Télécharger la transcription", text, file_name="transcription.txt")
            except sr.UnknownValueError:
                st.error("❌ Impossible de comprendre l'audio.")
            except sr.RequestError as e:
                st.error(f"⚠️ Erreur lors de l'utilisation de l'outil de reconnaissance vocale : {e}")

        os.remove(tmp_input.name)
        os.remove(wav_path)
