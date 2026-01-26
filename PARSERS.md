# Parser Architecture Documentation

#### `NoteParser` (Abstract Base Class)

The foundation of all parsers. Located in `parsers/base.py`, it defines the contract that all parsers must implement.

**Required Methods:**

- `can_parse(note_data: Any) -> bool`: Determines if this parser can handle the given note data
- `parse(note_data: Any) -> dict`: Extracts structured data from the note
- `get_schema() -> dict`: Returns the JSON schema for validating the parsed output

#### `ParserRegistry`

Manages parser registration and selection. Automatically chooses the appropriate parser for each note.

**Key Methods:**

- `register(parser_class: Type[NoteParser])`: Register a new parser type
- `get_parser(note_data: Any) -> NoteParser`: Find the appropriate parser for the data
- `parse(note_data: Any) -> dict`: Parse and validate data using the appropriate parser

## How to Add New Parser Types

### Step 1: Create Parser Class

Create a new file in the `parsers/` directory (e.g., `parsers/my_parser.py`):

```python
import re
import json
import os
from typing import Any, Dict, List
from parsers.base import NoteParser


class MyCustomParser(NoteParser):
    """Parser for extracting custom data from notes."""
    
    def can_parse(self, note_data: Any) -> bool:
        """
        Determine if this parser can handle the note.
        
        Return True if the note contains patterns/labels this parser handles.
        """
        if not isinstance(note_data, dict):
            return False
        
        text = note_data.get('text', '')
        labels = note_data.get('labels', [])
        
        # Check for specific label or text pattern
        has_label = 'MyLabel' in labels
        has_pattern = bool(re.search(r'PATTERN_TO_MATCH', text))
        
        return has_label or has_pattern
    
    def parse(self, note_data: Any) -> dict:
        """
        Extract structured data from the note.
        
        Returns a dictionary conforming to the parser's schema.
        """
        if not isinstance(note_data, dict):
            raise ValueError("note_data must be a dictionary")
        
        # Extract fields from note
        result = {
            'note_id': note_data.get('id', ''),
            'title': note_data.get('title', ''),
            'extracted_data': self._extract_custom_data(note_data.get('text', '')),
            'labels': note_data.get('labels', []),
            'raw_text': note_data.get('text', '')
        }
        
        return result
    
    def _extract_custom_data(self, text: str) -> List[Dict]:
        """Helper method to extract custom patterns from text."""
        # Implementation specific to your parser
        extracted = []
        # ... extraction logic ...
        return extracted
    
    def get_schema(self) -> dict:
        """Return JSON schema for validation."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'schemas', 
            'my_custom.schema.json'
        )
        with open(schema_path, 'r') as f:
            return json.load(f)
```

### Step 2: Create JSON Schema

Create a schema file at `schemas/my_custom.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "My Custom Parser Schema",
  "description": "Schema for custom extracted data",
  "type": "object",
  "properties": {
    "note_id": {
      "type": "string",
      "description": "Unique identifier of the note"
    },
    "title": {
      "type": "string",
      "description": "Title of the note"
    },
    "extracted_data": {
      "type": "array",
      "description": "Custom extracted data items",
      "items": {
        "type": "object",
        "properties": {
          "field1": {"type": "string"},
          "field2": {"type": "number"}
        },
        "required": ["field1", "field2"]
      }
    },
    "labels": {
      "type": "array",
      "items": {"type": "string"}
    },
    "raw_text": {
      "type": "string"
    }
  },
  "required": ["note_id", "title", "extracted_data", "raw_text"]
}
```

### Step 3: Register Parser

Register your parser in the application (typically in `parse_notes.py` or main script):

```python
from parsers.base import ParserRegistry
from parsers.my_parser import MyCustomParser

# Create registry and register parsers
registry = ParserRegistry()
registry.register(MyCustomParser)

# Use the registry
parsed_data = registry.parse(note_data)
```

## Built-in Parser Types

### 1. HackerNewsParser

**Purpose:** Extracts Hacker News URLs and metadata from notes.

**Detection Criteria:**
- Notes with label `Download-HN`
- Notes containing URLs matching `https://news.ycombinator.com/item?id=<ID>`

**Input Example:**
```json
{
  "id": "abc123.def456",
  "title": "Interesting HN Article",
  "text": "Check this out: https://news.ycombinator.com/item?id=12345678\nGreat discussion about AI",
  "labels": ["Download-HN", "tech"],
  "timestamps": {
    "created": "2023-10-15T14:30:00",
    "edited": "2023-10-15T14:30:00"
  }
}
```

