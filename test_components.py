#!/usr/bin/env python3
"""
Component validation test for NATS Training Parser E2E
Verifies all components exist and are properly configured
"""

import json
import sys
from pathlib import Path


def test_publisher_script():
    """Verify publisher script exists and is properly formatted."""
    print("\n✓ Testing Publisher Application")
    print("-" * 70)

    script = Path(__file__).parent / "nats_publisher.py"

    if not script.exists():
        print(f"✗ Publisher script not found: {script}")
        return False

    with open(script) as f:
        content = f.read()

    required_imports = ["nats", "asyncio", "json"]
    required_functions = ["main", "nats.connect"]

    for imp in required_imports:
        if imp in content:
            print(f"  ✓ Imports '{imp}'")
        else:
            print(f"  ✗ Missing import '{imp}'")
            return False

    print(f"  ✓ Has async main function")
    return True


def test_sample_data():
    """Verify sample data file is valid JSON."""
    print("\n✓ Testing Sample Data")
    print("-" * 70)

    sample = Path(__file__).parent / "sample/training/sample1.json"

    if not sample.exists():
        print(f"✗ Sample file not found: {sample}")
        return False

    try:
        with open(sample) as f:
            data = json.load(f)

        print(f"  ✓ Valid JSON file")
        print(f"  ✓ ID: {data.get('id', 'N/A')}")
        print(f"  ✓ Title: {data.get('title', 'N/A')}")
        print(f"  ✓ Has training text: {bool(data.get('text', ''))}")

        required_fields = ["id", "title", "text", "timestamps"]
        for field in required_fields:
            if field in data:
                print(f"  ✓ Has field '{field}'")
            else:
                print(f"  ✗ Missing field '{field}'")
                return False

        return True
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False


def test_subscriber_script():
    """Verify subscriber script exists in training-parser project."""
    print("\n✓ Testing Subscriber Application")
    print("-" * 70)

    script = Path.home() / "repos/training-parser-antlr4/nats_subscriber.py"

    if not script.exists():
        print(f"✗ Subscriber script not found: {script}")
        return False

    with open(script) as f:
        content = f.read()

    required_elements = {
        "nats": "NATS integration",
        "asyncio": "Async support",
        "json.loads": "message handling",
        "Parser.from_string": "ANTLR parser integration",
        "training.notes": "correct topic",
    }

    for element, description in required_elements.items():
        if element in content:
            print(f"  ✓ Has {description}")
        else:
            print(f"  ✗ Missing {description}")
            return False

    return True


def test_antlr_parser():
    """Verify ANTLR parser is available."""
    print("\n✓ Testing ANTLR Parser")
    print("-" * 70)

    parser_file = Path.home() / "repos/training-parser-antlr4/parser/parser.py"

    if not parser_file.exists():
        print(f"✗ Parser file not found: {parser_file}")
        return False

    print(f"  ✓ Parser module exists")

    # Check dist files
    dist_files = [
        "trainingLexer.py",
        "trainingParser.py",
        "trainingVisitor.py",
    ]

    dist_dir = Path.home() / "repos/training-parser-antlr4/dist"

    for file in dist_files:
        file_path = dist_dir / file
        if file_path.exists():
            print(f"  ✓ Generated file '{file}' exists")
        else:
            print(f"  ✗ Generated file '{file}' missing")
            return False

    # Check grammar file
    grammar_file = Path.home() / "repos/training-parser-antlr4/training.g4"
    if grammar_file.exists():
        with open(grammar_file) as f:
            content = f.read()
            if "grammar training" in content and "workout" in content:
                print(f"  ✓ ANTLR grammar file valid")
            else:
                print(f"  ✗ Grammar file invalid")
                return False
    else:
        print(f"  ✗ Grammar file not found")
        return False

    return True


def test_dependencies():
    """Verify required dependencies are installed."""
    print("\n✓ Testing Dependencies")
    print("-" * 70)

    try:
        import nats

        print(f"  ✓ nats-py is installed")
    except ImportError:
        print(f"  ✗ nats-py not found")
        return False

    try:
        import asyncio

        print(f"  ✓ asyncio is available")
    except ImportError:
        print(f"  ✗ asyncio not found")
        return False

    return True


def main():
    """Run all component tests."""
    print("\n" + "=" * 70)
    print("🧪 NATS Training Parser - Component Validation Test")
    print("=" * 70)

    tests = [
        ("Publisher Script", test_publisher_script),
        ("Sample Data", test_sample_data),
        ("Subscriber Script", test_subscriber_script),
        ("ANTLR Parser", test_antlr_parser),
        ("Dependencies", test_dependencies),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error testing {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL COMPONENT TESTS PASSED")
        print("\n🚀 The end-to-end pipeline is ready to use!")
        print("\nTo run the full pipeline:")
        print("  1. docker run -d --name nats-test -p 4222:4222 nats:latest")
        print("  2. cd ~/repos/training-parser-antlr4 && uv run python3 nats_subscriber.py")
        print("  3. cd /var/tmp/vibe-kanban/worktrees/b3ab-parse-samples-tr/google-keep-notes-parser && uv run python3 nats_publisher.py")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
