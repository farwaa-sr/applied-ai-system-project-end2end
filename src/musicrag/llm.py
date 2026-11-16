"""Gemini client (REST, standard library only) with typed failure so callers can fall back."""
import json
import os
import re
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

from .log import get_logger

log = get_logger("llm")

load_dotenv()
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class LLMError(RuntimeError):
    """Any LLM failure: no key, network error, bad HTTP status, or unparseable output."""


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 20.0):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate_json(self, prompt: str, retries: int = 1) -> dict:
        """Ask for a JSON object. Retries once on transient errors; raises LLMError otherwise."""
        if not self.available:
            raise LLMError("GEMINI_API_KEY is not set")
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        }).encode()
        req = urllib.request.Request(
            ENDPOINT.format(model=self.model), data=body, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )
        last: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = json.load(resp)
                text = payload["candidates"][0]["content"]["parts"][0]["text"]
                return _parse_json_object(text)
            except urllib.error.HTTPError as exc:
                last = exc
                retryable = exc.code in (429, 500, 502, 503, 504)
                log.warning("Gemini HTTP %s (attempt %d)", exc.code, attempt + 1)
                if not retryable:
                    break
            except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
                last = exc
                log.warning("Gemini call failed (attempt %d): %s", attempt + 1, type(exc).__name__)
            time.sleep(1.0 * (attempt + 1))
        raise LLMError(f"Gemini request failed: {type(last).__name__}") from last


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    if fence:
        text = fence.group(1)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("model did not return a JSON object")
    return data
