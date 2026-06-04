"""
cross_referencer.py - Cross-chain wallet tracking on Pharos.

Aggregates native balance and recent activity for a wallet
across Pharos Pacific Mainnet and Pharos Atlantic Testnet, and
(optionally) compares the two so the user can see at a glance
which chain holds which assets.
"""
from typing import Any, Dict, List, Optional

from utils.chain_connectors import PharosConnectors


class CrossReferencer:
    """Track a wallet across the Pharos networks."""

    SUPPORTED_CHAINS = ("pacific_mainnet", "atlantic_testnet")

    def __init__(self):
        self.chains = {c: PharosConnectors(c) for c in self.SUPPORTED_CHAINS}

    def track_wallet(
        self,
        address: str,
        chains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return per-chain native balance and current head block for a wallet."""
        if not address:
            return {"error": "No wallet address provided"}

        target_chains = chains or list(self.SUPPORTED_CHAINS)
        for c in target_chains:
            if c not in self.chains:
                return {"error": f"Unknown chain: {c}", "supported": list(self.SUPPORTED_CHAINS)}

        results: Dict[str, Any] = {}
        total_balance = 0.0
        for c in target_chains:
            connector = self.chains[c]
            balance = connector.get_balance(address)
            block = connector.get_block_number()
            results[c] = {
                "chain_name":       connector.config["name"],
                "chain_id":         connector.config["id"],
                "balance":          balance,
                "balance_formatted": f"{balance:.6f} {connector.symbol}",
                "symbol":           connector.symbol,
                "block_number":     block,
                "explorer_url":     connector.explorer_address_url(address),
            }
            total_balance += balance

        return {
            "type":              "wallet_analysis",
            "address":           address,
            "chains_analyzed":   target_chains,
            "chain_data":        results,
            "total_native":      total_balance,
            "total_native_usd":  None,  # would need a native-price oracle
        }

    def get_wallet_transactions(
        self,
        address: str,
        chain: str = "pacific_mainnet",
        from_block: int = 0,
        to_block: str = "latest",
    ) -> Dict[str, Any]:
        """Return the most recent ERC-20 Transfer events involving `address`."""
        if chain not in self.chains:
            return {"error": f"Unknown chain: {chain}", "supported": list(self.SUPPORTED_CHAINS)}
        connector = self.chains[chain]

        head = connector.get_block_number()
        if not head:
            return {"error": "Could not fetch block number", "chain": chain}

        # Look for ERC-20 Transfer events where the wallet is either
        # sender or receiver. Topics = [TRANSFER_TOPIC, from?, to?]
        from utils.chain_connectors import ERC20_TRANSFER_TOPIC
        padded = "0x" + address.lower().replace("0x", "").rjust(64, "0")

        sent = connector.get_logs(
            topics=[ERC20_TRANSFER_TOPIC, padded, None],
            from_block=from_block,
            to_block=to_block,
        )
        received = connector.get_logs(
            topics=[ERC20_TRANSFER_TOPIC, None, padded],
            from_block=from_block,
            to_block=to_block,
        )

        return {
            "type":               "wallet_tx_history",
            "address":            address,
            "chain":              chain,
            "from_block":         from_block,
            "to_block":           to_block if to_block != "latest" else head,
            "erc20_sent_count":   len(sent),
            "erc20_received_count": len(received),
            "recent_sent":        sent[-50:],
            "recent_received":    received[-50:],
        }

    def compare_chains(self, address: str) -> Dict[str, Any]:
        """Run track_wallet on both supported chains and return a side-by-side."""
        main = self.track_wallet(address, ["pacific_mainnet"])
        test = self.track_wallet(address, ["atlantic_testnet"])
        return {
            "type":      "chain_comparison",
            "address":   address,
            "pacific_mainnet":  main.get("chain_data", {}).get("pacific_mainnet", {}),
            "atlantic_testnet": test.get("chain_data", {}).get("atlantic_testnet", {}),
            "total_native":     (main.get("total_native", 0.0) + test.get("total_native", 0.0)),
        }
