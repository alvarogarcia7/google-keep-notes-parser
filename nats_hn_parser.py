#!/usr/bin/env python3
"""
HackerNews Parser - transforms messages.20.hn to messages.30.type.hn.10.parsed
Extracts and structures HackerNews data for downstream processing
"""

import asyncio
import json
import os
import re
import ssl
import sys
import uuid
from pathlib import Path

import nats

# Add parser path
_repo_root = Path(__file__).parent
_parser_path = _repo_root / "parsers"
if str(_parser_path) not in sys.path:
    sys.path.insert(0, str(_parser_path))

try:
    from hackernews_parser import HackerNewsParser
except ImportError as e:
    print(f"Error: Could not import HackerNewsParser: {e}")
    sys.exit(1)

NATS_URL = os.environ.get("NATS_URL")
if not NATS_URL:
    print("Error: NATS_URL environment variable not set")
    sys.exit(1)

CERTS_DIR = os.environ.get("CERTS_DIR", "/tmp/nats-certs")
INPUT_TOPIC = "messages.20.hn"
OUTPUT_TOPIC = "messages.30.type.hn.10.parsed"


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


async def parse_hackernews_message(input_msg: dict, client: nats.aio.client.Client) -> None:
    """Parse HackerNews message and publish to messages.30.type.hn.10.parsed."""
    original_note = input_msg.get("note", {})

    # Use HackerNewsParser to extract data
    parser = HackerNewsParser()
    try:
        parsed_data = parser.parse(original_note)
    except Exception as e:
        print(f"✗ Failed to parse HackerNews note: {e}")
        return

    # Create parsed message
    parsed_message = {
        "id": input_msg.get("id", str(uuid.uuid4())),
        "message_id": input_msg.get("id"),
        "note_id": parsed_data.note_id,
        "type": "hackernews",
        "parsed": {
            "title": parsed_data.title,
            "item_id": parsed_data.item_id,
            "url": parsed_data.url,
            "description": parsed_data.description,
            "labels": parsed_data.labels,
            "hn_links": [
                {
                    "url": link.url,
                    "item_id": link.item_id
                }
                for link in parsed_data.hn_links
            ]
        },
        "source": input_msg.get("source", "unknown"),
        "date": input_msg.get("date")
    }

    await client.publish(OUTPUT_TOPIC, json.dumps(parsed_message).encode())
    print(f"✓ Parsed and published to messages.30.type.hn.10.parsed: {parsed_data.title}")
    print(f"  Item ID: {parsed_data.item_id}")
    print(f"  Labels: {', '.join(parsed_data.labels)}")


async def main() -> None:
    """Subscribe to messages.20.hn and publish parsed results to messages.30.type.hn.10.parsed."""
    nc = await _connect_with_retry(NATS_URL)

    print(f"🔄 HackerNews Parser started")
    print(f"  Input topic:  {INPUT_TOPIC}")
    print(f"  Output topic: {OUTPUT_TOPIC}")

    try:
        async def handler(msg):
            try:
                message_data = json.loads(msg.data.decode())
                await parse_hackernews_message(message_data, nc)
            except json.JSONDecodeError as e:
                print(f"✗ Failed to decode message: {e}")
            except Exception as e:
                print(f"✗ Error processing message: {e}")

        await nc.subscribe(INPUT_TOPIC, cb=handler)
        await asyncio.Future()  # run forever

    except KeyboardInterrupt:
        print("\n✓ Parser stopped")
    finally:
        await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
