import re
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List
from datetime import datetime
from parsers.base import NoteParser


@dataclass
class ActionItem:
    text: str
    completed: bool


@dataclass
class Project:
    name: str
    items: List[ActionItem]


@dataclass
class NextNoteData:
    note_id: str
    note_date: str
    formatted_date: str
    projects: List[Project]
    raw_text: str


class NextParser(NoteParser):
    def can_parse(self, note_data: Any) -> bool:
        if not isinstance(note_data, dict):
            return False

        text: str = note_data.get('text', '')
        if not text:
            return False

        # Check if the note starts with "Next" (case-insensitive)
        lines = text.strip().split('\n')
        first_line = lines[0].strip() if lines else ''

        return first_line.lower() == 'next'

    def parse(self, note_data: Any) -> NextNoteData:
        if not isinstance(note_data, dict):
            raise ValueError("note_data must be a dictionary")

        text: str = note_data.get('text', '')
        timestamps: Dict[str, str] = note_data.get('timestamps', {})
        created: str = timestamps.get('created', '')

        # Parse the date
        note_date, formatted_date = self._parse_date(created)

        # Extract projects and action items
        projects: List[Project] = self._extract_projects(text)

        result = NextNoteData(
            note_id=note_data.get('id', ''),
            note_date=note_date,
            formatted_date=formatted_date,
            projects=projects,
            raw_text=text
        )

        return result

    def _parse_date(self, timestamp: str) -> tuple[str, str]:
        """Parse timestamp and return (ISO date, formatted date string)"""
        if not timestamp:
            return '', ''

        try:
            # Handle ISO format timestamps
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.split('.')[0])
            else:
                dt = datetime.strptime(timestamp.split('.')[0], '%Y-%m-%d %H:%M:%S')

            iso_date = dt.date().isoformat()
            formatted = dt.strftime('%-d/%-m' if '/' in '' else '%d/%m').lstrip('0').replace('/0', '/').replace('/', '/', 1).lstrip('0')
            # Format as d/m (without leading zeros)
            day = str(dt.day)
            month = str(dt.month)
            formatted = f"{day}/{month}"

            return iso_date, formatted
        except Exception:
            return timestamp, timestamp

    def _extract_projects(self, text: str) -> List[Project]:
        """Extract projects and their action items from the text"""
        projects: List[Project] = []
        lines = text.strip().split('\n')

        current_project: str | None = None
        current_items: List[ActionItem] = []

        for line in lines[1:]:  # Skip the "Next" header
            stripped = line.strip()

            if not stripped:
                # Empty line
                continue

            # Check if this is a project line (doesn't start with - [ ] or - [x])
            if not stripped.startswith('- ['):
                # This is a project name
                if current_project is not None:
                    # Save the previous project
                    projects.append(Project(name=current_project, items=current_items))

                current_project = stripped
                current_items = []
            else:
                # This is an action item
                # Check if it's completed [x] or pending [ ]
                completed = '[x]' in stripped or '[X]' in stripped

                # Extract the text after the checkbox
                text_match = re.search(r'-\s*\[[xX\s]\]\s*(.*)', stripped)
                if text_match:
                    item_text = text_match.group(1)
                    current_items.append(ActionItem(text=item_text, completed=completed))

        # Don't forget the last project
        if current_project is not None:
            projects.append(Project(name=current_project, items=current_items))

        return projects

    def get_schema(self) -> Dict[str, Any]:
        schema_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'next.schema.json')
        with open(schema_path, 'r') as f:
            schema: Dict[str, Any] = json.load(f)
            return schema

    @staticmethod
    def format_as_text(result: NextNoteData) -> str:
        """Format parsed result as plain text"""
        output: List[str] = [f"Next for {result.formatted_date}"]
        output.append(f"Total Projects: {len(result.projects)}\n")

        for project in result.projects:
            output.append(f"{project.name}")
            for item in project.items:
                status = "✓" if item.completed else "•"
                output.append(f"  {status} {item.text}")
            output.append("")

        return "\n".join(output)

    @staticmethod
    def format_as_org(result: NextNoteData) -> str:
        """Format parsed result as org mode"""
        output: List[str] = [f"* Next for {result.formatted_date}"]
        output.append(f"Total Projects: {len(result.projects)}\n")

        for project in result.projects:
            output.append(f"** {project.name}")
            for item in project.items:
                status = "DONE" if item.completed else "TODO"
                output.append(f"   - [{status}] {item.text}")
            output.append("")

        return "\n".join(output)
