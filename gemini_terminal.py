import google.generativeai as genai
import os
import subprocess
from dotenv import load_dotenv
import re
import speech_recognition as sr
from gtts import gTTS
import playsound

try:
    # Load the API key from environment variables
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    exit()
model = genai.GenerativeModel('gemini-2.5-flash')


# Initialize the recognizer for speech-to-text
r = sr.Recognizer()

# --- Helper Function to Interact with Gemini ---
def get_gemini_response(prompt_text, chat_history):
    """
    Sends the prompt and chat history to Gemini and returns the response.
    """
    try:
        # Add the current user prompt to the chat history
        chat_history.append({"role": "user", "parts": [{ "text": prompt_text }]})

        # Generate content using the model
        response = model.generate_content(chat_history)

        # Extract the text from the response
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            # Add the model's response to the chat history
            model_response_text = response.candidates[0].content.parts[0].text
            chat_history.append({"role": "model", "parts": [{ "text": model_response_text }]})
            return model_response_text
        else:
            return "Gemini did not return a valid response."
    except Exception as e:
        return f"An error occurred while communicating with Gemini: {e}"

# --- Speech Functions ---
def listen_for_command():
    """
    Listens for voice input from the microphone and converts it to text.
    """
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source) # Adjust for ambient noise
        audio = r.listen(source)

    try:
        print("Recognizing...")
        # Use Google Web Speech API for recognition
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

def speak(text):
    """
    Converts text to speech and plays it.
    """
    try:
        tts = gTTS(text=text, lang='en')
        filename = "response.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename) # Clean up the audio file
    except Exception as e:
        print(f"Error in text-to-speech: {e}")

# --- Main Assistant Logic ---
def run_assistant():
    """
    Main function to run the interactive AI terminal assistant with voice.
    """
    print("Welcome to your Gemini-powered Voice Terminal Assistant!")
    print("Say 'exit' or 'quit' to end the session.")
    print("To execute a command, say 'Run:' or 'Execute:' followed by your request.")
    print("-" * 50)

    # Initialize chat history for conversational context
    chat_history = [
        {"role": "user", "parts": [{"text": "You are a helpful AI assistant that can suggest and, with user permission, execute Linux terminal commands. When suggesting a command, always prefix it with 'COMMAND:' on a new line. Do not execute commands without explicit user confirmation."}]},
        {"role": "model", "parts": [{"text": "Understood! I'm ready to help. What can I do for you?"}]}
    ]
    speak("Hello! I'm ready to help. What can I do for you?")

    while True:
        user_input = listen_for_command()

        if not user_input: # If no speech was recognized
            continue

        if user_input.lower() in ["exit", "quit"]:
            speak("Exiting assistant. Goodbye!")
            print("Exiting assistant. Goodbye!")
            break

        # Check if the user wants to run a command
        if user_input.lower().startswith("run") or user_input.lower().startswith("execute"):
            command_request = user_input[user_input.lower().find(":") + 1:].strip()
            gemini_raw_response = get_gemini_response(f"Suggest a Linux command for: {command_request}. Prefix the command with 'COMMAND:'", chat_history)

            command_match = re.search(r"COMMAND:\s*(.*)", gemini_raw_response, re.IGNORECASE)
            suggested_command = None

            if command_match:
                suggested_command = command_match.group(1).strip()
                speak(f"I suggest the command: {suggested_command}. Do you want to execute this?")
                print(f"\nAI suggested command: `{suggested_command}`")
                confirm = input("Do you want to execute this command? (y/N): ").strip().lower()

                if confirm == 'y':
                    try:
                        print(f"\nExecuting: `{suggested_command}`")
                        speak("Executing command.")
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
                        speak("Command executed successfully. Check the terminal for output.")
                        chat_history.append({"role": "user", "parts": [{"text": f"Command executed: `{suggested_command}`. Output: {result.stdout}"}]})
                        chat_history.append({"role": "model", "parts": [{"text": "Command executed successfully."}]})

                    except subprocess.CalledProcessError as e:
                        error_message = f"Error executing command: {e.stderr.strip()}"
                        print(f"\n{error_message}")
                        speak(f"Error executing command. {e.stderr.strip()}")
                        chat_history.append({"role": "user", "parts": [{"text": f"Command execution failed: `{suggested_command}`. Error: {e.stderr}"}]})
                        chat_history.append({"role": "model", "parts": [{"text": "Command execution failed. Please check the error."}]})
                    except FileNotFoundError:
                        error_message = f"Error: Command '{suggested_command.split()[0]}' not found."
                        print(f"\n{error_message}")
                        speak(error_message)
                        chat_history.append({"role": "user", "parts": [{"text": f"Command not found: `{suggested_command}`"}]})
                        chat_history.append({"role": "model", "parts": [{"text": "Command not found."}]})
                    except Exception as e:
                        error_message = f"An unexpected error occurred during command execution: {e}"
                        print(f"\n{error_message}")
                        speak(error_message)
                        chat_history.append({"role": "user", "parts": [{"text": f"Unexpected error during command execution: {e}"}]})
                        chat_history.append({"role": "model", "parts": [{"text": "An unexpected error occurred."}]})
                else:
                    speak("Command execution cancelled.")
                    print("Command execution cancelled.")
                    chat_history.append({"role": "user", "parts": [{"text": f"User declined to execute command: `{suggested_command}`"}]})
                    chat_history.append({"role": "model", "parts": [{"text": "Command not executed."}]})
            else:
                speak("I could not extract a clear command from my response. Please try rephrasing.")
                print("\nAI could not extract a clear command from its response.")
                print("Gemini's full response was:")
                print(gemini_raw_response)
                chat_history.append({"role": "model", "parts": [{"text": "I couldn't parse a command from my last response. Please try rephrasing."}]})
        else:
            # Regular chat interaction
            response = get_gemini_response(user_input, chat_history)
            print(f"\nAI: {response}")
            speak(response)

# Run the assistant
if __name__ == "__main__":
    run_assistant()