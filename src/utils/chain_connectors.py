"""
chain_connectors.py - Pharos Network data connectors.

Reads from the same RPC endpoints the official
`pharos-skill-engine` ships with, so the tool works out of the
box on Pharos Pacific Mainnet and Pharos Atlantic Testnet.

Pass a chain name to `PharosConnectors(chain)`; the default is
`pacific_mainnet`. The chain registry mirrors the asset bundle
in the official skill engine, so any chain the engine supports
can be added here without changing the rest of the code.
"""
import json
import time
from typing import Any, Dict, List, Optional

import requests


# ERC-20 Transfer event topic (canonical keccak of
# "Transfer(address,address,uint256)"). Used by
# transaction_analyzer.get_token_transfers to filter logs.
ERC20_TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)

# Function selectors used by get_token_transfers pattern detection.
SELECTOR_ERC20_TRANSFER   = "0xa9059cbb"  # transfer(address,uint256)
SELECTOR_ERC20_APPROVAL  = "0x095ea7b3"  # approve(address,uint256)


class PharosConnectors:
    """JSON-RPC client + chain metadata for the Pharos networks."""

    CHAINS = {
        "pacific_mainnet": {
            "id": 1672,
            "name": "Pharos Pacific Mainnet",
            "rpc_url": "https://rpc.pharos.xyz",
            "explorer_url": "https://www.pharosscan.xyz",
            "symbol": "PROS",
        },
        "atlantic_testnet": {
            "id": 688689,
            "name": "Pharos Atlantic Testnet",
            "rpc_url": "https://atlantic.dplabs-internal.com",
            "explorer_url": "https://atlantic.pharosscan.xyz",
            "symbol": "PHRS",
        },
    }

    def __init__(self, chain: str = "pacific_mainnet"):
        if chain not in self.CHAINS:
            raise ValueError(
                f"unknown chain: {chain!r}; expected one of {list(self.CHAINS)}"
            )
        self.chain = chain
        self.config = self.CHAINS[chain]
        self.rpc_url = self.config["rpc_url"]
        self.explorer_url = self.config["explorer_url"]
        self.symbol = self.config["symbol"]
        self.chain_id = self.config["id"]

    # ---- low-level RPC ----

    def _request(self, method: str, params: List[Any]) -> Optional[Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        try:
            r = requests.post(self.rpc_url, json=payload, timeout=30)
            if r.status_code != 200:
                return None
            data = r.json()
            return data.get("result")
        except (requests.RequestException, ValueError):
            return None

    def _request_with_retry(self, method: str, params: List[Any], max_retries: int = 3) -> Optional[Any]:
        last_err = None
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    self.rpc_url,
                    json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                    timeout=30,
                )
                if r.status_code == 429 or r.status_code >= 500:
                    raise requests.RequestException(f"HTTP {r.status_code}")
                return r.json().get("result")
            except (requests.RequestException, ValueError) as e:
                last_err = e
                time.sleep(0.4 * (2 ** attempt))
        return None

    # ---- high-level reads ----

    def get_chain_id(self) -> Optional[int]:
        r = self._request("eth_chainId", [])
        return int(r, 16) if r else None

    def get_block_number(self) -> Optional[int]:
        r = self._request("eth_blockNumber", [])
        return int(r, 16) if r else None

    def get_balance(self, address: str) -> float:
        """Return native balance in human units (PROS / PHRS)."""
        r = self._request("eth_getBalance", [address, "latest"])
        if not r:
            return 0.0
        return int(r, 16) / 1e18

    def get_balance_wei(self, address: str) -> int:
        r = self._request("eth_getBalance", [address, "latest"])
        return int(r, 16) if r else 0

    def get_code(self, address: str) -> str:
        r = self._request("eth_getCode", [address, "latest"])
        return r or "0x"

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self._request("eth_getTransactionByHash", [tx_hash])

    def get_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self._request("eth_getTransactionReceipt", [tx_hash])

    def get_block(self, num: int, full_txs: bool = False) -> Optional[Dict[str, Any]]:
        return self._request("eth_getBlockByNumber", [hex(num), full_txs])

    def get_transaction_count(self, address: str) -> int:
        r = self._request("eth_getTransactionCount", [address, "latest"])
        return int(r, 16) if r else 0

    def call(self, to: str, data: str) -> Optional[str]:
        """eth_call — read-only contract call."""
        return self._request("eth_call", [{"to": to, "data": data}, "latest"])

    def get_logs(
        self,
        address: Optional[str] = None,
        topics: Optional[List[Any]] = None,
        from_block: Any = 0,
        to_block: Any = "latest",
    ) -> List[Dict[str, Any]]:
        """eth_getLogs. Pass `address` and/or `topics` to filter.

        `topics` follows the standard JSON-RPC shape:
          ["0xTopicA", ["0xTopicB1","0xTopicB2"], null, ...]
        """
        params: Dict[str, Any] = {
            "fromBlock": hex(from_block) if isinstance(from_block, int) else from_block,
            "toBlock":   hex(to_block)   if isinstance(to_block, int)   else to_block,
        }
        if address:
            params["address"] = address
        if topics:
            params["topics"] = topics
        result = self._request_with_retry("eth_getLogs", [params])
        return result if isinstance(result, list) else []

    # ---- helpers ----

    def explorer_tx_url(self, tx_hash: str) -> str:
        return f"{self.explorer_url}/tx/{tx_hash}"

    def explorer_address_url(self, address: str) -> str:
        return f"{self.explorer_url}/address/{address}"
