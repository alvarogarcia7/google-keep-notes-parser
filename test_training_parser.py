import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
from typing import Any, Dict, List, ClassVar
from dataclasses import asdict
from parsers.training_parser import TrainingParser, WorkoutData, ExerciseData, SetData, CompletedActivity


class TestTrainingParser(unittest.TestCase):
    actual_schema: ClassVar[Dict[str, Any]]
    
    @classmethod
    def setUpClass(cls) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'training.schema.json')
        with open(schema_path, 'r') as f:
            cls.actual_schema = json.load(f)

    def setUp(self) -> None:
        self.parser = TrainingParser()

    def test_can_parse_with_valid_training_note(self) -> None:
        note_data = {
            'text': 'Bp 3x8x100',
            'title': 'Workout'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_checkboxes(self) -> None:
        note_data = {
            'text': '\u2610 Bp 3x8x100\n\u2611 Sq 4x10x200',
            'title': 'Workout'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_multiple_exercises(self) -> None:
        note_data = {
            'text': 'Bp 3x8x100\nSq 4x10x200',
            'title': 'Workout'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_case_insensitive_abbreviation(self) -> None:
        note_data = {
            'text': 'bp 3x8x100',
            'title': 'Workout'
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_no_exercise(self) -> None:
        note_data = {
            'text': '3x8x100',
            'title': 'Workout'
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_no_set_format(self) -> None:
        note_data = {
            'text': 'Bp exercise today',
            'title': 'Workout'
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_empty_text(self) -> None:
        note_data = {
            'text': '',
            'title': 'Workout'
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_non_dict(self) -> None:
        note_data = "not a dict"
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_with_no_text_key(self) -> None:
        note_data = {
            'title': 'Workout'
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_parse_raises_error_with_non_dict(self) -> None:
        with self.assertRaises(ValueError) as context:
            self.parser.parse("not a dict")
        self.assertEqual(str(context.exception), "note_data must be a dictionary")

    def test_parse_example_from_docs(self) -> None:
        note_data = {
            "id": "fit123.gym456",
            "title": "Upper Body Workout",
            "text": "Bp 3 x 8 x 185\nBp 2 x 6 x 205\nMr 3 x 10 x 95\nPu 3 x 12 x 0",
            "labels": ["fitness", "strength"],
            "timestamps": {
                "created": "2023-10-15T18:00:00",
                "edited": "2023-10-15T19:30:00"
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.note_id, 'fit123.gym456')
        self.assertEqual(result.title, 'Upper Body Workout')
        self.assertEqual(result.workout_date, '2023-10-15T18:00:00')
        self.assertEqual(result.last_updated, '2023-10-15T19:30:00')
        self.assertEqual(len(result.exercises), 3)
        
        # Verify first exercise (Bench Press)
        bp_exercise = result.exercises[0]
        self.assertIsInstance(bp_exercise, ExerciseData)
        self.assertEqual(bp_exercise.exercise_name, 'Bench Press')
        self.assertEqual(bp_exercise.abbreviation, 'Bp')
        self.assertEqual(bp_exercise.total_sets, 2)
        self.assertEqual(len(bp_exercise.sets), 2)
        self.assertIsInstance(bp_exercise.sets[0], SetData)
        self.assertEqual(bp_exercise.sets[0].set, 3)
        self.assertEqual(bp_exercise.sets[0].reps, 8)
        self.assertEqual(bp_exercise.sets[0].weight, 185.0)
        self.assertEqual(bp_exercise.sets[1].set, 2)
        self.assertEqual(bp_exercise.sets[1].reps, 6)
        self.assertEqual(bp_exercise.sets[1].weight, 205.0)
        
        # Verify second exercise (Machine Row)
        mr_exercise = result.exercises[1]
        self.assertIsInstance(mr_exercise, ExerciseData)
        self.assertEqual(mr_exercise.exercise_name, 'Machine Row')
        self.assertEqual(mr_exercise.abbreviation, 'Mr')
        self.assertEqual(mr_exercise.total_sets, 1)
        self.assertEqual(mr_exercise.sets[0].set, 3)
        self.assertEqual(mr_exercise.sets[0].reps, 10)
        self.assertEqual(mr_exercise.sets[0].weight, 95.0)
        
        # Verify third exercise (Pull-up)
        pu_exercise = result.exercises[2]
        self.assertIsInstance(pu_exercise, ExerciseData)
        self.assertEqual(pu_exercise.exercise_name, 'Pull-up')
        self.assertEqual(pu_exercise.abbreviation, 'Pu')
        
        # Verify completed activities
        self.assertEqual(len(result.completed_activities), 1)
        self.assertIsInstance(result.completed_activities[0], CompletedActivity)
        self.assertEqual(result.completed_activities[0].timestamp, '2023-10-15T18:00:00')
        self.assertEqual(result.completed_activities[0].activity, 'Workout logged')
        
        self.assertEqual(result.raw_text, "Bp 3 x 8 x 185\nBp 2 x 6 x 205\nMr 3 x 10 x 95\nPu 3 x 12 x 0")

    def test_parse_with_checkboxes(self) -> None:
        note_data = {
            'id': 'checkbox123',
            'title': 'Workout Checklist',
            'text': '\u2610 Bp 3x8x100\n\u2611 Sq 4x10x200',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T11:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.note_id, 'checkbox123')
        self.assertEqual(len(result.exercises), 2)
        self.assertIn('- [ ]', result.raw_text)
        self.assertIn('- [x]', result.raw_text)

    def test_parse_basic_workout(self) -> None:
        note_data = {
            'id': 'note123',
            'title': 'Monday Workout',
            'text': 'Bp 3x8x100',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T11:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.note_id, 'note123')
        self.assertEqual(result.title, 'Monday Workout')
        self.assertEqual(result.workout_date, '2024-01-01T10:00:00')
        self.assertEqual(result.last_updated, '2024-01-01T11:00:00')
        self.assertEqual(result.raw_text, 'Bp 3x8x100')
        self.assertEqual(len(result.exercises), 1)

    def test_parse_multiple_exercises(self) -> None:
        note_data = {
            'id': 'note456',
            'title': 'Full Body',
            'text': 'Bp 3x8x100\nSq 4x10x200\nDl 5x5x250',
            'timestamps': {
                'created': '2024-01-02T10:00:00',
                'edited': '2024-01-02T11:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(len(result.exercises), 3)
        self.assertEqual(result.exercises[0].exercise_name, 'Bench Press')
        self.assertEqual(result.exercises[1].exercise_name, 'Squat')
        self.assertEqual(result.exercises[2].exercise_name, 'Deadlift')

    def test_parse_with_missing_timestamps(self) -> None:
        note_data = {
            'id': 'note789',
            'title': 'Test',
            'text': 'Bp 3x8x100',
            'timestamps': {}
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.workout_date, '')
        self.assertEqual(result.last_updated, '')

    def test_parse_with_no_timestamps_key(self) -> None:
        note_data = {
            'id': 'note999',
            'title': 'Test',
            'text': 'Bp 3x8x100'
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.workout_date, '')
        self.assertEqual(result.last_updated, '')

    def test_extract_exercises_single_set(self) -> None:
        text = 'Bp 3x8x100'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertIsInstance(exercises[0], ExerciseData)
        self.assertEqual(exercises[0].exercise_name, 'Bench Press')
        self.assertEqual(exercises[0].abbreviation, 'Bp')
        self.assertEqual(exercises[0].total_sets, 1)
        self.assertEqual(exercises[0].raw_line, 'Bp 3x8x100')

    def test_extract_exercises_multiple_sets_same_line(self) -> None:
        text = 'Bp 3x8x100 4x6x110'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].total_sets, 2)
        self.assertEqual(len(exercises[0].sets), 2)

    def test_extract_exercises_with_decimal_weight(self) -> None:
        text = 'Bp 3x8x100.5'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].sets[0].weight, 100.5)

    def test_extract_exercises_case_insensitive(self) -> None:
        text = 'bp 3x8x100'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].exercise_name, 'Bench Press')

    def test_extract_exercises_with_unicode_multiplication(self) -> None:
        text = 'Bp 3×8×100'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].sets[0].set, 3)
        self.assertEqual(exercises[0].sets[0].reps, 8)
        self.assertEqual(exercises[0].sets[0].weight, 100)

    def test_extract_exercises_ignores_line_without_sets(self) -> None:
        text = 'Bp warm up\nBp 3x8x100'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].raw_line, 'Bp 3x8x100')

    def test_extract_exercises_multiple_abbreviations_in_text(self) -> None:
        text = 'Bp 3x8x100\nSq 4x10x200'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 2)
        self.assertEqual(exercises[0].exercise_name, 'Bench Press')
        self.assertEqual(exercises[1].exercise_name, 'Squat')

    def test_extract_exercises_with_whitespace_variations(self) -> None:
        text = 'Bp 3 x 8 x 100'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].sets[0].set, 3)
        self.assertEqual(exercises[0].sets[0].reps, 8)
        self.assertEqual(exercises[0].sets[0].weight, 100)

    def test_extract_sets_single_set(self) -> None:
        line = '3x8x100'
        sets = self.parser._extract_sets(line)
        
        self.assertEqual(len(sets), 1)
        self.assertIsInstance(sets[0], SetData)
        self.assertEqual(sets[0].set, 3)
        self.assertEqual(sets[0].reps, 8)
        self.assertEqual(sets[0].weight, 100.0)

    def test_extract_sets_multiple_sets(self) -> None:
        line = '3x8x100 4x6x110 5x4x120'
        sets = self.parser._extract_sets(line)
        
        self.assertEqual(len(sets), 3)
        self.assertEqual(sets[0].set, 3)
        self.assertEqual(sets[0].reps, 8)
        self.assertEqual(sets[0].weight, 100.0)
        self.assertEqual(sets[1].set, 4)
        self.assertEqual(sets[1].reps, 6)
        self.assertEqual(sets[1].weight, 110.0)
        self.assertEqual(sets[2].set, 5)
        self.assertEqual(sets[2].reps, 4)
        self.assertEqual(sets[2].weight, 120.0)

    def test_extract_sets_with_decimal_weight(self) -> None:
        line = '3x8x100.75'
        sets = self.parser._extract_sets(line)
        
        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0].weight, 100.75)

    def test_extract_sets_no_matches(self) -> None:
        line = 'just some text'
        sets = self.parser._extract_sets(line)
        
        self.assertEqual(len(sets), 0)

    def test_extract_sets_with_unicode_x(self) -> None:
        line = '3×8×100'
        sets = self.parser._extract_sets(line)
        
        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0].set, 3)
        self.assertEqual(sets[0].reps, 8)
        self.assertEqual(sets[0].weight, 100.0)

    def test_extract_completed_activities_with_timestamps(self) -> None:
        text = '2024-01-02T12:00:00 Completed warmup\n2024-01-02T12:30:00 Finished workout'
        created = '2024-01-01T10:00:00'
        activities = self.parser._extract_completed_activities(text, created)
        
        self.assertEqual(len(activities), 2)
        self.assertIsInstance(activities[0], CompletedActivity)
        self.assertEqual(activities[0].timestamp, '2024-01-02T12:00:00')
        self.assertIn('Completed warmup', activities[0].activity)
        self.assertEqual(activities[1].timestamp, '2024-01-02T12:30:00')
        self.assertIn('Finished workout', activities[1].activity)

    def test_extract_completed_activities_with_space_format(self) -> None:
        text = '2024-01-02 12:00:00 Completed warmup'
        created = '2024-01-01T10:00:00'
        activities = self.parser._extract_completed_activities(text, created)
        
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].timestamp, '2024-01-02 12:00:00')

    def test_extract_completed_activities_filters_created_timestamp(self) -> None:
        text = '2024-01-01T10:00:00 Created note\n2024-01-02T12:00:00 Completed workout'
        created = '2024-01-01T10:00:00'
        activities = self.parser._extract_completed_activities(text, created)
        
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].timestamp, '2024-01-02T12:00:00')

    def test_extract_completed_activities_default_activity(self) -> None:
        text = 'Bp 3x8x100'
        created = '2024-01-01T10:00:00'
        activities = self.parser._extract_completed_activities(text, created)
        
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].timestamp, '2024-01-01T10:00:00')
        self.assertEqual(activities[0].activity, 'Workout logged')

    def test_extract_completed_activities_no_timestamps_no_created(self) -> None:
        text = 'Bp 3x8x100'
        created = ''
        activities = self.parser._extract_completed_activities(text, created)
        
        self.assertEqual(len(activities), 0)

    def test_extract_completed_activities_extracts_full_line(self) -> None:
        text = 'Some prefix\n2024-01-02T12:00:00 Completed warmup with notes\nSome suffix'
        created = '2024-01-01T10:00:00'
        activities = self.parser._extract_completed_activities(text, created)
        
        self.assertEqual(len(activities), 1)
        self.assertIn('2024-01-02T12:00:00', activities[0].activity)
        self.assertIn('Completed warmup with notes', activities[0].activity)

    def test_exercise_patterns_all_abbreviations(self) -> None:
        expected_patterns = {
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
        self.assertEqual(self.parser.EXERCISE_PATTERNS, expected_patterns)

    def test_parse_all_exercise_types(self) -> None:
        text = ('Bp 1x1x100\nMr 1x1x100\nMs 1x1x100\nSq 1x1x100\n'
                'Dl 1x1x100\nPu 1x1x100\nDip 1x1x100\nRow 1x1x100\n'
                'Curl 1x1x100\nPress 1x1x100')
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 10)
        exercise_names = [e.exercise_name for e in exercises]
        self.assertIn('Bench Press', exercise_names)
        self.assertIn('Machine Row', exercise_names)
        self.assertIn('Machine Squat', exercise_names)
        self.assertIn('Squat', exercise_names)
        self.assertIn('Deadlift', exercise_names)
        self.assertIn('Pull-up', exercise_names)
        self.assertIn('Dip', exercise_names)
        self.assertIn('Row', exercise_names)
        self.assertIn('Curl', exercise_names)
        self.assertIn('Press', exercise_names)

    def test_parse_preserves_abbreviation(self) -> None:
        note_data = {
            'id': 'note123',
            'title': 'Test',
            'text': 'Bp 3x8x100',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T10:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.exercises[0].abbreviation, 'Bp')

    def test_parse_with_empty_id(self) -> None:
        note_data = {
            'title': 'Test',
            'text': 'Bp 3x8x100',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T10:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, '')

    def test_parse_with_empty_title(self) -> None:
        note_data = {
            'id': 'note123',
            'text': 'Bp 3x8x100',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T10:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertEqual(result.title, '')

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    @patch('os.path.dirname')
    def test_get_schema(self, mock_dirname: Any, mock_join: Any, mock_file: Any) -> None:
        mock_dirname.return_value = '/mock/path/parsers'
        mock_join.return_value = '/mock/path/schemas/training.schema.json'
        mock_file.return_value.read.return_value = json.dumps(self.actual_schema)
        
        schema = self.parser.get_schema()
        
        self.assertIsInstance(schema, dict)
        mock_file.assert_called_once_with('/mock/path/schemas/training.schema.json', 'r')

    def test_set_rep_weight_pattern_regex(self) -> None:
        pattern = self.parser.SET_REP_WEIGHT_PATTERN
        import re
        
        self.assertIsNotNone(re.search(pattern, '3x8x100'))
        self.assertIsNotNone(re.search(pattern, '3x8x100.5'))
        self.assertIsNotNone(re.search(pattern, '3 x 8 x 100'))
        self.assertIsNotNone(re.search(pattern, '3×8×100'))
        self.assertIsNone(re.search(pattern, 'not a set'))
        self.assertIsNone(re.search(pattern, '3x8'))

    def test_extract_exercises_only_first_matching_abbreviation(self) -> None:
        text = 'Row and Press 3x8x100'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 1)

    def test_extract_exercises_multiline_with_empty_lines(self) -> None:
        text = 'Bp 3x8x100\n\n\nSq 4x10x200'
        exercises = self.parser._extract_exercises(text)
        
        self.assertEqual(len(exercises), 2)

    def test_parse_complex_workout(self) -> None:
        note_data = {
            'id': 'complex123',
            'title': 'Heavy Day',
            'text': ('Bp 3x8x100 4x6x110 5x4x120\n'
                    'Sq 4x10x200.5\n'
                    '2024-01-01T10:30:00 Finished warmup\n'
                    'Dl 5x5x250\n'
                    '2024-01-01T11:00:00 Workout complete'),
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T11:05:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.note_id, 'complex123')
        self.assertEqual(result.title, 'Heavy Day')
        self.assertEqual(len(result.exercises), 3)
        self.assertEqual(result.exercises[0].total_sets, 3)
        self.assertEqual(result.exercises[0].sets[0].weight, 100.0)
        self.assertEqual(result.exercises[0].sets[1].weight, 110.0)
        self.assertEqual(result.exercises[0].sets[2].weight, 120.0)
        self.assertEqual(result.exercises[1].sets[0].weight, 200.5)
        self.assertEqual(len(result.completed_activities), 2)

    def test_parse_empty_text(self) -> None:
        note_data = {
            'id': 'note123',
            'title': 'Empty',
            'text': '',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T10:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.raw_text, '')
        self.assertEqual(len(result.exercises), 0)
        self.assertEqual(len(result.completed_activities), 1)
        self.assertEqual(result.completed_activities[0].activity, 'Workout logged')

    def test_normalize_checkboxes(self) -> None:
        text = '\u2610 Unchecked item\n\u2611 Checked item'
        normalized = self.parser._normalize_checkboxes(text)
        
        self.assertIn('- [ ]', normalized)
        self.assertIn('- [x]', normalized)
        self.assertEqual(normalized, '- [ ]  Unchecked item\n- [x]  Checked item')

    def test_dataclass_to_dict_conversion(self) -> None:
        note_data = {
            'id': 'note123',
            'title': 'Test',
            'text': 'Bp 3x8x100',
            'timestamps': {
                'created': '2024-01-01T10:00:00',
                'edited': '2024-01-01T10:00:00'
            }
        }
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        
        result_dict = asdict(result)
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['note_id'], 'note123')
        self.assertEqual(result_dict['title'], 'Test')
        self.assertIsInstance(result_dict['exercises'], list)
        self.assertIsInstance(result_dict['exercises'][0], dict)
        self.assertIsInstance(result_dict['exercises'][0]['sets'], list)
        self.assertIsInstance(result_dict['exercises'][0]['sets'][0], dict)

    def test_acceptance_training_json_input(self) -> None:
        note_data = {
            "id": "19be8948de3.91a539a03affd1a7",
            "title": "Training ",
            "text": "☑ 637 code\n☑ 600 gym class \n☑ 658 strength training \n☐ Bp\n  ☐ 2x30x13.6\n  ☐ 2x15x22.1\n☐ Mr\n  ☐ 2x20x26\n  ☐ 2x10x32\n☐ Ms\n  ☐ 5x10x63\n☐ Ribp\n  ☐ 3x20x25\n☐ M pec fly \n  ☐ 2x20x19",
            "archived": False,
            "trashed": False,
            "timestamps": {
                "created": "2026-01-23 02:00:49.707000+00:00",
                "edited": "2026-01-23 03:52:32.077000+00:00"
            },
            "labels": [],
            "media_paths": [],
            "blob_names": [],
            "keep_url": "https://keep.google.com/#NOTE/19be8948de3.91a539a03affd1a7"
        }
        
        result = self.parser.parse(note_data)
        
        self.assertIsInstance(result, WorkoutData)
        self.assertEqual(result.note_id, "19be8948de3.91a539a03affd1a7")
        self.assertEqual(result.title, "Training ")
        self.assertEqual(result.workout_date, "2026-01-23 02:00:49.707000+00:00")
        self.assertEqual(result.last_updated, "2026-01-23 03:52:32.077000+00:00")
        
        self.assertIn('- [x]', result.raw_text)
        self.assertIn('- [ ]', result.raw_text)
        
        self.assertEqual(len(result.exercises), 3)
        
        bp_exercise = result.exercises[0]
        self.assertEqual(bp_exercise.exercise_name, 'Bench Press')
        self.assertEqual(bp_exercise.abbreviation, 'Bp')
        self.assertEqual(bp_exercise.total_sets, 2)
        self.assertEqual(len(bp_exercise.sets), 2)
        self.assertEqual(bp_exercise.sets[0].set, 2)
        self.assertEqual(bp_exercise.sets[0].reps, 30)
        self.assertEqual(bp_exercise.sets[0].weight, 13.6)
        self.assertEqual(bp_exercise.sets[1].set, 2)
        self.assertEqual(bp_exercise.sets[1].reps, 15)
        self.assertEqual(bp_exercise.sets[1].weight, 22.1)
        
        mr_exercise = result.exercises[1]
        self.assertEqual(mr_exercise.exercise_name, 'Machine Row')
        self.assertEqual(mr_exercise.abbreviation, 'Mr')
        self.assertEqual(mr_exercise.total_sets, 2)
        self.assertEqual(len(mr_exercise.sets), 2)
        self.assertEqual(mr_exercise.sets[0].set, 2)
        self.assertEqual(mr_exercise.sets[0].reps, 20)
        self.assertEqual(mr_exercise.sets[0].weight, 26.0)
        self.assertEqual(mr_exercise.sets[1].set, 2)
        self.assertEqual(mr_exercise.sets[1].reps, 10)
        self.assertEqual(mr_exercise.sets[1].weight, 32.0)
        
        ms_exercise = result.exercises[2]
        self.assertEqual(ms_exercise.exercise_name, 'Machine Squat')
        self.assertEqual(ms_exercise.abbreviation, 'Ms')
        self.assertEqual(ms_exercise.total_sets, 1)
        self.assertEqual(len(ms_exercise.sets), 1)
        self.assertEqual(ms_exercise.sets[0].set, 5)
        self.assertEqual(ms_exercise.sets[0].reps, 10)
        self.assertEqual(ms_exercise.sets[0].weight, 63.0)
        
        self.assertEqual(len(result.completed_activities), 1)
        self.assertEqual(result.completed_activities[0].timestamp, "2026-01-23 02:00:49.707000+00:00")
        self.assertEqual(result.completed_activities[0].activity, 'Workout logged')


if __name__ == '__main__':
    unittest.main()
