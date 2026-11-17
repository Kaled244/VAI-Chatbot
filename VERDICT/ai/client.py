"""Gemini client: loads the API key and sends the conversation to the model."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-3.7-flash"
# Tried in order when the chosen model is busy or has reached its limit.
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
REQUEST_TIMEOUT_MS = 60000  # give up on a request after 60 seconds

_client = None


class GeminiError(Exception):
    """Raised when Gemini cannot answer. The message is safe to show to the user."""


def has_api_key():
    """True when GEMINI_API_KEY is set in the environment or the .env file."""
    return bool(os.getenv("GEMINI_API_KEY"))


def get_client():
    """Create the Gemini client once and reuse it."""
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
    return _client


def build_contents(messages):
    """Convert our chat history into the format Gemini expects.

    Each message is a dict: {"role": "user" or "assistant", "content": str}.
    A user message may also carry "context" (hidden text sent before the content,
    such as the Case File category or an attached document).
    Gemini calls the assistant role "model", and consecutive messages from the
    same role are merged into one turn.
    """
    contents = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        text = msg["content"]
        if msg.get("context"):
            text = f"{msg['context']}\n\n---\n\n{text}"

        part = types.Part.from_text(text=text)
        if contents and contents[-1].role == role:
            contents[-1].parts.append(part)
        else:
            contents.append(types.Content(role=role, parts=[part]))
    return contents


def friendly_error(error):
    """Turn a raw API error into a message the user can act on."""
    code = getattr(error, "code", None)
    text = str(error)

    if code == 429 or "RESOURCE_EXHAUSTED" in text:
        return "The daily or per-minute limit of the Gemini API key has been reached. Wait a minute and try again."
    if code in (401, 403) or "API_KEY_INVALID" in text or "API key not valid" in text or "PERMISSION_DENIED" in text:
        return "The Gemini API key was rejected. Check GEMINI_API_KEY in the .env file."
    if code == 404 or "NOT_FOUND" in text:
        return "The selected model was not found. Check the model name in Settings."
    if code == 400 or "INVALID_ARGUMENT" in text:
        return "Gemini could not process that request. Try rephrasing or shortening it."
    if code in (500, 503) or "UNAVAILABLE" in text:
        return "The Gemini servers are overwhelmed right now. Try again shortly."
    return "Something went wrong while contacting Gemini. Check your internet connection and try again."


def is_temporary(error):
    """True when another model is worth trying (server busy or limit reached)."""
    code = getattr(error, "code", None)
    text = str(error)
    return (
        code in (429, 500, 503)
        or "UNAVAILABLE" in text
        or "RESOURCE_EXHAUSTED" in text
    )


def generate_reply(messages, system_instruction, model=DEFAULT_MODEL):
    """Send the conversation to Gemini. Returns the reply text.

    If the chosen model is busy, the fallback models are tried in order.
    Raises GeminiError with a user-friendly message when no reply can be produced.
    """
    contents = build_contents(messages)
    config = types.GenerateContentConfig(system_instruction=system_instruction)
    candidates = [model] + [name for name in FALLBACK_MODELS if name != model]

    first_error = None
    for name in candidates:
        try:
            response = get_client().models.generate_content(
                model=name,
                contents=contents,
                config=config,
            )
        except Exception as error:
            print(f"[Gemini error] {name}: {error}")  # full detail goes to the terminal
            if first_error is None:
                first_error = error
            if is_temporary(error) or name != model:
                continue  # try the next model
            raise GeminiError(friendly_error(error)) from error

        if not response.text:
            raise GeminiError("Gemini returned an empty answer. Try rephrasing your question.")
        if name != model:
            print(f"[Gemini] {model} was unavailable, answered with {name}")
        return response.text

    raise GeminiError(friendly_error(first_error)) from first_error