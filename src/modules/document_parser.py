"""
document_parser.py - Plain-text extraction + GPT-4 summarization.

Reads a local file (text-based or PDF), pulls out the text,
and asks the configured OpenAI model to produce a structured
summary.

Supported input formats (text-based):
  - .txt, .md, .markdown
  - .sol, .vyper (Solidity / Vyper source)
  - .json, .yaml, .yml
  - .pdf (via pypdf; optional)
  - .html, .htm (stripped via stdlib html.parser)

The PDF and DOCX backends are optional — if pypdf / python-docx
isn't installed, the parser returns a clear error rather than
crashing.

If `openai` is not installed or `OPENAI_API_KEY` is not set,
the parser still extracts the text but skips the LLM summary.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment,misc]
    _OPENAI_AVAILABLE = False

from prompts import DOCUMENT_SUMMARY


DEFAULT_MODEL = "gpt-4o-mini"
MAX_TEXT_CHARS = 60_000  # ~15k tokens; well under the GPT-4o context window


class DocumentParser:
    """Extract text from a document and summarize it with an LLM."""

    TEXT_EXTS = {".txt", ".md", ".markdown", ".sol", ".vyper", ".move", ".rs",
                 ".json", ".yaml", ".yml", ".csv", ".tsv", ".log"}
    PDF_EXTS  = {".pdf"}
    HTML_EXTS = {".html", ".htm"}

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None
        if _OPENAI_AVAILABLE and self.api_key:
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception:  # noqa: BLE001
                self._client = None

    def parse(self, doc_path: str) -> Dict[str, Any]:
        """Read a document and return a structured summary."""
        if not doc_path:
            return {"error": "No document path provided", "type": "document_analysis"}

        path = Path(doc_path)
        if not path.is_file():
            return {"error": f"document not found: {doc_path}", "type": "document_analysis"}

        ext = path.suffix.lower()
        try:
            text = self._extract_text(path, ext)
        except Exception as e:  # noqa: BLE001
            return {
                "type": "document_analysis",
                "document": doc_path,
                "error": f"failed to extract text: {e}",
            }

        if not text or not text.strip():
            return {
                "type": "document_analysis",
                "document": doc_path,
                "ext": ext,
                "char_count": 0,
                "error": "no extractable text (binary or empty file?)",
            }

        # Truncate to stay under context.
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS] + "\n\n[…truncated…]"

        if not _OPENAI_AVAILABLE or not self._client:
            return {
                "type":         "document_analysis",
                "document":     doc_path,
                "ext":          ext,
                "char_count":   len(text),
                "extracted":    text[:2000] + ("…" if len(text) > 2000 else ""),
                "summary":      "(LLM summarization skipped — openai not configured)",
            }

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are ChainMind. Always respond with a single JSON object, no prose.",
                    },
                    {
                        "role": "user",
                        "content": DOCUMENT_SUMMARY + "\n\n----- DOCUMENT TEXT -----\n" + text,
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=2048,
            )
            content = resp.choices[0].message.content or "{}"
            parsed = json.loads(content)
            parsed.setdefault("type", "document_analysis")
            parsed["document"] = doc_path
            parsed["ext"] = ext
            parsed["char_count"] = len(text)
            parsed["model"] = self.model
            return parsed
        except json.JSONDecodeError as e:
            return {
                "type": "document_analysis",
                "document": doc_path,
                "error": f"model returned non-JSON: {e}",
            }
        except Exception as e:  # noqa: BLE001
            return {
                "type": "document_analysis",
                "document": doc_path,
                "error": f"OpenAI call failed: {e}",
            }

    # ---- text extractors ----

    def _extract_text(self, path: Path, ext: str) -> str:
        if ext in self.TEXT_EXTS:
            return path.read_text(encoding="utf-8", errors="replace")
        if ext in self.HTML_EXTS:
            return self._strip_html(path.read_text(encoding="utf-8", errors="replace"))
        if ext in self.PDF_EXTS:
            return self._extract_pdf(path)
        # Fallback: best-effort UTF-8 read.
        return path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _strip_html(html: str) -> str:
        from html.parser import HTMLParser

        class Stripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts = []
                self.skip = 0

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style"):
                    self.skip += 1

            def handle_endtag(self, tag):
                if tag in ("script", "style") and self.skip:
                    self.skip -= 1

            def handle_data(self, data):
                if not self.skip:
                    self.parts.append(data)

        s = Stripper()
        s.feed(html)
        return "\n".join(p.strip() for p in s.parts if p.strip())

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"pypdf not installed; pip install pypdf to read PDFs ({e})"
            )
        reader = PdfReader(str(path))
        return "\n\n".join((p.extract_text() or "") for p in reader.pages)
