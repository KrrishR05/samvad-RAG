"""
SAMVAD — Sarvam AI First API Verification Script
Tests Text-to-Speech (Bulbul) and Speech-to-Text (Saaras) via Sarvam SDK.
"""

import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI

# Load key from environment (.env)
load_dotenv()
api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise RuntimeError("SARVAM_API_KEY is not set in environment or .env file.")

client = SarvamAI(api_subscription_key=api_key)

print("1. Testing Sarvam Text-to-Speech (model='bulbul:v3')...")
sample_text = "नमस्ते, संवाद में आपका स्वागत है। यह सर्वम एआई का परीक्षण है।"
tts_response = client.text_to_speech.convert(
    text=sample_text,
    language_code="hi-IN",
    speaker="aditya",
    model="bulbul:v3",
)

output_audio_path = Path("sarvam_test_output.mp3")
if tts_response.audios:
    audio_bytes = base64.b64decode(tts_response.audios[0])
    output_audio_path.write_bytes(audio_bytes)
    print(f"   [SUCCESS] Audio successfully synthesized and saved to: {output_audio_path.resolve()} ({len(audio_bytes)} bytes)")
else:
    print("   [FAILED] No audio returned.")

print("\n2. Testing Sarvam Speech-to-Text (model='saaras:v3')...")
with open(output_audio_path, "rb") as audio_file:
    stt_response = client.speech_to_text.transcribe(
        file=audio_file,
        model="saaras:v3",
        language_code="hi-IN",
    )

print(f"   [SUCCESS] Transcription Result: \"{stt_response.transcript}\"")
print(f"   Language Detected / Specified: {getattr(stt_response, 'language_code', 'hi-IN')}")
