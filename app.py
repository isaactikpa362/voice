import streamlit as st
import requests
import tempfile
import os
from pydub import AudioSegment
import time

# 🔐 Remplacez ceci par votre vraie clé API AssemblyAI
ASSEMBLYAI_API_KEY = "c979d3e6ba2a40f8b4a3d538d6df25de"

st.set_page_config(page_title="Transcription Audio", layout="centered")
st.title("🎙️ Transcription de fichiers audio multi-format")
st.markdown("Téléversez un fichier audio (.mp3, .wav, .m4a, .ogg, etc.) et obtenez sa transcription grâce à l'API AssemblyAI.")

uploaded_file = st.file_uploader("📤 Téléversez un fichier audio", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_input:
        tmp_input.write(uploaded_file.read())
        tmp_input.flush()

        # 🔄 Conversion en WAV (mono, 16kHz PCM)
        audio = AudioSegment.from_file(tmp_input.name)
        audio = audio.set_channels(1).set_frame_rate(16000)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            audio.export(tmp_wav.name, format="wav")
            converted_file_path = tmp_wav.name

        st.success("✅ Fichier converti et prêt pour la transcription.")
        st.audio(converted_file_path, format="audio/wav")

        if st.button("🚀 Lancer la transcription"):
            # 1. Upload vers AssemblyAI
            headers = {'authorization': ASSEMBLYAI_API_KEY}
            with open(converted_file_path, 'rb') as f:
                response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
            if response.status_code != 200:
                st.error("❌ Échec de l'upload vers AssemblyAI")
                st.stop()

            upload_url = response.json()['upload_url']

            # 2. Demande de transcription
            transcript_request = {
                'audio_url': upload_url,
                'language_code': 'fr'  # Peut être 'en', 'de', 'es' etc.
            }
            transcript_response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcript_request, headers=headers)
            transcript_id = transcript_response.json()['id']

            # 3. Attente du résultat
            st.info("⏳ Transcription en cours, veuillez patienter...")
            status = "processing"
            while status not in ("completed", "error"):
                polling_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
                status = polling_response.json()['status']
                time.sleep(3)

            if status == "completed":
                text = polling_response.json()['text']
                st.success("✅ Transcription terminée !")
                st.write(text)
                st.download_button("💾 Télécharger la transcription", text, file_name="transcription.txt")
            else:
                st.error("❌ La transcription a échoué.")

        # Nettoyage
        os.remove(tmp_input.name)
        os.remove(converted_file_path)
