# Agent Commands

## Setup
```bash
pip install -r requirements.txt
```

## Commands
- **Run**: `python parse_notes.py` (CLI tool for parsing notes)
- **Build**: N/A (no build step)
- **Lint**: `make lint`
- **Tests**: `make test`
- **Dev**: N/A (CLI tool, no dev server)

## Tech Stack
- **Language**: Python 3.14
- **Dependencies**: click, jsonschema, pillow (see requirements.txt)
- **Entry Point**: parse_notes.py (CLI using click)

## Architecture
- Parser registry system with pluggable note parsers
- Multiple specialized parsers: HackerNewsParser, TimeEntryParser, TrainingParser, GenericNotesParser
- JSON schema validation for parsed outputs
- Processes JSON input files and outputs parsed results

## Code Style
- Minimal comments (code is self-documenting)
- Type hints throughout
- Dataclasses for structured data
- Click decorators for CLI
