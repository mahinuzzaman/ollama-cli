# 🚀 Quick Start Guide

Get up and running with Olla CLI in 5 minutes.

## 📦 Step 1: Install Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## 🎯 Step 2: Install Olla CLI

```bash
pip install olla-cli
```

## 🤖 Step 3: Download AI Model

```bash
# Start Ollama service
ollama serve &

# Download CodeLlama (recommended)
ollama pull codellama
```

## 🎉 Step 4: First Commands

```bash
# Explain code
olla-cli explain "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"

# Review a file
olla-cli review script.py

# Generate code
olla-cli generate "function to calculate fibonacci numbers"

# Interactive mode
olla-cli chat
```

## ⚙️ Step 5: Basic Configuration

```bash
# Set default model
olla-cli config set model codellama

# Set theme
olla-cli config set output.theme dark

# View settings
olla-cli config show
```

## 🔧 Common Issues

### "Command not found"
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "Connection refused"
```bash
# Start Ollama
ollama serve
```

### "Model not found"
```bash
# Pull model
ollama pull codellama
```

## 📚 Next Steps

- [API Reference](./api-reference.md) - All commands
- [Examples](./examples.md) - Usage patterns
- [Troubleshooting](./troubleshooting.md) - Common issues