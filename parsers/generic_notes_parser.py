import re
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List
from parsers.base import NoteParser


@dataclass
class Checkbox:
    checked: bool
    text: str


@dataclass
class GenericNote:
    note_id: str
    title: str
    links: List[str]
    checkboxes: List[Checkbox]
    rest: List[str]


class GenericNotesParser(NoteParser):
    URL_PATTERN: str = r'https?://[^\s<>"\')}\]]+|www\.[^\s<>"\')}\]]+'
    CHECKBOX_PATTERN: str = r'^\s*([\u2610\u2611])\s*(.+)$'
    CHECKED_BOX: str = '\u2611'
    UNCHECKED_BOX: str = '\u2610'
    
    def can_parse(self, note_data: Any) -> bool:
        if not isinstance(note_data, dict):
            return False
        return True
    
    def parse(self, note_data: Any) -> GenericNote:
        if not isinstance(note_data, dict):
            raise ValueError("note_data must be a dictionary")
        
        text: str = note_data.get('text', '')
        title: str = note_data.get('title', '')
        
        links: List[str] = self._extract_links(text)
        checkboxes: List[Checkbox] = []
        rest: List[str] = []
        
        lines: List[str] = text.split('\n')
        for line in lines:
            stripped_line: str = line.strip()
            if not stripped_line:
                continue
            
            checkbox_match = re.match(self.CHECKBOX_PATTERN, stripped_line)
            if checkbox_match:
                checkbox_char: str = checkbox_match.group(1)
                checkbox_text: str = checkbox_match.group(2).strip()
                is_checked: bool = checkbox_char == self.CHECKED_BOX
                checkboxes.append(Checkbox(checked=is_checked, text=checkbox_text))
            else:
                rest.append(stripped_line)
        
        return GenericNote(
            note_id=note_data.get('id', ''),
            title=title,
            links=links,
            checkboxes=checkboxes,
            rest=rest
        )
    
    def _extract_links(self, text: str) -> List[str]:
        links: List[str] = []
        matches = re.finditer(self.URL_PATTERN, text)
        
        seen_links: set[str] = set()
        for match in matches:
            link: str = match.group(0)
            if link not in seen_links:
                links.append(link)
                seen_links.add(link)
        
        return links
    
    def get_schema(self) -> Dict[str, Any]:
        schema_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'generic_notes.schema.json')
        with open(schema_path, 'r') as f:
            schema: Dict[str, Any] = json.load(f)
            return schema
