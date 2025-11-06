import os
import ollama
import google.generativeai as genai
from dotenv import load_dotenv
import time
from typing import Union  # For Python 3.9/3.10 compatibility

# Load .env file *before* configuring APIs
load_dotenv()

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("---! ERROR !---")
    print("GEMINI_API_KEY not found. Did you create your .env file?")
    print("--------------")
    exit()

ollama_client = ollama.Client()

class SmartAIRouter:
    
    def __init__(self):
        try:
            print("Checking for 'qwen2.5-coder:7b'...")
            ollama_client.pull('qwen2.5-coder:7b') 
            print("✅ Local 'intern' (qwen2.5-coder:7b) is ready.")
        except Exception as e:
            print(f"⚠️ Warning: Could not connect to Ollama. Is it running? {e}")

    def query(self, prompt: str, model_type: str = "local") -> Union[str, None]:
        """
        Routes the prompt to the correct model.
        Returns the content as a string, or None if it fails.
        """
        print(f"--- [Router] Sending task to: {model_type} ---")
        try:
            if model_type == "gemini":
                return self._query_gemini(prompt)
            elif model_type == "local":
                return self._query_ollama(prompt)
            else:
                print(f"Warning: Unknown model '{model_type}'. Defaulting to 'local'.")
                return self._query_ollama(prompt)
        except Exception as e:
            print(f"---! UNHANDLED ROUTER ERROR: {e} !---")
            return None # Return None on failure

    def _query_gemini(self, prompt: str) -> Union[str, None]:
        """Sends a query to the Gemini 2.5 Pro API with automatic retries."""
        
        retries = 3
        wait_time = 40  # Wait 40s (more than the 36s requested)
        
        while retries > 0:
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                response = model.generate_content(prompt)
                
                # Check for safety blocks
                if not response.parts:
                    print(f"---! ERROR in Gemini query: Model returned no content. ---")
                    print(f"    Finish Reason: {response.candidates[0].finish_reason}")
                    print(f"    This often means the prompt was blocked by the safety filter.")
                    return None

                clean_response = response.text.strip().lstrip('```python').lstrip('```').rstrip('```')
                return clean_response # Success!
            
            except Exception as e:
                # Check for rate limit error
                if "429" in str(e):
                    print(f"---! [Router] Gemini Rate Limit Hit. {retries} retries left. ---")
                    print(f"    ...Sleeping for {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries -= 1
                    wait_time *= 1.5 # Exponential backoff
                else:
                    # It's a different, unexpected error
                    print(f"---! ERROR in Gemini query: {e} !---")
                    return None
        
        print("---! CRITICAL: Gemini query failed after all retries. !---")
        return None

    def _query_ollama(self, prompt: str) -> Union[str, None]:
        """Sends a query to the local Qwen Coder 7B model."""
        print("--- [Router] Contacting 'Intern' (local qwen:7b)... ---")
        try:
            response = ollama_client.chat(
                model='qwen2.5-coder:7b',
                messages=[{'role': 'user', 'content': prompt}]
            )
            clean_response = response['message']['content'].strip().lstrip('```python').lstrip('```').rstrip('```')
            return clean_response
        except Exception as e:
            print(f"---! ERROR in Ollama query: {e} !---")
            return None
