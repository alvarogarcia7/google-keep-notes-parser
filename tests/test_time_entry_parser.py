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

    def test_parse_activity_with_single_numbered_sub_item(self) -> None:
        note_data = {
            'id': 'sub_activity_single',
            'title': 'Sub-Activity Single Test',
            'text': '☐ 0900 Work 1. Code review\n☐ 1000 Break',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'Work 1. Code review')
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review')
        self.assertEqual(result.time_entries[1]['activity'], 'Break')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Break')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_parse_activity_with_multiple_numbered_sub_items(self) -> None:
        note_data = {
            'id': 'sub_activity_multiple',
            'title': 'Sub-Activity Multiple Test',
            'text': '☐ 0900 Work 1. Code review\n☐ 0930 Work 2. Testing\n☐ 1000 Work 3. Documentation',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Testing')
        self.assertEqual(result.time_entries[2]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[2]['sub_activity'], 'Documentation')

    def test_parse_activity_without_sub_items(self) -> None:
        note_data = {
            'id': 'no_sub_activity',
            'title': 'No Sub-Activity Test',
            'text': '☐ 0900 Morning meeting\n☐ 1000 Coffee break\n☐ 1100 Email',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T11:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        for entry in result.time_entries:
            self.assertEqual(entry['activity'], entry['main_activity'])
            self.assertEqual(entry['sub_activity'], '')

    def test_parse_mixed_activities_with_and_without_sub_items(self) -> None:
        note_data = {
            'id': 'mixed_activities',
            'title': 'Mixed Activities Test',
            'text': '☐ 0900 Work 1. Code review\n☐ 0930 Coffee break\n☐ 1000 Work 2. Testing\n☐ 1100 Lunch',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T11:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 4)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Coffee break')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')
        self.assertEqual(result.time_entries[2]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[2]['sub_activity'], 'Testing')
        self.assertEqual(result.time_entries[3]['main_activity'], 'Lunch')
        self.assertEqual(result.time_entries[3]['sub_activity'], '')

    def test_parse_activity_with_number_but_no_period(self) -> None:
        note_data = {
            'id': 'number_no_period',
            'title': 'Number No Period Test',
            'text': '☐ 0900 Task 1 complete\n☐ 1000 Task 2 in progress',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Task 1 complete')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Task 2 in progress')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_parse_activity_with_multiple_periods(self) -> None:
        note_data = {
            'id': 'multiple_periods',
            'title': 'Multiple Periods Test',
            'text': '☐ 0900 Work 1. Code review. Final check\n☐ 1000 Meeting 2. Q1 planning. Budget discussion',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review. Final check')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Meeting')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Q1 planning. Budget discussion')

    def test_parse_activity_with_double_digit_numbers(self) -> None:
        note_data = {
            'id': 'double_digit_numbers',
            'title': 'Double Digit Numbers Test',
            'text': '☐ 0900 Work 10. Code review\n☐ 1000 Work 11. Testing\n☐ 1100 Work 99. Final review',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T11:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Testing')
        self.assertEqual(result.time_entries[2]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[2]['sub_activity'], 'Final review')

    def test_parse_activity_with_whitespace_variations_in_sub_items(self) -> None:
        note_data = {
            'id': 'whitespace_sub_items',
            'title': 'Whitespace Sub Items Test',
            'text': '☐ 0900 Work  1.  Code review  \n☐ 1000 Meeting 2.    Planning session\n☐ 1100 Break',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T11:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Meeting')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Planning session')

    def test_parse_activity_edge_case_period_at_start(self) -> None:
        note_data = {
            'id': 'period_at_start',
            'title': 'Period At Start Test',
            'text': '☐ 0900 1. First task\n☐ 1000 Regular task',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], '1. First task')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Regular task')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_parse_activity_with_complex_sub_activity_text(self) -> None:
        note_data = {
            'id': 'complex_sub_activity',
            'title': 'Complex Sub-Activity Test',
            'text': '☐ 0900 Development 1. Implemented feature X with unit tests and documentation\n☐ 1030 Meeting 2. Discussed Q1 goals, budget allocation, and team structure',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Development')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Implemented feature X with unit tests and documentation')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Meeting')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Discussed Q1 goals, budget allocation, and team structure')

    def test_parse_validates_schema_with_sub_activities(self) -> None:
        note_data = {
            'id': 'schema_validation',
            'title': 'Schema Validation Test',
            'text': '☐ 0900 Work 1. Code review\n☐ 1000 Break',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        schema = self.parser.get_schema()
        
        for entry in result.time_entries:
            self.assertIn('main_activity', entry)
            self.assertIn('sub_activity', entry)
            self.assertIsInstance(entry['main_activity'], str)
            self.assertIsInstance(entry['sub_activity'], str)
        
        entry_properties = schema['properties']['time_entries']['items']['properties']
        self.assertIn('main_activity', entry_properties)
        self.assertIn('sub_activity', entry_properties)

    def test_parse_empty_sub_activity_is_empty_string(self) -> None:
        note_data = {
            'id': 'empty_sub_activity',
            'title': 'Empty Sub-Activity Test',
            'text': '☐ 0900 Simple task\n☐ 1000 Another task',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        for entry in result.time_entries:
            self.assertIsInstance(entry['sub_activity'], str)
            self.assertEqual(entry['sub_activity'], '')
            self.assertNotEqual(entry['sub_activity'], None)

    def test_parse_activity_preserves_full_activity_text(self) -> None:
        note_data = {
            'id': 'preserve_activity',
            'title': 'Preserve Activity Test',
            'text': '☐ 0900 Work 1. Code review\n☐ 1000 Regular task',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.time_entries[0]['activity'], 'Work 1. Code review')
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Code review')
        self.assertEqual(result.time_entries[1]['activity'], 'Regular task')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Regular task')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_parse_sub_activity_with_special_characters(self) -> None:
        note_data = {
            'id': 'special_chars_sub_activity',
            'title': 'Special Characters Test',
            'text': '☐ 0900 Work 1. Review PR #123 & merge\n☐ 1000 Meeting 2. Q&A session @ office',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Review PR #123 & merge')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Meeting')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Q&A session @ office')

    def test_parse_sub_activity_with_numbers_in_text(self) -> None:
        note_data = {
            'id': 'numbers_in_text',
            'title': 'Numbers In Text Test',
            'text': '☐ 0900 Work 1. Fixed 3 bugs in module 5\n☐ 1000 Meeting 2. Review 2024 Q1 plan',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], 'Work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Fixed 3 bugs in module 5')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Meeting')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Review 2024 Q1 plan')

    def test_parse_sequential_numbered_activities_same_main_activity(self) -> None:
        note_data = {
            'id': 'sequential_numbered',
            'title': 'Sequential Numbered Test',
            'text': '☐ 0900 Coding 1. Setup environment\n☐ 0930 Coding 2. Write tests\n☐ 1000 Coding 3. Implement feature\n☐ 1030 Coding 4. Code review',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T10:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 4)
        for i, expected_sub in enumerate(['Setup environment', 'Write tests', 'Implement feature', 'Code review'], 1):
            self.assertEqual(result.time_entries[i-1]['main_activity'], 'Coding')
            self.assertEqual(result.time_entries[i-1]['sub_activity'], expected_sub)

    def test_parse_non_sequential_numbered_activities(self) -> None:
        note_data = {
            'id': 'non_sequential',
            'title': 'Non-Sequential Test',
            'text': '☐ 0900 Work 5. Advanced task\n☐ 1000 Work 1. Basic task\n☐ 1100 Work 3. Medium task',
            'timestamps': {
                'created': '2024-01-15T09:00:00Z',
                'edited': '2024-01-15T11:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Advanced task')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Basic task')
        self.assertEqual(result.time_entries[2]['sub_activity'], 'Medium task')


if __name__ == '__main__':
    unittest.main()
