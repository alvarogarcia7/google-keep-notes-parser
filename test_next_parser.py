import unittest
import json
import os
from typing import Any, Dict, ClassVar
from dataclasses import asdict
from parsers.next_parser import NextParser, NextNoteData, Project, ActionItem


class TestNextParser(unittest.TestCase):
    actual_schema: ClassVar[Dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'next.schema.json')
        with open(schema_path, 'r') as f:
            cls.actual_schema = json.load(f)

    def setUp(self) -> None:
        self.parser = NextParser()

    def test_can_parse_with_valid_next_note(self) -> None:
        note_data = {
            'text': 'Next\n\nProject A\n\n- [ ] Task 1\n- [x] Task 2',
            'title': 'Next'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_without_next_header(self) -> None:
        note_data = {
            'text': 'Project A\n\n- [ ] Task 1',
            'title': 'Next'
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_empty_text(self) -> None:
        note_data = {
            'text': '',
            'title': 'Next'
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_non_dict(self) -> None:
        note_data = "not a dict"
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_case_insensitive(self) -> None:
        note_data = {
            'text': 'NEXT\n\nProject A\n\n- [ ] Task 1',
            'title': 'Next'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_parse_raises_error_with_non_dict(self) -> None:
        with self.assertRaises(ValueError) as context:
            self.parser.parse("not a dict")
        self.assertEqual(str(context.exception), "note_data must be a dictionary")

    def test_parse_simple_next_note(self) -> None:
        note_data = {
            "id": "next123",
            "title": "Next",
            "text": "Next\n\nProject A\n\n- [ ] Task 1\n- [x] Task 2",
            "timestamps": {
                "created": "2026-03-13T10:00:00",
                "edited": "2026-03-13T10:30:00"
            }
        }
        result = self.parser.parse(note_data)

        self.assertIsInstance(result, NextNoteData)
        self.assertEqual(result.note_id, 'next123')
        self.assertEqual(result.formatted_date, '13/3')
        self.assertEqual(len(result.projects), 1)
        self.assertEqual(result.projects[0].name, 'Project A')
        self.assertEqual(len(result.projects[0].items), 2)
        self.assertEqual(result.projects[0].items[0].text, 'Task 1')
        self.assertFalse(result.projects[0].items[0].completed)
        self.assertEqual(result.projects[0].items[1].text, 'Task 2')
        self.assertTrue(result.projects[0].items[1].completed)

    def test_parse_example_from_requirements(self) -> None:
        """Test with the example from the requirements"""
        note_data = {
            "id": "next_example",
            "title": "Next",
            "text": """Next

Project TCMS

- [ ] Achieve a doctor build that is off-line

- [ ] Download said images

- [ ] Upload them to FMA

- [ ] Get approval

Project admin

- [ ] Upload all hourly reports for boss

- [ ] Upload expenses for Claude

Project projector

- [ ] Configure project for TRM""",
            "timestamps": {
                "created": "2026-03-13T10:00:00",
                "edited": "2026-03-13T10:30:00"
            }
        }
        result = self.parser.parse(note_data)

        self.assertIsInstance(result, NextNoteData)
        self.assertEqual(result.formatted_date, '13/3')
        self.assertEqual(len(result.projects), 3)

        # Check Project TCMS
        self.assertEqual(result.projects[0].name, 'Project TCMS')
        self.assertEqual(len(result.projects[0].items), 4)
        self.assertEqual(result.projects[0].items[0].text, 'Achieve a doctor build that is off-line')
        self.assertFalse(result.projects[0].items[0].completed)

        # Check Project admin
        self.assertEqual(result.projects[1].name, 'Project admin')
        self.assertEqual(len(result.projects[1].items), 2)
        self.assertEqual(result.projects[1].items[0].text, 'Upload all hourly reports for boss')

        # Check Project projector
        self.assertEqual(result.projects[2].name, 'Project projector')
        self.assertEqual(len(result.projects[2].items), 1)
        self.assertEqual(result.projects[2].items[0].text, 'Configure project for TRM')

    def test_parse_with_mixed_completed_items(self) -> None:
        """Test with both completed and pending items"""
        note_data = {
            "id": "next_mixed",
            "title": "Next",
            "text": """Next

Project Work

- [x] Completed task
- [ ] Pending task
- [x] Another done task""",
            "timestamps": {
                "created": "2026-03-10T14:20:30",
                "edited": "2026-03-10T14:25:00"
            }
        }
        result = self.parser.parse(note_data)

        self.assertEqual(result.formatted_date, '10/3')
        self.assertEqual(len(result.projects), 1)
        self.assertEqual(len(result.projects[0].items), 3)
        self.assertTrue(result.projects[0].items[0].completed)
        self.assertFalse(result.projects[0].items[1].completed)
        self.assertTrue(result.projects[0].items[2].completed)

    def test_parse_multiple_projects(self) -> None:
        """Test parsing multiple projects"""
        note_data = {
            "id": "next_multi",
            "title": "Next",
            "text": """Next

Project 1

- [ ] Task 1.1
- [ ] Task 1.2

Project 2

- [ ] Task 2.1

Project 3

- [ ] Task 3.1
- [ ] Task 3.2
- [ ] Task 3.3""",
            "timestamps": {
                "created": "2026-03-13T10:00:00"
            }
        }
        result = self.parser.parse(note_data)

        self.assertEqual(len(result.projects), 3)
        self.assertEqual(result.projects[0].name, 'Project 1')
        self.assertEqual(len(result.projects[0].items), 2)
        self.assertEqual(result.projects[1].name, 'Project 2')
        self.assertEqual(len(result.projects[1].items), 1)
        self.assertEqual(result.projects[2].name, 'Project 3')
        self.assertEqual(len(result.projects[2].items), 3)

    def test_parse_outputs_dataclass(self) -> None:
        """Test that parse returns the correct dataclass"""
        note_data = {
            "id": "next123",
            "title": "Next",
            "text": "Next\n\nProject A\n\n- [ ] Task 1",
            "timestamps": {
                "created": "2026-03-13T10:00:00"
            }
        }
        result = self.parser.parse(note_data)

        # Convert to dict to check schema
        result_dict = asdict(result)
        self.assertIn('note_id', result_dict)
        self.assertIn('note_date', result_dict)
        self.assertIn('formatted_date', result_dict)
        self.assertIn('projects', result_dict)
        self.assertIn('raw_text', result_dict)

    def test_parse_empty_projects(self) -> None:
        """Test handling of projects without items"""
        note_data = {
            "id": "next_empty",
            "title": "Next",
            "text": """Next

Project Empty

Project Another""",
            "timestamps": {
                "created": "2026-03-13T10:00:00"
            }
        }
        result = self.parser.parse(note_data)

        self.assertEqual(len(result.projects), 2)
        self.assertEqual(len(result.projects[0].items), 0)
        self.assertEqual(len(result.projects[1].items), 0)


class TestNextParserOutputFormatting(unittest.TestCase):
    """Test output formatting in text and org modes"""

    def setUp(self) -> None:
        self.parser = NextParser()

    def test_text_mode_output(self) -> None:
        """Test generating text mode output"""
        note_data = {
            "id": "next_format",
            "title": "Next",
            "text": """Next

Project TCMS

- [ ] Achieve a doctor build that is off-line
- [x] Download said images

Project admin

- [ ] Upload all hourly reports for boss""",
            "timestamps": {
                "created": "2026-03-13T10:00:00"
            }
        }
        result = self.parser.parse(note_data)

        # Create text output
        text_output = self._format_as_text(result)
        self.assertIn('Next for 13/3', text_output)
        self.assertIn('Project TCMS', text_output)
        self.assertIn('Achieve a doctor build that is off-line', text_output)

    def test_org_mode_output(self) -> None:
        """Test generating org mode output"""
        note_data = {
            "id": "next_format",
            "title": "Next",
            "text": """Next

Project TCMS

- [ ] Achieve a doctor build that is off-line
- [x] Download said images""",
            "timestamps": {
                "created": "2026-03-13T10:00:00"
            }
        }
        result = self.parser.parse(note_data)

        # Create org mode output
        org_output = self._format_as_org(result)
        self.assertIn('Next for 13/3', org_output)
        self.assertIn('* Project TCMS', org_output)
        self.assertIn('[TODO]', org_output)
        self.assertIn('Achieve a doctor build that is off-line', org_output)

    def _format_as_text(self, result: NextNoteData) -> str:
        """Format result as plain text"""
        output = [f"Next for {result.formatted_date}"]
        output.append(f"Total Projects: {len(result.projects)}\n")

        for project in result.projects:
            output.append(f"{project.name}")
            for item in project.items:
                status = "✓" if item.completed else "•"
                output.append(f"  {status} {item.text}")
            output.append("")

        return "\n".join(output)

    def _format_as_org(self, result: NextNoteData) -> str:
        """Format result as org mode"""
        output = [f"* Next for {result.formatted_date}"]
        output.append(f"Total Projects: {len(result.projects)}\n")

        for project in result.projects:
            output.append(f"** {project.name}")
            for item in project.items:
                status = "DONE" if item.completed else "TODO"
                output.append(f"   - [{status}] {item.text}")
            output.append("")

        return "\n".join(output)


if __name__ == '__main__':
    unittest.main()
