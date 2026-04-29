import os
import json
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def call_openrouter(messages: list, max_tokens: int = 512) -> dict:
    """Fallback LLM call using OpenRouter Qwen2-7B-Instruct (free tier)."""
    from openai import OpenAI

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not set, cannot use fallback")
        raise RuntimeError("OpenRouter API key not configured")

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        response = client.chat.completions.create(
            model="qwen/qwen2-7b-instruct:free",
            messages=messages,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("OpenRouter JSON parse failed, returning raw text")
        return {"raw": content}
    except Exception as e:
        logger.error(f"OpenRouter call failed: {e}")
        raise
