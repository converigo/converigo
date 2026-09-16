#!/usr/bin/env bash
# Run the spike directly on a Linux host that already has LibreOffice installed
# (no Docker needed). Results are host-specific but cover G1, G3-G5 behaviour.
set -euo pipefail
cd "$(dirname "$0")"
command -v soffice >/dev/null 2>&1 || { echo "soffice not found; install libreoffice-calc"; exit 3; }
soffice --version
python3 lo_spike.py --fixtures ../fixtures --conc "${CONC:-4,8}" "$@"
