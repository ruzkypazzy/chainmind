"""Cross-Referencer - Pharos Network wallet tracking"""

from typing import Dict, Any, List, Optional
from .chain_connectors import PharosConnectors

class CrossReferencer:
    """Track wallets on Pharos Network"""

    def __init__(self):
        self.chains = {
            "pacific_mainnet": PharosConnectors("pacific_mainnet"),
            "atlantic_testnet": PharosConnectors("atlantic_testnet")
        }

    def track_wallet(self, address: str, chains: List[str] = None) -> Dict[str, Any]:
        """Track wallet activity on Pharos chains"""
        if not address:
            return {"error": "No wallet address provided"}

        # Default to all Pharos chains if none specified
        target_chains = chains or ["pacific_mainnet", "atlantic_testnet"]

        results = {}
        total_balance = 0.0

        for chain in target_chains:
            if chain in self.chains:
                connector = self.chains[chain]
                balance = connector.get_balance(address)
                block = connector.get_block_number()

                results[chain] = {
                    "balance": balance,
                    "balance_formatted": f"{balance:.6f} {connector.config['symbol']}",
                    "block_number": block,
                    "explorer_url": f"{connector.config['explorer_url']}/address/{address}"
                }
                total_balance += balance

        return {
            "type": "wallet_analysis",
            "address": address,
            "total_balance_usd": 0.0,  # Would need price oracle
            "chains_analyzed": target_chains,
            "chain_data": results,
            "summary": {
                "pacific_mainnet": f"{results.get('pacific_mainnet', {}).get('balance', 0):.6f} PHAR",
                "atlantic_testnet": f"{results.get('atlantic_testnet', {}).get('balance', 0):.6f} tPHAR"
            }
        }

    def get_wallet_transactions(self, address: str, chain: str = "pacific_mainnet",
                                start_block: int = 0) -> Dict[str, Any]:
        """Get transaction history for wallet on Pharos"""
        if chain not in self.chains:
            return {"error": f"Unknown chain: {chain}"}

        connector = self.chains[chain]

        # Get current block
        current_block = connector.get_block_number()
        if not current_block:
            return {"error": "Could not fetch block number"}

        # Get logs for the address (sent and received)
        # Note: Need indexed topics for from/to, simplified here
        logs_sent = connector.get_logs(address, start_block, current_block)

        return {
            "address": address,
            "chain": chain,
            "start_block": start_block,
            "current_block": current_block,
            "transaction_count": len(logs_sent),
            "recent_transactions": logs_sent[:50]  # Limit to 50
        }

    def compare_chains(self, address: str) -> Dict[str, Any]:
        """Compare wallet activity across Pharos chains"""
        mainnet_data = self.track_wallet(address, ["pacific_mainnet"])
        testnet_data = self.track_wallet(address, ["atlantic_testnet"])

        return {
            "address": address,
            "comparison": {
                "pacific_mainnet": mainnet_data.get("chain_data", {}).get("pacific_mainnet", {}),
                "atlantic_testnet": testnet_data.get("chain_data", {}).get("atlantic_testnet", {})
            },
            "total_native_tokens": mainnet_data.get("chain_data", {}).get("pacific_mainnet", {}).get("balance", 0) +
                                  testnet_data.get("chain_data", {}).get("atlantic_testnet", {}).get("balance", 0)
        }