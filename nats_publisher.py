#!/usr/bin/env python3
"""
NATS Publisher for Google Keep Notes Parser
Reads sample training data and publishes to NATS
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import nats


async def main():
    """Publish sample training data to NATS."""
    # Read sample1.json
    sample_file = Path(__file__).parent / "sample/training/sample1.json"

    if not sample_file.exists():
        print(f"Error: Sample file not found at {sample_file}")
        sys.exit(1)

    with open(sample_file) as f:
        data = json.load(f)

    # Connect to NATS
    try:
        nc = await nats.connect("nats://localhost:4222")
    except Exception as e:
        print(f"Error: Could not connect to NATS at localhost:4222")
        print(f"Make sure NATS server is running: {e}")
        sys.exit(1)

    # Publish the data as JSON string
    message = json.dumps(data)
    print(f"Publishing message: {json.dumps(data, indent=2)}")

    await nc.publish("training.notes", message.encode())
    print(f"✓ Published to topic 'training.notes'")

    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
