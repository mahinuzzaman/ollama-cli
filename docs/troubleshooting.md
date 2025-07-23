# 🔧 Troubleshooting Guide

Common issues and solutions for Olla CLI.

## 🚨 Connection Issues

### "Connection refused" Error
```bash
# Check if Ollama is running
ollama ps

# Start Ollama if not running
ollama serve

# Test connection
curl http://localhost:11434/api/tags

# Check custom API URL
olla-cli config show api_url
```

## 🤖 Model Issues

### "Model not found" Error
```bash
# List available models
ollama list
olla-cli models list

# Pull missing model
ollama pull codellama

# Check model name spelling
ollama pull mistral  # Common alternatives
```

### Slow Performance
```bash
# Use lighter model
olla-cli config set model mistral

# Reduce context length
olla-cli config set context_length 2048

# Lower temperature
olla-cli config set temperature 0.3
```

## 📦 Installation Issues

### Package Not Found
```bash
# Update pip
python -m pip install --upgrade pip

# Check Python version (requires 3.8+)
python --version

# Try user installation
pip install --user olla-cli

# Install from source
git clone https://github.com/mahinuzzaman/ollama-cli.git
cd ollama-cli
pip install -e .
```

### "Command not found"
```bash
# Check PATH
echo $PATH
which olla-cli

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Use python module directly
python -m olla_cli --help
```

## ⚙️ Configuration Issues

### Invalid Configuration
```bash
# Check configuration
olla-cli config show

# Reset to defaults
olla-cli config reset

# Fix file permissions
chmod 644 ~/.olla-cli/config.yaml
```

## 🎨 Output Issues

### No Colors/Formatting
```bash
# Enable syntax highlighting
olla-cli config set output.syntax_highlight true

# Check terminal support
echo $TERM

# Force color output
olla-cli explain --no-color script.py
```

## 🐛 Debug Mode

### Enable Verbose Logging
```bash
# Verbose output
olla-cli --verbose explain script.py

# Debug logging
olla-cli config set logging.level DEBUG

# Check log file
tail -f ~/.olla-cli/olla.log
```

### System Check Commands
```bash
# Check versions
olla-cli version
python --version
ollama --version

# Test basic functionality
olla-cli explain "print('test')"

# Check Ollama connection
curl http://localhost:11434/api/tags
```

## 🆘 Getting Help

### Include This Information When Reporting Issues:
```bash
# System information
olla-cli version
python --version
ollama --version
uname -a

# Configuration
olla-cli config show

# Error reproduction
olla-cli --verbose [your-command-here]
```

### Where to Get Help:
- [GitHub Issues](https://github.com/mahinuzzaman/ollama-cli/issues) - Bug reports
- [GitHub Discussions](https://github.com/mahinuzzaman/ollama-cli/discussions) - Questions
- Built-in help: `olla-cli --help`

## 🔄 Recovery

### Complete Reset
```bash
# Uninstall and reinstall
pip uninstall olla-cli
rm -rf ~/.olla-cli/
pip install olla-cli

# Verify installation
olla-cli version
```