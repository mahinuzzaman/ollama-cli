# 🎯 Examples & Workflows

Real-world examples and common workflows using Olla CLI.

## 🚀 Basic Examples

### Code Analysis
```bash
# Explain a function
olla-cli explain "def binary_search(arr, target): ..."

# Review a file
olla-cli review app.js

# Generate code
olla-cli generate "function to validate email addresses"

# Generate tests
olla-cli test --framework pytest utils.py
```

### File Operations
```bash
# Explain specific lines
olla-cli explain --line-range "25-40" complex_algorithm.py

# Security review with output
olla-cli review --focus security --output-file security_report.md auth.py

# Generate tests to file
olla-cli test --framework pytest --output-file test_utils.py utils.py
```

## 🔄 Complete Workflows

### Code Review Workflow
```bash
# 1. Comprehensive review
olla-cli review --focus all --output-file review_report.md src/main.py

# 2. Security review
olla-cli review --focus security src/auth.py

# 3. Performance review
olla-cli review --focus performance src/data_processor.py

# 4. Refactoring suggestions
olla-cli refactor --type optimize --show-diff src/slow_function.py

# 5. Generate tests
olla-cli test --framework pytest --coverage src/main.py
```

### New Feature Development
```bash
# 1. Generate initial code
olla-cli generate --template class "user authentication manager with JWT tokens"

# 2. Save generated code
olla-cli generate --output-file auth_manager.py "complete user authentication system"

# 3. Explain complex parts
olla-cli explain --detail-level comprehensive auth_manager.py

# 4. Generate tests
olla-cli test --framework pytest --type unit auth_manager.py

# 5. Create documentation
olla-cli document --format google --type api auth_manager.py

# 6. Final review
olla-cli review --focus all auth_manager.py
```

### Debugging Session
```bash
# 1. Interactive debugging
olla-cli chat --session debugging-session

# 2. Analyze specific error
olla-cli debug --error "KeyError: 'user_id'" --line-range "45-65" auth.py

# 3. Get fix suggestions
olla-cli refactor --type simplify auth.py

# 4. Generate regression tests
olla-cli test --framework pytest --output-file test_auth_fix.py auth.py
```

## 🎨 Interactive Mode Examples

### Learning Session
```bash
olla-cli chat --session learning-python

# In chat:
# > explain Python decorators with examples
# > show me how to use context managers
# > generate a decorator that measures execution time
# > /save "Python Learning Session"
```

### Architecture Discussion
```bash
olla-cli chat --session architecture-review

# In chat:
# > I'm designing a microservices architecture. What patterns should I consider?
# > how would you structure a Flask application with multiple services?
# > /save "Microservices Architecture Discussion"
```

## 🛠️ Development Workflows

### Test-Driven Development
```bash
# 1. Generate test cases first
olla-cli test --framework pytest --output-file test_calculator.py "calculator module with basic operations"

# 2. Generate implementation
olla-cli generate --output-file calculator.py "calculator module that passes the generated tests"

# 3. Review implementation
olla-cli review calculator.py

# 4. Refactor if needed
olla-cli refactor --type optimize calculator.py
```

### API Development
```bash
# 1. Generate API structure
olla-cli generate --framework flask --template api_endpoint "user registration endpoint with validation"

# 2. Save to file
olla-cli generate --output-file user_api.py "complete Flask API with authentication endpoints"

# 3. Security review
olla-cli review --focus security user_api.py

# 4. Generate API tests
olla-cli test --framework pytest --type integration user_api.py

# 5. Create documentation
olla-cli document --type api --format google user_api.py
```

## 🔄 Automation Examples

### Batch Processing
```bash
# Review multiple files
for file in src/*.py; do
    olla-cli review --output-file "reviews/$(basename $file .py)_review.md" "$file"
done

# Generate tests for all modules
find src/ -name "*.py" -exec olla-cli test --output-file "tests/test_{}.py" {} \;
```

### Git Hook Integration
```bash
#!/bin/bash
# pre-commit hook
changed_files=$(git diff --cached --name-only --diff-filter=AM | grep '\.py$')

for file in $changed_files; do
    echo "Reviewing $file..."
    olla-cli review --focus security "$file"
done
```

## 💡 Pro Tips

### Efficient Commands
```bash
# Chain explanations and reviews
olla-cli explain complex_function.py | tee explanation.txt && olla-cli review complex_function.py

# Generate and test immediately
olla-cli generate "sorting algorithm" > sort.py && olla-cli test sort.py
```

### Using Environment Variables
```bash
# Set model for session
export OLLA_MODEL=mistral
olla-cli explain code.py  # Uses mistral

# Set theme for batch operations
export OLLA_THEME=light
for file in *.py; do olla-cli review "$file"; done
```

### Configuration Management
```bash
# Save current config
cp ~/.olla-cli/config.yaml ~/.olla-cli/config-backup.yaml

# Project-specific settings
olla-cli config set model codellama
olla-cli config set temperature 0.6

# Work on project...

# Restore config
cp ~/.olla-cli/config-backup.yaml ~/.olla-cli/config.yaml
```

---

These examples showcase common patterns and workflows. Adapt them to your specific needs!