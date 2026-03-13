#!/usr/bin/env python3
"""
Demo script for the NEXT note parser.
Shows how to parse a NEXT note and output it in both text and org modes.
"""

from parsers.next_parser import NextParser


def demo() -> None:
    parser = NextParser()

    # Example NEXT note from the requirements
    example_note = {
        "id": "next_example_123",
        "title": "Next",
        "text": """Next

Project TCMS

- [ ] Achieve a doctor build that is off-line

- [ ] Download said images

- [ ] Upload them to FMA

- [ ] Get approval

Project admin

- [ ] Upload all hourly reports for boss

- [ ] Upload expenses for Claude

Project projector

- [ ] Configure project for TRM""",
        "timestamps": {
            "created": "2026-03-13T10:30:45",
            "edited": "2026-03-13T10:30:45"
        }
    }

    # Parse the note
    parsed = parser.parse(example_note)

    # Print in text mode
    print("=" * 60)
    print("TEXT MODE OUTPUT")
    print("=" * 60)
    print(parser.format_as_text(parsed))

    # Print in org mode
    print("\n" + "=" * 60)
    print("ORG MODE OUTPUT")
    print("=" * 60)
    print(parser.format_as_org(parsed))

    # Print raw parsed data
    print("\n" + "=" * 60)
    print("RAW PARSED DATA (JSON)")
    print("=" * 60)
    import json
    from dataclasses import asdict
    print(json.dumps(asdict(parsed), indent=2))


if __name__ == "__main__":
    demo()
