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

- 🎯 **Intelligent Code Analysis**: Explain, review, and debug code with AI assistance
- 🔄 **Code Generation**: Generate functions, classes, and complete programs from descriptions
- 🧪 **Test Generation**: Automatically create comprehensive test suites
- 📚 **Documentation**: Generate professional documentation for your code
- 🎨 **Rich Terminal Output**: Beautiful syntax highlighting, tables, and formatting
- 💬 **Interactive Mode**: Conversational REPL with session management
- 🌈 **Themes**: Dark, light, and auto themes for different environments
- 📄 **Export**: Save results as Markdown, HTML, or copy to clipboard
- 🔍 **Context-Aware**: Intelligent project analysis and dependency tracking
- ⚡ **Streaming Responses**: Real-time AI responses with progress indicators

## 📋 Requirements

- **Python**: 3.8 or higher
- **Ollama**: Latest version ([installation guide](https://ollama.ai))
- **Operating System**: Linux or Windows with WSL

## 🚀 Quick Start

### Installation
```bash
# PyPI coming soon...
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
# Explain code
olla-cli explain "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"

# Review a file
olla-cli review myfile.py

# Generate code
olla-cli generate "binary search algorithm in Python"

# Interactive mode
olla-cli chat

# Get help
olla-cli --help
```

## 🛠️ Commands Overview

| Command | Description |
|---------|-------------|
| `explain` | Explain code functionality and logic |
| `review` | Review code for issues and improvements |
| `refactor` | Get intelligent refactoring suggestions |
| `debug` | Debug code issues with AI assistance |
| `generate` | Generate code from descriptions |
| `test` | Generate comprehensive test suites |
| `document` | Generate professional documentation |
| `chat` | Start interactive conversational mode |
| `config` | Manage configuration settings |
| `models` | Manage Ollama models |

## 🎯 Example Workflows

### Code Review
```bash
# Review with specific focus
olla-cli review --focus security auth.py

# Get refactoring suggestions
olla-cli refactor --type optimize slow_function.py
```

### Development
```bash
# Generate code structure
olla-cli generate --template class "user authentication manager"

# Create tests
olla-cli test --framework pytest auth_manager.py

# Generate docs
olla-cli document --format google auth_manager.py
```

## 🤝 Contributing

We welcome contributions!

### Quick Development Setup
```bash
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli
python -m venv venv
source venv/bin/activate
pip install -e .
```

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