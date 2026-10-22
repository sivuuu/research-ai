import re
import json
import logging
from typing import Dict, Any, List, Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for local inference via Ollama with deterministic grounded fallbacks."""

    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3:latest')

    def generate(self, prompt: str, system: Optional[str] = None, format_json: bool = False, timeout: float = 6.0) -> Optional[str]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2}
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json().get('response', '')
        except Exception as e:
            logger.debug(f"Ollama call failed or timed out: {e}")

        return None
