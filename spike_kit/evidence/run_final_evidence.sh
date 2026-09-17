#!/usr/bin/env bash
# CONVERIGO - XLS->XLSX final evidence runner (one controlled CI iteration).
#
# Runs the evidence probe INSIDE THE PRODUCTION IMAGE under the exact Railway
# production envelope:
#       --memory 1000000000   (1,000,000,000 B, the Railway memory limit)
#       --pids-limit 1000     (the Railway pidLimit)
# so every G4/G6 number is measured against the real cap, not an uncapped host.
#
# Scope: CI/evidence harness only. No application source, plugin, contract,
# registry, ALLOWED_EXTENSIONS, ACCEPTED_BOF_VERSIONS or converter JSON is
# touched. The 21.8 MB bulk fixture is used for CI evidence ONLY and never
# enters the application runtime.
set -euo pipefail
cd "$(dirname "$0")/../.."                 # repo root

IMG=converigo-evidence:prod
OUT=spike_kit/evidence/out
PROBE=/app/spike_kit/evidence/lo_evidence.py
FIX=/app/spike_kit/evidence_fixtures          # in-image (COPY . .)
mkdir -p "$OUT"

# ---- 1. production image (the same Dockerfile the app ships: verifies soffice
#         is really the production LibreOffice, not a spike-only substitute)
docker build -t "$IMG" .

# ---- 2. envelope verification (fail loudly if the cap is not what we claim)
docker run --rm --memory 1000000000 --pids-limit 1000 \
  -v "$PWD/$OUT:/out" \
  --entrypoint python3 "$IMG" "$PROBE" \
  --phase env --out /out --fixtures "$FIX"

# ---- 3. G6 single-conversion envelope (sample / stress / bulk)
docker run --rm --memory 1000000000 --pids-limit 1000 \
  -v "$PWD/$OUT:/out" \
  --entrypoint python3 "$IMG" "$PROBE" \
  --phase single --out /out --fixtures "$FIX"

# ---- 4. G6 concurrency at the requested worker counts (default 2,4,8)
# Each container writes evidence_conc.json; preserve a per-N copy so the
# artifact holds the full 1/2/4/8 series instead of only the last run.
for N in ${CONC:-2 4 8}; do
  docker run --rm --memory 1000000000 --pids-limit 1000 \
    -v "$PWD/$OUT:/out" \
    --entrypoint python3 "$IMG" "$PROBE" \
    --phase conc --conc "$N" --out /out --fixtures "$FIX"
  mv "$OUT/evidence_conc.json" "$OUT/evidence_conc_${N}.json"
done

# ---- 5. G4 containment: forced termination against real soffice
docker run --rm --memory 1000000000 --pids-limit 1000 \
  -v "$PWD/$OUT:/out" \
  --entrypoint python3 "$IMG" "$PROBE" \
  --phase g4 --out /out --fixtures "$FIX"

# ---- 6. BIFF5 decision evidence (genuine BIFF5 / BIFF7 / 0x0550 / malformed)
docker run --rm --memory 1000000000 --pids-limit 1000 \
  -v "$PWD/$OUT:/out" \
  --entrypoint python3 "$IMG" "$PROBE" \
  --phase biff5 --out /out --fixtures "$FIX"

chmod -R a+r "$OUT" 2>/dev/null || true
echo "evidence JSON: $OUT/evidence_*.json"

