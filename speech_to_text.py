"""
speech_to_text.py - Speech recognition module
Uses SpeechRecognition library with Google Web Speech API.
Falls back to a manual transcript if audio is unavailable.
"""

import speech_recognition as sr
import os


def transcribe_audio_file(audio_path: str) -> dict:
    """
    Transcribe an audio file to text.
    Returns a dict with 'success', 'transcript', and 'error' keys.
    """
    recognizer = sr.Recognizer()

    if not os.path.exists(audio_path):
        return {'success': False, 'transcript': '', 'error': 'Audio file not found.'}

    try:
        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)

        transcript = recognizer.recognize_google(audio_data)
        return {'success': True, 'transcript': transcript, 'error': ''}

    except sr.UnknownValueError:
        return {'success': False, 'transcript': '', 'error': 'Could not understand the audio. Please speak clearly.'}
    except sr.RequestError as e:
        return {'success': False, 'transcript': '', 'error': f'Speech recognition service error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'transcript': '', 'error': f'Unexpected error: {str(e)}'}


def transcribe_microphone(timeout: int = 10) -> dict:
    """
    Capture audio from microphone and transcribe it.
    Returns a dict with 'success', 'transcript', and 'error' keys.
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Listening... Speak now.")
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=30)

        transcript = recognizer.recognize_google(audio_data)
        return {'success': True, 'transcript': transcript, 'error': ''}

    except sr.WaitTimeoutError:
        return {'success': False, 'transcript': '', 'error': 'No speech detected within timeout.'}
    except sr.UnknownValueError:
        return {'success': False, 'transcript': '', 'error': 'Could not understand the audio.'}
    except sr.RequestError as e:
        return {'success': False, 'transcript': '', 'error': f'Speech recognition service error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'transcript': '', 'error': f'Microphone error: {str(e)}'}
