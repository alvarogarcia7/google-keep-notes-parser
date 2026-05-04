#!/usr/bin/env python3
"""
NATS Publisher for Google Keep Notes
Reads notes from a directory and publishes to NATS
"""

import asyncio
import json
import os
import ssl
import sys
import uuid
import click
from pathlib import Path

import nats
from date_extractor import format_message_with_date

NATS_URL = os.environ.get("NATS_URL")
if not NATS_URL:
    print("Error: NATS_URL environment variable not set")
    sys.exit(1)
CERTS_DIR = os.environ.get("CERTS_DIR", "/tmp/nats-certs")
TOPIC = "messages.10.raw.type.googlenotes"


def _make_ssl_ctx() -> ssl.SSLContext:
    """Create SSL context with client certificate for mTLS."""
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=f"{CERTS_DIR}/rootCA.pem")
    ctx.load_cert_chain(
        certfile=f"{CERTS_DIR}/client.pem",
        keyfile=f"{CERTS_DIR}/client.key"
    )
    return ctx


async def _connect_with_retry(url: str) -> nats.aio.client.Client:
    """Connect to NATS with retry logic and TLS."""
    ssl_ctx = _make_ssl_ctx()
    for attempt in range(5):
        try:
            return await nats.connect(url, tls=ssl_ctx, connect_timeout=2)
        except Exception as e:
            if attempt < 4:
                print(f"Connection attempt {attempt + 1}/5 failed, retrying in 1s...")
                await asyncio.sleep(1)
            else:
                print(f"Error: Could not connect to NATS at {url} after 5 attempts")
                print(f"Make sure NATS server is running: {e}")
                sys.exit(1)


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

    nc = await _connect_with_retry(NATS_URL)

    try:
        for json_file in json_files:
            with open(json_file) as f:
                note_data = json.load(f)

            message = {
                "id": str(uuid.uuid4()),
                "note": note_data
            }

            # Add date field (with title override support)
            message = format_message_with_date(message, note_data)

            message_json = json.dumps(message)
            await nc.publish(TOPIC, message_json.encode())
            date_str = f" (date: {message['date']})" if message.get('date') else ""
            print(f"✓ Published {json_file.name} (note_id: {note_data.get('id', 'unknown')}){date_str}")
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
