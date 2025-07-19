# voice_io.py
import speech_recognition as sr
from gtts import gTTS
import playsound
import os
import sys # For sys.stdout.flush()
import time # For time.sleep()
import threading # For concurrent audio playback

class VoiceIO:
    """
    Handles speech input (listening) and speech output (speaking)
    for the AI assistant, including a typing effect for spoken text
    and simultaneous audio playback.
    """
    def __init__(self):
        """
        Initializes the Speech Recognition Recognizer and sets its properties.
        """
        self.recognizer = sr.Recognizer()
        # Set pause_threshold and phrase_time_limit as properties of the recognizer
        # This is compatible with a wider range of speech_recognition versions
        self.recognizer.pause_threshold = 3  # Seconds of non-speaking audio to consider a phrase complete
        self.recognizer.phrase_time_limit = 15 # Maximum duration of a phrase

    def _play_audio_and_cleanup(self, filename: str):
        """
        Internal method to play the audio file and then delete it.
        This runs in a separate thread.
        """
        try:
            playsound.playsound(filename)
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            # Ensure the file is removed after playback attempt
            if os.path.exists(filename):
                os.remove(filename)

    def listen(self) -> str:
        """
        Listens for voice input from the microphone and converts it to text.
        
        Returns:
            str: The recognized text, or an empty string if recognition fails.
        """
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source) # Adjust for ambient noise
            try:
                # Now, listen() does not need pause_threshold or phrase_time_limit arguments
                audio = self.recognizer.listen(source, timeout=5) 
            except sr.WaitTimeoutError:
                print("No speech detected.")
                return ""

        try:
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""

    def speak_text(self, text: str, typing_speed: float = 0.03):
        """
        Converts text to speech and plays it simultaneously with a typing effect
        in the terminal.
        
        Args:
            text (str): The text string to be spoken.
            typing_speed (float): Delay in seconds between each character printed
                                  to simulate typing. Default is 0.03 seconds.
        """
        filename = "response.mp3"
        try:
            # Generate and save the audio file
            tts = gTTS(text=text, lang='en')
            tts.save(filename)

            # Start playing audio in a separate thread
            audio_thread = threading.Thread(target=self._play_audio_and_cleanup, args=(filename,))
            audio_thread.start()

            # Print text with typing effect in the main thread
            print("\nAI: ", end="") # Start printing on a new line, no newline at end
            for char in text:
                sys.stdout.write(char) # Write character
                sys.stdout.flush()     # Flush buffer to show character immediately
                time.sleep(typing_speed) # Pause for typing effect
            print() # Print a final newline after the full text is displayed

            # Wait for the audio thread to finish (optional, but good for cleanup)
            audio_thread.join()

        except Exception as e:
            print(f"Error in text-to-speech or typing: {e}")
            # Ensure the file is removed even if an error occurs during processing
            if os.path.exists(filename):
                os.remove(filename)

