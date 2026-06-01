"""Pharos Network data connectors"""

import requests
from typing import Optional, Dict, Any

class PharosConnectors:
    """Connector for Pharos Network chains"""

    CHAINS = {
        "pacific_mainnet": {
            "id": 1672,
            "name": "Pharos Pacific Mainnet",
            "rpc_url": "https://rpc.pharoslabs.xyz",
            "explorer_url": "https://explorer.pharos.xyz",
            "symbol": "PHAR"
        },
        "atlantic_testnet": {
            "id": 688689,
            "name": "Pharos Atlantic Testnet",
            "rpc_url": "https://rpc.testnet.pharos.xyz",
            "explorer_url": "https://explorer.testnet.pharos.xyz",
            "symbol": "tPHAR"
        }
    }

    def __init__(self, chain: str = "pacific_mainnet"):
        self.chain = chain
        self.config = self.CHAINS.get(chain, self.CHAINS["pacific_mainnet"])
        self.rpc_url = self.config["rpc_url"]

    def _make_request(self, method: str, params: list = None) -> Optional[Dict[str, Any]]:
        """Make JSON-RPC request to Pharos RPC"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        try:
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get("result")
            return None
        except Exception as e:
            print(f"RPC request error: {e}")
            return None

    def get_balance(self, address: str) -> Optional[float]:
        """Get native token balance"""
        result = self._make_request(
            "eth_getBalance",
            [address, "latest"]
        )
        if result:
            # Convert hex to decimal and convert to ETH/PHAR
            balance_wei = int(result, 16)
            return balance_wei / 1e18
        return 0.0

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by hash"""
        return self._make_request(
            "eth_getTransactionByHash",
            [tx_hash]
        )

    def get_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction receipt"""
        return self._make_request(
            "eth_getTransactionReceipt",
            [tx_hash]
        )

    def get_block_number(self) -> Optional[int]:
        """Get current block number"""
        result = self._make_request("eth_blockNumber")
        if result:
            return int(result, 16)
        return None

    def get_code(self, address: str) -> Optional[str]:
        """Get contract code at address"""
        return self._make_request(
            "eth_getCode",
            [address, "latest"]
        )

    def call(self, to: str, data: str) -> Optional[str]:
        """Make a call to a contract"""
        payload = {
            "to": to,
            "data": data
        }
        return self._make_request("eth_call", [payload, "latest"])

    def get_logs(self, address: str, from_block: int = 0, to_block: str = "latest") -> list:
        """Get event logs from a contract"""
        filter_params = {
            "address": address,
            "fromBlock": hex(from_block) if isinstance(from_block, int) else from_block,
            "toBlock": hex(to_block) if isinstance(to_block, int) else to_block
        }
        result = self._make_request("eth_getLogs", [filter_params])
        return result or []