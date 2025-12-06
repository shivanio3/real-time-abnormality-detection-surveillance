# Contributing Guidelines

Thank you for your interest in contributing to the Real-Time Abnormality Detection System! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the work, not the person
- Help create a welcoming environment

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Screenshots or logs if applicable
   - System information (OS, Python version, GPU info)

### Suggesting Enhancements

1. Use Issues to suggest enhancements
2. Provide:
   - Clear description of the feature
   - Motivation and use case
   - Possible implementation approach
   - Additional context or mockups

### Pull Requests

1. **Fork the repository** and create your feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Make your changes**
   - Follow PEP 8 style guidelines
   - Add comments for complex logic
   - Write docstrings for functions and classes
   - Update README.md if needed

4. **Test your changes**
   ```bash
   python -m pytest tests/
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "type: Brief description of changes"
   ```
   Use commit types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

6. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   - Provide clear description of changes
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure all tests pass

## Development Setup

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up `.env` file with your configuration

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for >80% code coverage

## Code Style

- Follow PEP 8
- Use type hints where possible
- Maximum line length: 100 characters
- Use descriptive variable names

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions
- Include inline comments for complex logic
- Keep docs synchronized with code

## Project Structure

```
.
├── app.py              # Flask application
├── detector.py         # Detection pipeline
├── alert_system.py     # Email alerts
├── requirements.txt    # Dependencies
├── .env.example        # Configuration template
├── README.md           # Project documentation
└── templates/          # HTML templates
    └── index.html      # Dashboard UI
```

## Questions?

- Check existing Issues and Discussions
- Review README.md and code comments
- Open a Discussion for questions

Thank you for contributing! 🎉
