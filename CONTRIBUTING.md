# Contributing to Audio Pollinations

Thank you for your interest in contributing to Audio Pollinations! We welcome contributions from the community and appreciate your help in making this project better.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read our expectations for respectful collaboration:

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the work, not the person
- Report any code of conduct violations to the maintainers

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

**When reporting bugs, include:**
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Screenshots or logs (if applicable)
- Your environment details:
  - OS and version
  - Python version (should be 3.11+)
  - CUDA version (if using GPU)
  - Docker version (if using Docker)
  - Audio Pollinations version

### Suggesting Enhancements

**Enhancement suggestions should include:**
- A clear description of the enhancement
- Use cases and examples
- Potential implementation approach
- Why this enhancement would be useful

### Pull Requests

We love pull requests! Here's how to get started:

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Set up your development environment:**
   ```bash
   # Clone your fork
   git clone https://github.com/YOUR-USERNAME/lixaudio.git
   cd lixaudio
   
   # Create virtual environment (Python 3.11+)
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -e .  # If setup.py exists
   ```

3. **Make your changes:**
   - Follow the code style guidelines (see below)
   - Add or update tests as needed
   - Update documentation if needed
   - Ensure your code is well-commented

4. **Test your changes:**
   ```bash
   # Run linting
   ruff check api/
   
   # Run type checking (if applicable)
   python -m mypy api/
   
   # Run tests (if test suite exists)
   pytest tests/
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Brief description of changes
   
   - Detailed explanation if needed
   - Mention related issues (e.g., Fixes #123)"
   ```

6. **Push to your fork and submit a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Respond to feedback** during code review

## Code Style Guide

### Python Code Style

- **Follow PEP 8** for general Python style
- **Line length:** Maximum 100 characters
- **Use type hints** for function parameters and returns
- **Use descriptive names** for variables, functions, and classes
- **Use docstrings** for modules, classes, and functions

### Example:

```python
from typing import Optional, Tuple
import torch
from loguru import logger

def process_audio(
    audio_path: str, 
    sample_rate: int = 16000,
    duration_sec: Optional[int] = None
) -> Tuple[torch.Tensor, int]:
    """
    Process audio file and return tensor and sample rate.
    
    Args:
        audio_path: Path to audio file
        sample_rate: Target sample rate in Hz
        duration_sec: Optional duration limit in seconds
        
    Returns:
        Tuple of (audio_tensor, actual_sample_rate)
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If sample_rate is invalid
    """
    logger.info(f"Processing audio from {audio_path}")
    # Implementation here
    return audio_tensor, sample_rate
```

### Logging

Use `loguru` for logging, not `print()`:

```python
from loguru import logger

logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### Comments

- Comment **why**, not **what** (code should be clear enough for readers to understand what)
- Use comments sparingly for complex logic
- Keep comments up-to-date with code changes

```python
# Good
# Use Faster-Whisper for faster transcription with VAD filtering
segments, _ = model.transcribe(audio_path, vad_filter=True)

# Avoid
# Transcribe audio
segments, _ = model.transcribe(audio_path, vad_filter=True)
```

### Imports

- Organize imports in three groups:
  1. Standard library
  2. Third-party packages
  3. Local imports
- Sort within each group alphabetically
- Use absolute imports

```python
import asyncio
import os
from typing import Optional, Tuple

import torch
import torchaudio
from loguru import logger

from api.utility import validate_audio
from api.config import MAX_DURATION_SEC
```

## Project Structure

```
api/
├── app.py              # Flask application
├── config.py           # Configuration constants
├── intent.py           # Intent detection and content extraction
├── model_server.py     # Model serving with Faster-Whisper and TTS
├── server.py           # Audio pipeline orchestration
├── stt.py              # Speech-to-text wrapper
├── sts.py              # Speech-to-speech wrapper
├── tts.py              # Text-to-speech wrapper
├── ttt.py              # Text-to-text wrapper
├── utility.py          # Utility functions
├── voiceMap.py         # Voice mappings and configurations
└── requestID.py        # Request ID generation
```

## Testing

When adding new features:

1. **Write tests** for new functionality
2. **Test edge cases** (empty inputs, large files, etc.)
3. **Test error handling** (invalid inputs, failures)
4. **Test with different audio formats** if applicable

```python
# Example test structure
def test_audio_transcription():
    """Test basic audio transcription."""
    audio_path = "test_audio.wav"
    result = transcribe(audio_path)
    assert isinstance(result, str)
    assert len(result) > 0

def test_transcription_error_handling():
    """Test error handling for invalid audio."""
    with pytest.raises(FileNotFoundError):
        transcribe("nonexistent.wav")
```

## Documentation

- Update [README.md](README.md) for user-facing changes
- Add docstrings to all public functions and classes
- Include examples in docstrings for complex functions
- Update API documentation if endpoints change

## Performance Considerations

When contributing code:

- Consider GPU memory usage
- Batch operations where possible
- Use appropriate data types (e.g., float32 vs float64)
- Profile code for bottlenecks
- Document performance characteristics

```python
# Log performance metrics
start_time = time.time()
result = process_audio(audio)
elapsed = time.time() - start_time
logger.info(f"Processing took {elapsed:.2f} seconds")
```

## Docker Development

If testing Docker changes:

```bash
# Build local image
docker build -t lixaudio:dev .

# Run with docker-compose
docker-compose up

# Check logs
docker-compose logs -f audio-pollinations

# Stop services
docker-compose down
```

## Dependencies

- **Don't add unnecessary dependencies** - justify new packages
- **Pin versions** in requirements.txt - use exact versions (e.g., `==1.2.3`)
- **Verify compatibility** with Python 3.11 and CUDA 12.4
- **Check licenses** - ensure compatibility with GPL-3.0

## Commit Guidelines

- Write clear, descriptive commit messages
- Use present tense ("Add feature" not "Added feature")
- Reference related issues
- Keep commits atomic (one logical change per commit)

```bash
# Good commit message
git commit -m "Add Faster-Whisper language detection

- Automatically detect audio language without explicit parameter
- Reduces API calls for multilingual inputs
- Fixes #45"

# Avoid
git commit -m "update stuff"
git commit -m "Fixed bugs and added features"
```

## Release Process

Maintainers follow this process for releases:

1. Update version numbers
2. Update CHANGELOG
3. Run full test suite
4. Tag release on GitHub
5. Build and publish Docker image
6. Announce release

## Questions?

- **Check existing issues** for answers
- **Review documentation** and examples
- **Ask in discussions** if unsure

## Recognition

Contributors will be recognized:
- In commit history and pull requests
- In project README (for significant contributions)
- As project collaborators

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0 (GPL-3.0). See [LICENSE](LICENSE) for details.

---

**Thank you for contributing to Audio Pollinations!** 🎉

Your efforts help make this project better for everyone.
