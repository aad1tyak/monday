import speech_recognition as sr
from gtts import gTTS
import playsound
import os
import sys # For sys.stdout.flush()
import time # For time.sleep()

class VoiceIO:
    """
    Handles speech input (listening) and speech output (speaking)
    for the AI assistant, including a typing effect for spoken text.
    """
    def __init__(self):
        """
        Initializes the Speech Recognition Recognizer.
        """
        self.recognizer = sr.Recognizer()

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
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10) # Add timeout for robustness
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
        Converts text to speech and plays it. Also prints the text to the terminal
        with a typing effect.
        
        Args:
            text (str): The text string to be spoken.
            typing_speed (float): Delay in seconds between each character printed
                                  to simulate typing. Default is 0.03 seconds.
        """
        # Print text with typing effect
        print("\nAI: ", end="") # Start printing on a new line, no newline at end
        for char in text:
            sys.stdout.write(char) # Write character
            sys.stdout.flush()     # Flush buffer to show character immediately
            time.sleep(typing_speed) # Pause for typing effect
        print() # Print a final newline after the full text is displayed

        # Play the audio
        try:
            tts = gTTS(text=text, lang='en')
            filename = "response.mp3"
            tts.save(filename)
            playsound.playsound(filename)
            os.remove(filename) # Clean up the audio file
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
