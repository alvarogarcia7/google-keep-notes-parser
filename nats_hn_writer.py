#!/usr/bin/env python3
"""
HackerNews Writer - saves messages.30.type.hn.10.parsed to disk
Writes each parsed HackerNews message to a JSON file for storage and audit
"""

import asyncio
import json
import os
import ssl
import sys
import uuid
from datetime import datetime
from pathlib import Path

import nats

NATS_URL = os.environ.get("NATS_URL")
if not NATS_URL:
    print("Error: NATS_URL environment variable not set")
    sys.exit(1)

CERTS_DIR = os.environ.get("CERTS_DIR", "/tmp/nats-certs")
INPUT_TOPIC = "messages.30.type.hn.10.parsed"
OUTPUT_DIR = Path("/tmp/nats/messages.30.type.hn.10.parsed")


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


async def write_hackernews_message(input_msg: dict) -> None:
    """Write HackerNews parsed message to file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use message ID or generate a new one
    msg_id = input_msg.get("id", str(uuid.uuid4()))
    note_id = input_msg.get("note_id", "unknown")
    item_id = input_msg.get("parsed", {}).get("item_id", "unknown")

    # Create filename: timestamp_itemid_messageid.json
    timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
    filename = f"{timestamp}_{item_id}_{msg_id[:8]}.json"
    filepath = OUTPUT_DIR / filename

    try:
        with open(filepath, "w") as f:
            json.dump(input_msg, f, indent=2)

        title = input_msg.get("parsed", {}).get("title", "Untitled")[:60]
        print(f"✓ Saved HackerNews item #{item_id}")
        print(f"  Title: {title}...")
        print(f"  File: {filepath}")
    except Exception as e:
        print(f"✗ Failed to write message to {filepath}: {e}")


async def main() -> None:
    """Subscribe to messages.30.type.hn.10.parsed and write to disk."""
    nc = await _connect_with_retry(NATS_URL)

    print(f"📝 HackerNews Writer started")
    print(f"  Input topic:  {INPUT_TOPIC}")
    print(f"  Output dir:   {OUTPUT_DIR}")

    try:
        async def handler(msg):
            try:
                message_data = json.loads(msg.data.decode())
                await write_hackernews_message(message_data)
            except json.JSONDecodeError as e:
                print(f"✗ Failed to decode message: {e}")
            except Exception as e:
                print(f"✗ Error processing message: {e}")

        await nc.subscribe(INPUT_TOPIC, cb=handler)
        await asyncio.Future()  # run forever

    except KeyboardInterrupt:
        print("\n✓ Writer stopped")
    finally:
        await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
