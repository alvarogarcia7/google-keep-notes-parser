# NEXT Note Parser Implementation

## Overview

A complete implementation of a parser for the "NEXT" note type in the Google Keep Notes Parser project. NEXT notes contain a list of projects with associated action items (TODOs/DONEs) dated by their creation timestamp.

## Features

### Parsing Capabilities
- **Format Detection**: Automatically detects notes starting with "NEXT" (case-insensitive)
- **Project Extraction**: Parses multiple projects from the note text
- **Action Items**: Identifies TODO (`- [ ]`) and DONE (`- [x]`) items
- **Date Handling**: Extracts and formats creation date in both ISO and d/m formats
- **Status Tracking**: Tracks completion status of each action item

### Output Formats

#### Text Mode
```
Next for 13/3
Total Projects: 3

Project TCMS
  • Achieve a doctor build that is off-line
  • Download said images
  • Upload them to FMA
  • Get approval

Project admin
  • Upload all hourly reports for boss
  • Upload expenses for Claude
```

#### Org Mode
```org
* Next for 13/3
Total Projects: 3

** Project TCMS
   - [TODO] Achieve a doctor build that is off-line
   - [TODO] Download said images
   - [TODO] Upload them to FMA
   - [TODO] Get approval

** Project admin
   - [TODO] Upload all hourly reports for boss
   - [TODO] Upload expenses for Claude
```

## Files Created

### 1. **parsers/next_parser.py**
Main parser implementation with:
- `ActionItem`: Dataclass for a single action item (text + completed flag)
- `Project`: Dataclass for a project with its action items
- `NextNoteData`: Output dataclass containing parsed note data
- `NextParser`: Main parser class implementing `NoteParser` interface
- `format_as_text()`: Static method for text output formatting
- `format_as_org()`: Static method for org mode output formatting

### 2. **schemas/next.schema.json**
JSON Schema for validation of parsed NEXT notes, defining:
- `note_id`: Unique identifier
- `note_date`: ISO format creation date
- `formatted_date`: Human-readable date (d/m)
- `projects`: Array of projects with items
- `raw_text`: Original note text

### 3. **test_next_parser.py**
Comprehensive test suite with 14 test cases:

#### Parsing Tests
- ✓ Valid NEXT note detection
- ✓ Case-insensitive header matching
- ✓ Rejection of non-dict input
- ✓ Empty text handling
- ✓ Missing NEXT header rejection

#### Functionality Tests
- ✓ Simple note parsing
- ✓ Example from requirements (3 projects, 7 items)
- ✓ Mixed completed/pending items
- ✓ Multiple projects
- ✓ Empty projects
- ✓ Dataclass output validation
- ✓ Error handling

#### Output Format Tests
- ✓ Text mode formatting
- ✓ Org mode formatting

### 4. **demo_next_parser.py**
Demonstration script showing:
- Example NEXT note parsing
- Text mode output
- Org mode output
- Raw JSON representation

## Integration

The parser is integrated into the main parsing system via:

1. **Registration in parse_notes.py**:
   ```python
   registry.register(NextParser)
   ```

2. **Automatic Detection**: The parser automatically detects NEXT notes through the `can_parse()` method

3. **Schema Validation**: Parsed data is validated against `next.schema.json`

## Usage Examples

### Programmatic Usage
```python
from parsers.next_parser import NextParser

parser = NextParser()

note_data = {
    "id": "next123",
    "title": "Next",
    "text": "Next\n\nProject A\n\n- [ ] Task 1",
    "timestamps": {"created": "2026-03-13T10:00:00"}
}

parsed = parser.parse(note_data)

# Output in different formats
print(parser.format_as_text(parsed))
print(parser.format_as_org(parsed))
```

### Demo
```bash
python demo_next_parser.py
```

## Test Results

All 14 tests pass successfully:
```
test_can_parse_case_insensitive ... ok
test_can_parse_returns_false_with_empty_text ... ok
test_can_parse_returns_false_with_non_dict ... ok
test_can_parse_returns_false_without_next_header ... ok
test_can_parse_with_valid_next_note ... ok
test_parse_empty_projects ... ok
test_parse_example_from_requirements ... ok
test_parse_multiple_projects ... ok
test_parse_outputs_dataclass ... ok
test_parse_raises_error_with_non_dict ... ok
test_parse_simple_next_note ... ok
test_parse_with_mixed_completed_items ... ok
test_org_mode_output ... ok
test_text_mode_output ... ok

Ran 14 tests in 0.002s - OK
```

## Data Model

### Input Format
```
Next

Project Name

- [ ] Pending action item
- [x] Completed action item
```

### Output Data Structure
```json
{
  "note_id": "string",
  "note_date": "2026-03-13",
  "formatted_date": "13/3",
  "projects": [
    {
      "name": "Project Name",
      "items": [
        {
          "text": "Action item text",
          "completed": false
        }
      ]
    }
  ],
  "raw_text": "Original note text"
}
```

## Implementation Notes

- **Date Parsing**: Handles both ISO format (`2026-03-13T10:00:00`) and standard format timestamps
- **Flexible Formatting**: Uses day/month format without leading zeros (e.g., "13/3" not "13/03")
- **Case Insensitivity**: Note header "NEXT" is recognized in any case
- **Checkbox Recognition**: Handles both `[ ]` for pending and `[x]` or `[X]` for completed items
- **Project Identification**: Any non-checkbox line after the NEXT header is treated as a project name
- **Empty Line Tolerance**: Properly handles blank lines between projects and items

## Compatibility

- Python: 3.10+
- Dependencies: jsonschema, dataclasses, typing
- Tested with Python 3.14.3
