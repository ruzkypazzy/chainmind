"""
modules/__init__.py

Re-export the five analysis modules. The transaction and
cross-chain modules are local-only (no third-party deps), so
they always import. The vision, document, and NLP modules
depend on the `openai` package; if it's not installed the
imports are skipped and a stub is used instead.
"""
from .transaction_analyzer import TransactionAnalyzer
from .cross_referencer import CrossReferencer

# These three depend on the `openai` SDK. Try to import them
# eagerly; if `openai` is missing, fall back to the stub class
# declared in each module.
try:
    from .vision_analyzer import VisionAnalyzer  # noqa: F401
except Exception as _e:  # noqa: BLE001
    VisionAnalyzer = None  # type: ignore[assignment,misc]

try:
    from .document_parser import DocumentParser  # noqa: F401
except Exception:  # noqa: BLE001
    DocumentParser = None  # type: ignore[assignment,misc]

try:
    from .nlp_converter import NLPConverter  # noqa: F401
except Exception:  # noqa: BLE001
    NLPConverter = None  # type: ignore[assignment,misc]

__all__ = [
    "TransactionAnalyzer",
    "CrossReferencer",
    "VisionAnalyzer",
    "DocumentParser",
    "NLPConverter",
]
