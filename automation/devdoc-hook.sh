#!/bin/bash
# DevDoc Git Hook — Run automatically on commits
#
# Install: cp devdoc-hook.sh <project>/.git/hooks/post-commit && chmod +x <project>/.git/hooks/post-commit
# Or:      cd <project> && ln -sf ../../automation/devdoc-hook.sh .git/hooks/post-commit
#
# This hook runs DevDoc analysis after each commit and saves a snapshot
# for continuous trend tracking. Runs silently in the background.

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
DEVDOC_SCRIPTS="${HOME}/.withai/abilities/devdoc/codebase-analyzer/scripts"
SNAPSHOT_DIR="${PROJECT_ROOT}/.devdoc/snapshots"
OUTPUT_DIR="${PROJECT_ROOT}/.devdoc/latest"
COMMIT_HASH="$(git rev-parse --short HEAD)"
COMMIT_MSG="$(git log -1 --pretty=%s)"

# Only run if DevDoc is installed
if [ ! -f "${DEVDOC_SCRIPTS}/analyze.py" ]; then
    exit 0
fi

mkdir -p "${OUTPUT_DIR}" "${SNAPSHOT_DIR}"

echo "[DevDoc] Running post-commit analysis..."

# Run core analysis
python3 "${DEVDOC_SCRIPTS}/analyze.py" "${PROJECT_ROOT}" \
    --output "${OUTPUT_DIR}/analysis.json" 2>/dev/null

# Run security scan
python3 "${DEVDOC_SCRIPTS}/security_scanner.py" "${PROJECT_ROOT}" \
    --output "${OUTPUT_DIR}/security.json" 2>/dev/null

# Run AI governance check
python3 "${DEVDOC_SCRIPTS}/ai_governance.py" "${PROJECT_ROOT}" \
    --analysis "${OUTPUT_DIR}/analysis.json" \
    --output "${OUTPUT_DIR}/governance.json" 2>/dev/null

# Save snapshot with commit label
python3 "${DEVDOC_SCRIPTS}/snapshot_manager.py" save "${OUTPUT_DIR}/analysis.json" \
    --project-dir "${PROJECT_ROOT}" \
    --label "${COMMIT_HASH}" 2>/dev/null

# Check for regressions against previous snapshot
SNAPSHOT_COUNT=$(ls "${SNAPSHOT_DIR}"/snapshot_*.json 2>/dev/null | wc -l)
if [ "${SNAPSHOT_COUNT}" -ge 2 ]; then
    DIFF_OUTPUT=$(python3 "${DEVDOC_SCRIPTS}/snapshot_manager.py" diff \
        --project-dir "${PROJECT_ROOT}" 2>/dev/null)

    # Check if regression detected
    if echo "${DIFF_OUTPUT}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('regression_detected'):
    regs = data.get('regressions', [])
    print(f'[DevDoc] ⚠️  {len(regs)} regression(s) detected:')
    for r in regs:
        print(f'  - [{r[\"severity\"]}] {r[\"message\"]}')
    sys.exit(1)
" 2>/dev/null; then
        : # No regression
    fi
fi

echo "[DevDoc] Analysis complete for commit ${COMMIT_HASH}."
