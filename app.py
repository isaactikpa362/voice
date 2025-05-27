import streamlit as st
from pydub import AudioSegment
import speech_recognition as sr
import tempfile
import os

st.set_page_config(page_title="Transcription Audio Locale", layout="centered")
st.title("🎧 Transcription d'un fichier audio (locale, sans API)")

# Choix de langue
langue = st.selectbox("Choisissez la langue de l'audio :", [
    ("fr-FR", "Français"),
    ("en-US", "Anglais (US)"),
    ("es-ES", "Espagnol"),
    ("de-DE", "Allemand")
], format_func=lambda x: x[1])[0]

uploaded_file = st.file_uploader("📤 Téléversez un fichier audio", type=["mp3", "wav", "ogg", "flac", "m4a"])

if uploaded_file:
    st.audio(uploaded_file, format='audio')

    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as temp_input:
        temp_input.write(uploaded_file.read())
        temp_input.flush()

        try:
            audio = AudioSegment.from_file(temp_input.name)
            audio = audio.set_channels(1).set_frame_rate(16000)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                audio.export(temp_wav.name, format="wav")
                wav_path = temp_wav.name
        except Exception as e:
            st.error(f"Erreur lors de la conversion : {e}")
            st.stop()

        if st.button("📝 Lancer la transcription"):
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)

            try:
                texte = r.recognize_google(audio_data, language=langue)
                st.success("✅ Transcription réussie !")
                st.write(texte)
                st.download_button("📄 Télécharger la transcription", texte, file_name="transcription.txt")
            except sr.UnknownValueError:
                st.error("❌ Impossible de comprendre l'audio.")
            except sr.RequestError as e:
                st.error(f"⚠️ Erreur de reconnaissance vocale : {e}")

        os.remove(temp_input.name)
        os.remove(wav_path)