**Output Example:**
```json
{
  "note_id": "abc123.def456",
  "title": "Interesting HN Article",
  "url": "https://news.ycombinator.com/item?id=12345678",
  "item_id": "12345678",
  "labels": ["Download-HN", "tech"],
  "description": "Check this out: https://news.ycombinator.com/item?id=12345678\nGreat discussion about AI",
  "hn_links": [
    {
      "url": "https://news.ycombinator.com/item?id=12345678",
      "item_id": "12345678"
    }
  ]
}
```

### 2. TimeEntryParser

**Purpose:** Extracts time-tracking entries from notes using time codes.

**Detection Criteria:**
- Notes containing 2+ lines with time code format: `<3-4 digit time> <activity>`
- Time codes: `930` (9:30), `1445` (14:45), etc.

**Input Example:**
```json
{
  "id": "xyz789.uvw012",
  "title": "Daily Log - 2023-10-15",
  "text": "900 Started morning standup\n930 Code review for PR #234\n1100 Development work on feature X\n1445 Team meeting",
  "labels": ["timetracking"],
  "timestamps": {
    "created": "2023-10-15T09:00:00",
    "edited": "2023-10-15T15:00:00"
  }
}
```

**Output Example:**
```json
{
  "note_id": "xyz789.uvw012",
  "title": "Daily Log - 2023-10-15",
  "date": "2023-10-15",
  "created": "2023-10-15T09:00:00",
  "last_updated": "2023-10-15T15:00:00",
  "time_entries": [
    {
      "timestamp": "2023-10-15T09:00:00",
      "time": "09:00",
      "activity": "Started morning standup",
      "raw_line": "900 Started morning standup"
    },
    {
      "timestamp": "2023-10-15T09:30:00",
      "time": "09:30",
      "activity": "Code review for PR #234",
      "raw_line": "930 Code review for PR #234"
    },
    {
      "timestamp": "2023-10-15T11:00:00",
      "time": "11:00",
      "activity": "Development work on feature X",
      "raw_line": "1100 Development work on feature X"
    },
    {
      "timestamp": "2023-10-15T14:45:00",
      "time": "14:45",
      "activity": "Team meeting",
      "raw_line": "1445 Team meeting"
    }
  ],
  "raw_text": "900 Started morning standup\n930 Code review for PR #234\n1100 Development work on feature X\n1445 Team meeting"
}
```

### 3. TrainingParser

**Purpose:** Extracts workout data from training notes.

**Detection Criteria:**
- Notes containing exercise abbreviations: `Bp` (Bench Press), `Sq` (Squat), `Dl` (Deadlift), etc.
- Notes with set/rep/weight format: `3 x 8 x 135` (3 sets, 8 reps, 135 lbs)

**Input Example:**
```json
{
  "id": "fit123.gym456",
  "title": "Upper Body Workout",
  "text": "Bp 3 x 8 x 185\nBp 2 x 6 x 205\nMr 3 x 10 x 95\nPu 3 x 12 x bodyweight",
  "labels": ["fitness", "strength"],
  "timestamps": {
    "created": "2023-10-15T18:00:00",
    "edited": "2023-10-15T19:30:00"
  }
}
```

**Output Example:**
```json
{
  "note_id": "fit123.gym456",
  "title": "Upper Body Workout",
  "workout_date": "2023-10-15T18:00:00",
  "last_updated": "2023-10-15T19:30:00",
  "exercises": [
    {
      "exercise_name": "Bench Press",
      "abbreviation": "Bp",
      "sets": [
        {"set": 3, "reps": 8, "weight": 185.0},
        {"set": 2, "reps": 6, "weight": 205.0}
      ],
      "total_sets": 2,
      "raw_line": "Bp 3 x 8 x 185"
    },
    {
      "exercise_name": "Military Press",
      "abbreviation": "Mr",
      "sets": [
        {"set": 3, "reps": 10, "weight": 95.0}
      ],
      "total_sets": 1,
      "raw_line": "Mr 3 x 10 x 95"
    },
    {
      "exercise_name": "Pull-up",
      "abbreviation": "Pu",
      "sets": [
        {"set": 3, "reps": 12, "weight": 0.0}
      ],
      "total_sets": 1,
      "raw_line": "Pu 3 x 12 x bodyweight"
    }
  ],
  "completed_activities": [
    {
      "timestamp": "2023-10-15T18:00:00",
      "activity": "Workout logged"
    }
  ],
  "raw_text": "Bp 3 x 8 x 185\nBp 2 x 6 x 205\nMr 3 x 10 x 95\nPu 3 x 12 x bodyweight"
}
```

## Usage Examples

### Basic Usage

