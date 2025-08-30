# llm_interface.py

import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def query_ollama(model_name: str, prompt: str) -> str:
    """
    Sends a prompt to a model running on Ollama and returns the response.
    """
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,  
        "options": {
            "temperature": 0.0  # deterministic JSON and code
        }
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()  # Raises an exception for bad status codes

        # The actual response from the model is in the 'response' key
        return response.json().get("response", "").strip()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
        return None
