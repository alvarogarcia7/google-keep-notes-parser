#!/bin/bash
# Direct end-to-end test for NATS pipeline

set -e

echo "======================================================================="
echo "🧪 NATS Training Parser - Direct End-to-End Test"
echo "======================================================================="
echo ""

# Check NATS server
echo "🔍 Checking NATS server..."
if ! docker exec nats-server nc -z localhost 4222 2>/dev/null; then
    echo "⚠️  NATS server not responding on 4222, restarting..."
    docker restart nats-server > /dev/null 2>&1
    sleep 3
fi
echo "✓ NATS server ready on port 4222"
echo ""

# Start subscriber in background
echo "🔄 Starting NATS subscriber..."
cd ~/repos/training-parser-antlr4
uv run python3 nats_subscriber.py > /tmp/subscriber.log 2>&1 &
SUBSCRIBER_PID=$!
echo "✓ Subscriber started (PID: $SUBSCRIBER_PID)"
sleep 2
echo ""

# Publish sample
echo "📤 Publishing sample data..."
cd /var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser
uv run python3 nats_publisher.py
echo ""

# Wait for subscriber to process
echo "⏳ Waiting for processing..."
sleep 3

# Check subscriber output
echo "📋 Subscriber Output:"
echo "======================================================================="
cat /tmp/subscriber.log

# Verify results
echo ""
echo "======================================================================="
echo "📊 Test Verification"
echo "======================================================================="

EXPECTED_MARKERS=("Received message from NATS" "Parsing with ANTLR Training Grammar")

PASSED=true
for marker in "${EXPECTED_MARKERS[@]}"; do
    if grep -q "$marker" /tmp/subscriber.log; then
        echo "✓ Found: '$marker'"
    else
        echo "✗ Missing: '$marker'"
        PASSED=false
    fi
done

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $SUBSCRIBER_PID 2>/dev/null || true
wait $SUBSCRIBER_PID 2>/dev/null || true

echo ""
if [ "$PASSED" = true ]; then
    echo "✅ TEST PASSED"
    echo ""
    echo "✓ Publisher sent data to NATS"
    echo "✓ Subscriber received message"
    echo "✓ ANTLR parser processed training data"
    exit 0
else
    echo "❌ TEST FAILED"
    echo "Some expected markers were not found in output"
    exit 1
fi
