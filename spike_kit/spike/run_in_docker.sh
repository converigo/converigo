#!/usr/bin/env bash
# Build a container whose LibreOffice install matches the production Dockerfile
# and run the throwaway XLS->XLSX spike inside it. Nothing in the repository is
# touched; artifacts land next to this script.
set -euo pipefail
cd "$(dirname "$0")/.."           # spike_kit

IMG=converigo-lo-spike:prep
docker build -f spike/Dockerfile.spike -t "$IMG" .
# --fixtures/--out are absolute because inside the image lo_spike.py sits at
# /spike/lo_spike.py, so its relative defaults (/fixtures, /spike) miss the
# COPY'd fixtures and the /out mount that carries the report back to the host.
docker run --rm -v "$PWD/spike:/out" "$IMG" \
    python3 /spike/lo_spike.py --fixtures /spike/fixtures --out /out "$@"
chmod -R a+r spike/spike_report.* 2>/dev/null || true
echo "report: spike/spike_report.md"
