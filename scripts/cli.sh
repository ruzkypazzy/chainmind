#!/bin/bash
# chainmind CLI runner — calls the python main.py with sane defaults.
# Usage:
#   bash scripts/cli.sh tx <TX_HASH> [--chain pacific_mainnet|atlantic_testnet]
#   bash scripts/cli.sh wallet <ADDRESS>
#   bash scripts/cli.sh demo    # runs against a real public mainnet tx

set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/.."

CMD="${1:-}"
shift || true

case "$CMD" in
  tx)
    python3 src/main.py --task analyze_transaction --tx "$@"
    ;;
  wallet)
    python3 src/main.py --task track_wallet --address "$@"
    ;;
  demo)
    python3 src/main.py --task analyze_transaction \
      --tx 0x9606bcfd027b28e6783ca8b5fef1c3311476a1c30e5bf4464d0340a0d24ba7f7 \
      --chain pacific_mainnet
    echo ""
    echo "----- Cross-chain wallet tracker -----"
    python3 src/main.py --task track_wallet \
      --address 0x67992af9a87f2d6a3062c333d8a06abbe3929438
    ;;
  *)
    echo "Usage: bash scripts/cli.sh {tx|wallet|demo} [args...]"
    exit 1
    ;;
esac
