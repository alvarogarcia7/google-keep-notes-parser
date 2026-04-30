#!/usr/bin/env python3
"""
NATS Router for Google Keep Notes
Routes messages to type-specific topics based on content
"""

import asyncio
import json
import os
import sys
import uuid

import nats

from parsers.base import ParserRegistry
from parsers.hackernews_parser import HackerNewsParser
from parsers.time_entry_parser import TimeEntryParser
from parsers.training_parser import TrainingParser
from parsers.next_parser import NextParser
from parsers.generic_notes_parser import GenericNotesParser

NATS_URL = os.environ.get("NATS_URL", "nats://docker:4222")
INPUT_TOPIC = "messages.10.raw"

TYPE_TO_TOPIC = {
    "training": "messages.20.type.training",
    "toggl": "messages.20.type.toggl",
    "next": "messages.20.type.next",
    "hackernews": "messages.20.type.hn",
}

PARSER_TO_TYPE = {
    TrainingParser: "training",
    TimeEntryParser: "toggl",
    NextParser: "next",
    HackerNewsParser: "hackernews",
}


def setup_registry():
    """Create and setup parser registry."""
    registry = ParserRegistry()
    registry.register(HackerNewsParser)
    registry.register(TimeEntryParser)
    registry.register(TrainingParser)
    registry.register(NextParser)
    registry.register(GenericNotesParser)
    return registry


async def route_message(message_data: dict, nc, registry):
    """Route a message to the appropriate topic based on type."""
    note = message_data.get("note", {})

    for parser_class in registry.get_all_parsers():
        parser = parser_class()
        if parser.can_parse(note):
            note_type = PARSER_TO_TYPE.get(parser_class)
            if not note_type:
                print(f"⚠ No topic mapping for {parser_class.__name__}")
                return

            topic = TYPE_TO_TOPIC.get(note_type)
            if not topic:
                print(f"⚠ No topic configured for type '{note_type}'")
                return

            routed_message = {
                "id": message_data.get("id", str(uuid.uuid4())),
                "type": note_type,
                "note": note
            }

            await nc.publish(topic, json.dumps(routed_message).encode())
            print(f"✓ Routed to '{note_type}' ({topic}): {note.get('title', 'Untitled')}")
            return

    print(f"⚠ No parser found for note: {note.get('title', 'Untitled')}")


async def main():
    """Subscribe to messages.10.raw and route to type-specific topics."""
    registry = setup_registry()

    nc = None
    for attempt in range(5):
        try:
            nc = await nats.connect(NATS_URL, connect_timeout=2)
            break
        except Exception as e:
            if attempt < 4:
                print(f"Connection attempt {attempt + 1}/5 failed, retrying in 1s...")
                await asyncio.sleep(1)
            else:
                print(f"Error: Could not connect to NATS at {NATS_URL} after 5 attempts")
                print(f"Make sure NATS server is running: {e}")
                sys.exit(1)

    if not nc:
        print(f"Error: NATS connection failed")
        sys.exit(1)

    print(f"🔄 Router started, listening on '{INPUT_TOPIC}'...")

    async def handler(msg):
        try:
            message_data = json.loads(msg.data.decode())
            await route_message(message_data, nc, registry)
        except json.JSONDecodeError as e:
            print(f"✗ Failed to decode message: {e}")
        except Exception as e:
            print(f"✗ Error processing message: {e}")

    await nc.subscribe(INPUT_TOPIC, cb=handler)
    await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Router stopped")
