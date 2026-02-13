# NATS Training Parser - End-to-End Example

This is a complete end-to-end example that demonstrates:
1. **Publisher** (google-keep-notes-parser): Reads sample training data from JSON and sends it to NATS
2. **NATS Server**: Acts as the message broker
3. **Subscriber** (training-parser-antlr4): Consumes messages from NATS, parses with ANTLR grammar, and prints results

## Acceptance Criteria ✅

✅ **An application sends data to NATS**
- `nats_publisher.py`: Reads `sample/training/sample1.json` and publishes to NATS topic `training.notes`

✅ **ANTLR receives the message, parses it, and prints it to the console**
- `nats_subscriber.py` (in training-parser-antlr4): Subscribes to `training.notes`, uses ANTLR parser to parse training text, prints exercises to console

## Components

### 1. Publisher Application
**Location**: `/var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser/nats_publisher.py`

```python
# Reads sample/training/sample1.json
# Connects to NATS at localhost:4222
# Publishes JSON message to "training.notes" topic
```

**Data Structure** (from sample1.json):
```json
{
  "id": "aaaaaaaaaaa.bbbbbbbbbbbbbbbb",
  "title": "Training",
  "text": "☐ Bp\n  ☐ 2x30x13.6\n  ☐ 2x15x22.1\n...",
  "archived": false,
  "timestamps": {
    "created": "2026-01-23 02:00:49.707000+00:00",
    "edited": "2026-01-23 03:52:32.077000+00:00"
  },
  ...
}
```

### 2. NATS Message Broker
**Topic**: `training.notes`
- Lightweight, high-performance messaging system
- Runs in Docker: `nats:latest`
- Default port: `4222`

### 3. Subscriber Application
**Location**: `~/repos/training-parser-antlr4/nats_subscriber.py`

Subscribes to NATS and:
1. Receives JSON message with training data
2. Extracts the "text" field containing training exercises
3. Parses with ANTLR grammar (`training.g4`)
4. Converts to structured Exercise objects with:
   - Exercise name (e.g., "Bp", "Mr", "Ms")
   - Repetitions and weights for each set
5. Prints formatted output to console

## Running the Example

### Prerequisites
- Docker (for NATS server)
- Python 3.14+
- uv package manager

### Step 1: Start NATS Server
```bash
docker run -d --name nats-test -p 4222:4222 nats:latest
```

### Step 2: Start the Subscriber (in Terminal 1)
```bash
cd ~/repos/training-parser-antlr4
uv run python3 nats_subscriber.py
```

Expected output:
```
🚀 Starting NATS Training Parser Subscriber
Connecting to NATS at localhost:4222...
✓ Connected to NATS

Listening for messages on topic 'training.notes'...
Press Ctrl+C to exit
```

### Step 3: Publish Sample Data (in Terminal 2)
```bash
cd /var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser
uv run python3 nats_publisher.py
```

Expected output:
```
Publishing message: {
  "id": "aaaaaaaaaaa.bbbbbbbbbbbbbbbb",
  "title": "Training ",
  ...
}
✓ Published to topic 'training.notes'
```

### Step 4: Verify Subscriber Output
The subscriber terminal should show:

```
============================================================
📩 Received message from NATS
============================================================
Message ID: aaaaaaaaaaa.bbbbbbbbbbbbbbbb
Title: Training
Created: 2026-01-23 02:00:49.707000+00:00
Edited: 2026-01-23 03:52:32.077000+00:00

Raw training text:
☐ Bp
  ☐ 2x30x13.6
  ☐ 2x15x22.1
☐ Mr
  ☐ 2x20x26
  ☐ 2x10x32
...

------------------------------------------------------------
🔍 Parsing with ANTLR Training Grammar
------------------------------------------------------------
✓ Successfully parsed 5 exercises:

1. Bp
   Set 1: 30 reps × 13.6kg
   Set 2: 15 reps × 22.1kg
2. Mr
   Set 1: 20 reps × 26kg
   Set 2: 10 reps × 32kg
3. Ms
   Set 1: 10 reps × 63kg
4. Ribp
   Set 1: 20 reps × 25kg
5. M pec fly
   Set 1: 20 reps × 19kg

============================================================
```

## Component Testing

### Test Publisher Component
```bash
cd /var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser
uv run python3 test_e2e_simple.py
```

This verifies:
- ✓ Publisher can read sample JSON file
- ✓ NATS module is available
- ✓ ANTLR parser can be imported
- ✓ All required script files exist

### Test Full E2E Pipeline
Requires NATS server running:
```bash
docker run -d --name nats-test -p 4222:4222 nats:latest
uv run python3 test_e2e_full.py
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Google Keep Notes Parser (Publisher)                        │
├─────────────────────────────────────────────────────────────┤
│ sample/training/sample1.json                                │
│         ↓                                                   │
│ nats_publisher.py                                           │
│ ├─ Read JSON file                                          │
│ ├─ Connect to NATS                                         │
│ └─ Publish to "training.notes" topic                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  NATS Server         │
        │  Port: 4222          │
        │  Topic: training.notes
        └──────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────────────┐
│ Training Parser ANTLR4 (Subscriber)                         │
├──────────────────────────────────────────────────────────────┤
│ nats_subscriber.py                                          │
│ ├─ Connect to NATS                                         │
│ ├─ Subscribe to "training.notes"                           │
│ ├─ Parse JSON message                                      │
│ ├─ Extract training text                                   │
│ ├─ Use ANTLR Grammar (training.g4) to parse              │
│ └─ Print Exercises and Sets to console                    │
└──────────────────────────────────────────────────────────────┘
```

## File Locations

- **Publisher**: `/var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser/nats_publisher.py`
- **Sample Data**: `/var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser/sample/training/sample1.json`
- **Subscriber**: `~/repos/training-parser-antlr4/nats_subscriber.py`
- **ANTLR Grammar**: `~/repos/training-parser-antlr4/training.g4`
- **Parser Module**: `~/repos/training-parser-antlr4/parser/parser.py`

## Dependencies Added

Both projects have been updated with NATS support:

```toml
# google-keep-notes-parser/pyproject.toml
dependencies = [
    ...
    "nats-py>=2.6.0",
]

# training-parser-antlr4/pyproject.toml
dependencies = [
    ...
    "nats-py>=2.6.0",
    ...
]
```

## Implementation Details

### Publisher (`nats_publisher.py`)
- Uses Python `asyncio` for async operations
- Reads sample JSON file
- Serializes to JSON string
- Publishes to NATS broker
- Closes connection gracefully

### Subscriber (`nats_subscriber.py`)
- Uses Python `asyncio` for async operations
- Connects to NATS broker
- Subscribes to `training.notes` topic
- Handles incoming messages asynchronously
- Parses JSON to extract training text
- Uses ANTLR Parser to parse exercises
- Displays structured output with exercise names and sets
- Handles parsing errors gracefully

### ANTLR Grammar
The `training.g4` grammar defines:
```antlr
workout: exercise+;
exercise: exercise_name ':'? set_ NEWLINE*;
set_: (INT 'x' INT 'x' weight) | (INT 'x' INT) | weight;
```

This parses exercises like:
- `Bp 2x30x13.6` → Exercise "Bp", Set: 30 reps × 13.6kg
- `Mr 2x20x26` → Exercise "Mr", Set: 20 reps × 26kg

## Next Steps

For production deployment:
1. Use environment variables for NATS server URL
2. Add error handling and retry logic
3. Implement message acknowledgments
4. Add logging to files
5. Deploy NATS in Kubernetes or cloud platform
6. Add authentication to NATS
7. Implement message persistence (JetStream)
