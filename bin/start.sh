#!/bin/bash
# Start Google Keep publisher
set -e

PARSER_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$PARSER_ROOT/.." && pwd)"

# Load environment from parent .env if it exists
if [ -f "$REPO_ROOT/.env" ]; then
    export $(grep -v '^#' "$REPO_ROOT/.env" | xargs)
fi

# Set defaults if not already set
export NATS_URL="${NATS_URL:-tls://docker:4222}"
export CERTS_DIR="${CERTS_DIR:-$REPO_ROOT/nats/certs}"

# Activate virtual environment if it exists
if [ -f "$PARSER_ROOT/.venv/bin/activate" ]; then
    source "$PARSER_ROOT/.venv/bin/activate"
fi

# Change to parser directory
cd "$PARSER_ROOT"

# Start publisher
python3 nats_publisher.py &
PUBLISHER_PID=$!
echo "[google-keep-publisher] Publisher started (PID: $PUBLISHER_PID)"

# Wait for process
wait $PUBLISHER_PID
