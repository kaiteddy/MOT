# Contributing to MOT OCR System

Thank you for your interest in contributing to the MOT OCR System! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- API keys for vision models (Anthropic, OpenAI, Google)
- DVLA API key

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/MOTCHECK.git
cd MOTCHECK

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run tests to verify setup
python test_system.py
pytest tests/
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-model-support`
- `bugfix/fix-registration-validation`
- `improvement/optimize-ensemble-pipeline`
- `docs/update-api-documentation`

### Code Style

We follow PEP 8 with some modifications:

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for Gemini Pro Vision model
fix: resolve DVLA API timeout issues
docs: update installation guide
test: add comprehensive validation tests
```

## Project Structure

```
MOTCHECK/
├── src/
│   ├── vision_models/      # Vision-Language Model implementations
│   ├── pipeline/           # Ensemble processing pipeline
│   ├── validation/         # UK format validation
│   ├── dvla/              # DVLA API integration
│   ├── api/               # FastAPI endpoints
│   └── utils/             # Utilities (logging, file handling)
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/                # Configuration files
└── requirements.txt       # Dependencies
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validation.py

# Run system verification
python test_system.py
```

### Writing Tests

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Include both positive and negative test cases

Example test structure:

```python
class TestNewFeature:
    def setup_method(self):
        """Set up test fixtures."""
        pass
    
    def test_valid_input(self):
        """Test with valid input."""
        pass
    
    def test_invalid_input(self):
        """Test with invalid input."""
        pass
    
    def test_edge_cases(self):
        """Test edge cases."""
        pass
```

## Areas for Contribution

### High Priority

1. **Additional Vision Models**
   - Implement Florence-2 integration
   - Add support for other VLMs
   - Optimize model selection logic

2. **Performance Improvements**
   - Caching mechanisms
   - Parallel processing optimization
   - Memory usage optimization

3. **Validation Enhancements**
   - Additional UK registration formats
   - Enhanced date parsing
   - Business logic validation

### Medium Priority

1. **API Enhancements**
   - Batch processing endpoints
   - Webhook support
   - Rate limiting improvements

2. **Monitoring & Observability**
   - Metrics collection
   - Performance monitoring
   - Error tracking

3. **Documentation**
   - Tutorial videos
   - Integration examples
   - Troubleshooting guides

### Low Priority

1. **UI Development**
   - Web interface for testing
   - Admin dashboard
   - Result visualization

2. **Deployment Tools**
   - Docker improvements
   - Kubernetes manifests
   - CI/CD pipelines

## Submitting Changes

### Pull Request Process

1. **Create a Pull Request**
   - Use a descriptive title
   - Include a detailed description
   - Reference any related issues

2. **PR Description Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] New tests added
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   ```

3. **Review Process**
   - All PRs require review
   - Address feedback promptly
   - Keep PRs focused and small

### Code Review Guidelines

**For Authors:**
- Keep PRs small and focused
- Write clear descriptions
- Respond to feedback constructively

**For Reviewers:**
- Be constructive and helpful
- Focus on code quality and maintainability
- Test the changes locally when possible

## Reporting Issues

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. macOS, Linux, Windows]
- Python version: [e.g. 3.9]
- Version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## Development Guidelines

### Adding New Vision Models

1. Create new model class in `src/vision_models/`
2. Inherit from `BaseVisionModel`
3. Implement required methods
4. Add configuration options
5. Update ensemble pipeline
6. Add comprehensive tests

### API Development

1. Follow FastAPI best practices
2. Use Pydantic models for validation
3. Include proper error handling
4. Add comprehensive documentation
5. Write integration tests

### Documentation

1. Update relevant documentation
2. Include code examples
3. Keep API docs current
4. Add troubleshooting info

## Getting Help

- Check existing issues and documentation
- Join our community discussions
- Ask questions in pull requests
- Contact maintainers for guidance

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to the MOT OCR System!
