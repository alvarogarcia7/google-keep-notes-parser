#!/usr/bin/env python3
"""
Integration tests for publisher with date extraction.
Tests the actual message format that will be sent to NATS.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from date_extractor import format_message_with_date


class TestPublisherIntegration:
    """Integration tests for publisher message format."""

    def test_message_format_with_title_date(self):
        """Test complete message format with date extracted from title."""
        note_data = {
            "id": "note-123",
            "title": "Team Meeting 15/05",
            "content": "Discussed Q2 planning",
            "created": "2026-05-02T10:30:00Z"
        }

        message = {
            "id": "msg-uuid-123",
            "note": note_data
        }

        result = format_message_with_date(message, note_data)

        # Verify message structure
        assert "id" in result
        assert "note" in result
        assert "date" in result

        # Verify date is from title, not creation date
        assert result["date"] == "2026-05-15"

        # Verify note data is preserved
        assert result["note"]["title"] == "Team Meeting 15/05"
        assert result["note"]["content"] == "Discussed Q2 planning"

    def test_message_format_with_creation_date(self):
        """Test complete message format with creation date fallback."""
        note_data = {
            "id": "note-456",
            "title": "Regular Meeting Notes",
            "content": "Discussed roadmap",
            "created": "2026-05-02T14:30:00Z"
        }

        message = {
            "id": "msg-uuid-456",
            "note": note_data
        }

        result = format_message_with_date(message, note_data)

        # Verify date from creation date
        assert result["date"] == "2026-05-02"

    def test_message_format_apple_notes_with_source(self):
        """Test Apple Notes message format with source field."""
        note_data = {
            "id": "apple-note-789",
            "title": "Project Update 20/05",
            "content": "Progress on new features",
            "created": "2026-05-02T09:00:00Z"
        }

        message = {
            "id": "msg-uuid-789",
            "source": "apple-notes",
            "filename": "note-789.json",
            "note": note_data
        }

        result = format_message_with_date(message, note_data)

        # Verify Apple Notes specific fields
        assert result["source"] == "apple-notes"
        assert result["filename"] == "note-789.json"

        # Verify date from title
        assert result["date"] == "2026-05-20"

    def test_json_serialization(self):
        """Test that resulting message is JSON serializable."""
        note_data = {
            "id": "note-999",
            "title": "Notes 25/05",
            "content": "Some content",
            "created": "2026-05-02T10:00:00Z"
        }

        message = {
            "id": "msg-uuid-999",
            "note": note_data
        }

        result = format_message_with_date(message, note_data)

        # Should be JSON serializable
        json_str = json.dumps(result)
        deserialized = json.loads(json_str)

        assert deserialized["date"] == "2026-05-25"
        assert deserialized["id"] == "msg-uuid-999"

    def test_message_with_multiple_notes_in_batch(self):
        """Test batch processing of multiple notes."""
        notes_batch = [
            {
                "id": "note-1",
                "title": "Meeting 15/05",
                "created": "2026-05-01T10:00:00Z"
            },
            {
                "id": "note-2",
                "title": "Workshop Notes",
                "created": "2026-05-02T14:00:00Z"
            },
            {
                "id": "note-3",
                "title": "Planning Session 20/05",
                "created": "2026-05-03T09:00:00Z"
            }
        ]

        messages = []
        for i, note_data in enumerate(notes_batch):
            message = {
                "id": f"msg-{i}",
                "note": note_data
            }
            formatted = format_message_with_date(message, note_data)
            messages.append(formatted)

        # Verify batch processing
        assert len(messages) == 3

        # Verify dates
        assert messages[0]["date"] == "2026-05-15"  # Title override
        assert messages[1]["date"] == "2026-05-02"  # Creation date
        assert messages[2]["date"] == "2026-05-20"  # Title override

        # All should be JSON serializable
        for msg in messages:
            json.dumps(msg)


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_google_keep_export_scenario(self):
        """Simulate Google Keep note export workflow."""
        # Simulate Google Keep export format
        keep_note = {
            "id": "keep-abc123",
            "title": "Project Status 22/05",
            "content": "Completed: UI redesign, API updates\nNext: Testing, documentation",
            "labels": ["work", "updates"],
            "isPinned": False,
            "created": "2026-05-02T08:00:00Z",
            "updated": "2026-05-02T16:30:00Z"
        }

        message = {
            "id": "batch-001-001",
            "note": keep_note
        }

        result = format_message_with_date(message, keep_note)

        # Date should be from title
        assert result["date"] == "2026-05-22"

        # Message should be publication-ready
        json_ready = json.dumps(result)
        assert "date" in json_ready
        assert "2026-05-22" in json_ready  # Date should be in ISO format

    def test_apple_notes_export_scenario(self):
        """Simulate Apple Notes export workflow."""
        # Simulate Apple Notes export format (as JSON)
        apple_note = {
            "id": "icloud-xyz789",
            "title": "Team Sync 18/05",
            "content": "Q2 roadmap review\nDiscussed: timeline, resources, risks",
            "created": "2026-05-01T10:30:00Z",
            "modified": "2026-05-02T11:00:00Z",
            "folder": "Work",
            "color": None,
            "pinned": False
        }

        message = {
            "id": "batch-002-001",
            "source": "apple-notes",
            "filename": "icloud-xyz789.json",
            "note": apple_note
        }

        result = format_message_with_date(message, apple_note)

        # Date should be from title
        assert result["date"] == "2026-05-18"

        # Message should preserve source info
        assert result["source"] == "apple-notes"
        assert result["filename"] == "icloud-xyz789.json"

        # Should be publication-ready
        json_ready = json.dumps(result)
        assert "2026-05-18" in json_ready

    def test_missing_date_graceful_handling(self):
        """Test that missing dates are handled gracefully."""
        note_without_dates = {
            "id": "note-nodates",
            "title": "Regular Note",
            "content": "No date information"
            # Missing created, modified, and no date in title
        }

        message = {
            "id": "msg-001",
            "note": note_without_dates
        }

        result = format_message_with_date(message, note_without_dates)

        # Should still produce valid message, but with None date
        assert result["date"] is None
        assert json.dumps(result)  # Still JSON serializable


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
