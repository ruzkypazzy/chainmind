"""Transaction Analyzer - Pharos Network transaction analysis"""

from typing import Dict, Any, Optional, List
from .chain_connectors import PharosConnectors

class TransactionAnalyzer:
    """Analyze transactions on Pharos Network"""

    def __init__(self, chain: str = "pacific_mainnet"):
        self.chain = chain
        self.connector = PharosConnectors(chain)
        self.patterns = []

    def analyze(self, tx_hash: str, chain: str = None) -> Dict[str, Any]:
        """Analyze a transaction on Pharos Network"""
        if not tx_hash:
            return {"error": "No transaction hash provided"}

        # Use specified chain or default
        connector = PharosConnectors(chain) if chain else self.connector

        # Fetch transaction data
        tx = connector.get_transaction(tx_hash)
        receipt = connector.get_receipt(tx_hash)

        if not tx:
            return {"error": "Transaction not found", "tx_hash": tx_hash}

        # Extract key information
        from_address = tx.get("from", "")
        to_address = tx.get("to", "")
        value_wei = int(tx.get("value", "0x0"), 16)
        value_native = value_wei / 1e18

        gas_price = int(tx.get("gasPrice", "0x0"), 16)
        gas_used = int(receipt.get("gasUsed", "0x0"), 16) if receipt else 0
        status = receipt.get("status", "0x0") == "0x1" if receipt else None

        # Detect patterns
        patterns = self._detect_patterns(tx, receipt)

        # Calculate risk score
        risk_score = self._calculate_risk(tx, receipt)

        return {
            "type": "transaction_analysis",
            "chain": chain or self.chain,
            "tx_hash": tx_hash,
            "from": from_address,
            "to": to_address,
            "value": value_native,
            "value_wei": value_wei,
            "gas_price": gas_price,
            "gas_used": gas_used,
            "status": "confirmed" if status else "failed",
            "is_contract_call": bool(to_address and connector.get_code(to_address) != "0x"),
            "patterns": patterns,
            "risk_score": risk_score,
            "explorer_url": f"{connector.config['explorer_url']}/tx/{tx_hash}"
        }

    def _detect_patterns(self, tx: Dict, receipt: Dict) -> List[str]:
        """Detect transaction patterns"""
        detected = []

        to_address = tx.get("to", "")
        data = tx.get("data", "0x")

        # Check if it's a contract deployment
        if not to_address:
            detected.append("contract_deployment")

        # Check if it has data (contract interaction)
        if data and data != "0x":
            detected.append("contract_interaction")

        # Check value transfer
        value_wei = int(tx.get("value", "0x0"), 16)
        if value_wei > 0:
            detected.append("native_transfer")

        # Check for token transfers (ERC-20)
        if len(data) >= 10 and data[:10] == "0xa9059cbb":
            detected.append("erc20_transfer")

        # Check for approvals
        if len(data) >= 10 and data[:10] == "0x095ea7b3":
            detected.append("erc20_approval")

        return detected

    def _calculate_risk(self, tx: Dict, receipt: Dict) -> float:
        """Calculate risk score (0.0 - 1.0)"""
        risk = 0.0

        # Check if transaction failed
        if receipt:
            status = receipt.get("status", "0x1")
            if status == "0x0":
                risk += 0.3

        # Check for large value transfers
        value_wei = int(tx.get("value", "0x0"), 16)
        if value_wei > 1e21:  # > 1000 ETH
            risk += 0.3

        # Check for contract interaction without known function
        data = tx.get("data", "0x")
        to_address = tx.get("to", "")
        if data and data != "0x" and not to_address:
            risk += 0.2

        return min(risk, 1.0)

    def get_token_transfers(self, tx_hash: str) -> List[Dict[str, Any]]:
        """Extract token transfers from transaction logs"""
        connector = self.connector
        receipt = connector.get_receipt(tx_hash)

        if not receipt:
            return []

        transfers = []
        logs = receipt.get("logs", [])

        for log in logs:
            # ERC-20 Transfer event signature
            if log.get("topics", [])[0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df35b9dc":
                transfers.append({
                    "address": log.get("address"),
                    "from": "0x" + log.get("topics", [None, None])[1][-40:],
                    "to": "0x" + log.get("topics", [None, None, None])[2][-40:],
                    "topics": log.get("topics", [])
                })

        return transfers