"""
vision_analyzer.py - OpenAI Vision-powered image analysis.

The analyzer accepts a path to a local image (PNG / JPG /
WEBP / GIF) and asks GPT-4o (or the configured model) to
classify the image and extract structured data points.

If the `openai` package isn't installed, or `OPENAI_API_KEY`
isn't set, the analyzer returns a clear, structured error
rather than crashing — so the rest of the skill can keep
running.

If the file doesn't exist, the analyzer returns a clear
"file not found" error rather than attempting a network call.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Optional import — analyzer should still *load* even if openai
# is missing, so other modules can keep working.
try:
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment,misc]
    _OPENAI_AVAILABLE = False

from prompts import VISION_ANALYSIS


DEFAULT_MODEL = "gpt-4o"
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20 MB hard cap


class VisionAnalyzer:
    """OpenAI Vision-backed image analysis."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None
        if _OPENAI_AVAILABLE and self.api_key:
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception:  # noqa: BLE001
                self._client = None

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """Analyze an image and return a structured JSON report."""
        if not image_path:
            return {"error": "No image path provided", "type": "vision_analysis"}

        path = Path(image_path)
        if not path.is_file():
            return {
                "error": f"image not found: {image_path}",
                "type": "vision_analysis",
            }
        if path.stat().st_size > MAX_IMAGE_BYTES:
            return {
                "error": f"image too large (>{MAX_IMAGE_BYTES} bytes): {image_path}",
                "type": "vision_analysis",
            }

        if not _OPENAI_AVAILABLE:
            return {
                "type": "vision_analysis",
                "image": image_path,
                "error": "openai package not installed; pip install openai to enable vision",
            }
        if not self._client:
            return {
                "type": "vision_analysis",
                "image": image_path,
                "error": "OPENAI_API_KEY not set; export it before calling analyze()",
            }

        try:
            data_url = self._to_data_url(path)
        except Exception as e:  # noqa: BLE001
            return {
                "type": "vision_analysis",
                "image": image_path,
                "error": f"failed to read image: {e}",
            }

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are ChainMind, an onchain intelligence assistant. "
                                   "Always respond with a single JSON object, no prose.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": VISION_ANALYSIS},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=1024,
            )
            content = resp.choices[0].message.content or "{}"
            parsed = json.loads(content)
            parsed.setdefault("type", "vision_analysis")
            parsed["image"] = image_path
            parsed["model"] = self.model
            return parsed
        except json.JSONDecodeError as e:
            return {
                "type": "vision_analysis",
                "image": image_path,
                "error": f"model returned non-JSON: {e}",
                "raw": content if "content" in locals() else None,
            }
        except Exception as e:  # noqa: BLE001
            return {
                "type": "vision_analysis",
                "image": image_path,
                "error": f"OpenAI call failed: {e}",
            }

    # ---- helpers ----

    @staticmethod
    def _to_data_url(path: Path) -> str:
        mime, _ = mimetypes.guess_type(str(path))
        if mime is None:
            mime = "image/png"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
