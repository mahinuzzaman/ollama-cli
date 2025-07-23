# Configuration Guide

Complete guide to configuring and customizing Olla CLI.

## Configuration File

Olla CLI uses a YAML configuration file located at `~/.olla-cli/config.yaml`.

### Default Configuration

```yaml
# ~/.olla-cli/config.yaml

# Model settings
model: "codellama"
temperature: 0.7
context_length: 4096

# API settings
api_url: "http://localhost:11434"
timeout: 30

# Output formatting
output:
  theme: "dark"                 # dark, light, auto
  syntax_highlight: true        # Enable syntax highlighting
  show_line_numbers: true       # Show line numbers in code
  wrap_text: true              # Wrap long lines
  show_progress: true          # Show progress indicators
  enable_pager: true           # Use pager for long output
  max_width: null              # Terminal width (null = auto)
  streaming: true              # Enable streaming responses
  
  # Custom theme colors
  custom_colors:
    primary: "bright_cyan"
    secondary: "cyan"
    success: "bright_green"
    warning: "yellow"
    error: "bright_red"
    info: "blue"
    code: "white on black"
    comment: "dim"

# Interactive mode settings
interactive:
  auto_save: true              # Auto-save sessions
  max_history: 1000           # Maximum history entries
  default_session_name: "General"
  session_timeout: 3600       # Session timeout in seconds
  enable_autocomplete: true   # Enable command autocomplete
  
# Context management
context:
  max_files: 50               # Maximum files to analyze
  max_file_size: 1048576      # Maximum file size (1MB)
  ignore_patterns:            # Files to ignore
    - "*.pyc"
    - "*.pyo"
    - "__pycache__/"
    - ".git/"
    - ".svn/"
    - "node_modules/"
    - "venv/"
    - "env/"
    - ".pytest_cache/"
    - "*.log"
  include_hidden: false       # Include hidden files
  follow_symlinks: false      # Follow symbolic links

# Task management
tasks:
  auto_confirm: false         # Auto-confirm task steps
  save_history: true          # Save task history
  max_history: 100           # Maximum task history
  backup_files: true          # Backup files before modification
  
# Logging
logging:
  level: "INFO"               # DEBUG, INFO, WARNING, ERROR
  file: "~/.olla-cli/olla.log"
  max_size: 10485760         # 10MB
  backup_count: 5
```

## Configuration Management

### View Current Configuration

```bash
# Show all configuration
olla-cli config show

# Show specific section
olla-cli config show output

# Show specific value
olla-cli config show model
```

### Set Configuration Values

```bash
# Basic settings
olla-cli config set model mistral
olla-cli config set temperature 0.8
olla-cli config set context_length 2048

# Nested settings
olla-cli config set output.theme light
olla-cli config set output.syntax_highlight false
olla-cli config set interactive.auto_save true
olla-cli config set context.max_files 100

# API settings
olla-cli config set api_url http://localhost:11434
olla-cli config set timeout 60
```

### Reset Configuration

```bash
# Reset all settings to defaults
olla-cli config reset

# Reset specific section
olla-cli config reset output

# Reset specific value
olla-cli config reset temperature
```

## Environment Variables

Override configuration with environment variables:

```bash
# Model settings
export OLLA_MODEL=codellama
export OLLA_TEMPERATURE=0.8
export OLLA_CONTEXT_LENGTH=4096

# API settings
export OLLA_API_URL=http://localhost:11434
export OLLA_TIMEOUT=30

# Output settings
export OLLA_THEME=dark
export OLLA_NO_COLOR=true
export OLLA_STREAMING=false

# Interactive settings
export OLLA_AUTO_SAVE=true
export OLLA_MAX_HISTORY=2000
```

### Permanent Environment Variables

Add to your shell profile:

```bash
# ~/.bashrc or ~/.zshrc
export OLLA_MODEL=codellama
export OLLA_THEME=dark
export OLLA_TEMPERATURE=0.7
```

