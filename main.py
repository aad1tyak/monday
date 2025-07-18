# Your main_assistant.py file (updated to use VoiceIO)
from gemini import GeminiClient
from voiceIO import VoiceIO # Import your new class
import subprocess
import re

# Initialize the VoiceIO class
voice_io = VoiceIO()


# --- Main Assistant Logic ---
def run_assistant():
    """
    Main function to run the interactive AI terminal assistant with voice.
    """
    print("Welcome to your Gemini-powered Voice Terminal Assistant!")
    print("Say 'exit' or 'quit' to end the session.")
    print("To execute a command, say 'Run:' or 'Execute:' followed by your request.")
    print("-" * 50)

    # Initialize the GeminiClient
    gemini_client = GeminiClient() 

    # Initial greeting from the AI
    initial_greeting = "Hello! I'm ready to help. What can I do for you?"
    print(f"AI: {initial_greeting}")
    voice_io.speak_text(initial_greeting) # Use the method from VoiceIO

    while True:
        user_input = voice_io.listen() # Use the method from VoiceIO

        if not user_input: # If no speech was recognized
            continue

        if user_input.lower() in ["exit", "quit"]:
            voice_io.speak_text("Exiting assistant. Goodbye!") # Use the method from VoiceIO
            print("Exiting assistant. Goodbye!")
            break

        # Check if the user wants to run a command
        if user_input.lower().startswith("run:") or user_input.lower().startswith("execute:"):
            command_request = user_input[user_input.lower().find(":") + 1:].strip()

            gemini_raw_response = gemini_client.send_prompt(f"Suggest a Linux command for: {command_request}. Prefix the command with 'COMMAND:'")

            command_match = re.search(r"COMMAND:\s*(.*)", gemini_raw_response, re.IGNORECASE)
            suggested_command = None

            if command_match:
                suggested_command = command_match.group(1).strip()
                voice_io.speak_text(f"I suggest the command: {suggested_command}. Do you want to execute this?") # Use the method from VoiceIO
                print(f"\nAI suggested command: `{suggested_command}`")

                # Command confirmation is still text-based for safety
                confirm = input("Do you want to execute this command? (y/N): ").strip().lower()

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

                        # You might want to send the command result back to Gemini for context
                        # gemini_client.send_prompt(f"Command executed: `{suggested_command}`. Output: {result.stdout}")

                    except subprocess.CalledProcessError as e:
                        error_message = f"Error executing command: {e.stderr.strip()}"
                        print(f"\n{error_message}")
                        voice_io.speak_text(f"Error executing command. {e.stderr.strip()}") # Use the method from VoiceIO
                        # gemini_client.send_prompt(f"Command execution failed: `{suggested_command}`. Error: {e.stderr}")
                    except FileNotFoundError:
                        error_message = f"Error: Command '{suggested_command.split()[0]}' not found."
                        print(f"\n{error_message}")
                        voice_io.speak_text(error_message) # Use the method from VoiceIO
                        # gemini_client.send_prompt(f"Command not found: `{suggested_command}`")
                    except Exception as e:
                        error_message = f"An unexpected error occurred during command execution: {e}"
                        print(f"\n{error_message}")
                        voice_io.speak_text(error_message) # Use the method from VoiceIO
                        # gemini_client.send_prompt(f"Unexpected error during command execution: {e}")
                else:
                    voice_io.speak_text("Command execution cancelled.") # Use the method from VoiceIO
                    print("Command execution cancelled.")
                    # gemini_client.send_prompt(f"User declined to execute command: `{suggested_command}`")
            else:
                voice_io.speak_text("I could not extract a clear command from my response. Please try rephrasing.") # Use the method from VoiceIO
                print("\nAI could not extract a clear command from its response.")
                print("Gemini's full response was:")
                print(gemini_raw_response)
        else:
            # Regular chat interaction
            response = gemini_client.send_prompt(user_input)
            print(f"\nAI: {response}")
            voice_io.speak_text(response) # Use the method from VoiceIO

# Run the assistant
if __name__ == "__main__":
    run_assistant()