# 🚀 Quick Start Guide

Get up and running with Olla CLI in 2 minutes.

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

# Download CodeLlama (recommended for coding)
ollama pull codellama
```

## 🎉 Step 4: Start Interactive Session

```bash
# Just run olla-cli - that's it!
olla-cli
```

You'll see:
```
🤖 Interactive Intelligent Assistant
Type your requests in natural language. Type 'exit' to quit.

You: 
```

## 💬 Step 5: Start Talking!

Now just describe what you want in natural language:

```bash
You: create a hello world function
🤖 Assistant:
  def hello_world():
      print("Hello, World!")
  File written: hello_world.py

You: create a todo react app
🤖 Assistant:
  import React, { useState } from 'react';
  // ... complete React component ...
  File written: TodoApp.js

You: explain how the hello world function works
🤖 Assistant:
  This function is a simple Python function that prints "Hello, World!"...

You: exit
👋 Goodbye!
```

## ⚙️ Optional: Configuration

```bash
# View current settings
olla-cli config show

# Set different model (if you have it)
olla-cli config set model deepseek-coder:33b

# Set theme
olla-cli config set output.theme light
```

## 🎯 What You Can Do

### Code Generation
- "create a calculator function"
- "build a React todo app"
- "generate a Python class for user management"

### Code Analysis
- "explain this code: [paste code]"
- "review my file for bugs"
- "suggest improvements to my function"

### File Operations
- "read the config file"
- "save this to calculator.py"
- "create multiple files for a web app"

### Complex Tasks
- "create a REST API with authentication"
- "build a complete project structure"
- "generate unit tests for my code"

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

### Interactive mode not starting
```bash
# Check help
olla-cli --help

# Try with verbose output
olla-cli --verbose
```

## 📚 Next Steps

- [Interactive Mode Guide](./interactive-mode.md) - Detailed usage guide
- [Examples](./examples.md) - Real-world usage patterns
- [API Reference](./api-reference.md) - All available commands
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions

## 💡 Pro Tips

1. **Be Specific**: "create a Python calculator" works better than "make calculator"
2. **Context Matters**: The AI remembers your conversation, so you can say "now add tests for that"
3. **File Names**: If you don't specify a filename, it will create one automatically
4. **Languages**: Works with Python, JavaScript, React, and many other languages
5. **Complex Tasks**: You can ask for multi-file projects and it will create them all