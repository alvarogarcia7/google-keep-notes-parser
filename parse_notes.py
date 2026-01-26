import os
import json
import click
from pathlib import Path
from dataclasses import is_dataclass, asdict
from typing import Any, cast

from parsers.base import ParserRegistry
from parsers.hackernews_parser import HackerNewsParser
from parsers.time_entry_parser import TimeEntryParser
from parsers.training_parser import TrainingParser


def create_output_path(output_dir: str) -> None:
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def process_json_file(json_path: str, output_dir: str, registry: ParserRegistry) -> bool:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            note_data = json.load(f)
        
        parsed_results: Any = registry.parse(note_data)
        
        if is_dataclass(parsed_results):
            parsed_results = asdict(cast(Any, parsed_results))
        
        output_filename: str = Path(json_path).stem + "_parsed.json"
        output_path: str = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_results, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        click.echo(f"Error processing {json_path}: {e}")
        return False


@click.command()
@click.option('--input-dir', default='mdfiles', help='Input directory containing JSON files')
@click.option('--output-dir', default='parsed_output', help='Output directory for parsed results')
def main(input_dir: str, output_dir: str) -> None:
    if not os.path.exists(input_dir):
        click.echo(f"Error: Input directory '{input_dir}' does not exist")
        return
    
    create_output_path(output_dir)
    
    registry: ParserRegistry = ParserRegistry()
    registry.register(HackerNewsParser)
    registry.register(TimeEntryParser)
    registry.register(TrainingParser)
    
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    if not json_files:
        click.echo(f"No JSON files found in '{input_dir}'")
        return
    
    click.echo(f"Found {len(json_files)} JSON file(s) in '{input_dir}'")
    
    processed_count: int = 0
    for json_file in json_files:
        json_path: str = os.path.join(input_dir, json_file)
        if process_json_file(json_path, output_dir, registry):
            processed_count += 1
            click.echo(f"Processed: {json_file}")
    
    click.echo(f"\nProcessed {processed_count}/{len(json_files)} files successfully")
    click.echo(f"Results saved to '{output_dir}'")


if __name__ == '__main__':
    main()
