# ChainMind - Multi-Modal Onchain Intelligence

Multi-modal intelligence combining visual analysis, document parsing, transaction pattern recognition, cross-chain correlation, and natural language to onchain actions.

## Supported Chains

Ethereum | Polygon | Arbitrum | Base | Optimism | Solana | **Pharos Pacific** | **Pharos Atlantic**

## Overview

ChainMind is a comprehensive onchain intelligence skill designed for AI agents to understand and interact with blockchain data through multiple modalities:

- **Visual Analysis**: Analyze charts, NFTs, and portfolio images
- **Document Intelligence**: Parse smart contracts, whitepapers, and audits
- **Transaction Analysis**: Pattern recognition and MEV detection
- **Cross-Chain Correlation**: Track wallets across multiple chains
- **NLP Actions**: Convert natural language to onchain actions

## Quick Start

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_api_key
python src/main.py --task "Analyze wallet" --address 0x...
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ruzkypazzy/chainmind.git
cd chainmind
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your API key:
```bash
export OPENAI_API_KEY=your_openai_api_key
```

## Usage Examples

### Vision Analysis
```bash
python src/main.py --task "analyze image" --image chart.png
```

### Document Parsing
```bash
python src/main.py --task "parse document" --document contract.pdf
```

### Transaction Analysis
```bash
python src/main.py --task "analyze transaction" --tx 0x... --chain ethereum
```

### Wallet Tracking
```bash
python src/main.py --task "track wallet" --address 0x...
```

### NLP to Action
```bash
python src/main.py --task "convert to action" --text "swap 1 ETH for USDC"
```

## Capabilities

| Capability | Description |
|------------|-------------|
| Visual Chart Analysis | GPT-4 Vision powered chart and graph analysis |
| NFT Recognition | Identify and analyze NFT collections |
| Contract Parsing | Extract key information from smart contracts |
| Whitepaper Analysis | Summarize and extract insights from whitepapers |
| Transaction Pattern | Detect trading patterns and anomalies |
| MEV Detection | Identify potential MEV opportunities |
| Multi-Chain Tracking | Correlate wallet activity across chains |
| NLP Action Conversion | Convert natural language to actionable onchain tasks |

## Dependencies

- openai >= 1.0.0
- langchain >= 0.1.0
- langchain-openai >= 0.0.5
- viem >= 2.0.0
- python-dotenv >= 1.0.0
- pyyaml >= 6.0
- requests >= 2.31.0
- pillow >= 10.0.0
- numpy >= 1.24.0
- pandas >= 2.0.0

## Supported Framework

**Pharos Agent Kit** - Pharos Agent Centre Skill Builder Campaign

## License

MIT License
