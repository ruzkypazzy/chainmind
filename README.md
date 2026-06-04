# ChainMind — Multi-Modal Onchain Intelligence

> Vision + document + transaction + cross-chain + NLP-to-action
> in one skill for the Pharos Network.

[![python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![license](https://img.shields.io/badge/license-MIT-green)]()
[![rpc](https://img.shields.io/badge/RPC-JSON--RPC%20%7C%20EVM-orange)]()

## Overview

ChainMind is a multi-modal onchain intelligence skill designed
for AI agents that need to understand and interact with
blockchain data through more than just raw `eth_call` results:

- **Vision** — analyze charts, NFTs, and portfolio screenshots
  via GPT-4o vision
- **Document** — parse smart contracts, whitepapers, and audit
  reports via GPT-4
- **Transaction** — decode a tx, detect patterns (contract
  deployment, ERC-20 transfer, approval), and score risk
- **Cross-Chain** — track a wallet across Pharos Pacific
  Mainnet and Pharos Atlantic Testnet in one call
- **NLP → Action** — convert free-form requests like
  "swap 0.5 PROS for PHRS" into structured actions

## Features

- **Single CLI** with a `--task` router for all five modalities
- **OpenAI Vision / Document / NLP** with graceful fallback
  when `openai` is missing or `OPENAI_API_KEY` is unset
- **Pharos RPC + explorer integration** out of the box
- **JSONL-safe outputs** — every module returns a JSON object
  with a `type` and (on error) an `error` field
- **No signer / key management** — read-only by default
- **Multi-chain aware** — `pacific_mainnet` and
  `atlantic_testnet` are first-class

## Supported networks

ChainMind reads from the same RPC endpoints the official
`pharos-skill-engine` ships with.

| Network                 | Chain ID | RPC URL                                | Native token | Explorer                          |
|-------------------------|----------|----------------------------------------|--------------|-----------------------------------|
| Pharos Pacific Mainnet  | `1672`   | `https://rpc.pharos.xyz`               | PROS         | https://www.pharosscan.xyz/       |
| Pharos Atlantic Testnet | `688689` | `https://atlantic.dplabs-internal.com` | PHRS         | https://atlantic.pharosscan.xyz/  |

## Overview

For a deeper explanation of what each module does, see
[`SKILL.md`](./SKILL.md) at the repo root. The structure of
the repo is:

```
chainmind/
├── SKILL.md                 # Agent-facing skill spec (load this first)
├── README.md                # This file
├── LICENSE                  # MIT
├── requirements.txt
├── config/
│   └── config.yaml          # Chain registry + API key template
├── skill.json               # Skill manifest for the Pharos Agent Center
├── src/
│   ├── main.py              # CLI entry point
│   ├── modules/
│   │   ├── vision_analyzer.py
│   │   ├── document_parser.py
│   │   ├── transaction_analyzer.py
│   │   ├── cross_referencer.py
│   │   └── nlp_converter.py
│   ├── prompts/
│   │   └── __init__.py      # Named prompt templates
│   └── utils/
│       ├── chain_connectors.py
│       ├── data_formatters.py
│       └── cache_manager.py
└── examples/
    └── (sample inputs)
```

## Framework

- **Language:** Python 3.9+
- **RPC protocol:** JSON-RPC (`eth_chainId`, `eth_blockNumber`,
  `eth_getBalance`, `eth_getTransactionByHash`,
  `eth_getTransactionReceipt`, `eth_getCode`, `eth_getLogs`,
  `eth_call`)
- **LLM:** OpenAI Python SDK (`openai>=1.0.0`); uses `gpt-4o`
  for vision and `gpt-4o-mini` for document / NLP by default
- **No web3 framework** — plain `requests` over JSON-RPC
- **Storage:** none (read-only)

## Dependencies

Runtime (Python):

- `requests>=2.31.0` — HTTP client used by `chain_connectors.py`
- `PyYAML>=6.0` — config loader
- `openai>=1.0.0` — required for vision, document, and NLP
  modules; transaction and cross-chain modules work without it

Optional:

- `pypdf>=4.0.0` — only needed for PDF document parsing
  (uncomment the line in `requirements.txt` if you need it)

## Installation

```bash
git clone https://github.com/ruzkypazzy/chainmind.git
cd chainmind
pip install -r requirements.txt

# Only needed for vision / document / NLP modules
export OPENAI_API_KEY=sk-...
```

## Usage

### 1. Track a wallet across both Pharos chains

```bash
python src/main.py --task "track wallet" --address 0xYourWallet
```

### 2. Decode a transaction on Pharos mainnet

```bash
python src/main.py --task "analyze transaction" \
  --tx 0xYourTxHash \
  --chain pacific_mainnet
```

### 3. Read a chart screenshot

```bash
python src/main.py --task "analyze image" --image chart.png
```

### 4. Parse a contract source file

```bash
python src/main.py --task "parse document" \
  --document contracts/MyContract.sol
```

### 5. Convert free-form text into an action

```bash
python src/main.py --task "convert to action" \
  --text "swap 0.5 PROS for PHRS"
```

### 6. Compare a wallet across both Pharos chains

```bash
python src/main.py --task "compare chains" --address 0xYourWallet
```

## Capabilities

| Capability            | Description                                            | Requires OpenAI? |
|-----------------------|--------------------------------------------------------|------------------|
| Visual Chart Analysis | GPT-4o reads charts and extracts data points           | Yes              |
| Portfolio Screenshot  | Identify holdings and allocations from an image        | Yes              |
| NFT Grid Analysis     | Identify collection and rarity tier from a grid       | Yes              |
| Contract Parsing      | Summarize a Solidity / Vyper / Move source file       | Yes              |
| Whitepaper Analysis   | Summarize a project whitepaper or audit report        | Yes              |
| Transaction Decode    | Identify patterns, extract transfers, score risk      | No               |
| Cross-Chain Tracking  | Aggregate balance across both Pharos networks          | No               |
| NLP → Action          | Parse free-form text into a structured onchain action  | Yes              |

## Supported Framework

**Pharos Agent Center** — Skill Builder Campaign
(`https://silken-muskox-24e.notion.site/pharos-agent-center-skill-builder-campaign`)

## License

MIT License — see [`LICENSE`](./LICENSE).
