# Usage Guide

Complete guide to using Olla CLI commands and features.

## Basic Command Structure

```bash
olla-cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

### Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `-m, --model` | Override model | `--model mistral` |
| `-t, --temperature` | Set temperature (0.0-1.0) | `--temperature 0.8` |
| `-c, --context-length` | Set context length | `--context-length 2048` |
| `-v, --verbose` | Enable verbose output | `--verbose` |
| `--theme` | Set theme (dark/light/auto) | `--theme light` |
| `--no-color` | Disable colors | `--no-color` |

## Code Analysis Commands

### `explain` - Code Explanation

Explain code functionality and logic.

```bash
# Basic usage
olla-cli explain "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"

# From file
olla-cli explain script.py

# With specific options
olla-cli explain --detail-level comprehensive \
                 --line-range "10-20" \
                 --output-file explanation.md \
                 complex_algorithm.py

# From stdin
echo "lambda x: x**2" | olla-cli explain --stdin
```

**Options:**
- `--detail-level`: `brief`, `normal`, `comprehensive`
- `--line-range`: Specific lines (e.g., "10-20")
- `--output-file`: Save to file
- `--stdin`: Read from stdin
- `--stream`: Real-time streaming (default)

### `review` - Code Review

Review code for issues and improvements.

```bash
# Basic review
olla-cli review application.py

# Security-focused review
olla-cli review --focus security auth_module.py

# Performance review with output
olla-cli review --focus performance \
                --output-file performance_review.md \
                slow_function.py

# Comprehensive review
olla-cli review --focus all --detail-level comprehensive codebase.py
```

**Options:**
- `--focus`: `security`, `performance`, `style`, `bugs`, `all`
- `--detail-level`: `brief`, `normal`, `comprehensive`
- `--output-file`: Save results to file

### `refactor` - Code Refactoring

Get intelligent refactoring suggestions.

```bash
# General refactoring
olla-cli refactor legacy_code.py

# Specific refactoring type
olla-cli refactor --type optimize performance_critical.py
olla-cli refactor --type modernize old_code.py
olla-cli refactor --type simplify complex_function.py

# Show before/after diff
olla-cli refactor --show-diff messy_code.py
```

**Options:**
- `--type`: `simplify`, `optimize`, `modernize`, `general`
- `--show-diff`: Show before/after comparison
- `--output-file`: Save suggestions

### `debug` - Debugging Assistant

Get help debugging code issues.

```bash
# Debug with error message
olla-cli debug --error "IndexError: list index out of range" buggy_script.py

# Debug with stack trace
olla-cli debug --stack-trace error_trace.txt problematic_code.py

# Interactive debugging
olla-cli debug --interactive broken_app.py

# Focus on specific lines
olla-cli debug --line-range "45-60" --error "ValueError" script.py
```

**Options:**
- `--error`: Error message or type
- `--stack-trace`: Path to stack trace file
- `--line-range`: Focus on specific lines
- `--interactive`: Interactive debugging mode

## Code Generation Commands

### `generate` - Code Generation

Generate code from natural language descriptions.

```bash
# Basic generation
olla-cli generate "function to calculate prime numbers"

# With specific language
olla-cli generate --language python "REST API for user authentication"

# Using templates
olla-cli generate --template class "binary search tree implementation"
olla-cli generate --template function "email validation with regex"

# Framework-specific
olla-cli generate --framework flask "user registration endpoint"
olla-cli generate --framework react "todo list component with hooks"
```

**Options:**
- `--language`: Target programming language
- `--framework`: Specific framework (`flask`, `django`, `react`, `vue`, etc.)
- `--template`: Code template (`function`, `class`, `api_endpoint`)
- `--output-file`: Save generated code

### `test` - Test Generation

Generate comprehensive tests for your code.

```bash
# Generate tests for a function
olla-cli test "def add_numbers(a, b): return a + b"

# Test file with specific framework
olla-cli test --framework pytest calculator.py

# Include coverage analysis
olla-cli test --coverage --output-file test_suite.py math_utils.py

# Generate different test types
olla-cli test --type unit core_functions.py
olla-cli test --type integration api_client.py
olla-cli test --type e2e user_workflow.py
```

**Options:**
- `--framework`: Test framework (`pytest`, `unittest`, `jest`, etc.)
- `--coverage`: Include coverage analysis
- `--type`: Test type (`unit`, `integration`, `e2e`)
- `--output-file`: Save tests to file

### `document` - Documentation Generation

Generate professional documentation.

```bash
# Basic documentation
olla-cli document api_module.py

