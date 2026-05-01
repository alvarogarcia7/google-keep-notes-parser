"""
Compatibility shim for TimeEntryParser.

The actual logic has been moved to time-entry-notes-parser/src/time_entry_parser.py.
This module re-exports the parser with NoteParser inheritance for compatibility.
"""
import sys
from pathlib import Path
from typing import Any, Dict
from parsers.base import NoteParser

# Add time-entry-notes-parser/src to path
_repo_root = Path(__file__).parent.parent.parent
_time_entry_path = _repo_root / "time-entry-notes-parser" / "src"
if str(_time_entry_path) not in sys.path:
    sys.path.insert(0, str(_time_entry_path))

# Import from the new project
from time_entry_parser import TimeEntryParser as TimeEntryParserBase, ParseResult

__all__ = ["TimeEntryParser", "ParseResult"]


# Wrapper to add NoteParser compatibility
class TimeEntryParser(NoteParser):
    """TimeEntryParser with NoteParser base class for ParserRegistry compatibility."""

    def __init__(self) -> None:
        self._parser = TimeEntryParserBase()

    def can_parse(self, note_data: Any) -> bool:
        """Check if this parser can handle the note."""
        return self._parser.can_parse(note_data)

    def parse(self, note_data: Any) -> ParseResult:
        """Parse a note."""
        return self._parser.parse(note_data)

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for validation."""
        return self._parser.get_schema()
