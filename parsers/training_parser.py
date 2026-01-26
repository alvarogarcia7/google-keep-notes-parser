import re
import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List
from parsers.base import NoteParser


@dataclass
class SetData:
    set: int
    reps: int
    weight: float


@dataclass
class ExerciseData:
    exercise_name: str
    abbreviation: str
    sets: List[SetData]
    total_sets: int
    raw_line: str


@dataclass
class CompletedActivity:
    timestamp: str
    activity: str


@dataclass
class WorkoutData:
    note_id: str
    title: str
    workout_date: str
    last_updated: str
    exercises: List[ExerciseData]
    completed_activities: List[CompletedActivity]
    raw_text: str


class TrainingParser(NoteParser):
    EXERCISE_PATTERNS: Dict[str, str] = {
        'Bp': 'Bench Press',
        'Mr': 'Machine Row',
        'Ms': 'Machine Squat',
        'Sq': 'Squat',
        'Dl': 'Deadlift',
        'Pu': 'Pull-up',
        'Dip': 'Dip',
        'Row': 'Row',
        'Curl': 'Curl',
        'Press': 'Press'
    }
    
    SET_REP_WEIGHT_PATTERN: str = r'(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)'
    
    def can_parse(self, note_data: Any) -> bool:
        if not isinstance(note_data, dict):
            return False
        
        text: str = note_data.get('text', '')
        if not text:
            return False
        
        text = self._normalize_checkboxes(text)
        
        has_exercise: bool = any(
            re.search(rf'\b{abbr}\b', text, re.IGNORECASE) 
            for abbr in self.EXERCISE_PATTERNS.keys()
        )
        
        has_set_format: bool = bool(re.search(self.SET_REP_WEIGHT_PATTERN, text))
        
        return has_exercise and has_set_format
    
    def _normalize_checkboxes(self, text: str) -> str:
        text = text.replace('\u2610', '- [ ] ')
        text = text.replace('\u2611', '- [x] ')
        return text
    
    def parse(self, note_data: Any) -> WorkoutData:
        if not isinstance(note_data, dict):
            raise ValueError("note_data must be a dictionary")
        
        text: str = note_data.get('text', '')
        text = self._normalize_checkboxes(text)
        
        title: str = note_data.get('title', '')
        timestamps: Dict[str, str] = note_data.get('timestamps', {})
        
        created: str = timestamps.get('created', '')
        edited: str = timestamps.get('edited', '')
        
        exercises: List[ExerciseData] = self._extract_exercises(text)
        
        result = WorkoutData(
            note_id=note_data.get('id', ''),
            title=title,
            workout_date=created,
            last_updated=edited,
            exercises=exercises,
            completed_activities=self._extract_completed_activities(text, created),
            raw_text=text
        )
        
        return result
    
    def _extract_exercises(self, text: str) -> List[ExerciseData]:
        exercises_dict: Dict[str, ExerciseData] = {}
        lines: List[str] = text.split('\n')
        
        current_exercise: str | None = None
        previous_indent: int = 0
        
        for i, line in enumerate(lines):
            current_indent = len(line) - len(line.lstrip())
            
            matched_abbr: str | None = None
            for abbr, full_name in self.EXERCISE_PATTERNS.items():
                if re.search(rf'\b{abbr}\b', line, re.IGNORECASE):
                    matched_abbr = abbr
                    current_exercise = abbr
                    previous_indent = current_indent
                    break
            
            sets: List[SetData] = self._extract_sets(line)
            
            if sets:
                abbr_to_use = matched_abbr if matched_abbr else current_exercise
                
                if abbr_to_use:
                    full_name = self.EXERCISE_PATTERNS[abbr_to_use]
                    
                    if abbr_to_use in exercises_dict:
                        exercises_dict[abbr_to_use].sets.extend(sets)
                        exercises_dict[abbr_to_use].total_sets = len(exercises_dict[abbr_to_use].sets)
                        exercises_dict[abbr_to_use].raw_line += '\n' + line.strip()
                    else:
                        exercises_dict[abbr_to_use] = ExerciseData(
                            exercise_name=full_name,
                            abbreviation=abbr_to_use,
                            sets=sets,
                            total_sets=len(sets),
                            raw_line=line.strip()
                        )
            
            if current_indent <= previous_indent and not matched_abbr and not sets:
                current_exercise = None
        
        return list(exercises_dict.values())
    
    def _extract_sets(self, line: str) -> List[SetData]:
        sets: List[SetData] = []
        matches = re.finditer(self.SET_REP_WEIGHT_PATTERN, line)
        
        for match in matches:
            groups = match.groups()
            set_num: str = groups[0]
            reps: str = groups[1]
            weight: str = groups[2]
            sets.append(SetData(
                set=int(set_num),
                reps=int(reps),
                weight=float(weight)
            ))
        
        return sets
    
    def _extract_completed_activities(self, text: str, created_timestamp: str) -> List[CompletedActivity]:
        activities: List[CompletedActivity] = []
        
        timestamp_pattern: str = r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})'
        timestamp_matches = re.finditer(timestamp_pattern, text)
        
        for match in timestamp_matches:
            timestamp_str: str = match.group(1)
            if timestamp_str != created_timestamp.split('.')[0].replace(' ', 'T'):
                line_start: int = text.rfind('\n', 0, match.start())
                line_end: int = text.find('\n', match.end())
                if line_end == -1:
                    line_end = len(text)
                if line_start == -1:
                    line_start = 0
                
                activity_line: str = text[line_start:line_end].strip()
                activities.append(CompletedActivity(
                    timestamp=timestamp_str,
                    activity=activity_line
                ))
        
        if not activities and created_timestamp:
            activities.append(CompletedActivity(
                timestamp=created_timestamp,
                activity='Workout logged'
            ))
        
        return activities
    
    def get_schema(self) -> Dict[str, Any]:
        schema_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'training.schema.json')
        with open(schema_path, 'r') as f:
            schema: Dict[str, Any] = json.load(f)
            return schema
