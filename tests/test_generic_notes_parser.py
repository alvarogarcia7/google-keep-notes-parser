import unittest
import json
import os
from typing import Any, Dict, List
from unittest.mock import mock_open, patch, MagicMock
from parsers.generic_notes_parser import GenericNotesParser, GenericNote, Checkbox


class TestGenericNotesParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = GenericNotesParser()

    def test_can_parse_returns_true_for_dict(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'test123',
            'title': 'Test Note',
            'text': 'Some text'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_returns_true_for_empty_dict(self) -> None:
        note_data: Dict[str, Any] = {}
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_non_dict(self) -> None:
        self.assertFalse(self.parser.can_parse("not a dict"))
        self.assertFalse(self.parser.can_parse(None))
        self.assertFalse(self.parser.can_parse([]))
        self.assertFalse(self.parser.can_parse(123))

    def test_parse_basic_note_without_links_or_checkboxes(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note123',
            'title': 'My Note',
            'text': 'This is a simple note\nWith multiple lines\nOf text'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, 'note123')
        self.assertEqual(result.title, 'My Note')
        self.assertEqual(result.links, [])
        self.assertEqual(result.checkboxes, [])
        self.assertEqual(result.rest, ['This is a simple note', 'With multiple lines', 'Of text'])

    def test_parse_note_with_single_http_link(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note456',
            'title': 'Note with link',
            'text': 'Check out http://example.com for more info'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 1)
        self.assertIn('http://example.com', result.links)

    def test_parse_note_with_single_https_link(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note789',
            'title': 'Secure link',
            'text': 'Visit https://secure-example.com'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 1)
        self.assertIn('https://secure-example.com', result.links)

    def test_parse_note_with_www_link(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note999',
            'title': 'WWW link',
            'text': 'Go to www.example.com'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 1)
        self.assertIn('www.example.com', result.links)

    def test_parse_note_with_multiple_links(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note111',
            'title': 'Multiple links',
            'text': 'Visit https://example1.com and http://example2.com or www.example3.com'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 3)
        self.assertIn('https://example1.com', result.links)
        self.assertIn('http://example2.com', result.links)
        self.assertIn('www.example3.com', result.links)

    def test_parse_note_with_duplicate_links(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note222',
            'title': 'Duplicate links',
            'text': 'https://example.com and https://example.com again'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 1)
        self.assertIn('https://example.com', result.links)

    def test_parse_note_with_unchecked_checkbox(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note333',
            'title': 'Todo list',
            'text': '☐ Buy groceries'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 1)
        self.assertEqual(result.checkboxes[0].checked, False)
        self.assertEqual(result.checkboxes[0].text, 'Buy groceries')

    def test_parse_note_with_checked_checkbox(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note444',
            'title': 'Completed task',
            'text': '☑ Finish homework'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 1)
        self.assertEqual(result.checkboxes[0].checked, True)
        self.assertEqual(result.checkboxes[0].text, 'Finish homework')

    def test_parse_note_with_multiple_checkboxes(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note555',
            'title': 'Todo list',
            'text': '☐ Task 1\n☑ Task 2\n☐ Task 3'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 3)
        self.assertEqual(result.checkboxes[0].checked, False)
        self.assertEqual(result.checkboxes[0].text, 'Task 1')
        self.assertEqual(result.checkboxes[1].checked, True)
        self.assertEqual(result.checkboxes[1].text, 'Task 2')
        self.assertEqual(result.checkboxes[2].checked, False)
        self.assertEqual(result.checkboxes[2].text, 'Task 3')

    def test_parse_note_with_checkboxes_and_links(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note666',
            'title': 'Mixed content',
            'text': '☐ Check https://example.com\n☑ Visit http://test.com'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 2)
        self.assertEqual(len(result.links), 2)
        self.assertIn('https://example.com', result.links)
        self.assertIn('http://test.com', result.links)

    def test_parse_note_with_checkboxes_links_and_rest(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note777',
            'title': 'Full note',
            'text': 'Introduction text\n☐ Task 1 https://example.com\nMiddle paragraph\n☑ Task 2\nConclusion'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 2)
        self.assertEqual(len(result.links), 1)
        self.assertEqual(len(result.rest), 3)
        self.assertIn('Introduction text', result.rest)
        self.assertIn('Middle paragraph', result.rest)
        self.assertIn('Conclusion', result.rest)

    def test_parse_note_with_empty_lines_ignored(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note888',
            'title': 'Empty lines',
            'text': 'Line 1\n\n\nLine 2\n\n'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.rest), 2)
        self.assertEqual(result.rest, ['Line 1', 'Line 2'])

    def test_parse_note_with_whitespace_variations(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note999',
            'title': 'Whitespace',
            'text': '  ☐  Task with spaces  \n☑   Another task   '
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 2)
        self.assertEqual(result.checkboxes[0].text, 'Task with spaces')
        self.assertEqual(result.checkboxes[1].text, 'Another task')

    def test_parse_note_with_empty_text(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note000',
            'title': 'Empty',
            'text': ''
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(result.links, [])
        self.assertEqual(result.checkboxes, [])
        self.assertEqual(result.rest, [])

    def test_parse_note_with_missing_fields(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'Some text https://example.com'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, '')
        self.assertEqual(result.title, '')
        self.assertEqual(len(result.links), 1)

    def test_parse_note_with_missing_text_field(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note123',
            'title': 'No text'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, 'note123')
        self.assertEqual(result.title, 'No text')
        self.assertEqual(result.links, [])
        self.assertEqual(result.checkboxes, [])
        self.assertEqual(result.rest, [])

    def test_parse_raises_error_for_non_dict(self) -> None:
        with self.assertRaises(ValueError) as context:
            self.parser.parse("not a dict")
        self.assertIn("note_data must be a dictionary", str(context.exception))

    def test_parse_note_with_complex_urls(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'url_test',
            'title': 'Complex URLs',
            'text': 'Check https://example.com/path/to/page?param=value&other=123#anchor'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 1)
        self.assertIn('https://example.com/path/to/page?param=value&other=123#anchor', result.links)

    def test_parse_note_with_urls_in_markdown_links(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'markdown_test',
            'title': 'Markdown',
            'text': '[Example](https://example.com) and [Test](http://test.com)'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 2)
        self.assertIn('https://example.com', result.links)
        self.assertIn('http://test.com', result.links)

    def test_parse_note_with_urls_in_parentheses(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'parens_test',
            'title': 'Parentheses',
            'text': 'Check out (https://example.com) for details'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.links), 1)
        self.assertIn('https://example.com', result.links)

    def test_extract_links_from_multiline_text(self) -> None:
        text: str = 'Line 1 https://example1.com\nLine 2 http://example2.com\nLine 3 www.example3.com'
        links: List[str] = self.parser._extract_links(text)
        
        self.assertEqual(len(links), 3)
        self.assertIn('https://example1.com', links)
        self.assertIn('http://example2.com', links)
        self.assertIn('www.example3.com', links)

    def test_extract_links_with_no_links(self) -> None:
        text: str = 'This text has no links at all'
        links: List[str] = self.parser._extract_links(text)
        
        self.assertEqual(len(links), 0)

    def test_extract_links_empty_string(self) -> None:
        text: str = ''
        links: List[str] = self.parser._extract_links(text)
        
        self.assertEqual(len(links), 0)

    def test_extract_links_deduplication(self) -> None:
        text: str = 'https://example.com and https://example.com again'
        links: List[str] = self.parser._extract_links(text)
        
        self.assertEqual(len(links), 1)

    def test_checkbox_pattern_matches_unchecked(self) -> None:
        import re
        pattern = self.parser.CHECKBOX_PATTERN
        text = '☐ Some task'
        match = re.match(pattern, text)
        
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group(1), '☐')
        self.assertEqual(match.group(2), 'Some task')

    def test_checkbox_pattern_matches_checked(self) -> None:
        import re
        pattern = self.parser.CHECKBOX_PATTERN
        text = '☑ Completed task'
        match = re.match(pattern, text)
        
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group(1), '☑')
        self.assertEqual(match.group(2), 'Completed task')

    def test_checkbox_pattern_matches_with_whitespace(self) -> None:
        import re
        pattern = self.parser.CHECKBOX_PATTERN
        text = '  ☐   Task with spaces  '
        match = re.match(pattern, text.strip())
        
        self.assertIsNotNone(match)

    def test_url_pattern_attribute(self) -> None:
        self.assertIsNotNone(self.parser.URL_PATTERN)
        self.assertIn('https?', self.parser.URL_PATTERN)

    def test_checkbox_pattern_attribute(self) -> None:
        self.assertEqual(self.parser.CHECKBOX_PATTERN, r'^\s*([\u2610\u2611])\s*(.+)$')

    def test_checked_box_constant(self) -> None:
        self.assertEqual(self.parser.CHECKED_BOX, '☑')

    def test_unchecked_box_constant(self) -> None:
        self.assertEqual(self.parser.UNCHECKED_BOX, '☐')

    def test_get_schema_returns_valid_dict(self) -> None:
        schema: Dict[str, Any] = self.parser.get_schema()
        
        self.assertIsInstance(schema, dict)
        self.assertIn('$schema', schema)
        self.assertIn('type', schema)
        self.assertIn('properties', schema)

    def test_get_schema_has_required_properties(self) -> None:
        schema: Dict[str, Any] = self.parser.get_schema()
        
        properties = schema.get('properties', {})
        self.assertIn('note_id', properties)
        self.assertIn('title', properties)
        self.assertIn('links', properties)
        self.assertIn('checkboxes', properties)
        self.assertIn('rest', properties)

    def test_get_schema_links_is_array_of_strings(self) -> None:
        schema: Dict[str, Any] = self.parser.get_schema()
        
        links_schema = schema['properties']['links']
        self.assertEqual(links_schema['type'], 'array')
        self.assertEqual(links_schema['items']['type'], 'string')

    def test_get_schema_checkboxes_structure(self) -> None:
        schema: Dict[str, Any] = self.parser.get_schema()
        
        checkboxes_schema = schema['properties']['checkboxes']
        self.assertEqual(checkboxes_schema['type'], 'array')
        self.assertIn('items', checkboxes_schema)
        
        checkbox_item = checkboxes_schema['items']
        self.assertEqual(checkbox_item['type'], 'object')
        self.assertIn('checked', checkbox_item['properties'])
        self.assertIn('text', checkbox_item['properties'])

    def test_get_schema_rest_is_array_of_strings(self) -> None:
        schema: Dict[str, Any] = self.parser.get_schema()
        
        rest_schema = schema['properties']['rest']
        self.assertEqual(rest_schema['type'], 'array')
        self.assertEqual(rest_schema['items']['type'], 'string')

    @patch('builtins.open', new_callable=mock_open, read_data='{"$schema": "test"}')
    def test_get_schema_reads_from_file(self, mock_file: MagicMock) -> None:
        schema = self.parser.get_schema()
        mock_file.assert_called_once()
        call_args = mock_file.call_args[0][0]
        self.assertTrue(call_args.endswith('generic_notes.schema.json'))

    def test_checkbox_dataclass_fields(self) -> None:
        checkbox = Checkbox(checked=True, text='Test task')
        
        self.assertTrue(hasattr(checkbox, 'checked'))
        self.assertTrue(hasattr(checkbox, 'text'))
        self.assertEqual(checkbox.checked, True)
        self.assertEqual(checkbox.text, 'Test task')

    def test_generic_note_dataclass_fields(self) -> None:
        note = GenericNote(
            note_id='123',
            title='Test',
            links=['http://example.com'],
            checkboxes=[],
            rest=['Some text']
        )
        
        self.assertTrue(hasattr(note, 'note_id'))
        self.assertTrue(hasattr(note, 'title'))
        self.assertTrue(hasattr(note, 'links'))
        self.assertTrue(hasattr(note, 'checkboxes'))
        self.assertTrue(hasattr(note, 'rest'))

    def test_parse_note_with_special_characters_in_text(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'special_chars',
            'title': 'Special',
            'text': 'Text with émojis 🎉 and spëcial çhars'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.rest), 1)
        self.assertIn('émojis', result.rest[0])

    def test_parse_note_with_long_checkbox_text(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'long_checkbox',
            'title': 'Long',
            'text': '☐ This is a very long checkbox text that goes on and on with lots of details'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(len(result.checkboxes), 1)
        self.assertEqual(result.checkboxes[0].text, 'This is a very long checkbox text that goes on and on with lots of details')

    def test_parse_note_preserves_order_of_elements(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'order_test',
            'title': 'Order',
            'text': 'First line\n☐ Checkbox 1\nSecond line\n☑ Checkbox 2\nThird line'
        }
        result: GenericNote = self.parser.parse(note_data)
        
        self.assertEqual(result.rest[0], 'First line')
        self.assertEqual(result.checkboxes[0].text, 'Checkbox 1')
        self.assertEqual(result.rest[1], 'Second line')
        self.assertEqual(result.checkboxes[1].text, 'Checkbox 2')
        self.assertEqual(result.rest[2], 'Third line')


if __name__ == '__main__':
    unittest.main()
