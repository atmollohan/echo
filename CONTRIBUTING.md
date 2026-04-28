# Contributing to Echo Protocol

We welcome contributions! Whether you want to add a new feature, fix a bug, or improve the documentation, we're glad to have you involved.

## Ways to Contribute

### Report Bugs
Found something not working as expected? Open an issue on GitHub:
https://github.com/atmollohan/echo/issues

Include:
- What you expected to happen
- What actually happened
- Steps to reproduce the issue
- Your environment (OS, Docker version, etc.)

### Suggest Features
Have an idea for how to make this tool more useful? Open a GitHub issue with the label "enhancement". Describe:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you considered

### Contribute Code

#### Prerequisites
- Python 3.11 or higher
- Git

#### 1. Fork the Repository

Click the "Fork" button on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/echo.git
cd echo
```

#### 2. Set Up Your Development Environment

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

#### 3. Run the App Locally

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

#### 4. Make Your Changes

- Create a new branch for your feature:
  ```bash
  git checkout -b feature/my-new-feature
  ```

- Make your changes and commit them:
  ```bash
  git add .
  git commit -m "Add brief description of your changes"
  ```

#### 5. Submit a Pull Request

Push your branch and open a pull request on GitHub:
https://github.com/atmollohan/echo/pulls

## Development Tips

### Running Tests
Check the tests pass before submitting:
```bash
pytest
```

### Code Style
We use ruff for linting and mypy for type checking:
```bash
ruff check echo_run/
mypy echo_run/ --ignore-missing-imports
```

## Getting Help

- Open an issue on GitHub: https://github.com/atmollohan/echo/issues
- Check existing issues before opening a new one

## Code of Conduct

Be respectful and inclusive. We're all here to help lab scientists automate their work.