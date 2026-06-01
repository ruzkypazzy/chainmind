"""
ChainMind - Multi-Modal Onchain Intelligence Skill
Entry point for Pharos Agent Kit integration
"""

import argparse
import json
import os
from typing import Dict, Any, Optional

class ChainMindSkill:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.modules = {}
        
    def initialize(self) -> bool:
        """Initialize all analysis modules"""
        try:
            from .modules.vision_analyzer import VisionAnalyzer
            from .modules.document_parser import DocumentParser
            from .modules.transaction_analyzer import TransactionAnalyzer
            from .modules.cross_referencer import CrossReferencer
            from .modules.nlp_converter import NLPConverter
            
            self.modules["vision"] = VisionAnalyzer()
            self.modules["document"] = DocumentParser()
            self.modules["transaction"] = TransactionAnalyzer()
            self.modules["cross_ref"] = CrossReferencer()
            self.modules["nlp"] = NLPConverter()
            return True
        except Exception as e:
            print(f"Initialization error: {e}")
            return False
    
    def analyze(self, task: str, **kwargs) -> Dict[str, Any]:
        """Route analysis task to appropriate module"""
        task_lower = task.lower()
        
        if "vision" in task_lower or "chart" in task_lower or "image" in task_lower:
            return self.modules["vision"].analyze(kwargs.get("image_path"))
        elif "document" in task_lower or "contract" in task_lower or "whitepaper" in task_lower:
            return self.modules["document"].parse(kwargs.get("doc_path"))
        elif "transaction" in task_lower or "tx" in task_lower:
            return self.modules["transaction"].analyze(kwargs.get("tx_hash"), kwargs.get("chain"))
        elif "wallet" in task_lower or "address" in task_lower:
            return self.modules["cross_ref"].track_wallet(kwargs.get("address"), kwargs.get("chains"))
        elif "nlp" in task_lower or "natural" in task_lower or "action" in task_lower:
            return self.modules["nlp"].convert(kwargs.get("text"))
        else:
            return {"error": "Unknown task type", "task": task}

def main():
    parser = argparse.ArgumentParser(description="ChainMind Multi-Modal Onchain Intelligence")
    parser.add_argument("--task", type=str, required=True, help="Analysis task")
    parser.add_argument("--address", type=str, help="Wallet address")
    parser.add_argument("--chain", type=str, help="Blockchain name")
    parser.add_argument("--image", type=str, help="Image file path")
    parser.add_argument("--document", type=str, help="Document file path")
    parser.add_argument("--tx", type=str, help="Transaction hash")
    parser.add_argument("--text", type=str, help="Natural language input")
    parser.add_argument("--chains", type=str, nargs="+", help="List of chains")
    
    args = parser.parse_args()
    skill = ChainMindSkill()
    
    if not skill.initialize():
        print(json.dumps({"error": "Failed to initialize ChainMind"}))
        return
    
    kwargs = {
        "image_path": args.image,
        "doc_path": args.document,
        "tx_hash": args.tx,
        "address": args.address,
        "chain": args.chain,
        "chains": args.chains,
        "text": args.text
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    result = skill.analyze(args.task, **kwargs)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
