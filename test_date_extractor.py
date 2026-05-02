#!/usr/bin/env python3
"""
Tests for date_extractor module.
"""

import pytest
from datetime import datetime
from date_extractor import extract_date_from_title, get_note_date, format_message_with_date


class TestExtractDateFromTitle:
    """Tests for extract_date_from_title function."""

    def test_dd_mm_format(self):
        """Test extraction of dd/mm format."""
        assert extract_date_from_title("Meeting 15/05") == (15, 5)
        assert extract_date_from_title("15/05 Team Sync") == (15, 5)
        assert extract_date_from_title("Date: 01/01") == (1, 1)

    def test_single_digit_dates(self):
        """Test extraction of single digit dates."""
        assert extract_date_from_title("Meeting 5/5") == (5, 5)
        assert extract_date_from_title("15/5") == (15, 5)
        assert extract_date_from_title("5/05") == (5, 5)

    def test_leading_zeros(self):
        """Test extraction with leading zeros."""
        assert extract_date_from_title("01/01") == (1, 1)
        assert extract_date_from_title("09/12") == (9, 12)
        assert extract_date_from_title("31/12") == (31, 12)

    def test_no_date_found(self):
        """Test when no date is in title."""
        assert extract_date_from_title("Just a title") is None
        assert extract_date_from_title("2026-05-15") is None  # YYYY-MM-DD not matched
        assert extract_date_from_title("") is None
        assert extract_date_from_title(None) is None

    def test_invalid_dates(self):
        """Test rejection of invalid dates."""
        assert extract_date_from_title("32/12") is None  # Invalid day
        assert extract_date_from_title("15/13") is None  # Invalid month
        assert extract_date_from_title("0/0") is None  # Zero values
        assert extract_date_from_title("31/02") is None  # Feb 31 doesn't exist

    def test_multiple_dates_in_title(self):
        """Test extraction of first date when multiple present."""
        # Should match the first occurrence
        result = extract_date_from_title("15/05 to 20/05")
        assert result == (15, 5)

    def test_word_boundaries(self):
        """Test that dates must have word boundaries."""
        # This should match (has word boundaries)
        assert extract_date_from_title("The date is 15/05 today") == (15, 5)
        # Word boundary prevents matching numbers directly adjacent
        assert extract_date_from_title("abc15/05def") is None  # No word boundaries


class TestGetNoteDate:
    """Tests for get_note_date function."""

    def test_title_override_creation_date(self):
        """Test that title date overrides creation date."""
        note = {
            "created": "2026-05-02T10:30:00Z",
            "title": "Meeting 15/05"
        }
        # Should use title date (15/05 of current year)
        result = get_note_date(note)
        assert result is not None
        assert "15" in result and "05" in result

    def test_title_override_via_parameter(self):
        """Test that title parameter overrides note['title']."""
        note = {
            "created": "2026-05-02T10:30:00Z",
            "title": "Original Title"
        }
        result = get_note_date(note, title="15/05 Override")
        assert result is not None
        assert "15" in result and "05" in result

    def test_iso_creation_date(self):
        """Test extraction of ISO format creation date."""
        note = {"created": "2026-05-02T10:30:00Z"}
        result = get_note_date(note)
        assert result == "2026-05-02"

    def test_iso_creation_date_without_time(self):
        """Test extraction of ISO format date without time."""
        note = {"created": "2026-05-02"}
        result = get_note_date(note)
        assert result == "2026-05-02"

    def test_unix_timestamp(self):
        """Test extraction from Unix timestamp."""
        # Convert a known date to Unix timestamp
        target_date = datetime(2026, 5, 2, 0, 0, 0)
        timestamp = int(target_date.timestamp())
        note = {"created": timestamp}
        result = get_note_date(note)
        assert result == "2026-05-02"

    def test_fallback_to_modified_date(self):
        """Test fallback to modified date when created not present."""
        note = {"modified": "2026-05-02T10:30:00Z"}
        result = get_note_date(note)
        assert result == "2026-05-02"

    def test_various_date_field_names(self):
        """Test various date field name conventions."""
        # createdTime
        assert get_note_date({"createdTime": "2026-05-02T10:30:00Z"}) == "2026-05-02"
        # timestamp
        assert get_note_date({"timestamp": "2026-05-02T10:30:00Z"}) == "2026-05-02"
        # updatedTime
        assert get_note_date({"updatedTime": "2026-05-02T10:30:00Z"}) == "2026-05-02"
        # updated
        assert get_note_date({"updated": "2026-05-02T10:30:00Z"}) == "2026-05-02"

    def test_no_date_found(self):
        """Test when no date can be extracted."""
        note = {"title": "No Date Here"}
        assert get_note_date(note) is None

    def test_empty_note(self):
        """Test with empty note dictionary."""
        assert get_note_date({}) is None

    def test_invalid_date_values(self):
        """Test handling of invalid date values."""
        note = {"created": "invalid-date"}
        # Should not crash, but return None
        assert get_note_date(note) is None

    def test_null_date_fields(self):
        """Test handling of null/empty date fields."""
        note = {"created": None, "modified": "2026-05-02T10:30:00Z"}
        result = get_note_date(note)
        assert result == "2026-05-02"

    def test_uses_current_year_for_title_date(self):
        """Test that title dates use current year."""
        # Extract dd/mm from title and use current year
        note = {"title": "15/12"}
        result = get_note_date(note)
        assert result is not None
        # Should be in current year (2026)
        current_year = datetime.now().year
        assert str(current_year) in result

    def test_title_priority_over_all(self):
        """Test that title date has highest priority."""
        note = {
            "title": "Meeting 15/05",
            "created": "2026-05-02T10:30:00Z",
            "modified": "2026-05-01T10:30:00Z",
        }
        result = get_note_date(note)
        # Should use title date, not created or modified
        assert "15" in result and "05" in result


