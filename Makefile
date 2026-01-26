.PHONY: help install run parse-notes clean docker-build docker-run mypy lint

help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies using pip"
	@echo "  run           - Run kim.py to process JSON notes"
	@echo "  parse-notes   - Run parse_notes.py parser tool"
	@echo "  mypy          - Run mypy type checking on parsers and parse_notes.py"
	@echo "  lint          - Run ruff and mypy checks (if installed)"
	@echo "  clean         - Remove generated files and directories"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  help          - Show this help message"

install:
	pip install -r requirements.txt

run:
	python kim.py --help

parse-notes:
	python parse_notes.py --help

mypy:
	mypy parsers/ parse_notes.py

lint: mypy
	ruff check parsers/ parse_notes.py kim.py

clean:
	rm -rf mdfiles/
	rm -rf media/
	rm -rf parsed_output/
	rm -f settings.cfg
	rm -rf __pycache__/
	rm -rf parsers/__pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/

docker-build:
	docker build -t kim-parser .

docker-run:
	docker run -it kim-parser
