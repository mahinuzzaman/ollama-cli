# Installation Guide

This guide covers various methods to install Olla CLI and its dependencies.

## Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows with WSL
- **Ollama**: Required for AI model interaction

## Installing Ollama

### Linux/macOS
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
```powershell
# PowerShell (Run as Administrator)
iex (irm ollama.ai/install.ps1)
```

### Manual Installation
Visit [ollama.ai](https://ollama.ai) for platform-specific installers.

## Installing Olla CLI

### Method 1: PyPI (Recommended)

```bash
pip install olla-cli
```

### Method 2: From Source

```bash
# Clone the repository
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: Using Poetry

```bash
# Clone and install with Poetry
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli
poetry install
poetry shell
```

### Method 4: Using pipx (Isolated Installation)

```bash
# Install globally but isolated
pipx install olla-cli

# Or from source
pipx install git+https://github.com/mahinuzzaman/ollama-cli.git
```

## Model Setup

After installing Ollama and Olla CLI, you need to pull at least one AI model:

### Recommended Models

```bash
# Code-focused model (recommended)
ollama pull codellama

# General purpose models
ollama pull llama2
ollama pull mistral
ollama pull deepseek-coder

# Lightweight options
ollama pull tinyllama
ollama pull phi
```

### Model Comparison

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| `codellama` | ~7GB | Code analysis, generation | Medium |
| `deepseek-coder` | ~6GB | Advanced coding tasks | Medium |
| `mistral` | ~4GB | General purpose | Fast |
| `llama2` | ~7GB | General purpose | Medium |
| `tinyllama` | ~700MB | Quick responses | Very Fast |
| `phi` | ~2GB | Code and reasoning | Fast |

## Verification

### Test Installation

```bash
# Check Olla CLI version
olla-cli version

# List available models
olla-cli models list

# Test basic functionality
olla-cli explain "print('Hello, World!')"
```

### Test Ollama Connection

```bash
# Check Ollama service
ollama ps

# Test API connection
curl http://localhost:11434/api/tags
```

## Platform-Specific Instructions

### macOS

```bash
# Using Homebrew (if available)
brew install ollama

# Install Olla CLI
pip3 install olla-cli

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Linux (Ubuntu/Debian)

```bash
# Update system
sudo apt update

# Install Python and pip if needed
sudo apt install python3 python3-pip

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install Olla CLI
pip3 install olla-cli

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Windows (WSL)

```bash
# Install in WSL Ubuntu
sudo apt update
sudo apt install python3 python3-pip

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install Olla CLI
pip3 install olla-cli
```

### Docker Installation

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Install Olla CLI
RUN pip install olla-cli

# Pull a model
RUN ollama pull codellama

ENTRYPOINT ["olla-cli"]
```

```bash
# Build and run
docker build -t olla-cli .
docker run -it olla-cli --help
```

## Troubleshooting Installation

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version
python3 --version

# Use specific Python version
python3.9 -m pip install olla-cli
```

#### Permission Issues
```bash
# Install in user directory
pip install --user olla-cli

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install olla-cli
```

#### PATH Issues
```bash
# Find installation location
pip show -f olla-cli

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Make permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

#### Ollama Connection Issues
```bash
# Start Ollama service manually
ollama serve

# Check if running
ps aux | grep ollama

# Check logs
journalctl -u ollama
```

### Clean Installation

If you encounter issues, try a clean installation:

```bash
# Uninstall
pip uninstall olla-cli

# Clear cache
pip cache purge

# Remove config (optional)
rm -rf ~/.olla-cli/

# Reinstall
pip install olla-cli
```

## Development Installation

For developers who want to contribute:

```bash
# Clone repository
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8 src/
black src/
```

## Updating

### Update Olla CLI
```bash
pip install --upgrade olla-cli
```

### Update Ollama
```bash
# Update Ollama
ollama update

# Update models
ollama pull codellama
```

## Next Steps

After successful installation:

1. **Configure**: See [Configuration Guide](./configuration.md)
2. **Learn Usage**: Check [Usage Guide](./usage.md)
3. **Try Examples**: Explore [Examples](./examples.md)
4. **Get Help**: Read [Troubleshooting](./troubleshooting.md)