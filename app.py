import streamlit as st
import speech_recognition as sr
import tempfile
import os
from datetime import datetime

# --- Initialisation de l'état de session ---
if "paused" not in st.session_state:
    st.session_state.paused = False
if "transcription" not in st.session_state:
    st.session_state.transcription = ""

# --- Interface utilisateur ---
st.title("🎙️ Application de reconnaissance vocale")
st.markdown("Sélectionnez vos options, puis commencez à parler.")

# Choix de l'API de reconnaissance vocale
api_choice = st.selectbox("Choisissez l'API de reconnaissance vocale :", ["Google", "Sphinx (hors ligne)"])

# Choix de la langue
language = st.selectbox("Choisissez votre langue :", [
    ("fr-FR", "Français"),
    ("en-US", "Anglais (US)"),
    ("es-ES", "Espagnol"),
    ("de-DE", "Allemand"),
    ("it-IT", "Italien")
], format_func=lambda x: x[1])[0]

# Boutons Pause / Reprise
col1, col2 = st.columns(2)
with col1:
    if st.button("⏸️ Mettre en pause"):
        st.session_state.paused = True
with col2:
    if st.button("▶️ Reprendre"):
        st.session_state.paused = False

# --- Fonction de transcription ---
def transcribe_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Parlez maintenant...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            if st.session_state.paused:
                st.warning("Reconnaissance en pause.")
                return

            if api_choice == "Google":
                text = r.recognize_google(audio, language=language)
            elif api_choice == "Sphinx (hors ligne)":
                text = r.recognize_sphinx(audio, language=language)
            else:
                text = "[API non prise en charge]"

            st.success("Transcription :")
            st.write(text)
            st.session_state.transcription += text + "\n"

        except sr.WaitTimeoutError:
            st.error("⏱️ Aucun son détecté. Essayez à nouveau.")
        except sr.UnknownValueError:
            st.error("❌ L'API n'a pas compris l'audio.")
        except sr.RequestError as e:
            st.error(f"🚨 Erreur avec le service de reconnaissance : {e}")
        except Exception as e:
            st.error(f"❗ Une erreur est survenue : {str(e)}")

# --- Bouton de démarrage ---
if st.button("🎤 Commencer la reconnaissance vocale"):
    transcribe_speech()

# --- Téléchargement du texte ---
if st.session_state.transcription:
    if st.download_button("💾 Télécharger le texte", st.session_state.transcription, file_name="transcription.txt"):
        st.success("Téléchargement prêt.")

# --- Pied de page ---
st.markdown("---")
st.markdown("Développé avec ❤️ en Python et Streamlit.")

