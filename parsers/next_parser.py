"""
Compatibility shim for NextParser.

The actual logic has been moved to notes-parser-next-entry/src/next_parser.py.
This module re-exports the parser with NoteParser inheritance for compatibility.
"""
import sys
from pathlib import Path
from typing import Any, Dict
from parsers.base import NoteParser

# Add notes-parser-next-entry/src to path
_repo_root = Path(__file__).parent.parent.parent
_next_path = _repo_root / "notes-parser-next-entry" / "src"
if str(_next_path) not in sys.path:
    sys.path.insert(0, str(_next_path))

# Import from the new project
from next_parser import NextParser as NextParserBase, NextNoteData, ActionItem, Project

__all__ = ["NextParser", "NextNoteData", "ActionItem", "Project"]


# Wrapper to add NoteParser compatibility
class NextParser(NoteParser):
    """NextParser with NoteParser base class for ParserRegistry compatibility."""

    def __init__(self) -> None:
        self._parser = NextParserBase()

    def can_parse(self, note_data: Any) -> bool:
        """Check if this parser can handle the note."""
        return self._parser.can_parse(note_data)

    def parse(self, note_data: Any) -> NextNoteData:
        """Parse a note."""
        return self._parser.parse(note_data)

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for validation."""
        return self._parser.get_schema()