## Theme Configuration

### Built-in Themes

```yaml
output:
  theme: "dark"    # Dark theme with bright colors
  theme: "light"   # Light theme with muted colors
  theme: "auto"    # Auto-detect based on terminal
  theme: "custom"  # Use custom colors
```

### Custom Theme Colors

```yaml
output:
  theme: "custom"
  custom_colors:
    # Basic colors
    primary: "bright_cyan"      # Primary accent color
    secondary: "cyan"           # Secondary accent color
    success: "bright_green"     # Success messages
    warning: "yellow"           # Warning messages
    error: "bright_red"         # Error messages
    info: "blue"                # Info messages
    
    # Code highlighting
    code: "white on black"      # Code blocks
    keyword: "magenta"          # Programming keywords
    string: "green"             # String literals
    number: "cyan"              # Numbers
    comment: "dim"              # Comments
    
    # UI elements
    header: "bold bright_white" # Headers and titles
    border: "dim"               # Table borders
    prompt: "bright_yellow"     # Interactive prompts
```

### Available Colors

Rich color names supported:
- Basic: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- Bright: `bright_black`, `bright_red`, `bright_green`, etc.
- RGB: `rgb(255,0,0)` or `#ff0000`
- Styles: `bold`, `dim`, `italic`, `underline`
- Backgrounds: `on_black`, `on_red`, etc.

## Model Configuration

### Model Settings

```yaml
# Default model
model: "codellama"

# Model-specific settings
models:
  codellama:
    temperature: 0.7
    context_length: 4096
    system_prompt: "You are a helpful coding assistant."
    
  mistral:
    temperature: 0.8
    context_length: 8192
    system_prompt: "You are an expert programmer."
    
  llama2:
    temperature: 0.6
    context_length: 2048
```

### Model Management

```bash
# Set default model
olla-cli config set model deepseek-coder

# List available models
olla-cli models list

# Pull new models
ollama pull phi
olla-cli config set model phi
```

## Interactive Mode Configuration

### Session Settings

```yaml
interactive:
  # Auto-save sessions
  auto_save: true
  
  # Maximum history entries per session
  max_history: 1000
  
  # Default session name
  default_session_name: "General"
  
  # Session timeout (seconds)
  session_timeout: 3600
  
  # Enable command autocomplete
  enable_autocomplete: true
  
  # Show typing indicators
  show_typing: true
  
  # Auto-format code blocks
  auto_format_code: true
```

### Keybindings

```yaml
interactive:
  keybindings:
    # Navigation
    history_up: "ctrl+p"
    history_down: "ctrl+n"
    
    # Editing
    clear_line: "ctrl+u"
    delete_word: "ctrl+w"
    
    # Commands
    save_session: "ctrl+s"
    load_session: "ctrl+o"
    exit: "ctrl+d"
```

## Context Configuration

### File Discovery

```yaml
context:
  # Maximum number of files to analyze
  max_files: 50
  
  # Maximum file size (bytes)
  max_file_size: 1048576  # 1MB
  
  # Include hidden files/directories
  include_hidden: false
  
  # Follow symbolic links
  follow_symlinks: false
  
  # File patterns to ignore
  ignore_patterns:
    - "*.pyc"
    - "*.pyo"
    - "__pycache__/"
    - ".git/"
    - ".svn/"
    - ".hg/"
    - "node_modules/"
    - "venv/"
    - "env/"
    - ".pytest_cache/"
    - "*.log"
    - "*.tmp"
    - ".DS_Store"
    
  # File patterns to always include
  include_patterns:
    - "*.py"
    - "*.js"
    - "*.ts"
    - "*.java"
    - "*.cpp"
    - "*.c"
    - "*.h"
    - "*.md"
    - "*.txt"
```

### Language-Specific Settings

