# 🎯 Interactive Mode Guide

Complete guide to using Olla CLI's interactive mode - your conversational AI coding assistant.

## 🚀 Getting Started

Interactive mode is the default behavior of Olla CLI. Just run:

```bash
olla-cli
```

You'll see:
```
🤖 Interactive Intelligent Assistant
Type your requests in natural language. Type 'exit' to quit.

You: 
```

That's it! Now start talking to your AI assistant.

## 🧠 How It Works

Olla CLI uses Claude-like intelligent processing:

1. **Intent Classification** - Understands what you want to do
2. **Task Planning** - Breaks complex requests into steps
3. **Tool Orchestration** - Uses appropriate tools automatically
4. **File Operations** - Creates, reads, and manages files
5. **Context Memory** - Remembers your conversation

## 💬 Natural Language Patterns

### Code Generation
```bash
You: create a hello world function
You: build a React todo app
You: generate a Python calculator with basic operations
You: make a REST API for user management
You: create a sorting algorithm in JavaScript
```

### Code Analysis
```bash
You: explain this code: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)
You: review my authentication function for security issues
You: check this file for bugs: auth.py
You: suggest improvements to my sorting algorithm
You: analyze the performance of this code
```

### File Operations
```bash
You: read the config file
You: save this code to calculator.py
You: create a new component called UserCard
You: write this function to utils.py
You: show me the contents of main.py
```

### Complex Tasks
```bash
You: create a complete web app with authentication
You: build a project structure for a Python CLI tool
You: generate unit tests for all my functions
You: create documentation for my API endpoints
You: set up a React project with TypeScript
```

## 🎯 Advanced Features

### Session Memory
The AI remembers your conversation context:

```bash
You: create a calculator function
🤖 Assistant: [creates calculator.py]

You: now add unit tests for it
🤖 Assistant: [creates test_calculator.py with tests for the calculator]

You: review the calculator for any issues
🤖 Assistant: [analyzes the previously created calculator.py]
```

### Multi-step Tasks
Complex requests are automatically broken down:

```bash
You: create a todo app with React and save it to a file
🤖 Assistant:
  Step 1: Generating React todo app code...
  Step 2: Saving to TodoApp.js...
  File written: TodoApp.js
```

### Smart File Naming
If you don't specify a filename, the AI chooses appropriately:

- "create a hello world function" → `hello_world.py`
- "build a React todo app" → `TodoApp.js`
- "make a calculator" → `calculator.py`
- "generate a factorial function" → `factorial.py`

## 🛠️ Supported Languages & Frameworks

### Programming Languages
- **Python** - Functions, classes, scripts, web apps
- **JavaScript** - Functions, Node.js apps, utilities
- **TypeScript** - Type-safe JavaScript applications
- **React** - Components, hooks, complete apps
- **HTML/CSS** - Web pages, stylesheets
- **Java** - Classes, methods, applications
- **Go** - Functions, packages, web services
- **Rust** - Functions, structs, applications

### Frameworks & Tools
- **React** - Components, hooks, context
- **Node.js** - Express apps, APIs, utilities
- **Flask/Django** - Python web applications
- **FastAPI** - Modern Python APIs
- **Unit Testing** - pytest, Jest, JUnit
- **Configuration** - JSON, YAML, TOML

## 🎨 Customization Options

### Command Line Options
```bash
olla-cli --model deepseek-coder:33b    # Use specific model
olla-cli --temperature 0.3             # More deterministic
olla-cli --verbose                      # Show debug info
olla-cli --theme light                  # Light theme
olla-cli --no-color                     # Disable colors
```

### Configuration
```bash
# Set default model
olla-cli config set model codellama

# Set output theme
olla-cli config set output.theme dark

# Set temperature
olla-cli config set temperature 0.7

# View all settings
olla-cli config show
```

## 🔧 Troubleshooting

### Common Issues

**AI doesn't understand my request**
- Be more specific: "create a Python function" vs "make function"
- Include context: "create a sorting function for integers"
- Use familiar terms: "build", "create", "generate", "make"

**Files not being created**
- Check current directory permissions
- Be explicit: "save this to filename.py"
- Use absolute paths if needed

**Poor code quality**
- Ask for improvements: "make this code more robust"
- Specify requirements: "add error handling and documentation"
- Request reviews: "review this code for best practices"

**Session memory issues**
- Reference previous work: "the calculator function we just created"
- Be explicit: "using the TodoApp.js file you made"
- Start fresh if needed: restart `olla-cli`

### Debug Mode
```bash
olla-cli --verbose
```
Shows detailed processing information including:
- Intent classification results
- Execution plan steps
- Tool selection and parameters
- File operations

## 🎯 Best Practices

### 1. Be Specific
❌ "make a function"
✅ "create a Python function to calculate factorial"

### 2. Provide Context
❌ "fix this"
✅ "review this authentication function for security vulnerabilities"

### 3. Use Natural Language
❌ "gen_func calc_fib"
✅ "generate a function to calculate fibonacci numbers"

### 4. Build Incrementally
```bash
You: create a basic calculator
You: add error handling to the calculator
You: now create unit tests for it
You: generate documentation for the calculator
```

### 5. Leverage Memory
```bash
You: create a user authentication system
You: add password hashing to the auth system
You: create unit tests for the authentication functions
```

## 🚀 Power User Tips

### Batch Operations
```bash
You: create a complete Python project structure with main.py, utils.py, tests/, and README.md
```

### Language Switching
```bash
You: convert this Python function to JavaScript
You: rewrite this React component in TypeScript
```

### Code Transformation
```bash
You: refactor this function to use async/await
You: optimize this algorithm for better performance
You: add type hints to this Python code
```

### Documentation Generation
```bash
You: create comprehensive documentation for this API
You: generate docstrings for all functions in this file
You: write a README for this project
```

## 🔚 Exiting

To exit interactive mode:
```bash
You: exit
👋 Goodbye!
```

Or use `Ctrl+C` to interrupt at any time.