```bash
# Parse all JSON files in mdfiles directory
python parse_notes.py

# Specify custom input directory
python parse_notes.py --input-dir my_notes

# Specify custom output directory
python parse_notes.py --output-dir parsed_results

# Combine options
python parse_notes.py --input-dir exports --output-dir processed
```

### Command-Line Options

```
--input-dir   Input directory containing JSON files (default: 'mdfiles')
--output-dir  Output directory for parsed results (default: 'parsed_output')
```

### Programmatic Usage

```python
from parsers.base import ParserRegistry
from parsers.hackernews_parser import HackerNewsParser
from parsers.time_entry_parser import TimeEntryParser
from parsers.training_parser import TrainingParser
import json

# Initialize registry and register parsers
registry = ParserRegistry()
registry.register(HackerNewsParser)
registry.register(TimeEntryParser)
registry.register(TrainingParser)

# Load note data
with open('note.json', 'r') as f:
    note_data = json.load(f)

# Parse the note (automatically selects appropriate parser)
try:
    parsed_data = registry.parse(note_data)
    print(json.dumps(parsed_data, indent=2))
except ValueError as e:
    print(f"Error: {e}")
```

### Processing Multiple Notes

```python
import os
import json
from pathlib import Path
from parsers.base import ParserRegistry
from parsers.hackernews_parser import HackerNewsParser
from parsers.time_entry_parser import TimeEntryParser
from parsers.training_parser import TrainingParser

# Setup registry
registry = ParserRegistry()
registry.register(HackerNewsParser)
registry.register(TimeEntryParser)
registry.register(TrainingParser)

# Process all JSON files in directory
input_dir = 'mdfiles'
output_dir = 'parsed_output'
os.makedirs(output_dir, exist_ok=True)

for json_file in Path(input_dir).glob('*.json'):
    with open(json_file, 'r', encoding='utf-8') as f:
        note_data = json.load(f)
    
    try:
        parsed = registry.parse(note_data)
        output_file = output_dir / f"{json_file.stem}_parsed.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Parsed: {json_file.name}")
    except ValueError as e:
        print(f"✗ Skipped {json_file.name}: {e}")
```

## Best Practices

### Parser Implementation

1. **Single Responsibility**: Each parser should handle one specific type of note pattern
2. **Robust Detection**: `can_parse()` should be conservative - only return `True` when confident
3. **Error Handling**: Validate input types and handle missing fields gracefully
4. **Schema Validation**: Always provide a JSON schema and test against it
5. **Documentation**: Document the patterns your parser recognizes and example outputs

### Pattern Matching

1. Use regex for flexible text pattern matching
2. Combine multiple detection criteria (labels + text patterns) for accuracy
3. Make patterns case-insensitive when appropriate
4. Handle variations in formatting (extra whitespace, different separators)

### Testing

1. Test with real Keep note exports
2. Verify both positive and negative cases for `can_parse()`
3. Validate output against JSON schema
4. Test edge cases (empty notes, malformed data, etc.)

## Troubleshooting

### Parser Not Triggering

- Check that `can_parse()` logic matches your note structure
- Verify label names match exactly (case-sensitive)
- Test regex patterns independently
- Add debug logging to `can_parse()` method

### Schema Validation Errors

- Ensure all required fields are included in `parse()` output
- Check that data types match schema definitions
- Verify array items conform to schema
- Use online JSON schema validators for testing

### Multiple Parsers Matching

- Make `can_parse()` more specific
- Order matters: parsers are tested in registration order
- First matching parser is used
- Consider parser priority or specificity rules

## Advanced Topics

### Custom Validation

Beyond JSON schema validation, you can add custom validation in `parse()`:

```python
def parse(self, note_data: Any) -> dict:
    result = self._extract_data(note_data)
    
    # Custom validation
    if len(result['items']) == 0:
        raise ValueError("No valid items found")
    
    return result
```

### Parser Composition

Combine multiple extraction strategies:

```python
class CompositeParser(NoteParser):
    def parse(self, note_data: Any) -> dict:
        result = {
            'basic_data': self._extract_basic(note_data),
            'links': self._extract_links(note_data),
            'metadata': self._extract_metadata(note_data)
        }
        return result
```

### Dynamic Parser Registration

Load parsers dynamically:

```python
import importlib
import pkgutil
import parsers

def load_all_parsers(registry):
    for importer, modname, ispkg in pkgutil.iter_modules(parsers.__path__):
        if modname.endswith('_parser'):
            module = importlib.import_module(f'parsers.{modname}')
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, NoteParser) and 
                    item is not NoteParser):
                    registry.register(item)
```
