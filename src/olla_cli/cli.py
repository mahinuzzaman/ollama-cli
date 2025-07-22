"""New main CLI entry point with restructured commands."""

from .cli.main import main
from .cli.config_commands import config
from .cli.model_commands import models
from .cli.code_commands import explain, review, refactor, debug, generate, test, document
from .cli.task_commands import task, resume, tasks
from .context.context_cli import context


def setup_cli():
    """Setup the complete CLI with all command groups."""
    
    # Add command groups to main
    main.add_command(config)
    main.add_command(models)
    main.add_command(context)
    main.add_command(tasks)
    
    # Add individual commands
    main.add_command(explain)
    main.add_command(review)
    main.add_command(refactor)
    main.add_command(debug)
    main.add_command(generate)
    main.add_command(test)
    main.add_command(document)
    main.add_command(task)
    main.add_command(resume)
    
    return main


# Setup the CLI when module is imported
cli = setup_cli()

if __name__ == '__main__':
    cli()