import streamlit as st
import speech_recognition as sr
import tempfile
import os

st.set_page_config(page_title="Transcription Audio", layout="centered")
st.title("🎧 Transcription de fichier audio")

st.markdown("Téléversez un fichier audio (.wav, .mp3, .m4a) pour obtenir sa transcription.")

# Langue
language = st.selectbox("Langue de la reconnaissance :", [
    ("fr-FR", "Français"),
    ("en-US", "Anglais (US)"),
    ("es-ES", "Espagnol"),
    ("de-DE", "Allemand")
], format_func=lambda x: x[1])[0]

# Téléversement du fichier
uploaded_file = st.file_uploader("📤 Fichier audio", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        tmpfile.write(uploaded_file.read())
        tmpfile_path = tmpfile.name

    st.audio(uploaded_file, format="audio/wav")

    if st.button("🚀 Transcrire"):
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmpfile_path) as source:
            audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio, language=language)
                st.success("📝 Transcription :")
                st.write(text)

                st.download_button("💾 Télécharger la transcription", text, file_name="transcription.txt")
            except sr.UnknownValueError:
                st.error("❌ Impossible de comprendre l'audio.")
            except sr.RequestError as e:
                st.error(f"⚠️ Erreur de service : {e}")

    # Nettoyage
    os.remove(tmpfile_path)
