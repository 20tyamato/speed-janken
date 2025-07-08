# Python Template

This repository contains templates for a python project. Copy this repository and start your project.

## Python and Pip Installation

- Python 3.11.5
- pip 25.0.1

## Installation

The package can be installed like this:

```shell
git clone https://github.com/20tyamato/python-template.git new-project
cd new-project
rm -rf .git
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin "https://$GIT_PERSONAL_TOKEN@github.com/20tyamato/new-project.git"
git push -u origin main
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements.txt
pre-commit install
```

## Lint & Format

This repository uses [Ruff](https://github.com/astral-sh/ruff) to run lint & format codes.
You can set up pre-commit git hooks by running following commands, then formatter is run automatically before commit.

```console
pre-commit install
```

or you can also run manually

```console
python -m ruff check
python -m ruff format
```

## Tests

```console
export PYTHONPATH=$(pwd)
pytest -c config/pytest.ini
pip check
```

## pip packages installed

```console
pip install python-dotenv
pip install colorlog
pip install pytest
pip install pre-commit
pip install ruff
pip install openai
pip install torch
pip install pandas
```

## How to push to GitHub

```console
git remote set-url origin "https://$GIT_PERSONAL_TOKEN@github.com/20tyamato/python-template.git"
git push -u origin main
```
