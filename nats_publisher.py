#!/usr/bin/env python3
"""
NATS Publisher for Google Keep Notes
Reads notes from a directory and publishes to NATS
"""

import asyncio
import json
import os
import sys
import uuid
import click
from pathlib import Path

import nats

NATS_URL = os.environ.get("NATS_URL", "nats://localhost:4222")
TOPIC = "messages.10.raw"


async def publish_notes(input_dir: str):
    """Publish all JSON notes from a directory to NATS."""
    input_path = Path(input_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    json_files = sorted(input_path.glob("**/*.json"))
    if not json_files:
        print(f"Error: No JSON files found in '{input_dir}'")
        sys.exit(1)

    print(f"Found {len(json_files)} note(s) to publish")

    try:
        nc = await nats.connect(NATS_URL)
    except Exception as e:
        print(f"Error: Could not connect to NATS at {NATS_URL}")
        print(f"Make sure NATS server is running: {e}")
        sys.exit(1)

    try:
        for json_file in json_files:
            with open(json_file) as f:
                note_data = json.load(f)

            message = {
                "id": str(uuid.uuid4()),
                "note": note_data
            }

            message_json = json.dumps(message)
            await nc.publish(TOPIC, message_json.encode())
            print(f"✓ Published {json_file.name} (note_id: {note_data.get('id', 'unknown')})")
    finally:
        await nc.close()

    print(f"✓ All {len(json_files)} note(s) published to '{TOPIC}'")


@click.command()
@click.option('--input-dir', default='sample', help='Input directory containing JSON note files')
def main(input_dir: str):
    """Publish Google Keep notes from a directory to NATS."""
    asyncio.run(publish_notes(input_dir))


if __name__ == "__main__":
    main()
