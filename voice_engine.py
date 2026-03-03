import os
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
import edge_tts
import asyncio
import pygame
import tempfile
import uuid

class VoiceEngine:
    def __init__(self):
        # Initialize high-quality Edge-TTS Neural Voice (Irish) fallback
        pygame.mixer.init()
        self.edge_voice = "en-IE-EmilyNeural"
                
        self.elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        if self.elevenlabs_api_key and self.elevenlabs_api_key != "your_elevenlabs_api_key_here":
            self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
            self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "pFZP5JQG7iQjIQuC4Bku") 
        else:
            print("WARNING: Valid ELEVENLABS_API_KEY not set. Using Neural TTS (Edge-TTS) for high-quality speaker voice.")
            self.client = None
        
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.5 # Allow longer pauses between words (like "Friday... open Notepad")
        self.recognizer.dynamic_energy_threshold = True
        
    def listen(self, timeout=None, phrase_time_limit=10) -> str:
        """Listens to the microphone and returns transcribed text. Blocks until speech is detected."""
        with sr.Microphone() as source:
            print("[F.R.I.D.A.Y.] Listening (Ready for commands)...")
            try:
                # listen for input
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("[F.R.I.D.A.Y.] Processing audio...")
                # We'll use Google's free web STT API for speed in this foundation.
                # In a purely offline mode, we would switch to generic Whisper locally here.
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                print(f"Could not request results from STT service: {e}")
                return ""

    def speak(self, text: str):
        """Speaks the provided text using ElevenLabs (or fallback local TTS)."""
        print(f"[F.R.I.D.A.Y.] {text}")
        if not text:
            return

        if self.client:
            try:
                audio_stream = self.client.text_to_speech.convert_as_stream(
                    text=text,
                    voice_id=self.voice_id,
                    model_id="eleven_turbo_v2" # Fast model for reduced latency
                )
                stream(audio_stream)
            except Exception as e:
                print(f"ElevenLabs TTS Error: {e}. Falling back to local TTS.")
                self._speak_local(text)
        else:
            self._speak_local(text)

    def _speak_local(self, text: str):
        try:
            # Fix Edge-TTS Irish pronunciation of "Hrix"
            text_to_speak = text.replace("Hrix", "Hr-Ricks")
            
            # Use UUID to prevent file lock/PermissionError on consecutive speak calls
            file_id = str(uuid.uuid4())
            temp_file = os.path.join(tempfile.gettempdir(), f"friday_speech_{file_id}.mp3")
            
            async def generate_speech():
                communicate = edge_tts.Communicate(text_to_speak, self.edge_voice)
                await communicate.save(temp_file)
                
            asyncio.run(generate_speech())
            
            if os.path.exists(temp_file):
                # Play the generated mp3
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
                pygame.mixer.music.unload()
                
                # Cleanup safely
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Warning: Could not remove temporary speech file: {e}")
                
        except Exception as e:
            print(f"Failed to generate neural voice: {e}")

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(".env")
    ve = VoiceEngine()
    ve.speak("Systems are fully operational, Hrix.")