# Specific format
olla-cli document --format google auth_service.py
olla-cli document --format sphinx complex_library.py

# API documentation
olla-cli document --type api --output-file api_docs.md server.py

# Project documentation
olla-cli document --type project --format markdown src/
```

**Options:**
- `--format`: Documentation format (`google`, `numpy`, `sphinx`)
- `--type`: Documentation type (`api`, `user`, `project`)
- `--output-file`: Save documentation

## Interactive Commands

### `chat` - Interactive Mode

Start conversational REPL with session management.

```bash
# Start interactive mode
olla-cli chat

# Load specific session
olla-cli chat --session my-project

# Force new session
olla-cli chat --new-session
```

#### Interactive Commands

Once in chat mode, use these commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/save [name]` | Save current session |
| `/load <id>` | Load session by ID |
| `/sessions` | List all sessions |
| `/context` | Show current context |
| `/stats` | Session statistics |
| `/model <name>` | Change model |
| `/temperature <value>` | Set temperature |
| `/history [limit]` | Show recent messages |
| `/search <query>` | Search sessions |
| `/exit` | Exit interactive mode |

## Configuration Commands

### `config` - Configuration Management

Manage Olla CLI settings.

```bash
# Show current configuration
olla-cli config show

# Set configuration values
olla-cli config set model codellama
olla-cli config set temperature 0.7
olla-cli config set output.theme dark
olla-cli config set interactive.auto_save true

# Reset to defaults
olla-cli config reset
```

## Model Management Commands

### `models` - Model Management

Manage Ollama models.

```bash
# List available models
olla-cli models list

# Show model information
olla-cli models info codellama

# Pull new model
olla-cli models pull mistral
```

## Task Management Commands

### `task` - Complex Task Execution

Execute complex tasks with AI assistance and step-by-step progress.

```bash
# Execute task
olla-cli task "refactor this Python file to use type hints"

# Dry run (show what would be done)
olla-cli task --dry-run "optimize database queries in the application"

# Auto-confirm all steps
olla-cli task --auto-confirm "add error handling to all API endpoints"

# Specify context directory
olla-cli task --context-path ./src "implement user authentication system"

# Save execution log
olla-cli task --output-file task_log.md "migrate from Python 2 to 3"
```

**Options:**
- `--dry-run`: Show what would be done without making changes
- `--auto-confirm`: Automatically confirm all steps
- `--context-path`: Specify working directory context
- `--output-file`: Save task execution log

### `resume` - Resume Tasks

Resume previously paused tasks.

```bash
# Resume task by ID
olla-cli resume task-123-abc

# Auto-confirm remaining steps
olla-cli resume --auto-confirm task-123-abc
```

### `tasks` - Task History

Manage task history and execution.

```bash
# List recent tasks
olla-cli tasks list

# List with filters
olla-cli tasks list --limit 10 --status completed
olla-cli tasks list --type fix_bug --days 7

# Show task details
olla-cli tasks show task-123-abc

# Search tasks
olla-cli tasks search "authentication"

# Show statistics
olla-cli tasks stats
```

## Context Management Commands

### `context` - Project Analysis

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

## Output Options

### Themes

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

### Export Options

```bash
# Save to Markdown
olla-cli explain --output-file explanation.md algorithm.py

# Export to HTML (if supported)
olla-cli review --format html --output-file report.html codebase/

# Copy to clipboard
olla-cli explain "lambda x: x**2" | pbcopy  # macOS
olla-cli explain "lambda x: x**2" | xclip   # Linux
```

## Advanced Usage

### Piping and Chaining

```bash
# Chain commands
olla-cli explain script.py | tee explanation.txt

# From stdin
cat script.py | olla-cli review --stdin

# Multiple files
find . -name "*.py" -exec olla-cli review {} \;
```

### Environment Variables

```bash
# Set environment variables
export OLLA_MODEL=mistral
export OLLA_TEMPERATURE=0.8
export OLLA_THEME=light

# Use in commands
olla-cli explain code.py  # Uses env variables
```

### Batch Operations

```bash
# Review multiple files
for file in src/*.py; do
    olla-cli review --output-file "reviews/$(basename $file .py)_review.md" "$file"
done

# Generate tests for all modules
find src/ -name "*.py" -exec olla-cli test --output-file "tests/test_{}.py" {} \;
```

## Getting Help

```bash
# General help
olla-cli --help

# Command-specific help
olla-cli explain --help
olla-cli chat --help
olla-cli task --help

# Version information
olla-cli version
```