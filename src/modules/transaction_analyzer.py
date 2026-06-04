"""
transaction_analyzer.py - Pharos Network transaction analysis.

Fetches a transaction and its receipt via PharosConnectors,
extracts key fields (from / to / value / gas / status), detects
common patterns (contract deployment, native transfer, ERC-20
transfer, ERC-20 approval), and assigns a heuristic risk score.

The risk score is intentionally simple — see
`docs/transaction-analyzer.md` for the exact formula.
"""
from typing import Any, Dict, List, Optional

from utils.chain_connectors import (
    PharosConnectors,
    ERC20_TRANSFER_TOPIC,
    SELECTOR_ERC20_TRANSFER,
    SELECTOR_ERC20_APPROVAL,
)


# Common ERC-20 method selectors we recognize.
KNOWN_SELECTORS = {
    SELECTOR_ERC20_TRANSFER:  "erc20_transfer",
    SELECTOR_ERC20_APPROVAL: "erc20_approval",
}


class TransactionAnalyzer:
    """Analyze transactions on Pharos Network."""

    def __init__(self, chain: str = "pacific_mainnet"):
        self.chain = chain
        self.connector = PharosConnectors(chain)

    def analyze(self, tx_hash: str, chain: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a single transaction and return a structured summary."""
        if not tx_hash:
            return {"error": "No transaction hash provided"}

        connector = PharosConnectors(chain) if chain else self.connector
        tx = connector.get_transaction(tx_hash)
        receipt = connector.get_receipt(tx_hash)

        if not tx:
            return {"error": "Transaction not found", "tx_hash": tx_hash, "chain": connector.chain}

        from_address = (tx.get("from") or "").lower()
        to_address   = (tx.get("to") or "").lower() or None
        value_wei    = int(tx.get("value", "0x0"), 16)
        value_native = value_wei / 1e18
        gas_price    = int(tx.get("gasPrice", "0x0"), 16)
        data         = tx.get("input", tx.get("data", "0x")) or "0x"

        gas_used = 0
        status_ok: Optional[bool] = None
        if receipt:
            gas_used = int(receipt.get("gasUsed", "0x0"), 16)
            status_int = int(receipt.get("status", "0x0"), 16)
            status_ok = (status_int == 1)

        # was the `to` address a contract at execution time?
        to_is_contract = False
        if to_address:
            try:
                code = connector.get_code(to_address)
                to_is_contract = code not in ("0x", "0x0", "", None)
            except Exception:  # noqa: BLE001
                to_is_contract = False

        patterns = self._detect_patterns(tx, receipt, to_is_contract)
        risk = self._calculate_risk(tx, receipt, to_is_contract, value_wei)

        return {
            "type":             "transaction_analysis",
            "chain":            connector.chain,
            "chain_name":       connector.config["name"],
            "tx_hash":          tx_hash,
            "from":             from_address,
            "to":               to_address,
            "value_native":     value_native,
            "value_wei":        value_wei,
            "native_symbol":    connector.symbol,
            "gas_price_wei":    gas_price,
            "gas_used":         gas_used,
            "status":           "confirmed" if status_ok is True else ("failed" if status_ok is False else "pending"),
            "is_contract_call": to_is_contract,
            "patterns":         patterns,
            "risk_score":       risk,
            "explorer_url":     connector.explorer_tx_url(tx_hash),
        }

    # ---- helpers ----

    def _detect_patterns(
        self,
        tx: Dict[str, Any],
        receipt: Optional[Dict[str, Any]],
        to_is_contract: bool,
    ) -> List[str]:
        detected: List[str] = []
        to_address = (tx.get("to") or "").lower()
        data = tx.get("input", tx.get("data", "0x")) or "0x"
        value_wei = int(tx.get("value", "0x0"), 16)

        # contract deployment: `to` is empty/null
        if not to_address:
            detected.append("contract_deployment")
        if data and data != "0x":
            detected.append("contract_interaction")
        if value_wei > 0:
            detected.append("native_transfer")
        if len(data) >= 10 and data[:10] == SELECTOR_ERC20_TRANSFER:
            detected.append("erc20_transfer")
        if len(data) >= 10 and data[:10] == SELECTOR_ERC20_APPROVAL:
            detected.append("erc20_approval")
        return detected

    def _calculate_risk(
        self,
        tx: Dict[str, Any],
        receipt: Optional[Dict[str, Any]],
        to_is_contract: bool,
        value_wei: int,
    ) -> float:
        risk = 0.0
        if receipt and int(receipt.get("status", "0x1"), 16) == 0:
            risk += 0.3
        # > 1000 native = big transfer
        if value_wei > 1_000 * 1e18:
            risk += 0.3
        # contract creation
        if not (tx.get("to") or ""):
            risk += 0.2
        # approval to a contract
        data = tx.get("input", tx.get("data", "0x")) or "0x"
        if to_is_contract and len(data) >= 10 and data[:10] == SELECTOR_ERC20_APPROVAL:
            risk += 0.1
        return min(risk, 1.0)

    # ---- token-transfer extraction ----

    def get_token_transfers(self, tx_hash: str, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse ERC-20 Transfer events from a transaction's receipt logs."""
        connector = PharosConnectors(chain) if chain else self.connector
        receipt = connector.get_receipt(tx_hash)
        if not receipt:
            return []

        transfers: List[Dict[str, Any]] = []
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if not topics or topics[0].lower() != ERC20_TRANSFER_TOPIC.lower():
                continue
            if len(topics) < 3:
                continue
            try:
                amount = int(log.get("data", "0x0"), 16)
            except ValueError:
                amount = 0
            transfers.append({
                "token":     (log.get("address") or "").lower(),
                "from":      "0x" + topics[1][-40:].lower(),
                "to":        "0x" + topics[2][-40:].lower(),
                "amount":    amount,
            })
        return transfers
