#!/usr/bin/env python3
"""
Demo: HackerNews Data Pipeline
Shows how data transforms from Google Keep note to parsed HackerNews message
"""

import json
import uuid
import sys
from pathlib import Path

# Add parser path
_parser_path = Path(__file__).parent / "parsers"
if str(_parser_path) not in sys.path:
    sys.path.insert(0, str(_parser_path))

from hackernews_parser import HackerNewsParser

def demo():
    """Demonstrate the HackerNews data pipeline."""

    # Load sample
    sample_file = Path(__file__).parent / "sample/hn/1.json"
    with open(sample_file) as f:
        note = json.load(f)

    print("=" * 80)
    print("HACKERNEWS DATA PIPELINE DEMONSTRATION")
    print("=" * 80)

    # =========================================================================
    # STAGE 1: Publisher Input (messages.10.raw.type.googlenotes)
    # =========================================================================
    print("\n📥 STAGE 1: Publisher Input")
    print("-" * 80)
    print("Topic: messages.10.raw.type.googlenotes")
    print("Source: Google Keep Note (sample/hn/1.json)")

    stage1_msg = {
        "id": str(uuid.uuid4()),
        "note": note,
        "date": "2026-01-15"
    }

    print("\nMessage sent to messages.10.raw.type.googlenotes:")
    print(json.dumps(stage1_msg, indent=2))

    # =========================================================================
    # STAGE 2: Router Detection (messages.10.raw.type.googlenotes)
    # =========================================================================
    print("\n" + "=" * 80)
    print("🔀 STAGE 2: Router Detection")
    print("-" * 80)

    # Check if HackerNews
    parser = HackerNewsParser()
    is_hn = parser.can_parse(note)

    print(f"Analyzing note: '{note.get('title', 'Untitled')}'")
    print(f"Has 'Download-HN' label: {'Download-HN' in note.get('labels', [])}")
    print(f"Has HackerNews URL: {bool(parser.can_parse(note))}")
    print(f"Detection result: {'✓ HackerNews' if is_hn else '✗ Generic Google Note'}")

    # =========================================================================
    # STAGE 3: Router Output (messages.20.hn)
    # =========================================================================
    print("\n" + "=" * 80)
    print("📤 STAGE 3: Router Output")
    print("-" * 80)
    print("Topic: messages.20.hn")

    stage3_msg = {
        "id": stage1_msg["id"],
        "message_type": "hackernews",
        "note": {
            "id": note.get("id", str(uuid.uuid4())),
            "title": note.get("title", "Untitled"),
            "text": note.get("text"),
            "url": note.get("url"),
            "date": stage1_msg.get("date"),
        },
        "source": "google-keep"
    }

    print("\nMessage sent to messages.20.hn:")
    print(json.dumps(stage3_msg, indent=2))

    # =========================================================================
    # STAGE 4: Parser Extraction (messages.20.hn → messages.30.type.hn.10.parsed)
    # =========================================================================
    print("\n" + "=" * 80)
    print("🔧 STAGE 4: HackerNews Parser")
    print("-" * 80)
    print("Parsing HackerNews data from messages.20.hn...")

    try:
        parsed_data = parser.parse(note)

        print(f"\n✓ Successfully parsed HackerNews note")
        print(f"  Title: {parsed_data.title}")
        print(f"  Item ID: {parsed_data.item_id}")
        print(f"  URL: {parsed_data.url}")
        print(f"  Labels: {', '.join(parsed_data.labels)}")
        print(f"  HN Links found: {len(parsed_data.hn_links)}")

        # =====================================================================
        # STAGE 5: Final Output (messages.30.type.hn.10.parsed)
        # =====================================================================
        print("\n" + "=" * 80)
        print("✅ STAGE 5: Final Output")
        print("-" * 80)
        print("Topic: messages.30.type.hn.10.parsed")

        stage5_msg = {
            "id": stage1_msg["id"],
            "message_id": stage1_msg["id"],
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
            "source": "google-keep",
            "date": stage1_msg.get("date")
        }

        print("\nFinal message sent to messages.30.type.hn.10.parsed:")
        print(json.dumps(stage5_msg, indent=2))

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "=" * 80)
        print("📊 PIPELINE SUMMARY")
        print("-" * 80)
        print(f"Input:     Google Keep Note ({note.get('id')})")
        print(f"Stage 1:   messages.10.raw.type.googlenotes ✓")
        print(f"Stage 2:   Router detects HackerNews ✓")
        print(f"Stage 3:   messages.20.hn ✓")
        print(f"Stage 4:   HackerNews Parser ✓")
        print(f"Stage 5:   messages.30.type.hn.10.parsed ✓")
        print(f"\nResult: HackerNews item #{parsed_data.item_id} ready for processing")
        print("=" * 80)

    except Exception as e:
        print(f"✗ Error parsing HackerNews note: {e}")
        sys.exit(1)


if __name__ == "__main__":
    demo()
