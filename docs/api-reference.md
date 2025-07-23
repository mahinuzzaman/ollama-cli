# 📚 API Reference

Complete reference for all Olla CLI commands and options.

## 🌐 Global Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--model` | `-m` | Override default model | `--model mistral` |
| `--temperature` | `-t` | Set randomness (0.0-1.0) | `--temperature 0.8` |
| `--verbose` | `-v` | Enable verbose output | `--verbose` |
| `--theme` | | Set theme (dark/light/auto) | `--theme light` |
| `--no-color` | | Disable colored output | `--no-color` |
| `--help` | `-h` | Show help message | `--help` |

## 📖 Commands

### `explain` - Code Explanation

```bash
olla-cli explain [OPTIONS] [FILE_OR_CODE]
```

**Options:**
- `--stdin` - Read from stdin
- `--line-range` - Focus on specific lines (e.g., "10-20")
- `--detail-level` - brief/normal/comprehensive
- `--output-file` - Save to file

**Examples:**
```bash
olla-cli explain "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
olla-cli explain --line-range "10-25" script.py
olla-cli explain --detail-level comprehensive --output-file explanation.md algorithm.py
```

### `review` - Code Review

```bash
olla-cli review [OPTIONS] [FILE_OR_CODE]
```

**Options:**
- `--focus` - security/performance/style/bugs/all
- `--output-file` - Save review to file

**Examples:**
```bash
olla-cli review --focus security auth_module.py
olla-cli review --focus performance --output-file perf_review.md slow_function.py
```

### `refactor` - Code Refactoring

```bash
olla-cli refactor [OPTIONS] [FILE_OR_CODE]
```

**Options:**
- `--type` - simplify/optimize/modernize/general
- `--show-diff` - Show before/after comparison

**Examples:**
```bash
olla-cli refactor --type optimize --show-diff performance_critical.py
olla-cli refactor --type modernize old_python2_code.py
```

### `debug` - Debugging Assistant

```bash
olla-cli debug [OPTIONS] [FILE_OR_CODE]
```

**Options:**
- `--error` - Error message or type
- `--stack-trace` - Path to stack trace file
- `--line-range` - Focus on specific lines

**Examples:**
```bash
olla-cli debug --error "IndexError: list index out of range" buggy_script.py
olla-cli debug --stack-trace error.log problematic_code.py
```

### `generate` - Code Generation

```bash
olla-cli generate [OPTIONS] DESCRIPTION
```

**Options:**
- `--language` - Target language (python, javascript, etc.)
- `--framework` - Specific framework
- `--template` - function/class/api_endpoint
- `--output-file` - Save to file

**Examples:**
```bash
olla-cli generate "function to calculate fibonacci numbers"
olla-cli generate --language javascript --framework react "todo list component"
olla-cli generate --template class "binary search tree data structure"
```

### `test` - Test Generation

```bash
olla-cli test [OPTIONS] [FILE_OR_CODE]
```

**Options:**
- `--framework` - pytest/unittest/jest/mocha
- `--type` - unit/integration/e2e
- `--coverage` - Include coverage analysis
- `--output-file` - Save tests to file

**Examples:**
```bash
olla-cli test calculator.py
olla-cli test --framework jest --coverage math_utils.js
olla-cli test --type integration --output-file test_integration.py api_client.py
```

### `document` - Documentation Generation

```bash
olla-cli document [OPTIONS] [FILE_OR_CODE]
```

**Options:**
- `--format` - google/numpy/sphinx
- `--type` - api/user/project
- `--output-file` - Save to file

**Examples:**
```bash
olla-cli document api_module.py
olla-cli document --type user --format sphinx tutorial_code.py
```

### `chat` - Interactive Mode

```bash
olla-cli chat [OPTIONS]
```

**Options:**
- `--session` - Load specific session
- `--new-session` - Force create new session

**Interactive Commands:**
- `/help` - Show commands
- `/clear` - Clear history
- `/save [name]` - Save session
- `/load <id>` - Load session
- `/exit` - Exit chat

### `config` - Configuration

```bash
olla-cli config COMMAND [OPTIONS]
```

**Subcommands:**
- `show [SECTION]` - Display configuration
- `set KEY VALUE` - Set configuration value
- `reset [SECTION]` - Reset configuration

**Examples:**
```bash
olla-cli config show
olla-cli config set model mistral
olla-cli config set output.theme light
olla-cli config reset
```

### `models` - Model Management

```bash
olla-cli models COMMAND [OPTIONS]
```

**Subcommands:**
- `list` - List available models
- `info MODEL_NAME` - Show model information
- `pull MODEL_NAME` - Download model

**Examples:**
```bash
olla-cli models list
olla-cli models info codellama
olla-cli models pull mistral
```

### `task` - Task Management

```bash
olla-cli task [OPTIONS] DESCRIPTION
```

**Options:**
- `--dry-run` - Show what would be done
- `--auto-confirm` - Auto-confirm all steps

**Examples:**
```bash
olla-cli task "refactor this Python file to use type hints"
olla-cli task --dry-run "optimize database queries"
```

## 🌍 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OLLA_MODEL` | Default model | `export OLLA_MODEL=mistral` |
| `OLLA_TEMPERATURE` | Default temperature | `export OLLA_TEMPERATURE=0.8` |
| `OLLA_API_URL` | Ollama API URL | `export OLLA_API_URL=http://localhost:11434` |
| `OLLA_THEME` | Output theme | `export OLLA_THEME=light` |
| `OLLA_NO_COLOR` | Disable colors | `export OLLA_NO_COLOR=1` |

## 📝 Configuration File

Configuration is stored at `~/.olla-cli/config.yaml`:

```yaml
model: "codellama"
temperature: 0.7
context_length: 4096
api_url: "http://localhost:11434"

output:
  theme: "dark"
  syntax_highlight: true
  streaming: true

interactive:
  auto_save: true
  max_history: 1000
```

## 🔧 Return Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Configuration error |
| 4 | Connection error |
| 5 | Model not found |