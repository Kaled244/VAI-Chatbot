"""Gemini client: loads the API key and sends prompts to the model."""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-3.8-flash"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3

_client = None


def has_api_key():
    """True when GEMINI_API_KEY is set in the environment or the .env file."""
    return bool(os.getenv("GEMINI_API_KEY"))


def get_client():
    """Create the Gemini client once and reuse it."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def generate_reply(prompt, system_instruction, model=DEFAULT_MODEL, extra_context=""):
    """Send a prompt to Gemini with retry logic. Returns the reply text."""
    full_prompt = prompt
    if extra_context:
        full_prompt = f"{extra_context}\n\n---\n\n{prompt}"

    for attempt in range(MAX_RETRIES):
        try:
            response = get_client().models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction),
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    return "The servers are overwhelmed. I cannot give you an answer right now. Try again shortly."
            else:
                return f"⚠️ Error: `{error_msg}`"
    return "⚠️ Unknown error."