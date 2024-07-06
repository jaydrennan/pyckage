init:
	rye sync
	. .venv/bin/activate


up:
	rye build --clean
	rye uninstall pyckage
	rye install .

format:
	ruff format

lint:
	ruff c