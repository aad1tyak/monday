import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from PIL import Image 

class GeminiClient:
    """
    A simple client class for interacting with the Google Gemini API,
    supporting text-only and multimodal (text + image) prompts.
    Manages chat history persistence in 'history.json'.
    """
    def __init__(self):
        """
        Initializes the Gemini client and configures the API key.
        The API key is loaded from environment variables (e.g., from a .env file).
        """
        try:
            # Load environment variables from .env file (if it exists)
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            load_dotenv(env_path)
            
            # Configure the Gemini API with the key from environment variables
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        except KeyError:
            print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
            print("Please set it before running the script.")
            exit() # Exit if API key is not found

        # Initialize the Gemini model with gemini-2.5-flash as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.history_file = "history.json"




    def _load_history(self) -> list:
        """Loads chat history from history.json."""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
            return []
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode {self.history_file}. Starting with empty history.")
            return []



    def _save_history(self, history: list):
        """Saves chat history to history.json."""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)



    def send_prompt(self, prompt: str, image_path: str = None) -> str:
        """
        Sends a prompt to the Gemini model, optionally with an image,
        and manages chat history persistence.
        
        Args:
            prompt (str): The text prompt for Gemini. (Mandatory)
            image_path (str, optional): Path to an image file. If provided,
                                        the prompt will be multimodal. Defaults to None.

        Returns:
            str: The text response from the Gemini model.
        """
        chat_history = self._load_history()
        current_turn_contents = []

        # Add image if provided for the current turn
        if image_path:
            try:
                # Directly using genai.upload_file with the path.
                # This is the simplest way to provide a local image file to Gemini.
                current_turn_contents.append(genai.upload_file(image_path))
            except Exception as e:
                return f"Error loading image from path '{image_path}': {e}. Please ensure the image path is correct and it's a valid image file."

        # Add text prompt (always mandatory for a user turn)
        current_turn_contents.append(prompt)

        # Append the current user turn to the history
        # Note: If image was used, its 'Part' object is here. When saved to JSON,
        # only the textual content from the prompt will persist in 'parts'.
        # For full multimodal history re-submission, a more complex storage solution
        # (e.g., storing image bytes or re-uploading) would be needed, but this
        # aligns with the "simple reading a json file" request for text history.
        chat_history.append({"role": "user", "parts": [part.to_dict() if hasattr(part, 'to_dict') else part for part in current_turn_contents]})

        try:
            # Send the entire conversation history (including the current turn) to Gemini
            # Gemini's `generate_content` will handle the actual content objects (like uploaded images)
            response = self.model.generate_content(chat_history).text.strip()
            
            # Append Gemini's response to the history
            chat_history.append({"role": "model", "parts": [{"text": response}]})

            # Save the updated history to history.json
            self._save_history(chat_history)

            return response

        except Exception as e:
            # If an error occurs, save history before the failed model response
            self._save_history(chat_history) # Save what we have so far
            return f"An error occurred while communicating with Gemini: {e}"