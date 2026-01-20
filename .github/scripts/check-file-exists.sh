#!/bin/bash
# Check if a file exists and emit GitHub Actions error annotation if not
# Usage: check-file-exists.sh <filepath> <description>

set -euo pipefail

FILEPATH="${1:-}"
DESCRIPTION="${2:-file}"

if [ -z "$FILEPATH" ]; then
    echo "::error::Usage: check-file-exists.sh <filepath> <description>"
    exit 1
fi

if [ ! -f "$FILEPATH" ]; then
    echo "::error file=${FILEPATH}::${DESCRIPTION} not found at expected path: ${FILEPATH}"
    echo "❌ ${DESCRIPTION} not found: ${FILEPATH}"
    exit 1
fi

echo "✅ ${DESCRIPTION} found: ${FILEPATH}"
exit 0
