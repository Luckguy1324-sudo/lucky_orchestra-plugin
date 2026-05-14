#!/usr/bin/env bash
# orchestra-init.sh — initialize a new orchestra run directory
#
# Usage: orchestra-init.sh <slug>
#   <slug>: short kebab-case identifier for this run (no spaces)
#
# Output: echoes the absolute path to the new run directory
#
# Side effects:
#   - Creates <cwd>/.orchestra/runs/<run-id>/{,_tmp,03-research}
#   - Writes meta.json with initial state

set -euo pipefail

SLUG="${1:-untitled}"
SLUG=$(printf '%s' "$SLUG" | tr ' ' '-' | tr -c '[:alnum:]-' '-' | tr -s '-' | sed 's/^-//;s/-$//')
SLUG="${SLUG:-untitled}"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RUN_ID="${TIMESTAMP}-${SLUG}"

CWD=$(pwd)
RUN_DIR="${CWD}/.orchestra/runs/${RUN_ID}"

mkdir -p "${RUN_DIR}/_tmp" "${RUN_DIR}/_refs" "${RUN_DIR}/03-research"

# meta.json — initial state
cat > "${RUN_DIR}/meta.json" <<EOF
{
  "run_id": "${RUN_ID}",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "current_stage": "1-brief",
  "round": 1,
  "verdict_history": []
}
EOF

# .gitignore — keep raw responses out of git by default
cat > "${RUN_DIR}/.gitignore" <<'EOF'
_tmp/
EOF

# Echo the path so caller can capture
echo "${RUN_DIR}"
