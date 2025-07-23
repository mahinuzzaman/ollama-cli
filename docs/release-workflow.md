# Release Workflow

This document describes how to release new versions of Olla CLI using the Makefile commands.

## Prerequisites

Make sure you have the following tools installed:
- Python 3.8+
- Docker (for containerized builds)
- Make
- Git

### PyPI Credentials

Set up your PyPI credentials in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Install in development mode
make install-dev

# Check dependencies
make check-deps
```

### 2. Code Quality Checks

```bash
# Format code
make format

# Run linters
make lint

# Run security checks
make security

# Run all checks
make check-all
```

### 3. Testing

```bash
# Run tests
make test

# Run tests in Docker
make run-command-test
```

### 4. Build Package

```bash
# Build distribution packages
make build
```

## Release Process

### 1. Test Release (TestPyPI)

```bash
# Release to TestPyPI for testing
make release-test
```

This will:
- Run all quality checks
- Build the package
- Upload to TestPyPI
- Provide a link to verify the release

Test the release:
```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ olla-cli

# Test basic functionality
olla-cli version
olla-cli --help
```

### 2. Production Release (PyPI)

```bash
# Release to production PyPI
make release-prod
```

This will:
- Run all quality checks
- Build the package
- Prompt for confirmation
- Upload to PyPI
- Suggest creating a Git tag

### 3. Create Git Tag

After successful release:
```bash
# Create and push tag
git tag v$(make version | cut -d' ' -f3)
git push origin v$(make version | cut -d' ' -f3)
```

## Docker Workflow

### Build Docker Image

```bash
# Build development Docker image
make docker-build
```

### Run Commands in Docker

You can run any Makefile command in a Docker container:

```bash
# Run tests in Docker
make run-command-test

# Run linting in Docker
make run-command-lint

# Run all checks in Docker
make run-command-check-all

# Build package in Docker
make run-command-build
```

### Clean Docker Images

```bash
# Clean up Docker images
make docker-clean
```

## Version Management

### Check Current Version

```bash
make version
```

### Update Version

Edit `src/olla_cli/__init__.py` and update the `__version__` variable:

```python
__version__ = "0.4.0"
```

Or use bump2version (if installed):

```bash
# Install bump2version
pip install bump2version

# Bump patch version (0.3.0 -> 0.3.1)
bump2version patch

# Bump minor version (0.3.0 -> 0.4.0)
bump2version minor

# Bump major version (0.3.0 -> 1.0.0)
bump2version major
```

## Complete Release Example

Here's a complete example of releasing version 0.4.0:

```bash
# 1. Update version
# Edit src/olla_cli/__init__.py: __version__ = "0.4.0"

# 2. Run all checks
make check-all

# 3. Test release
make release-test

# 4. Test the TestPyPI package
pip install --index-url https://test.pypi.org/simple/ olla-cli==0.4.0
olla-cli version

# 5. Production release
make release-prod

# 6. Create Git tag
git tag v0.4.0
git push origin v0.4.0

# 7. Clean up
make clean
```

## Troubleshooting

### Build Issues

```bash
# Check dependencies
make check-deps

# Clean and rebuild
make clean
make build
```

### Docker Issues

```bash
# Rebuild Docker image
make docker-clean
make docker-build

# Check Docker is running
docker ps
```

### Release Issues

```bash
# Check PyPI credentials
cat ~/.pypirc

# Verify package can be uploaded
twine check dist/*

# Manual upload (if needed)
twine upload dist/*
```

### Testing Issues

```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_specific.py -v

# Run tests in Docker for consistency
make run-command-test
```

## CI/CD Integration

The Makefile commands can be easily integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
- name: Install dependencies
  run: make install-dev

- name: Run all checks
  run: make check-all

- name: Build package
  run: make build

- name: Release to TestPyPI
  run: make release-test
  if: github.ref == 'refs/heads/develop'

- name: Release to PyPI
  run: make release-prod
  if: github.ref == 'refs/heads/main'
```

### Docker CI Example

```yaml
- name: Run tests in Docker
  run: make run-command-check-all

- name: Build and release in Docker
  run: |
    make docker-build
    docker run --rm -v $(pwd):/workspace \
      -v ~/.pypirc:/root/.pypirc:ro \
      olla-cli-dev:latest make release-prod
```