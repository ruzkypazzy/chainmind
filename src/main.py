"""
ChainMind - Multi-Modal Onchain Intelligence Skill.

Entry point for the Pharos Agent Center.

Usage:
  python src/main.py --task "analyze transaction" --tx 0x... --chain pacific_mainnet
  python src/main.py --task "analyze image" --image chart.png
  python src/main.py --task "parse document" --document contract.pdf
  python src/main.py --task "track wallet" --address 0x... --chains pacific_mainnet atlantic_testnet
  python src/main.py --task "convert to action" --text "swap 1 ETH for USDC"

The CLI routes each `--task` to the appropriate module and
prints the result as JSON. Errors are returned in-band (never
raised) so the calling agent can parse the response.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Make `src/` importable as a package root no matter how the
# script is invoked. This avoids the broken relative imports
# that the original main.py had.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from modules.transaction_analyzer import TransactionAnalyzer  # noqa: E402
from modules.cross_referencer import CrossReferencer  # noqa: E402

# Vision / document / NLP are optional (need the `openai` package).
try:
    from modules.vision_analyzer import VisionAnalyzer  # type: ignore
except Exception:  # noqa: BLE001
    VisionAnalyzer = None  # type: ignore[assignment,misc]

try:
    from modules.document_parser import DocumentParser  # type: ignore
except Exception:  # noqa: BLE001
    DocumentParser = None  # type: ignore[assignment,misc]

try:
    from modules.nlp_converter import NLPConverter  # type: ignore
except Exception:  # noqa: BLE001
    NLPConverter = None  # type: ignore[assignment,misc]


class ChainMindSkill:
    """Top-level facade for the multi-modal onchain skill."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.modules: Dict[str, Any] = {}

    def initialize(self) -> bool:
        """Wire up the available modules. Returns True if at least
        the on-chain modules came up (vision / doc / NLP may be
        None if `openai` is missing)."""
        try:
            self.modules["transaction"] = TransactionAnalyzer()
            self.modules["cross_ref"]    = CrossReferencer()
            if VisionAnalyzer is not None:
                self.modules["vision"] = VisionAnalyzer()
            if DocumentParser is not None:
                self.modules["document"] = DocumentParser()
            if NLPConverter is not None:
                self.modules["nlp"] = NLPConverter()
            return True
        except Exception as e:  # noqa: BLE001
            print(f"Initialization error: {e}", file=sys.stderr)
            return False

    def analyze(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        """Dispatch a task string to the matching module."""
        t = (task or "").lower()
        if any(k in t for k in ("vision", "chart", "image", "nft", "portfolio")):
            mod = self.modules.get("vision")
            if mod is None:
                return {
                    "type": "vision_analysis",
                    "error": "VisionAnalyzer unavailable (openai not installed?)",
                }
            return mod.analyze(kwargs.get("image_path"))
        if any(k in t for k in ("document", "contract", "whitepaper", "audit", "parse")):
            mod = self.modules.get("document")
            if mod is None:
                return {
                    "type": "document_analysis",
                    "error": "DocumentParser unavailable (openai not installed?)",
                }
            return mod.parse(kwargs.get("doc_path"))
        if any(k in t for k in ("transaction", "tx")):
            return self.modules["transaction"].analyze(
                kwargs.get("tx_hash"), kwargs.get("chain")
            )
        if any(k in t for k in ("wallet", "address", "track", "compare")):
            if "compare" in t:
                return self.modules["cross_ref"].compare_chains(kwargs.get("address"))
            return self.modules["cross_ref"].track_wallet(
                kwargs.get("address"), kwargs.get("chains")
            )
        if any(k in t for k in ("nlp", "natural", "action", "convert")):
            mod = self.modules.get("nlp")
            if mod is None:
                return {
                    "type": "nlp_conversion",
                    "error": "NLPConverter unavailable (openai not installed?)",
                }
            return mod.convert(kwargs.get("text"))
        return {"error": "Unknown task type", "task": task}


def main() -> int:
    p = argparse.ArgumentParser(
        description="ChainMind — multi-modal onchain intelligence for Pharos."
    )
    p.add_argument("--task", required=True,
                   help="Analysis task (e.g. 'analyze transaction', 'analyze image', "
                        "'track wallet', 'convert to action')")
    p.add_argument("--address", help="Wallet address (for 'track wallet' / 'compare chains')")
    p.add_argument("--chain", default=None,
                   help="Chain name (pacific_mainnet | atlantic_testnet)")
    p.add_argument("--chains", nargs="+", default=None,
                   help="Multiple chains (for cross-chain tracking)")
    p.add_argument("--image", help="Image file path (for 'analyze image')")
    p.add_argument("--document", help="Document file path (for 'parse document')")
    p.add_argument("--tx", help="Transaction hash (for 'analyze transaction')")
    p.add_argument("--text", help="Natural language input (for 'convert to action')")
    p.add_argument("--api-key", default=None,
                   help="OpenAI API key (overrides $OPENAI_API_KEY)")
    args = p.parse_args()

    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    skill = ChainMindSkill()
    if not skill.initialize():
        print(json.dumps({"error": "Failed to initialize ChainMind"}))
        return 1

    kwargs = {
        "image_path": args.image,
        "doc_path":   args.document,
        "tx_hash":    args.tx,
        "address":    args.address,
        "chain":      args.chain,
        "chains":     args.chains,
        "text":       args.text,
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    result = skill.analyze(args.task, **kwargs)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