class TestFormatMessageWithDate:
    """Tests for format_message_with_date function."""

    def test_adds_date_to_message(self):
        """Test that date field is added to message."""
        message = {
            "id": "msg-123",
            "note": {"title": "Meeting 15/05"}
        }
        note_data = {
            "created": "2026-05-02T10:30:00Z",
            "title": "Meeting 15/05"
        }
        result = format_message_with_date(message, note_data)

        assert "date" in result
        assert "15" in result["date"] and "05" in result["date"]

    def test_preserves_existing_fields(self):
        """Test that existing message fields are preserved."""
        message = {
            "id": "msg-123",
            "note": {"title": "Test"},
            "source": "google-keep"
        }
        note_data = {"created": "2026-05-02T10:30:00Z"}
        result = format_message_with_date(message, note_data)

        assert result["id"] == "msg-123"
        assert result["source"] == "google-keep"
        assert "date" in result

    def test_handles_filename_as_fallback_title(self):
        """Test that filename is used as fallback for title."""
        message = {
            "id": "msg-123",
            "filename": "note-15-05.json"
        }
        note_data = {"created": "2026-05-02T10:30:00Z"}
        result = format_message_with_date(message, note_data)

        assert "date" in result


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_google_keep_note_format(self):
        """Test with realistic Google Keep note format."""
        message = {
            "id": "uuid-123",
            "note": {
                "id": "keep-123",
                "title": "Team Sync 15/05",
                "content": "Discussed Q2 planning",
                "created": "2026-05-02T10:30:00Z"
            }
        }
        note_data = message["note"]
        result = format_message_with_date(message, note_data)

        assert result["date"] == "2026-05-15"  # Title override
        assert result["id"] == "uuid-123"

    def test_apple_notes_format(self):
        """Test with realistic Apple Notes format."""
        message = {
            "id": "uuid-456",
            "source": "apple-notes",
            "filename": "note-789.json",
            "note": {
                "id": "notes-789",
                "title": "Meeting Notes 20/05",
                "content": "Discussed project timeline",
                "created": "2026-05-02T14:30:00Z",
                "modified": "2026-05-02T15:45:00Z"
            }
        }
        note_data = message["note"]
        result = format_message_with_date(message, note_data)

        assert result["date"] == "2026-05-20"  # Title override
        assert result["source"] == "apple-notes"

    def test_message_without_title_override(self):
        """Test message that doesn't have date in title."""
        message = {
            "id": "uuid-789",
            "note": {
                "id": "keep-789",
                "title": "Regular Meeting Notes",
                "created": "2026-05-02T10:30:00Z"
            }
        }
        note_data = message["note"]
        result = format_message_with_date(message, note_data)

        assert result["date"] == "2026-05-02"  # Uses creation date


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
