"""LLM abstraction — uses local Ollama (free, no API key needed)."""

import json
import time
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:12b"


def generate_json(prompt: str, context: str, max_retries: int = 3) -> dict:
    """Call local Ollama to generate a JSON response.

    Args:
        prompt: System/instruction prompt
        context: User context data
        max_retries: Number of retries on failure

    Returns:
        Parsed JSON dict, or dict with 'error' key on failure
    """
    full_prompt = f"{prompt}\n\n{context}"

    for attempt in range(max_retries):
        try:
            logger.info(f"Ollama call (attempt {attempt + 1}, model={MODEL})...")
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a competitive intelligence analyst. You MUST respond with a valid JSON object only. No markdown, no explanation, just the JSON object as specified in the prompt.",
                        },
                        {
                            "role": "user",
                            "content": full_prompt,
                        },
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 8192,
                        "num_ctx": 32768,
                    },
                },
                timeout=600,  # 10 min timeout for executive-grade synthesis
            )
            response.raise_for_status()
            data = response.json()
            text = data.get("message", {}).get("content", "").strip()

            # Strip markdown fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)

            # Log timing
            total_ns = data.get("total_duration", 0)
            if total_ns:
                logger.info(f"Ollama completed in {total_ns / 1e9:.1f}s")

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
        except requests.ConnectionError:
            logger.error(
                "Cannot connect to Ollama. Make sure it's running: ollama serve"
            )
            return {"error": "Ollama not running. Start it with: ollama serve"}
        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"Ollama call failed (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
            if attempt < max_retries - 1:
                time.sleep(wait)

    logger.error("All Ollama attempts failed")
    return {"error": "LLM generation failed after retries"}
