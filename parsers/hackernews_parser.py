import re
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List
from parsers.base import NoteParser


@dataclass
class HNLink:
    url: str
    item_id: str


@dataclass
class ParsedNote:
    note_id: str
    title: str
    url: str
    item_id: str
    labels: List[str]
    description: str
    hn_links: List[HNLink]


class HackerNewsParser(NoteParser):
    HN_URL_PATTERN: str = r'https?://news\.ycombinator\.com/item\?id=(\d+)'
    DOWNLOAD_HN_LABEL: str = 'Download-HN'
    HASHTAG_PATTERN: str = r'#(\w+)'
    
    def can_parse(self, note_data: Any) -> bool:
        if not isinstance(note_data, dict):
            return False
        
        text: str = note_data.get('text', '')
        title: str = note_data.get('title', '')
        labels: List[Any] = note_data.get('labels', [])
        
        has_hn_label: bool = any(str(label) == self.DOWNLOAD_HN_LABEL for label in labels)
        has_hn_url: bool = bool(re.search(self.HN_URL_PATTERN, text)) or bool(re.search(self.HN_URL_PATTERN, title))
        
        return has_hn_label or has_hn_url
    
    def parse(self, note_data: Any) -> ParsedNote:
        if not isinstance(note_data, dict):
            raise ValueError("note_data must be a dictionary")
        
        text: str = note_data.get('text', '')
        title: str = note_data.get('title', '')
        labels: List[Any] = note_data.get('labels', [])
        
        hn_urls: List[HNLink] = self._extract_hn_urls_from_title_and_body(title, text)
        
        all_labels: List[str] = [str(label) for label in labels]
        hashtag_labels: List[str] = self._extract_hashtag_labels(text)
        all_labels.extend(hashtag_labels)
        
        return ParsedNote(
            note_id=note_data.get('id', ''),
            title=title,
            url=hn_urls[0].url if hn_urls else '',
            item_id=hn_urls[0].item_id if hn_urls else '',
            labels=all_labels,
            description=text,
            hn_links=hn_urls
        )
    
    def _extract_hn_urls_from_title_and_body(self, title: str, text: str) -> List[HNLink]:
        urls: List[HNLink] = []
        
        urls.extend(self._extract_hn_urls(title))
        urls.extend(self._extract_hn_urls(text))
        
        return urls
    
    def _extract_hn_urls(self, text: str) -> List[HNLink]:
        urls: List[HNLink] = []
        matches = re.finditer(self.HN_URL_PATTERN, text)
        
        for match in matches:
            item_id: str = match.group(1)
            url: str = match.group(0)
            urls.append(HNLink(url=url, item_id=item_id))
        
        return urls
    
    def _extract_hashtag_labels(self, text: str) -> List[str]:
        labels: List[str] = []
        matches = re.finditer(self.HASHTAG_PATTERN, text)
        
        for match in matches:
            label: str = match.group(1)
            labels.append(label)
        
        return labels
    
    def get_schema(self) -> Dict[str, Any]:
        schema_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', 'hackernews.schema.json')
        with open(schema_path, 'r') as f:
            schema: Dict[str, Any] = json.load(f)
            return schema
