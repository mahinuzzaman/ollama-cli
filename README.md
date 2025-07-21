# 🚀 Olla CLI

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
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-green.svg)](https://ollama.ai)

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
- **Operating System**: Linux, macOS, or Windows with WSL

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

### Method 3: Using Poetry
```bash
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli
poetry install
```

## 🛠️ Setup

1. **Install Ollama** (if not already installed):
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows (PowerShell)
   iex (irm ollama.ai/install.ps1)
   ```

2. **Pull a supported model**:
   ```bash
   ollama pull codellama      # Recommended for coding
   ollama pull llama2         # Alternative option
   ollama pull mistral        # Lightweight option
   ```

3. **Verify installation**:
   ```bash
   olla-cli version
   olla-cli models list
   ```

## ⚡ Quick Start

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
```

### With Options
```bash
# Use different theme
olla-cli --theme light explain code.py

# Use specific model
olla-cli --model mistral review --focus security app.py

# Export results
olla-cli explain --output-file explanation.md "complex code here"
```

## 📖 Commands Reference

### 🔍 `explain` - Code Explanation
Explain code functionality and logic with AI intelligence.

```bash
# Basic usage
olla-cli explain "print('Hello, World!')"

# From file
olla-cli explain myfile.py

# With options
olla-cli explain --detail-level comprehensive \
                 --line-range "10-20" \
                 --output-file explanation.md \
                 code.py

# From stdin
echo "lambda x: x**2" | olla-cli explain --stdin
```

**Options:**
- `--detail-level`: `brief`, `normal`, `comprehensive`
- `--line-range`: Specific lines (e.g., "10-20")
- `--output-file`: Save to file
- `--stdin`: Read from stdin
- `--stream`: Real-time streaming (default: true)

### 🔎 `review` - Code Review
Review code for issues and improvements with AI expertise.

```bash
# Basic review
olla-cli review app.py

# Security-focused review
olla-cli review --focus security --detail-level comprehensive auth.py

# Performance review
olla-cli review --focus performance --output-file review.md slow_function.py

# Review multiple areas
olla-cli review --focus all database.py
```

**Options:**
- `--focus`: `security`, `performance`, `style`, `bugs`, `all`
- `--detail-level`: `brief`, `normal`, `comprehensive`
- `--output-file`: Save results to file

### 🔧 `refactor` - Code Refactoring
Get intelligent refactoring suggestions.

```bash
# General refactoring
olla-cli refactor legacy_code.py

# Specific refactoring type
olla-cli refactor --type optimize slow_algorithm.py
olla-cli refactor --type modernize old_python2_code.py
olla-cli refactor --type simplify complex_function.py

# With before/after diff
olla-cli refactor --show-diff messy_code.py
```

**Options:**
- `--type`: `simplify`, `optimize`, `modernize`, `general`
- `--show-diff`: Show before/after comparison
- `--output-file`: Save suggestions

### 🐛 `debug` - Debugging Assistant
Get help debugging code issues and errors.

```bash
# Debug with error message
olla-cli debug --error "IndexError: list index out of range" buggy_code.py

# Debug with stack trace
olla-cli debug --stack-trace trace.txt problematic_function.py

# Interactive debugging
olla-cli debug --interactive broken_script.py

# Debug specific lines
olla-cli debug --line-range "45-60" --error "ValueError" script.py
```

**Options:**
- `--error`: Error message or type
- `--stack-trace`: Path to stack trace file
- `--line-range`: Focus on specific lines
- `--interactive`: Interactive debugging mode

### 🎯 `generate` - Code Generation
Generate code from natural language descriptions.

```bash
# Basic generation
olla-cli generate "fibonacci sequence function"

# With specific language
olla-cli generate --language python "REST API endpoint for user authentication"

# Using templates
olla-cli generate --template class "data structure for binary tree"
olla-cli generate --template function "validate email address"

# Framework-specific
olla-cli generate --framework flask "user registration endpoint"
olla-cli generate --framework react "todo list component"
```

**Options:**
- `--language`: Target programming language
- `--framework`: Specific framework (`flask`, `django`, `react`, `vue`, etc.)
- `--template`: Code template (`function`, `class`, `api_endpoint`)
- `--output-file`: Save generated code

### 🧪 `test` - Test Generation
Generate comprehensive tests for your code.

```bash
# Generate tests for a function
olla-cli test "def add(a, b): return a + b"

# Test file with specific framework
olla-cli test --framework pytest calculator.py

# Include coverage analysis
olla-cli test --coverage --output-file test_calculator.py math_utils.py

# Generate integration tests
olla-cli test --type integration api_client.py
```

**Options:**
- `--framework`: Test framework (`pytest`, `unittest`, `jest`, etc.)
- `--coverage`: Include coverage analysis
- `--type`: Test type (`unit`, `integration`, `e2e`)
- `--output-file`: Save tests to file

### 📚 `document` - Documentation Generation
Generate professional documentation.

```bash
# Basic documentation
olla-cli document utils.py

# Specific format
olla-cli document --format google api_client.py
olla-cli document --format sphinx complex_module.py

# API documentation
olla-cli document --type api --output-file api_docs.md server.py

# Full project documentation
olla-cli document --type project --format markdown src/
```

**Options:**
- `--format`: Documentation format (`google`, `numpy`, `sphinx`)
- `--type`: Documentation type (`api`, `user`, `project`)
- `--output-file`: Save documentation

### 💬 `chat` - Interactive Mode
Start conversational REPL with session management.

```bash
# Start interactive mode
olla-cli chat

# Load specific session
olla-cli chat --session my-project

# Force new session
olla-cli chat --new-session
```

**Interactive Commands:**
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/save [name]` - Save current session
- `/load <id>` - Load session by ID
- `/sessions` - List all sessions
- `/context` - Show current context
- `/stats` - Session statistics
- `/model <name>` - Change model
- `/temperature <value>` - Set temperature
- `/history [limit]` - Show recent messages
- `/search <query>` - Search sessions
- `/exit` - Exit interactive mode

### 🔧 `config` - Configuration Management
Manage olla-cli settings.

```bash
# Show current configuration
olla-cli config show

# Set configuration values
olla-cli config set model mistral
olla-cli config set temperature 0.8
olla-cli config set output.theme light

# Reset to defaults
olla-cli config reset
```

### 🤖 `models` - Model Management
Manage Ollama models.

```bash
# List available models
olla-cli models list

# Show model information
olla-cli models info codellama

# Pull new model
olla-cli models pull llama2
```

### 📊 `context` - Project Analysis
Analyze project structure and context.

```bash
# Show project summary
olla-cli context summary

# Show project tree
olla-cli context tree --depth 3

# Analyze dependencies
olla-cli context deps myfile.py

# Show file relationships
olla-cli context graph
```

## ⚙️ Configuration

Olla CLI uses a YAML configuration file located at `~/.olla-cli/config.yaml`.

### Example Configuration

```yaml
# ~/.olla-cli/config.yaml

# Model settings
model: "codellama"
temperature: 0.7
context_length: 4096

# API settings
api_url: "http://localhost:11434"

# Output formatting
output:
  theme: "dark"                 # dark, light, auto
  syntax_highlight: true        # Enable syntax highlighting
  show_line_numbers: true       # Show line numbers in code
  wrap_text: true              # Wrap long lines
  show_progress: true          # Show progress indicators
  enable_pager: true           # Use pager for long output
  max_width: null              # Terminal width (null = auto)
  custom_colors:               # Custom theme colors
    primary: "bright_cyan"
    success: "bright_green"
    error: "bright_red"

# Interactive mode settings
interactive:
  auto_save: true              # Auto-save sessions
  max_history: 1000           # Maximum history entries
  default_session_name: "General"

# Context management
context:
  max_files: 50               # Maximum files to analyze
  ignore_patterns:            # Files to ignore
    - "*.pyc"
    - "__pycache__/"
    - ".git/"
    - "node_modules/"
  include_hidden: false       # Include hidden files
```

### Environment Variables

You can also configure olla-cli using environment variables:

```bash
export OLLA_MODEL=codellama
export OLLA_TEMPERATURE=0.8
export OLLA_API_URL=http://localhost:11434
export OLLA_THEME=dark
```

## 🔄 Common Workflows

### 1. Code Review Workflow
```bash
# Step 1: Review entire file
olla-cli review --focus all --detail-level comprehensive src/app.py

# Step 2: Focus on security issues
olla-cli review --focus security --output-file security_review.md src/auth.py

# Step 3: Get refactoring suggestions
olla-cli refactor --type optimize src/slow_module.py

# Step 4: Generate tests for fixed code
olla-cli test --framework pytest --coverage src/app.py
```

### 2. New Feature Development
```bash
# Step 1: Generate initial code structure
olla-cli generate --template class "user authentication manager"

# Step 2: Explain complex parts
olla-cli explain --detail-level comprehensive auth_manager.py

# Step 3: Generate comprehensive tests
olla-cli test --framework pytest --type unit auth_manager.py

# Step 4: Create documentation
olla-cli document --format google --type api auth_manager.py
```

### 3. Debugging Session
```bash
# Step 1: Start interactive debugging
olla-cli chat --session debugging

# In interactive mode:
# > explain this error: AttributeError: 'NoneType' object has no attribute 'get'
# > /context  # Show current context
# > debug --error "AttributeError" --line-range "25-35" problematic.py

# Step 2: Get specific debugging help
olla-cli debug --error "AttributeError" --stack-trace error.log buggy_script.py

# Step 3: Verify fix with tests
olla-cli test --framework pytest fixed_script.py
```

### 4. Learning and Exploration
```bash
# Step 1: Start learning session
olla-cli chat --session learning-python

# Interactive exploration:
# > explain how decorators work in Python
# > generate example of decorator with parameters  
# > show me best practices for error handling
# > /save "Python Learning Session"

# Step 2: Generate practice exercises
olla-cli generate "create 5 Python exercises for beginners with solutions"

# Step 3: Export learning materials
olla-cli document --type user --output-file python_notes.md
```

## 🎨 Themes and Customization

### Available Themes

```bash
# Dark theme (default)
olla-cli --theme dark explain code.py

# Light theme  
olla-cli --theme light review app.py

# Auto-detect theme
olla-cli --theme auto generate "function"

# Disable colors
olla-cli --no-color explain script.py
```

### Custom Colors

Add custom colors to your config file:

```yaml
output:
  theme: "custom"
  custom_colors:
    primary: "bright_magenta"
    secondary: "cyan"
    success: "green"
    warning: "yellow"
    error: "red"
    info: "blue"
    code: "white on black"
```

## 📤 Export Options

### Markdown Export
```bash
# Export explanation as Markdown
olla-cli explain --output-file explanation.md complex_algorithm.py

# Export with custom title
olla-cli review --output-file "Security Review.md" auth_system.py
```

### HTML Export
```bash
# Generate HTML report
olla-cli review --format html --output-file report.html codebase/

# Beautiful HTML with syntax highlighting
olla-cli document --format html --output-file docs.html src/
```

### Clipboard Integration
```bash
# Copy result to clipboard
olla-cli explain "lambda x: x**2" | pbcopy  # macOS
olla-cli explain "lambda x: x**2" | xclip   # Linux

# Or use built-in export
olla-cli explain --export clipboard "code here"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Connection refused" Error
```bash
# Check if Ollama is running
ollama ps

# Start Ollama service
ollama serve

# Check connection
curl http://localhost:11434/api/tags
```

#### 2. Model Not Found
```bash
# List available models
ollama list

# Pull required model
ollama pull codellama

# Update olla-cli model setting
olla-cli config set model codellama
```

#### 3. Slow Performance
```bash
# Use lighter model
olla-cli config set model mistral

# Reduce context length
olla-cli config set context_length 2048

# Disable some features
olla-cli config set output.syntax_highlight false
```

#### 4. Permission Issues
```bash
# Check file permissions
ls -la ~/.olla-cli/

# Fix permissions
chmod 755 ~/.olla-cli/
chmod 644 ~/.olla-cli/config.yaml
```

#### 5. Installation Issues
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Reinstall with verbose output
pip install -v olla-cli

# Install with specific Python version
python3.9 -m pip install olla-cli
```

### Debug Mode
```bash
# Enable verbose logging
olla-cli --verbose explain code.py

# Check configuration
olla-cli config show

# Test connection
olla-cli models list
```

### Getting Help

#### 1. Built-in Help
```bash
# General help
olla-cli --help

# Command-specific help  
olla-cli explain --help
olla-cli chat --help

# Interactive help
olla-cli chat
# Then use: /help
```

#### 2. Check Status
```bash
# Version information
olla-cli version

# Model information
olla-cli models info codellama

# System status
olla-cli context summary
```

#### 3. Reset Configuration
```bash
# Reset to defaults
olla-cli config reset

# Remove all data
rm -rf ~/.olla-cli/
olla-cli config show  # Will recreate defaults
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 src/
black src/
```

### Report Issues
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/mahinuzzaman/ollama-cli/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/mahinuzzaman/ollama-cli/discussions)
- 📖 **Documentation**: Help improve our docs!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for the amazing local LLM platform
- [Rich](https://github.com/Textualize/rich) for beautiful terminal formatting
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for interactive features

## 🌟 Star History

If you find Olla CLI useful, please consider giving it a star on GitHub! ⭐

---

<div align="center">

**Made with ❤️ by developers, for developers**

[⬆️ Back to Top](#-olla-cli) | [📖 Documentation](https://github.com/mahinuzzaman/ollama-cli/wiki) | [🚀 Releases](https://github.com/mahinuzzaman/ollama-cli/releases)

</div>