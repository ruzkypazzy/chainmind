"""Multi-chain data connectors"""

class ChainConnectors:
    CHAINS = {
        "ethereum": {"id": 1, "rpc": "https://eth.llamarpc.com"},
        "polygon": {"id": 137, "rpc": "https://polygon-rpc.com"},
        "arbitrum": {"id": 42161, "rpc": "https://arb1.arbitrum.io/rpc"},
        "base": {"id": 8453, "rpc": "https://mainnet.base.org"},
        "optimism": {"id": 10, "rpc": "https://mainnet.optimism.io"},
        "solana": {"id": "mainnet", "rpc": "https://api.mainnet-beta.solana.com"},
        "pacific_mainnet": {"id": 1672, "rpc": "https://Pacific-rpc.com"},
        "atlantic_testnet": {"id": 688689, "rpc": "https://Atlantic-rpc.com"},
    }
    
    def get_balance(self, address: str, chain: str) -> float:
        return 0.0
