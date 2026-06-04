"""
nlp_converter.py - Natural-language → onchain action.

Given a free-form user request, asks the configured OpenAI model
to extract a single, structured action (swap, transfer, check
balance, tx_status, analyze, noop) plus a confidence and any
clarification questions.

If `openai` is not installed or `OPENAI_API_KEY` is not set,
the converter returns a clear, structured error.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment,misc]
    _OPENAI_AVAILABLE = False

from prompts import NLP_TO_ACTION


DEFAULT_MODEL = "gpt-4o-mini"


class NLPConverter:
    """Parse natural language into a structured onchain action."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None
        if _OPENAI_AVAILABLE and self.api_key:
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception:  # noqa: BLE001
                self._client = None

    def convert(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"error": "No text provided", "type": "nlp_conversion"}

        if not _OPENAI_AVAILABLE or not self._client:
            return {
                "type": "nlp_conversion",
                "input": text,
                "action": "noop",
                "params": {},
                "confidence": 0.0,
                "explanation": "openai not configured; install openai and set OPENAI_API_KEY",
                "needs_clarification": [],
            }

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are ChainMind. Always respond with a single JSON object, no prose.",
                    },
                    {"role": "user", "content": NLP_TO_ACTION + "\n\n----- USER REQUEST -----\n" + text},
                ],
                response_format={"type": "json_object"},
                max_tokens=512,
            )
            content = resp.choices[0].message.content or "{}"
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            return {
                "type": "nlp_conversion",
                "input": text,
                "error": f"model returned non-JSON: {e}",
            }
        except Exception as e:  # noqa: BLE001
            return {
                "type": "nlp_conversion",
                "input": text,
                "error": f"OpenAI call failed: {e}",
            }

        parsed.setdefault("type", "nlp_conversion")
        parsed["input"] = text
        parsed["model"] = self.model
        return parsed
