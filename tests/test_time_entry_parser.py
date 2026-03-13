import unittest
from unittest.mock import patch, mock_open, MagicMock
from parsers.time_entry_parser import TimeEntryParser


class TestTimeEntryParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = TimeEntryParser()

    def test_can_parse_valid_time_entry_with_3_digit_timestamps(self) -> None:
        note_data = {
            'id': 'test123',
            'title': 'Daily Log',
            'text': '☐ 637 start\n☐ 845 Breakfast\n☐ 1030 Meeting',
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
            'text': '☐ 0637 start\n☐ 1053 Coffee break\n☐ 1420 Lunch',
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
            'text': '☐ 637 start\n☐ 1053 Coffee\n☐ 730 Exercise',
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
            'text': '☐  637   start  \n☐ 1053  Coffee break\n☐  1420    Lunch  ',
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
            'text': '☐ 0637 start',
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
            'text': '☐ 0637 start\nSome regular text\n☐ 1053 Coffee break\nMore notes here\n☐ 1420 Lunch',
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
            'text': '☑ 0637 start\n☑ 1053 Coffee break\n☐ 1420 Lunch',
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
            'text': '☐ 0637 start\n☐ 1053 Coffee break\n☐ 1420 Lunch',
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
        self.assertEqual(result.time_entries[0]['activity'], 'start')
        self.assertEqual(result.time_entries[1]['time'], '10:53')
        self.assertEqual(result.time_entries[1]['activity'], 'Coffee break')
        self.assertEqual(result.time_entries[2]['time'], '14:20')
        self.assertEqual(result.time_entries[2]['activity'], 'Lunch')

    def test_parse_chronological_sorting(self) -> None:
        note_data = {
            'id': 'sort_test',
            'title': 'Sort Test',
            'text': '☐ 1420 Lunch\n☐ 0637 Morning\n☐ 1053 Coffee break',
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
            'text': '☐ 637 start\n☐ 845 Breakfast',
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
            'text': '☐ 0637 start\nThis is a regular note\nNot a time entry\n☐ 1053 Coffee break',
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
            'text': '☐ 0637 start\n☐ 1053 Coffee',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.raw_text, '☐ 0637 start\n☐ 1053 Coffee')

    def test_parse_generates_full_timestamps(self) -> None:
        note_data = {
            'id': 'timestamp_test',
            'title': 'Timestamp Test',
            'text': '☐ 0637 start',
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
            'text': '☐ 0637 start early today',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T06:37:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.time_entries[0]['raw_line'], '☐ 0637 start early today')

    def test_parse_raises_error_for_non_dict(self) -> None:
        with self.assertRaises(ValueError):
            self.parser.parse("not a dict")

    def test_parse_warning_for_out_of_order_chronological_notes(self) -> None:
        note_data = {
            'id': 'warning_test',
            'title': 'Out of Order',
            'text': '☐ 1420 Lunch\n☐ 0637 Morning\n☐ 1053 Coffee',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.warnings), 1)
        self.assertIn('time entries are out of chronological order', result.warnings[0].lower())
        self.assertIn('06:37', result.warnings[0])

    def test_parse_no_warning_for_in_order_chronological_notes(self) -> None:
        note_data = {
            'id': 'no_warning_test',
            'title': 'In Order',
            'text': '☐ 0637 start\n☐ 1053 Coffee\n☐ 1420 Lunch',
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
        self.parser.get_schema()
        mock_file.assert_called_once()
        call_args = mock_file.call_args[0][0]
        self.assertTrue(call_args.endswith('time_entry.schema.json'))

    def test_parse_handles_missing_timestamps(self) -> None:
        note_data = {
            'id': 'missing_timestamps',
            'title': 'Missing Timestamps',
            'text': '☐ 0637 start\n☐ 1053 Coffee',
            'timestamps': {}
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.created, '')
        self.assertEqual(result.date, '')

    def test_parse_handles_missing_title(self) -> None:
        note_data = {
            'id': 'missing_title',
            'text': '☐ 0637 start\n☐ 1053 Coffee',
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
            'text': '☐ 0637 start\n☐ 1053 Coffee',
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

    def test_parse_activity_with_numbered_sub_item_extracts_main_and_sub(self) -> None:
        note_data = {
            'id': 'sub_activity_test',
            'title': 'Sub-Activity Test',
            'text': '☐ 0637 start\n☐ 1103 work 1. CMS',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T11:03:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[1]['activity'], 'work 1. CMS')
        self.assertEqual(result.time_entries[1]['main_activity'], 'work')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'CMS')

    def test_parse_activity_without_sub_item_leaves_sub_activity_empty(self) -> None:
        note_data = {
            'id': 'no_sub_activity_test',
            'title': 'No Sub-Activity Test',
            'text': '☐ 0637 start\n☐ 1053 Coffee break',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T10:53:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'start')
        self.assertEqual(result.time_entries[0]['main_activity'], 'start')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')
        self.assertEqual(result.time_entries[1]['activity'], 'Coffee break')
        self.assertEqual(result.time_entries[1]['main_activity'], 'Coffee break')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_parse_activity_preserves_original_activity_field(self) -> None:
        note_data = {
            'id': 'preserve_activity_test',
            'title': 'Preserve Activity Test',
            'text': '☐ 0637 morning routine\n☐ 1103 work 1. CMS project\n☐ 1420 lunch break',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T14:20:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        self.assertEqual(result.time_entries[0]['activity'], 'morning routine')
        self.assertEqual(result.time_entries[1]['activity'], 'work 1. CMS project')
        self.assertEqual(result.time_entries[2]['activity'], 'lunch break')

    def test_parse_activity_with_multiple_periods_in_text(self) -> None:
        note_data = {
            'id': 'multiple_periods_test',
            'title': 'Multiple Periods Test',
            'text': '☐ 0637 reading Dr. Smith\'s book\n☐ 1103 work 1. Review P.R. for client',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T11:03:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'reading Dr. Smith\'s book')
        self.assertEqual(result.time_entries[0]['main_activity'], 'reading Dr. Smith\'s book')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')
        self.assertEqual(result.time_entries[1]['activity'], 'work 1. Review P.R. for client')
        self.assertEqual(result.time_entries[1]['main_activity'], 'work')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Review P.R. for client')

    def test_parse_activity_with_various_numbering_formats(self) -> None:
        note_data = {
            'id': 'numbering_formats_test',
            'title': 'Numbering Formats Test',
            'text': '☐ 0637 work 1. Task A\n☐ 0730 coding 2. Feature B\n☐ 0845 meeting 3. Sprint planning',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T08:45:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 3)
        
        self.assertEqual(result.time_entries[0]['activity'], 'work 1. Task A')
        self.assertEqual(result.time_entries[0]['main_activity'], 'work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Task A')
        
        self.assertEqual(result.time_entries[1]['activity'], 'coding 2. Feature B')
        self.assertEqual(result.time_entries[1]['main_activity'], 'coding')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Feature B')
        
        self.assertEqual(result.time_entries[2]['activity'], 'meeting 3. Sprint planning')
        self.assertEqual(result.time_entries[2]['main_activity'], 'meeting')
        self.assertEqual(result.time_entries[2]['sub_activity'], 'Sprint planning')

    def test_parse_mixed_entries_structured_and_unstructured(self) -> None:
        note_data = {
            'id': 'mixed_entries_test',
            'title': 'Mixed Entries Test',
            'text': '☐ 0637 breakfast\n☐ 0730 work 1. Email responses\n☐ 0845 coffee\n☐ 0900 work 2. Code review',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T09:00:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 4)
        
        self.assertEqual(result.time_entries[0]['activity'], 'breakfast')
        self.assertEqual(result.time_entries[0]['main_activity'], 'breakfast')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')
        
        self.assertEqual(result.time_entries[1]['activity'], 'work 1. Email responses')
        self.assertEqual(result.time_entries[1]['main_activity'], 'work')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Email responses')
        
        self.assertEqual(result.time_entries[2]['activity'], 'coffee')
        self.assertEqual(result.time_entries[2]['main_activity'], 'coffee')
        self.assertEqual(result.time_entries[2]['sub_activity'], '')
        
        self.assertEqual(result.time_entries[3]['activity'], 'work 2. Code review')
        self.assertEqual(result.time_entries[3]['main_activity'], 'work')
        self.assertEqual(result.time_entries[3]['sub_activity'], 'Code review')

    def test_parse_activity_with_double_digit_numbering(self) -> None:
        note_data = {
            'id': 'double_digit_test',
            'title': 'Double Digit Numbering Test',
            'text': '☐ 0637 tasks 10. Important item\n☐ 0730 work 99. Last task',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'tasks 10. Important item')
        self.assertEqual(result.time_entries[0]['main_activity'], 'tasks')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Important item')
        self.assertEqual(result.time_entries[1]['activity'], 'work 99. Last task')
        self.assertEqual(result.time_entries[1]['main_activity'], 'work')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Last task')

    def test_parse_activity_with_leading_trailing_whitespace(self) -> None:
        note_data = {
            'id': 'whitespace_activity_test',
            'title': 'Whitespace Activity Test',
            'text': '☐ 0637   work 1. Task   \n☐ 0730   simple task   ',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['main_activity'], 'work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Task')
        self.assertEqual(result.time_entries[1]['main_activity'], 'simple task')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_parse_activity_with_period_in_sub_activity(self) -> None:
        note_data = {
            'id': 'period_in_sub_test',
            'title': 'Period in Sub-Activity Test',
            'text': '☐ 0637 work 1. Review v2.0 release\n☐ 0730 coding 2. Fix bug in app.py',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'work 1. Review v2.0 release')
        self.assertEqual(result.time_entries[0]['main_activity'], 'work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Review v2.0 release')
        self.assertEqual(result.time_entries[1]['activity'], 'coding 2. Fix bug in app.py')
        self.assertEqual(result.time_entries[1]['main_activity'], 'coding')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Fix bug in app.py')

    def test_parse_activity_only_number_and_period_no_sub_activity(self) -> None:
        note_data = {
            'id': 'only_number_period_test',
            'title': 'Only Number Period Test',
            'text': '☐ 0637 task 1.\n☐ 0730 work',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'task 1.')
        self.assertEqual(result.time_entries[0]['main_activity'], 'task 1.')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')

    def test_parse_activity_number_without_period(self) -> None:
        note_data = {
            'id': 'number_no_period_test',
            'title': 'Number No Period Test',
            'text': '☐ 0637 work 1 task\n☐ 0730 coding 2 feature',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'work 1 task')
        self.assertEqual(result.time_entries[0]['main_activity'], 'work 1 task')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')
        self.assertEqual(result.time_entries[1]['activity'], 'coding 2 feature')
        self.assertEqual(result.time_entries[1]['main_activity'], 'coding 2 feature')
        self.assertEqual(result.time_entries[1]['sub_activity'], '')

    def test_schema_includes_main_activity_and_sub_activity_fields(self) -> None:
        schema = self.parser.get_schema()
        
        entry_schema = schema['properties']['time_entries']['items']
        entry_properties = entry_schema['properties']
        
        self.assertIn('main_activity', entry_properties)
        self.assertIn('sub_activity', entry_properties)
        self.assertEqual(entry_properties['main_activity']['type'], 'string')
        self.assertEqual(entry_properties['sub_activity']['type'], 'string')

    def test_schema_requires_main_activity_and_sub_activity(self) -> None:
        schema = self.parser.get_schema()
        
        entry_schema = schema['properties']['time_entries']['items']
        required_fields = entry_schema.get('required', [])
        
        self.assertIn('main_activity', required_fields)
        self.assertIn('sub_activity', required_fields)

    def test_parse_activity_complex_sub_activity_with_special_chars(self) -> None:
        note_data = {
            'id': 'special_chars_test',
            'title': 'Special Characters Test',
            'text': '☐ 0637 work 1. Review PR #123\n☐ 0730 meeting 2. Q&A session',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'work 1. Review PR #123')
        self.assertEqual(result.time_entries[0]['main_activity'], 'work')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Review PR #123')
        self.assertEqual(result.time_entries[1]['activity'], 'meeting 2. Q&A session')
        self.assertEqual(result.time_entries[1]['main_activity'], 'meeting')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Q&A session')

    def test_parse_validates_against_schema(self) -> None:
        note_data = {
            'id': 'schema_validation_test',
            'title': 'Schema Validation Test',
            'text': '☐ 0637 work 1. CMS\n☐ 0730 break',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        for entry in result.time_entries:
            self.assertIn('main_activity', entry)
            self.assertIn('sub_activity', entry)
            self.assertIsInstance(entry['main_activity'], str)
            self.assertIsInstance(entry['sub_activity'], str)

    def test_parse_activity_with_multi_word_main_activity(self) -> None:
        note_data = {
            'id': 'multi_word_main_test',
            'title': 'Multi-Word Main Activity Test',
            'text': '☐ 0637 client meeting 1. Project kickoff\n☐ 0730 code review 2. Feature branch',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 2)
        self.assertEqual(result.time_entries[0]['activity'], 'client meeting 1. Project kickoff')
        self.assertEqual(result.time_entries[0]['main_activity'], 'client meeting')
        self.assertEqual(result.time_entries[0]['sub_activity'], 'Project kickoff')
        self.assertEqual(result.time_entries[1]['activity'], 'code review 2. Feature branch')
        self.assertEqual(result.time_entries[1]['main_activity'], 'code review')
        self.assertEqual(result.time_entries[1]['sub_activity'], 'Feature branch')

    def test_parse_activity_empty_activity_string(self) -> None:
        note_data = {
            'id': 'empty_activity_test',
            'title': 'Empty Activity Test',
            'text': '☐ 0637 \n☐ 0730 work',
            'timestamps': {
                'created': '2024-01-15T06:37:00Z',
                'edited': '2024-01-15T07:30:00Z'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(len(result.time_entries), 1)
        self.assertEqual(result.time_entries[0]['activity'], 'work')
        self.assertEqual(result.time_entries[0]['main_activity'], 'work')
        self.assertEqual(result.time_entries[0]['sub_activity'], '')


if __name__ == '__main__':
    unittest.main()
