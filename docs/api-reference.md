# 📚 API Reference

Complete reference for Olla CLI commands and options.

## 🌐 Global Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--model` | `-m` | Override default model | `--model deepseek-coder:33b` |
| `--temperature` | `-t` | Set randomness (0.0-1.0) | `--temperature 0.3` |
| `--context-length` | `-c` | Override context length | `--context-length 8192` |
| `--verbose` | `-v` | Enable verbose output | `--verbose` |
| `--theme` | | Set theme (dark/light/auto) | `--theme light` |
| `--no-color` | | Disable colored output | `--no-color` |
| `--help` | `-h` | Show help message | `--help` |

## 📖 Commands

### Main Command (Interactive Mode)

```bash
olla-cli [OPTIONS]
```

**Default Behavior:** Starts interactive mode immediately

**Options:** All global options apply

**Examples:**
```bash
olla-cli                              # Start interactive mode
olla-cli --model codellama            # Use specific model
olla-cli --verbose                    # Show debug information
olla-cli --theme light --no-color     # Customize appearance
```

### `config` - Configuration Management

```bash
olla-cli config COMMAND [OPTIONS]
```

**Subcommands:**
- `show [SECTION]` - Display configuration
- `set KEY VALUE` - Set configuration value
- `reset [SECTION]` - Reset configuration to defaults

**Examples:**
```bash
olla-cli config show                  # Show all settings
olla-cli config show output           # Show output settings only
olla-cli config set model codellama   # Set default model
olla-cli config set output.theme dark # Set theme
olla-cli config set temperature 0.5   # Set temperature
olla-cli config reset                 # Reset all to defaults
```

**Configuration Keys:**
- `model` - Default AI model name
- `temperature` - Response randomness (0.0-1.0)
- `context_length` - Maximum context window size
- `api_url` - Ollama server URL
- `output.theme` - Display theme (dark/light/auto)
- `output.syntax_highlight` - Enable syntax highlighting
- `output.show_progress` - Show progress indicators

### `version` - Version Information

```bash
olla-cli version
```

Shows the current version of Olla CLI.

## 🎯 Interactive Mode Commands

Once in interactive mode, you can use natural language requests:

### Code Generation
```bash
You: create a hello world function
You: build a React todo app
You: generate a Python calculator with basic operations
You: make a REST API for user management
```

### Code Analysis
```bash
You: explain this code: [paste code here]
You: review my authentication function for security issues
You: check this file for bugs: filename.py
You: suggest improvements to my sorting algorithm
```

### File Operations
```bash
You: read the config file
You: save this code to calculator.py
You: create a new component called UserCard
You: show me the contents of main.py
```

### Complex Tasks
```bash
You: create a complete web app with authentication
You: build a project structure for a Python CLI tool
You: generate unit tests for all my functions
You: create documentation for my API endpoints
```

### Session Control
```bash
You: exit                    # Exit interactive mode
```

Or use `Ctrl+C` to interrupt at any time.

## 🌍 Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OLLA_MODEL` | Default model | `deepseek-coder:33b` | `export OLLA_MODEL=codellama` |
| `OLLA_TEMPERATURE` | Default temperature | `0.7` | `export OLLA_TEMPERATURE=0.5` |
| `OLLA_API_URL` | Ollama API URL | `http://localhost:11434` | `export OLLA_API_URL=http://server:11434` |
| `OLLA_THEME` | Output theme | `dark` | `export OLLA_THEME=light` |
| `OLLA_NO_COLOR` | Disable colors | `false` | `export OLLA_NO_COLOR=1` |

## 📝 Configuration File

Configuration is stored at `~/.olla-cli/config.yaml`:

```yaml
model: "deepseek-coder:33b"
temperature: 0.7
context_length: 4096
api_url: "http://localhost:11434"

output:
  theme: "dark"
  syntax_highlight: true
  show_line_numbers: true
  wrap_text: true
  show_progress: true
  enable_pager: true
  max_width: null
  custom_colors: {}
```

## 🧠 Intelligent Processing

Olla CLI uses advanced natural language processing:

### Intent Classification
Automatically identifies what you want to do:
- **Code Generation** - Creating new code
- **Code Analysis** - Explaining or reviewing code
- **File Operations** - Reading, writing, managing files
- **Complex Tasks** - Multi-step operations

### Task Planning
Breaks down complex requests:
1. **Single Step** - Simple operations
2. **Multi Step** - Complex tasks requiring multiple actions
3. **Parallel** - Independent operations run simultaneously
4. **Sequential** - Dependent operations run in order

### Tool Orchestration
Automatically selects and uses appropriate tools:
- **Code Analysis** - For understanding and reviewing code
- **File System** - For reading and writing files
- **Web Tools** - For fetching external resources (future)

### Context Management
Maintains conversation context:
- **Session Memory** - Remembers what was discussed
- **File Awareness** - Tracks created and modified files
- **Project Context** - Understands project structure

## 🔧 Return Codes

| Code | Description | Meaning |
|------|-------------|---------|
| 0 | Success | Operation completed successfully |
| 1 | General error | Unexpected error occurred |
| 2 | Invalid arguments | Command line arguments invalid |
| 3 | Configuration error | Config file or settings issue |
| 4 | Connection error | Cannot connect to Ollama server |
| 5 | Model not found | Requested AI model not available |

## 🎛️ Advanced Usage

### Model Selection Priority
1. Command line `--model` option
2. Environment variable `OLLA_MODEL`
3. Configuration file setting
4. Default: `deepseek-coder:33b`

### Temperature Settings
- **0.0-0.3**: Very deterministic, good for code generation
- **0.4-0.7**: Balanced creativity and consistency
- **0.8-1.0**: More creative, less predictable

### Context Length
- **4096**: Standard, good for most tasks
- **8192**: Extended context for larger code files
- **16384**: Maximum context for complex projects

### Debug Mode
Use `--verbose` to see:
- Intent classification results
- Execution plan details
- Tool selection process
- File operation logs
- Error details and stack traces

## 🔍 Troubleshooting Commands

```bash
# Check configuration
olla-cli config show

# Test with verbose output
olla-cli --verbose

# Check version
olla-cli version

# Reset configuration
olla-cli config reset

# Get help
olla-cli --help
```