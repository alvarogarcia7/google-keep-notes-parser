import re
import json
import os
from typing import Any, Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from parsers.base import NoteParser


@dataclass
class ParseResult:
    note_id: str
    title: str
    date: str
    created: str
    last_updated: str
    time_entries: List[Dict[str, Any]]
    raw_text: str
    warnings: List[str]


class TimeEntryParser(NoteParser):
    TIME_CODE_PATTERN: str = r'^\s*[\u2610\u2611]?\s*(\d{3,4})\s+(.+)$'
    
    def can_parse(self, note_data: Any) -> bool:
        if not isinstance(note_data, dict):
            return False
        
        text: str = note_data.get('text', '')
        if not text:
            return False
        
        lines: List[str] = text.strip().split('\n')
        time_entry_count: int = 0
        
        for line in lines:
            match = re.match(self.TIME_CODE_PATTERN, line.strip())
            if match:
                time_code: str = match.group(1)
                if self._is_valid_time_code(time_code):
                    time_entry_count += 1
        
        return time_entry_count >= 2
    
    def _is_valid_time_code(self, time_code: str) -> bool:
        hours: int
        minutes: int
        
        if len(time_code) == 3:
            hours = int(time_code[0])
            minutes = int(time_code[1:])
        elif len(time_code) == 4:
            hours = int(time_code[:2])
            minutes = int(time_code[2:])
        else:
            return False
        
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    
    def _parse_time_code(self, time_code: str) -> str:
        hours_str: str
        minutes_str: str
        
        if len(time_code) == 3:
            hours_str = time_code[0]
            minutes_str = time_code[1:]
        elif len(time_code) == 4:
            hours_str = time_code[:2]
            minutes_str = time_code[2:]
        else:
            return ""
        
        hours_str = hours_str.zfill(2)
        minutes_str = minutes_str.zfill(2)
        
        return f"{hours_str}:{minutes_str}"
    
    def parse(self, note_data: Any) -> ParseResult:
        if not isinstance(note_data, dict):
            raise ValueError("note_data must be a dictionary")
        
        text: str = note_data.get('text', '')
        title: str = note_data.get('title', '')
        timestamps: Dict[str, str] = note_data.get('timestamps', {})
        
        created: str = timestamps.get('created', '')
        edited: str = timestamps.get('edited', '')
        
        entries, parse_warnings = self._extract_time_entries(text, created)
        
        result = ParseResult(
            note_id=note_data.get('id', ''),
            title=title,
            date=self._extract_date_from_timestamp(created),
            created=created,
            last_updated=edited,
            time_entries=entries,
            raw_text=text,
            warnings=parse_warnings
        )
        
        return result
    
    def _extract_date_from_timestamp(self, timestamp: str) -> str:
        if not timestamp:
            return ''
        
        try:
            dt: datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return timestamp.split('T')[0] if 'T' in timestamp else timestamp.split(' ')[0]
    
    def _extract_time_entries(self, text: str, created_timestamp: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        entries: List[Dict[str, Any]] = []
        parse_warnings: List[str] = []
        lines: List[str] = text.strip().split('\n')
        
        base_date: str = self._extract_date_from_timestamp(created_timestamp)
        
        original_order: List[str] = []
        for line in lines:
            match = re.match(self.TIME_CODE_PATTERN, line.strip())
            if match:
                time_code: str = match.group(1)
                activity: str = match.group(2).strip()
                
                if self._is_valid_time_code(time_code):
                    time_str: str = self._parse_time_code(time_code)
                    original_order.append(time_str)
                    
                    timestamp_str: str
                    if base_date:
                        timestamp_str = f"{base_date}T{time_str}:00"
                    else:
                        timestamp_str = f"{time_str}:00"
                    
                    entries.append({
                        'timestamp': timestamp_str,
                        'time': time_str,
                        'date': base_date,
                        'activity': activity,
                        'raw_line': line.strip()
                    })
        
        entries.sort(key=lambda x: x['time'])
        
        sorted_order: List[str] = [entry['time'] for entry in entries]
        if original_order != sorted_order:
            warning_msg = (
                f"Time entries are out of chronological order. "
                f"Original order: {original_order}, Sorted order: {sorted_order}"
            )
            parse_warnings.append(warning_msg)
        
        return entries, parse_warnings
    
    def get_schema(self) -> Dict[str, Any]:
        schema_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'time_entry.schema.json')
        with open(schema_path, 'r') as f:
            schema: Dict[str, Any] = json.load(f)
            return schema
