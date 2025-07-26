"""Simplified CLI entry point - Interactive mode only."""

from .cli.main import main

# CLI is already configured in main.py with only essential commands
cli = main

if __name__ == '__main__':
    cli()