# pyckage

pyckage is a basic NodeJS package manager implemented in Python.

## Features

- Add packages to package.json
- Install packages from package.json
- Automatically check and resolve dependency conflicts

## Installation

You can install pyckage directly from GitHub using pip:

```bash
pip install git+https://github.com/jaydrennan/pyckage.git
```

Alternatively, you can add it to your project's `requirements.txt` file:

```
git+https://github.com/jaydrennan/pyckage.git
```

Or in your `pyproject.toml`:

```toml
dependencies = [
    "pyckage @ git+https://github.com/jaydrennan/pyckage.git",
]
```

## Examples

```bash
pyckage add is-thirteen@2.0.0
```

```bash
pyckage install
```

