# Olla CLI

```
 ██████╗ ██╗     ██╗      █████╗       ██████╗██╗     ██╗
██╔═══██╗██║     ██║     ██╔══██╗     ██╔════╝██║     ██║
██║   ██║██║     ██║     ███████║     ██║     ██║     ██║
██║   ██║██║     ██║     ██╔══██║     ██║     ██║     ██║
╚██████╔╝███████╗███████╗██║  ██║     ╚██████╗███████╗██║
 ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝      ╚═════╝╚══════╝╚═╝
```

**Your AI-Powered Coding Assistant in the Terminal** ⚡

Olla CLI is a powerful command-line interface that brings AI coding assistance directly to your terminal. Built on top of Ollama, it provides intelligent code analysis, generation, debugging, and more with beautiful Rich-formatted output.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🤖 **Interactive by Default**: Conversational AI assistant that starts immediately
- 🔄 **Automatic Execution**: Multi-step task planning and automatic tool orchestration
- 📁 **Smart File Creation**: Automatically creates and saves code to appropriately named files
- 🎯 **Intent Classification**: Understands what you want to do from natural language
- 💬 **Session Memory**: Maintains context throughout conversations
- 🔍 **Context-Aware**: Intelligent project analysis and dependency tracking
- ⚡ **Streaming Responses**: Real-time AI responses with progress indicators
## 📋 Requirements

- **Python**: 3.8 or higher
- **Ollama**: Latest version ([installation guide](https://ollama.ai))
- **Operating System**: Linux or Windows with WSL

## 🚀 Installation

### Method 1: Install from PyPI (Recommended)
```bash
pip install olla-cli
```

### Method 2: Install from Source
```bash
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli
pip install -e .
```

### Setup
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull codellama

# Verify installation
ollama -v
```

### Basic Usage
```bash
# Start interactive mode (default behavior)
olla-cli

# Then just talk to your AI assistant:
# You: create a todo react app
# You: explain how this code works
# You: review my authentication function
# You: generate unit tests for my calculator

# Other commands
olla-cli config show    # Manage configuration
olla-cli version        # Show version
olla-cli --help         # Get help
```

## 🛠️ Commands Overview

| Command | Description |
|---------|-------------|
| `olla-cli` | Start interactive AI assistant (default) |
| `olla-cli config` | Manage configuration settings |
| `olla-cli version` | Show version information |

### 🎯 Interactive Mode Capabilities

Once in interactive mode, you can:
- **Code Generation**: "create a hello world function", "build a React todo app"
- **Code Analysis**: "explain this code", "review my function for bugs"
- **File Operations**: "read this file", "save the code to calculator.py"
- **Complex Tasks**: "create a REST API with authentication"
- **Project Help**: "analyze my codebase", "suggest improvements"


### Development Setup
```bash
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli
python -m venv venv
source venv/bin/activate
pip install -e .

# Start using immediately
olla-cli
```

## 📚 Documentation

For comprehensive documentation, visit the [docs/](./docs/) directory:

| Document | Description |
|----------|-------------|
| [📖 Complete Documentation](./docs/README.md) | Main documentation index |
| [🚀 Quick Start Guide](./docs/quick-start.md) | 5-minute setup guide |
| [📚 API Reference](./docs/api-reference.md) | Complete command reference |
| [🔧 Troubleshooting](./docs/troubleshooting.md) | Common issues and solutions |

## 🔗 Links

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/mahinuzzaman/ollama-cli/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/mahinuzzaman/ollama-cli/discussions)
- 🚀 **Releases**: [GitHub Releases](https://github.com/mahinuzzaman/ollama-cli/releases)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

⭐ If you find Olla CLI useful, please consider giving it a star!

</div>