```yaml
context:
  languages:
    python:
      file_extensions: [".py", ".pyi"]
      ignore_patterns: ["__pycache__/", "*.pyc"]
      include_tests: true
      
    javascript:
      file_extensions: [".js", ".jsx", ".mjs"]
      ignore_patterns: ["node_modules/", "dist/"]
      include_tests: true
      
    typescript:
      file_extensions: [".ts", ".tsx"]
      ignore_patterns: ["node_modules/", "dist/", "*.d.ts"]
      include_tests: true
```

## Output Configuration

### Formatting Options

```yaml
output:
  # Syntax highlighting
  syntax_highlight: true
  
  # Show line numbers in code blocks
  show_line_numbers: true
  
  # Wrap long lines
  wrap_text: true
  
  # Show progress indicators
  show_progress: true
  
  # Use pager for long output
  enable_pager: true
  
  # Maximum terminal width (null = auto)
  max_width: null
  
  # Enable streaming responses
  streaming: true
  
  # Show response timing
  show_timing: false
```

### Export Settings

```yaml
output:
  export:
    # Default export format
    default_format: "markdown"
    
    # Include metadata in exports
    include_metadata: true
    
    # Timestamp exports
    timestamp: true
    
    # Export directory
    export_dir: "~/olla-exports"
```

## Task Configuration

### Task Execution

```yaml
tasks:
  # Auto-confirm task steps
  auto_confirm: false
  
  # Save task history
  save_history: true
  
  # Maximum task history entries
  max_history: 100
  
  # Backup files before modification
  backup_files: true
  
  # Backup directory
  backup_dir: "~/.olla-cli/backups"
  
  # Task timeout (seconds)
  timeout: 3600
```

### Task Templates

```yaml
tasks:
  templates:
    code_review:
      steps:
        - "Analyze code structure"
        - "Check for security issues"
        - "Review performance"
        - "Suggest improvements"
        
    refactor:
      steps:
        - "Identify refactoring opportunities"
        - "Create backup"
        - "Apply refactoring"
        - "Run tests"
        - "Verify functionality"
```

## Logging Configuration

### Log Settings

```yaml
logging:
  # Log level
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  
  # Log file location
  file: "~/.olla-cli/olla.log"
  
  # Maximum log file size (bytes)
  max_size: 10485760  # 10MB
  
  # Number of backup files
  backup_count: 5
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Date format
  date_format: "%Y-%m-%d %H:%M:%S"
```

### Enable Debug Logging

```bash
# Temporary debug logging
olla-cli --verbose explain code.py

# Permanent debug logging
olla-cli config set logging.level DEBUG
```

## Profile-Specific Configuration

### Multiple Profiles

Create profile-specific configs:

```bash
# Create profiles
mkdir -p ~/.olla-cli/profiles

# Work profile
cat > ~/.olla-cli/profiles/work.yaml << EOF
model: "codellama"
temperature: 0.6
output:
  theme: "light"
  syntax_highlight: true
EOF

# Personal profile
cat > ~/.olla-cli/profiles/personal.yaml << EOF
model: "mistral"
temperature: 0.8
output:
  theme: "dark"
  streaming: true
EOF
```

### Using Profiles

```bash
# Use specific profile
olla-cli --profile work explain code.py

# Set default profile
olla-cli config set default_profile work
```

## Validation and Troubleshooting

### Validate Configuration

```bash
# Validate configuration file
olla-cli config validate

# Check for issues
olla-cli config check
```

### Configuration Backup

```bash
# Backup configuration
cp ~/.olla-cli/config.yaml ~/.olla-cli/config.yaml.backup

# Restore configuration
cp ~/.olla-cli/config.yaml.backup ~/.olla-cli/config.yaml
```

### Reset to Defaults

```bash
# Reset everything
rm -rf ~/.olla-cli/
olla-cli config show  # Will recreate defaults

# Reset specific settings
olla-cli config reset output
olla-cli config reset interactive
```