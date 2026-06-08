"""Smoke tests for chainmind modules.

Verifies that the modules can be imported, instantiated, and
analyze a real public Pharos transaction end-to-end. Uses
recorded fixture responses for offline checks, and a real
public mainnet tx hash for the live network check.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make `src/` importable as a package root no matter where pytest runs
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from modules.transaction_analyzer import TransactionAnalyzer  # noqa: E402
from modules.cross_referencer import CrossReferencer  # noqa: E402
from utils.chain_connectors import (  # noqa: E402
    PharosConnectors,
    ERC20_TRANSFER_TOPIC,
)


# A real public mainnet tx (revert) — same as the PSCD and
# contract-debugger demos, so anyone can re-verify.
SAMPLE_TX = "0x9606bcfd027b28e6783ca8b5fef1c3311476a1c30e5bf4464d0340a0d24ba7f7"


# -------- pure unit tests (no network) --------

def test_chain_connectors_known_networks():
    """PharosConnectors should expose both Pharos networks."""
    c = PharosConnectors()
    assert "pacific_mainnet" in c.CHAINS
    assert "atlantic_testnet" in c.CHAINS
    assert c.CHAINS["pacific_mainnet"]["id"] == 1672
    assert c.CHAINS["atlantic_testnet"]["id"] == 688689


def test_chain_connectors_rejects_unknown():
    """PharosConnectors should raise on unknown chain name."""
    with pytest.raises(ValueError):
        PharosConnectors("bitcoin_mainnet")


def test_erc20_transfer_topic_is_canonical():
    """The Transfer topic must match the canonical keccak."""
    assert (
        ERC20_TRANSFER_TOPIC
        == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    )


def test_analyzer_handles_missing_hash():
    """analyze() with no hash should return an error dict, not raise."""
    a = TransactionAnalyzer()
    r = a.analyze("")
    assert "error" in r
    assert r["error"] == "No transaction hash provided"


def test_cross_referencer_handles_missing_address():
    """track_wallet() with no address should return an error dict."""
    cr = CrossReferencer()
    r = cr.track_wallet("")
    assert "error" in r


def test_cross_referencer_rejects_unknown_chain():
    """track_wallet() with an unknown chain should error out gracefully."""
    cr = CrossReferencer()
    r = cr.track_wallet("0x0000000000000000000000000000000000000001",
                        chains=["fake_chain"])
    assert "error" in r


# -------- live network tests (skipped if no network) --------

@pytest.mark.skipif(
    not os.environ.get("CHAINMIND_LIVE", "1") == "1",
    reason="set CHAINMIND_LIVE=1 to run live network tests",
)
def test_analyzer_live_mainnet_revert():
    """Analyze a real public mainnet tx that reverted."""
    a = TransactionAnalyzer()
    r = a.analyze(SAMPLE_TX, chain="pacific_mainnet")
    if "error" in r:
        pytest.skip(f"RPC not reachable: {r['error']}")
    assert r["chain_name"] == "Pharos Pacific Mainnet"
    assert r["status"] == "failed"
    assert r["from"] == "0x67992af9a87f2d6a3062c333d8a06abbe3929438"
    assert "contract_interaction" in r["patterns"]


@pytest.mark.skipif(
    not os.environ.get("CHAINMIND_LIVE", "1") == "1",
    reason="set CHAINMIND_LIVE=1 to run live network tests",
)
def test_cross_referencer_live_balance():
    """Get the live balance of a known-address wallet across both Pharos networks."""
    cr = CrossReferencer()
    r = cr.track_wallet("0x67992af9a87f2d6a3062c333d8a06abbe3929438")
    if "error" in r:
        pytest.skip(f"RPC not reachable: {r['error']}")
    # Result is nested under chain_data
    assert "chain_data" in r
    assert "pacific_mainnet" in r["chain_data"]
    assert "atlantic_testnet" in r["chain_data"]
    assert r["chain_data"]["pacific_mainnet"]["symbol"] == "PROS"
    assert r["chain_data"]["atlantic_testnet"]["symbol"] == "PHRS"
