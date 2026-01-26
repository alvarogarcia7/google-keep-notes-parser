import unittest
from typing import Any
from unittest.mock import patch, mock_open, MagicMock
from parsers.time_entry_parser import TimeEntryParser


class TestTimeEntryParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = TimeEntryParser()

    def test_can_parse_valid_time_entry_with_3_digit_timestamps(self) -> None:
        note_data = {
            'id': 'test123',
            'title': 'Daily Log',
            'text': '☐ 637 Woke up\n☐ 845 Breakfast\n☐ 1030 Meeting',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:30:00Z'
            }
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_valid_time_entry_with_4_digit_timestamps(self) -> None:
        note_data = {
            'id': 'test456',
            'title': 'Work Log',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee break\n☐ 1420 Lunch',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_mixed_3_and_4_digit_timestamps(self) -> None:
        note_data = {
            'id': 'test789',
            'title': 'Mixed Log',
            'text': '☐ 637 Woke up\n☐ 1053 Coffee\n☐ 730 Exercise',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_whitespace_variations(self) -> None:
        note_data = {
            'id': 'test_whitespace',
            'title': 'Whitespace Test',
            'text': '☐  637   Woke up  \n☐ 1053  Coffee break\n☐  1420    Lunch  ',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_single_entry(self) -> None:
        note_data = {
            'id': 'test_single',
            'title': 'Single Entry',
            'text': '☐ 0637 Woke up',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_invalid_timestamp_format(self) -> None:
        note_data = {
            'id': 'test_invalid',
            'title': 'Invalid Format',
            'text': '☐ 12345 Too many digits\n☐ 67 Too few digits',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_invalid_time_values(self) -> None:
        note_data = {
            'id': 'test_invalid_time',
            'title': 'Invalid Time Values',
            'text': '☐ 2560 Invalid hour\n☐ 1270 Invalid minute',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T12:70:00Z'
            }
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_no_timestamps(self) -> None:
        note_data = {
            'id': 'test_no_timestamps',
            'title': 'No Timestamps',
            'text': 'Just some regular text without timestamps',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_empty_text(self) -> None:
        note_data = {
            'id': 'test_empty',
            'title': 'Empty',
            'text': '',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_non_dict_input(self) -> None:
        self.assertFalse(self.parser.can_parse("not a dict"))
        self.assertFalse(self.parser.can_parse(None))
        self.assertFalse(self.parser.can_parse([]))

    def test_can_parse_with_sub_notes_mixed_with_entries(self) -> None:
        note_data = {
            'id': 'test_subnotes',
            'title': 'With Sub-notes',
            'text': '☐ 0637 Woke up\nSome regular text\n☐ 1053 Coffee break\nMore notes here\n☐ 1420 Lunch',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_checked_boxes(self) -> None:
        note_data = {
            'id': 'test_checked',
            'title': 'Checked Boxes',
            'text': '☑ 0637 Woke up\n☑ 1053 Coffee break\n☐ 1420 Lunch',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_parse_extracts_timestamp_activity_pairs(self) -> None:
        note_data = {
            'id': 'parse_test',
            'title': 'Parse Test',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee break\n☐ 1420 Lunch',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, 'parse_test')
        self.assertEqual(result.title, 'Parse Test')
        self.assertEqual(result.date, '2024-01-15')
        self.assertEqual(len(result.time_entries), 3)
        
        self.assertEqual(result.time_entries[0]['time'], '06:37')
        self.assertEqual(result.time_entries[0]['activity'], 'Woke up')
        self.assertEqual(result.time_entries[1]['time'], '10:53')
        self.assertEqual(result.time_entries[1]['activity'], 'Coffee break')
        self.assertEqual(result.time_entries[2]['time'], '14:20')
        self.assertEqual(result.time_entries[2]['activity'], 'Lunch')

    def test_parse_chronological_sorting(self) -> None:
        note_data = {
            'id': 'sort_test',
            'title': 'Sort Test',
            'text': '☐ 1420 Lunch\n☐ 0637 Woke up\n☐ 1053 Coffee break',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        self.assertEqual(result.time_entries[0]['time'], '06:37')
        self.assertEqual(result.time_entries[1]['time'], '10:53')
        self.assertEqual(result.time_entries[2]['time'], '14:20')

    def test_parse_with_3_digit_timestamps(self) -> None:
        note_data = {
            'id': '3digit_test',
            'title': '3 Digit Test',
            'text': '☐ 637 Woke up\n☐ 845 Breakfast',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T08:45:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['time'], '06:37')
        self.assertEqual(result.time_entries[1]['time'], '08:45')

    def test_parse_with_sub_notes_ignored(self) -> None:
        note_data = {
            'id': 'subnotes_test',
            'title': 'Sub-notes Test',
            'text': '☐ 0637 Woke up\nThis is a regular note\nNot a time entry\n☐ 1053 Coffee break',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['time'], '06:37')
        self.assertEqual(result.time_entries[1]['time'], '10:53')

    def test_parse_preserves_raw_text(self) -> None:
        note_data = {
            'id': 'raw_test',
            'title': 'Raw Test',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.raw_text, '☐ 0637 Woke up\n☐ 1053 Coffee')

    def test_parse_generates_full_timestamps(self) -> None:
        note_data = {
            'id': 'timestamp_test',
            'title': 'Timestamp Test',
            'text': '☐ 0637 Woke up',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.time_entries[0]['timestamp'], '2024-01-15T06:37:00')

    def test_parse_preserves_raw_line(self) -> None:
        note_data = {
            'id': 'rawline_test',
            'title': 'Raw Line Test',
            'text': '☐ 0637 Woke up early today',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.time_entries[0]['raw_line'], '☐ 0637 Woke up early today')

    def test_parse_raises_error_for_non_dict(self) -> None:
        with self.assertRaises(ValueError):
            self.parser.parse("not a dict")

    def test_parse_warning_for_out_of_order_chronological_notes(self) -> None:
        note_data = {
            'id': 'warning_test',
            'title': 'Out of Order',
            'text': '☐ 1420 Lunch\n☐ 0637 Woke up\n☐ 1053 Coffee',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.warnings), 1)
        self.assertIn('out of chronological order', result.warnings[0].lower())
        self.assertIn("['14:20', '06:37', '10:53']", result.warnings[0])
        self.assertIn("['06:37', '10:53', '14:20']", result.warnings[0])

    def test_parse_no_warning_for_in_order_chronological_notes(self) -> None:
        note_data = {
            'id': 'no_warning_test',
            'title': 'In Order',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee\n☐ 1420 Lunch',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.warnings), 0)

    def test_get_schema_returns_valid_dict(self) -> None:
        schema = self.parser.get_schema()
        
        self.assertIsInstance(schema, dict)
        self.assertIn('$schema', schema)
        self.assertIn('title', schema)
        self.assertIn('type', schema)
        self.assertIn('properties', schema)

    def test_get_schema_has_required_properties(self) -> None:
        schema = self.parser.get_schema()
        
        properties = schema.get('properties', {})
        self.assertIn('note_id', properties)
        self.assertIn('title', properties)
        self.assertIn('date', properties)
        self.assertIn('created', properties)
        self.assertIn('time_entries', properties)
        self.assertIn('raw_text', properties)

    def test_get_schema_has_time_entries_structure(self) -> None:
        schema = self.parser.get_schema()
        
        time_entries = schema['properties']['time_entries']
        self.assertEqual(time_entries['type'], 'array')
        self.assertIn('items', time_entries)
        
        entry_schema = time_entries['items']
        entry_properties = entry_schema['properties']
        self.assertIn('timestamp', entry_properties)
        self.assertIn('time', entry_properties)
        self.assertIn('activity', entry_properties)
        self.assertIn('raw_line', entry_properties)

    @patch('builtins.open', new_callable=mock_open, read_data='{"$schema": "test"}')
    def test_get_schema_reads_from_file(self, mock_file: MagicMock) -> None:
        schema = self.parser.get_schema()
        mock_file.assert_called_once()
        call_args = mock_file.call_args[0][0]
        self.assertTrue(call_args.endswith('time_entry.schema.json'))

    def test_parse_handles_missing_timestamps(self) -> None:
        note_data = {
            'id': 'missing_timestamps',
            'title': 'Missing Timestamps',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee',
            'timestamps': {}
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.created, '')
        self.assertEqual(result.date, '')

    def test_parse_handles_missing_title(self) -> None:
        note_data = {
            'id': 'missing_title',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.title, '')

    def test_edge_case_midnight_timestamp(self) -> None:
        note_data = {
            'id': 'midnight_test',
            'title': 'Midnight Test',
            'text': '☐ 0000 Midnight\n☐ 0637 Morning',
            'timestamps': {
                'created': '2024-01-15T00:00:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['time'], '00:00')
        self.assertEqual(result.time_entries[1]['time'], '06:37')

    def test_edge_case_late_night_timestamp(self) -> None:
        note_data = {
            'id': 'late_night_test',
            'title': 'Late Night Test',
            'text': '☐ 2359 Before midnight\n☐ 2300 Evening',
            'timestamps': {
                'created': '2024-01-15T23:00:00Z',
                'edited': '2024-01-15T23:59:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['time'], '23:00')
        self.assertEqual(result.time_entries[1]['time'], '23:59')
        self.assertEqual(len(result.warnings), 1)

    def test_parse_result_dataclass_fields(self) -> None:
        note_data = {
            'id': 'dataclass_test',
            'title': 'Dataclass Test',
            'text': '☐ 0637 Woke up\n☐ 1053 Coffee',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertTrue(hasattr(result, 'note_id'))
        self.assertTrue(hasattr(result, 'title'))
        self.assertTrue(hasattr(result, 'date'))
        self.assertTrue(hasattr(result, 'created'))
        self.assertTrue(hasattr(result, 'last_updated'))
        self.assertTrue(hasattr(result, 'time_entries'))
        self.assertTrue(hasattr(result, 'raw_text'))
        self.assertTrue(hasattr(result, 'warnings'))


if __name__ == '__main__':
    unittest.main()
