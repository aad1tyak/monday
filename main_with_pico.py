# main_assistant.py
from gemini import GeminiClient
from voiceIO import VoiceIO
import subprocess
import re
import pvporcupine
import pyaudio
import struct
import os
import sys
from dotenv import load_dotenv



env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)
PICOVOICE_ACCESS_KEY = os.environ["pico_voice_key"]


MODEL_PATH = os.path.join(os.path.dirname(__file__), "porcupine_params.pv") 

#NOTE:WORK IN PROGRESS
WAKE_WORD_PATH = os.path.join(os.path.dirname(__file__), "Wake-Up-Monday_en_linux_v3_0_0.ppn") 

# --- Initialize VoiceIO ---
voice_io = VoiceIO() # Corrected class name to VoiceIO based on previous output

# --- Main Assistant Logic ---
def run_monday():
    """
    Main function to run the Monday assistant with voice interaction.
    """
    print("Monday is active! You can now interact.")

    # Initialize the GeminiClient
    gemini_client = GeminiClient() 

    # Initial greeting from the AI
    initial_greeting = "Hello! Monday here ready to assist you. Remember, you can say 'Run' or 'Execute' followed by your command request, and exit or quit to end the session. Let's get started!"
    voice_io.speak_text(initial_greeting) # Use the method from VoiceIO

    while True:
        user_input = voice_io.listen() # Use the method from VoiceIO

        if not user_input: # If no speech was recognized
            continue

        if user_input.lower() in ["exit", "quit", "goodbye monday"]:
            voice_io.speak_text("Exiting assistant. Goodbye!")
            break

        # Check if the user wants to run a command
        if user_input.lower() in ["run", "execute"]:
            command_request = user_input[user_input.lower().find(":") + 1:].strip()

            gemini_raw_response = gemini_client.send_prompt(f"Suggest a Linux command for: {command_request}. Prefix the command with 'COMMAND:'")

            command_match = re.search(r"COMMAND:\s*(.*)", gemini_raw_response, re.IGNORECASE)
            suggested_command = None

            if command_match:
                suggested_command = command_match.group(1).strip()
                voice_io.speak_text(f"I suggest the command: {suggested_command}. Do you want to execute this?") 

                # Command confirmation is now voice-based for convenience
                voice_io.speak_text("Please say yes to confirm, or no to cancel.")
                confirm = voice_io.listen().strip().lower()
                while confirm not in ["yes", "no"]:
                    voice_io.speak_text("I didn't catch that. Please say yes or no.")
                    confirm = voice_io.listen().strip().lower()

                if confirm == 'y':
                    try:
                        print(f"\nExecuting: `{suggested_command}`")
                        voice_io.speak_text("Executing command.") # Use the method from VoiceIO
                        result = subprocess.run(
                            suggested_command,
                            shell=True,
                            check=True,
                            capture_output=True,
                            text=True
                        )
                        print("\n--- Command Output ---")
                        print(result.stdout)
                        if result.stderr:
                            print("--- Command Error Output ---")
                            print(result.stderr)
                        print("----------------------")
                        voice_io.speak_text("Command executed successfully. Check the terminal for output.") # Use the method from VoiceIO

                    except subprocess.CalledProcessError as e:
                        error_message = f"Error executing command: {e.stderr.strip()}"
                        print(f"\n{error_message}")
                        voice_io.speak_text(f"Error executing command. {e.stderr.strip()}") # Use the method from VoiceIO
                    except FileNotFoundError:
                        error_message = f"Error: Command '{suggested_command.split()[0]}' not found."
                        print(f"\n{error_message}")
                        voice_io.speak_text(error_message) # Use the method from VoiceIO
                    except Exception as e:
                        error_message = f"An unexpected error occurred during command execution: {e}"
                        print(f"\n{error_message}")
                        voice_io.speak_text(error_message) # Use the method from VoiceIO
                else:
                    voice_io.speak_text("Command execution cancelled.") # Use the method from VoiceIO
                    print("Command execution cancelled.")
            else:
                # Regular chat interaction
                # If Gemini's response didn't contain a COMMAND: prefix,
                # it's treated as a regular conversational response.
                response = gemini_client.send_prompt(user_input)
                voice_io.speak_text(response) # Use the method from VoiceIO


# --- Wake Word Detection Logic ---
def wake_word_listener():
    """
    Listens continuously for the wake word "Wake Up! Monday" and then
    starts the main assistant function.
    """
    print("Monday is in standby mode. Say 'Wake Up! Monday' to activate.")
    
    porcupine = None
    pa = None
    audio_stream = None

    try:
        # Initialize Porcupine
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=[WAKE_WORD_PATH],
            model_path=MODEL_PATH
        )

        # Initialize PyAudio
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print(f"Listening for '{os.path.basename(WAKE_WORD_PATH).split('_')[0]}'...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("\nWake word detected! Activating Monday...")
                voice_io.speak_text("Yes, I'm here. How can I help you?")
                run_monday() # Start the main assistant
                print("\nMonday is returning to standby mode. Say 'Wake Up! Monday' to activate.")
                voice_io.speak_text("Returning to standby mode.")
                # After run_monday exits, we continue listening for the wake word
                # This allows Monday to go back to sleep and be re-woken.

    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"Porcupine Argument Error: {e}")
        print("Please check your AccessKey, model paths, and ensure they are valid.")
    except pvporcupine.PorcupineActivationError as e:
        print(f"Porcupine Activation Error: {e}")
        print("Your AccessKey might be invalid or expired.")
    except pvporcupine.PorcupineError as e:
        print(f"Porcupine Error: {e}")
        print("A general Porcupine error occurred. Check your setup.")
    except Exception as e:
        print(f"An unexpected error occurred in wake word listener: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()

# --- Run the assistant ---
if __name__ == "__main__":
    wake_word_listener() # Start listening for the wake word