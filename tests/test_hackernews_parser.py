import unittest
import json
import os
from typing import Any, Dict, List, Optional
from unittest.mock import mock_open, patch
from parsers.hackernews_parser import HackerNewsParser, HNLink, ParsedNote


class TestHackerNewsParser(unittest.TestCase):
    schema: Optional[Dict[str, Any]] = None
    parser: HackerNewsParser
    
    @classmethod
    def setUpClassmethod(cls) -> None:
        schema_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'hackernews.schema.json')
        with open(schema_path, 'r') as f:
            cls.schema = json.load(f)
    
    def setUp(self) -> None:
        self.parser = HackerNewsParser()

    def test_can_parse_with_hn_label(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'Some text without URL',
            'labels': ['Download-HN']
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_hn_url_http(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'Check out http://news.ycombinator.com/item?id=12345',
            'labels': []
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_hn_url_https(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'Check out https://news.ycombinator.com/item?id=67890',
            'labels': []
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_hn_url_in_title(self) -> None:
        note_data: Dict[str, Any] = {
            'title': 'https://news.ycombinator.com/item?id=12345',
            'text': 'Some text',
            'labels': []
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_with_both_label_and_url(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'Check out https://news.ycombinator.com/item?id=12345',
            'labels': ['Download-HN']
        }
        self.assertTrue(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_without_label_or_url(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'Some random text',
            'labels': ['Other-Label']
        }
        self.assertFalse(self.parser.can_parse(note_data))

    def test_can_parse_returns_false_for_non_dict(self) -> None:
        self.assertFalse(self.parser.can_parse("not a dict"))
        self.assertFalse(self.parser.can_parse(None))
        self.assertFalse(self.parser.can_parse([]))

    def test_can_parse_with_empty_note_data(self) -> None:
        note_data: Dict[str, Any] = {}
        self.assertFalse(self.parser.can_parse(note_data))

    def test_parse_basic_note_with_single_url(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note123',
            'title': 'My HN Post',
            'text': 'Check this out: https://news.ycombinator.com/item?id=12345',
            'labels': ['Download-HN', 'Tech']
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, 'note123')
        self.assertEqual(result.title, 'My HN Post')
        self.assertEqual(result.url, 'https://news.ycombinator.com/item?id=12345')
        self.assertEqual(result.item_id, '12345')
        self.assertEqual(result.labels, ['Download-HN', 'Tech'])
        self.assertEqual(result.description, 'Check this out: https://news.ycombinator.com/item?id=12345')
        self.assertEqual(len(result.hn_links), 1)
        self.assertEqual(result.hn_links[0].url, 'https://news.ycombinator.com/item?id=12345')
        self.assertEqual(result.hn_links[0].item_id, '12345')

    def test_parse_note_with_url_in_title(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note999',
            'title': 'https://news.ycombinator.com/item?id=55555',
            'text': 'This is in the title',
            'labels': []
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.url, 'https://news.ycombinator.com/item?id=55555')
        self.assertEqual(result.item_id, '55555')

    def test_parse_note_with_url_in_both_title_and_body(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note888',
            'title': 'https://news.ycombinator.com/item?id=11111',
            'text': 'Also https://news.ycombinator.com/item?id=22222',
            'labels': []
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.url, 'https://news.ycombinator.com/item?id=11111')
        self.assertEqual(result.item_id, '11111')
        self.assertEqual(len(result.hn_links), 2)

    def test_parse_note_with_multiple_urls(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note456',
            'title': 'Multiple HN Posts',
            'text': 'First: https://news.ycombinator.com/item?id=11111 and second: http://news.ycombinator.com/item?id=22222',
            'labels': []
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.url, 'https://news.ycombinator.com/item?id=11111')
        self.assertEqual(result.item_id, '11111')
        self.assertEqual(len(result.hn_links), 2)
        self.assertEqual(result.hn_links[0].url, 'https://news.ycombinator.com/item?id=11111')
        self.assertEqual(result.hn_links[0].item_id, '11111')
        self.assertEqual(result.hn_links[1].url, 'http://news.ycombinator.com/item?id=22222')
        self.assertEqual(result.hn_links[1].item_id, '22222')

    def test_parse_note_without_urls(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note789',
            'title': 'No URL',
            'text': 'Just some text',
            'labels': ['Download-HN']
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, 'note789')
        self.assertEqual(result.url, '')
        self.assertEqual(result.item_id, '')
        self.assertEqual(result.hn_links, [])

    def test_parse_note_with_missing_fields(self) -> None:
        note_data: Dict[str, Any] = {
            'text': 'https://news.ycombinator.com/item?id=99999'
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.note_id, '')
        self.assertEqual(result.title, '')
        self.assertEqual(result.url, 'https://news.ycombinator.com/item?id=99999')
        self.assertEqual(result.item_id, '99999')
        self.assertEqual(result.labels, [])

    def test_parse_raises_error_for_non_dict(self) -> None:
        with self.assertRaises(ValueError) as context:
            self.parser.parse("not a dict")
        self.assertIn("note_data must be a dictionary", str(context.exception))

    def test_parse_with_hashtag_labels_in_body(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note777',
            'title': 'Test Note',
            'text': 'Some text #python #tech https://news.ycombinator.com/item?id=12345 more text #coding',
            'labels': ['Download-HN']
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertIn('python', result.labels)
        self.assertIn('tech', result.labels)
        self.assertIn('coding', result.labels)
        self.assertIn('Download-HN', result.labels)

    def test_parse_with_only_hashtag_labels_in_body(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note666',
            'title': 'Test',
            'text': 'Check this #ai #ml post https://news.ycombinator.com/item?id=12345',
            'labels': []
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertIn('ai', result.labels)
        self.assertIn('ml', result.labels)
        self.assertEqual(len(result.labels), 2)

    def test_parse_with_mixed_labels_and_hashtags(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note555',
            'title': 'Mixed',
            'text': 'Text with #hashtag1 and #hashtag2',
            'labels': ['Label1', 'Label2']
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertIn('Label1', result.labels)
        self.assertIn('Label2', result.labels)
        self.assertIn('hashtag1', result.labels)
        self.assertIn('hashtag2', result.labels)

    def test_extract_hn_urls_single_url(self) -> None:
        text: str = 'Check out https://news.ycombinator.com/item?id=12345'
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].url, 'https://news.ycombinator.com/item?id=12345')
        self.assertEqual(urls[0].item_id, '12345')

    def test_extract_hn_urls_multiple_urls(self) -> None:
        text: str = 'First: https://news.ycombinator.com/item?id=11111 Second: http://news.ycombinator.com/item?id=22222'
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0].item_id, '11111')
        self.assertEqual(urls[1].item_id, '22222')

    def test_extract_hn_urls_no_urls(self) -> None:
        text: str = 'No HN URLs here'
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 0)
        self.assertEqual(urls, [])

    def test_extract_hn_urls_empty_string(self) -> None:
        text: str = ''
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 0)
        self.assertEqual(urls, [])

    def test_extract_hn_urls_http_protocol(self) -> None:
        text: str = 'http://news.ycombinator.com/item?id=12345'
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].url, 'http://news.ycombinator.com/item?id=12345')

    def test_extract_hn_urls_https_protocol(self) -> None:
        text: str = 'https://news.ycombinator.com/item?id=67890'
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].url, 'https://news.ycombinator.com/item?id=67890')

    def test_extract_hn_urls_multiline_text(self) -> None:
        text: str = '''First line with https://news.ycombinator.com/item?id=11111
        Second line with http://news.ycombinator.com/item?id=22222
        Third line with https://news.ycombinator.com/item?id=33333'''
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 3)
        self.assertEqual(urls[0].item_id, '11111')
        self.assertEqual(urls[1].item_id, '22222')
        self.assertEqual(urls[2].item_id, '33333')

    def test_extract_hn_urls_with_surrounding_text(self) -> None:
        text: str = 'Some text before (https://news.ycombinator.com/item?id=12345) and after'
        urls: List[HNLink] = self.parser._extract_hn_urls(text)
        
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].url, 'https://news.ycombinator.com/item?id=12345')
        self.assertEqual(urls[0].item_id, '12345')

    def test_get_schema(self) -> None:
        schema: Dict[str, Any] = self.parser.get_schema()
        
        self.assertIsNotNone(schema)
        self.assertIn('$schema', schema)
        self.assertIn('properties', schema)

    def test_labels_converted_to_strings(self) -> None:
        note_data: Dict[str, Any] = {
            'id': 'note123',
            'title': 'Test',
            'text': 'https://news.ycombinator.com/item?id=12345',
            'labels': ['Download-HN', 123, None]
        }
        result: ParsedNote = self.parser.parse(note_data)
        
        self.assertEqual(result.labels, ['Download-HN', '123', 'None'])

    def test_extract_hashtag_labels_single(self) -> None:
        text: str = 'Some text with #test'
        labels: List[str] = self.parser._extract_hashtag_labels(text)
        
        self.assertEqual(labels, ['test'])

    def test_extract_hashtag_labels_multiple(self) -> None:
        text: str = 'Text with #tag1 and #tag2 plus #tag3'
        labels: List[str] = self.parser._extract_hashtag_labels(text)
        
        self.assertEqual(set(labels), {'tag1', 'tag2', 'tag3'})

    def test_extract_hashtag_labels_none(self) -> None:
        text: str = 'Text without hashtags'
        labels: List[str] = self.parser._extract_hashtag_labels(text)
        
        self.assertEqual(labels, [])

    def test_extract_hashtag_labels_with_special_chars(self) -> None:
        text: str = 'Text #python-dev #c++ #123numbers'
        labels: List[str] = self.parser._extract_hashtag_labels(text)
        
        self.assertIn('python', labels)

    def test_hn_url_pattern_attribute(self) -> None:
        self.assertEqual(self.parser.HN_URL_PATTERN, r'https?://news\.ycombinator\.com/item\?id=(\d+)')

    def test_download_hn_label_attribute(self) -> None:
        self.assertEqual(self.parser.DOWNLOAD_HN_LABEL, 'Download-HN')


if __name__ == '__main__':
    unittest.main()
