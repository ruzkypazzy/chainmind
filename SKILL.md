---
name: chainmind
description: >
  REQUIRED for any task that requires multi-modal onchain
  intelligence on the Pharos Network. Combines (1) OpenAI
  Vision chart / NFT / portfolio analysis, (2) document
  intelligence for smart contracts, whitepapers, and audit
  reports, (3) on-chain transaction analysis with pattern
  detection and risk scoring, (4) cross-chain wallet tracking
  on Pharos Pacific Mainnet and Atlantic Testnet, and
  (5) natural-language to onchain action conversion. Invoke
  when the user asks to "analyze this chart", "parse this
  contract", "explain this transaction", "track this wallet",
  or "what does this mean: 'swap 1 ETH for USDC'". Use the
  bundled `src/main.py` CLI or import the modules directly.
  Do not attempt multi-modal onchain analysis without reading
  this skill.
version: 0.2.0
requires:
  - python >= 3.9
  - requests
  - openai
  - anyBins:
      - jq     # optional, used for ergonomic config inspection
---

# ChainMind — Multi-Modal Onchain Intelligence

A unified skill that lets an AI agent reason about onchain data
across five modalities:

| Modality        | What it does                                        | Module                |
|-----------------|-----------------------------------------------------|-----------------------|
| Vision          | Analyze charts, NFTs, portfolio screenshots         | `VisionAnalyzer`      |
| Document        | Parse contracts, whitepapers, audit reports        | `DocumentParser`      |
| Transaction     | Decode a tx, detect patterns, score risk            | `TransactionAnalyzer` |
| Cross-Chain     | Track a wallet across Pharos mainnet + testnet      | `CrossReferencer`     |
| NLP → Action    | Convert free-form requests into structured actions  | `NLPConverter`        |

## When to use

- The user uploads a chart / NFT grid / portfolio screenshot.
- The user uploads a contract source / whitepaper / audit PDF.
- The user asks "what did this transaction do?"
- The user asks "is this wallet the same on Pharos mainnet and
  Atlantic testnet?"
- The user types a free-form request that should be executed
  onchain ("send 50 USDC to alice.eth").

## When NOT to use

- Trading / order routing (use a swap-router skill).
- Pure data aggregation (use a wallet-aggregator skill).
- Anything that requires write operations without explicit
  user confirmation (ChainMind is read-only by default).

## Inputs

### CLI flags

| Flag          | Required | Description                                          |
|---------------|----------|------------------------------------------------------|
| `--task`      | yes      | Task key (see table below)                           |
| `--tx`        | depends  | Transaction hash (for `--task analyze transaction`)  |
| `--address`   | depends  | Wallet address                                       |
| `--chain`     | no       | `pacific_mainnet` (default) or `atlantic_testnet`    |
| `--chains`    | no       | Multiple chains for cross-chain tracking             |
| `--image`     | depends  | Path to image (for vision tasks)                     |
| `--document`  | depends  | Path to document (for parse tasks)                   |
| `--text`      | depends  | Free-form text (for NLP tasks)                       |
| `--api-key`   | no       | OpenAI API key (overrides `$OPENAI_API_KEY`)         |

### Task keys

| Substring in `--task`      | Module           | Required extras              |
|----------------------------|------------------|------------------------------|
| `vision`, `chart`, `image` | `VisionAnalyzer` | `--image`                    |
| `document`, `contract`, `parse` | `DocumentParser` | `--document`              |
| `transaction`, `tx`        | `TransactionAnalyzer` | `--tx`, optional `--chain` |
| `wallet`, `address`, `track` | `CrossReferencer` | `--address`               |
| `compare`                  | `CrossReferencer` | `--address`                |
| `nlp`, `natural`, `action`, `convert` | `NLPConverter` | `--text`        |

## Outputs

Every command prints a JSON object on stdout. Errors are
returned in-band (never raised) so the calling agent can parse
the response. Every JSON object has at minimum a `type` field
and an `error` field (only when something went wrong).

## Quick start

```bash
# 1. Install
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...

# 2. Track a wallet across both Pharos chains
python src/main.py --task "track wallet" --address 0xYourWallet

# 3. Decode a transaction
python src/main.py --task "analyze transaction" --tx 0xYourTxHash --chain pacific_mainnet

# 4. Read a chart screenshot
python src/main.py --task "analyze image" --image chart.png

# 5. Parse a contract source
python src/main.py --task "parse document" --document contracts/MyContract.sol

# 6. Convert a free-form request into an action
python src/main.py --task "convert to action" --text "swap 0.5 PROS for PHRS"
```

## Agent invocation pattern

When the user makes a request that fits one of the modalities:

1. Pick the matching `--task` key (or use the natural-language
   one: `chainmind analyze`).
2. Pass the relevant extras (`--tx`, `--address`, `--image`,
   `--document`, `--text`).
3. Pipe stdout into a JSON parser.
4. If the response has `error`, surface it to the user; if
   `type` is `nlp_conversion`, use the `action` / `params` /
   `confidence` fields to drive the next step.

## Error handling

| Error                      | Cause                            | Action |
|----------------------------|----------------------------------|--------|
| `OPENAI_API_KEY not set`   | Env var missing for vision/doc/NLP | Tell the user to set the key, or skip that modality |
| `image not found`          | Wrong path                        | Verify the path                       |
| `openai package not installed` | `pip install openai` missing  | Vision / doc / NLP are unavailable   |
| `RPC request error`        | Pharos RPC unreachable           | Try the alt chain or wait            |
| `model returned non-JSON`  | LLM drift                         | Retry with lower temperature         |

## Supported networks

The connector reads from the same RPC endpoints the official
`pharos-skill-engine` ships with.

| Network                  | Chain ID | RPC URL                                | Native token | Explorer                          |
|--------------------------|----------|----------------------------------------|--------------|-----------------------------------|
| Pharos Pacific Mainnet   | `1672`   | `https://rpc.pharos.xyz`               | PROS         | https://www.pharosscan.xyz/       |
| Pharos Atlantic Testnet  | `688689` | `https://atlantic.dplabs-internal.com` | PHRS         | https://atlantic.pharosscan.xyz/  |

## Limitations

- The OpenAI-backed modules (`VisionAnalyzer`, `DocumentParser`,
  `NLPConverter`) require `OPENAI_API_KEY`. The on-chain
  modules (`TransactionAnalyzer`, `CrossReferencer`) work
  without it.
- Vision and document calls are rate-limited by OpenAI; the
  skill does not currently batch or queue them.
- Cross-chain tracking only spans the two Pharos networks.
  Adding more networks is a config-only change in
  `config/config.yaml` and `skill.json`.
- The skill is read-only by default. There is no signer /
  key-management code in this repository.
