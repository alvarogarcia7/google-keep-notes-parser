from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type
from jsonschema import validate, ValidationError
from dataclasses import asdict, is_dataclass


class NoteParser(ABC):
    @abstractmethod
    def can_parse(self, note_data: Any) -> bool:
        pass

    @abstractmethod
    def parse(self, note_data: Any) -> Any:
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        pass


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: List[Type[NoteParser]] = []

    def register(self, parser_class: Type[NoteParser]) -> None:
        if not issubclass(parser_class, NoteParser):
            raise TypeError(f"{parser_class} must be a subclass of NoteParser")
        self._parsers.append(parser_class)

    def unregister(self, parser_class: Type[NoteParser]) -> None:
        if parser_class in self._parsers:
            self._parsers.remove(parser_class)

    def get_parser(self, note_data: Any) -> NoteParser:
        for parser_class in self._parsers:
            parser = parser_class()
            if parser.can_parse(note_data):
                return parser
        raise ValueError("No suitable parser found for the given note data")

    def get_all_parsers(self) -> List[Type[NoteParser]]:
        return self._parsers.copy()

    def clear(self) -> None:
        self._parsers.clear()

    def parse(self, note_data: Any) -> Any:
        parser = self.get_parser(note_data)
        parsed_data = parser.parse(note_data)
        schema = parser.get_schema()
        
        # Convert dataclass to dict for validation if needed
        if is_dataclass(parsed_data) and not isinstance(parsed_data, type):
            validation_data = asdict(parsed_data)
        else:
            validation_data = parsed_data
        
        try:
            validate(instance=validation_data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Parsed data does not conform to schema: {e.message}")
        
        return parsed_data
