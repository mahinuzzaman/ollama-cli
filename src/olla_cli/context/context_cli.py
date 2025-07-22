"""CLI commands for context management."""

import click
from pathlib import Path
import json

from .context_builder import ContextManager, ContextStrategy
from ..utils import format_error_message


@click.group()
@click.pass_context
def context(ctx):
    """Manage code context and project analysis."""
    pass


@context.command('analyze')
@click.argument('target_file', required=False)
@click.option('--strategy', '-s', 
              type=click.Choice(['single', 'related', 'overview']), 
              default='single',
              help='Context building strategy')
@click.option('--max-tokens', '-t', type=int, help='Maximum tokens in context')
@click.option('--depth', '-d', type=int, default=1, help='Dependency depth for related files')
@click.option('--output', '-o', help='Output file for context')
@click.pass_context
def context_analyze(ctx, target_file, strategy, max_tokens, depth, output):
    """Analyze and build context for a file."""
    try:
        # Initialize context manager
        context_manager = ContextManager()
        
        # Determine target file
        if not target_file:
            target_file = Path.cwd() / "main.py"  # Default
        else:
            target_file = Path(target_file)
        
        # Map strategy
        strategy_map = {
            'single': ContextStrategy.SINGLE_FILE,
            'related': ContextStrategy.RELATED_FILES,
            'overview': ContextStrategy.PROJECT_OVERVIEW
        }
        
        context_strategy = strategy_map[strategy]
        
        click.echo(f"🔍 Analyzing {target_file} using {strategy} strategy...")
        
        # Build context
        result = context_manager.build_context(
            target_file=target_file,
            strategy=context_strategy,
            max_tokens=max_tokens,
            dependency_depth=depth
        )
        
        # Display results
        click.echo(f"\n✅ Context built successfully!")
        click.echo(f"📊 Strategy: {result.strategy.value}")
        click.echo(f"📝 Token count: {result.token_count}")
        click.echo(f"📁 Files included: {len(result.files)}")
        
        if ctx.obj.get('verbose'):
            click.echo(f"📋 Metadata: {json.dumps(result.metadata, indent=2)}")
        
        # Output context
        if output:
            with open(output, 'w') as f:
                f.write(result.content)
            click.echo(f"💾 Context saved to: {output}")
        else:
            click.echo(f"\n{'='*60}")
            click.echo("CONTEXT CONTENT:")
            click.echo('='*60)
            click.echo(result.content)
            click.echo('='*60)
    
    except Exception as e:
        click.echo(f"❌ Error analyzing context: {format_error_message(e)}", err=True)


@context.command('tree')
@click.option('--depth', '-d', type=int, default=3, help='Maximum tree depth')
@click.option('--max-files', '-f', type=int, default=50, help='Maximum files to show')
@click.pass_context
def context_tree(ctx, depth, max_files):
    """Show project file tree."""
    try:
        context_manager = ContextManager()
        
        click.echo(f"📁 Project structure for: {context_manager.project_root.name}")
        click.echo("")
        
        tree = context_manager.file_tree.generate_tree(max_depth=depth, max_files=max_files)
        click.echo(tree)
        
    except Exception as e:
        click.echo(f"❌ Error generating tree: {format_error_message(e)}", err=True)


@context.command('summary')
@click.pass_context
def context_summary(ctx):
    """Show project summary."""
    try:
        context_manager = ContextManager()
        summary = context_manager.get_project_summary()
        
        click.echo(f"📊 Project Summary: {context_manager.project_root.name}")
        click.echo("")
        click.echo(f"🗂️  Root: {summary['root']}")
        click.echo(f"🔤 Language: {summary['language']}")
        if summary['framework']:
            click.echo(f"⚡ Framework: {summary['framework']}")
        click.echo(f"📄 Total files: {summary['total_files']}")
        
        click.echo("\n📈 File types:")
        for lang, count in sorted(summary['file_types'].items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  • {lang}: {count}")
        
        click.echo(f"\n🔗 Dependencies:")
        dep_stats = summary['dependency_stats']
        click.echo(f"  • Internal: {dep_stats['total_internal_dependencies']}")
        click.echo(f"  • External: {dep_stats['total_external_dependencies']}")
        click.echo(f"  • Files with deps: {dep_stats['files_with_dependencies']}")
        
    except Exception as e:
        click.echo(f"❌ Error generating summary: {format_error_message(e)}", err=True)


@context.command('deps')
@click.argument('target_file')
@click.option('--depth', '-d', type=int, default=1, help='Dependency depth')
@click.option('--show-external', is_flag=True, help='Show external dependencies')
@click.pass_context
def context_deps(ctx, target_file, depth, show_external):
    """Show file dependencies."""
    try:
        context_manager = ContextManager()
        target_path = Path(target_file)
        
        if not target_path.is_absolute():
            target_path = context_manager.project_root / target_path
        
        click.echo(f"🔗 Dependencies for: {target_path.relative_to(context_manager.project_root)}")
        click.echo("")
        
        # Get dependencies
        deps = context_manager.dependency_graph.get_dependencies(target_path, depth)
        
        if deps:
            click.echo("📥 Internal dependencies:")
            for dep in sorted(deps):
                rel_path = dep.relative_to(context_manager.project_root)
                click.echo(f"  • {rel_path}")
        else:
            click.echo("📥 No internal dependencies found")
        
        if show_external and target_path in context_manager.dependency_graph.nodes:
            node = context_manager.dependency_graph.nodes[target_path]
            if node.external_dependencies:
                click.echo(f"\n🌐 External dependencies:")
                for ext_dep in sorted(node.external_dependencies):
                    click.echo(f"  • {ext_dep}")
        
        # Show dependents
        dependents = context_manager.dependency_graph.get_dependents(target_path)
        if dependents:
            click.echo(f"\n📤 Files that depend on this:")
            for dep in sorted(dependents):
                rel_path = dep.relative_to(context_manager.project_root)
                click.echo(f"  • {rel_path}")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing dependencies: {format_error_message(e)}", err=True)


@context.command('cache')
@click.option('--clear', is_flag=True, help='Clear cache')
@click.option('--stats', is_flag=True, help='Show cache statistics')
@click.pass_context
def context_cache(ctx, clear, stats):
    """Manage context cache."""
    try:
        context_manager = ContextManager()
        
        if clear:
            # Clear cache
            import shutil
            if context_manager.cache_dir.exists():
                shutil.rmtree(context_manager.cache_dir)
                context_manager.cache_dir.mkdir(parents=True, exist_ok=True)
            click.echo("🗑️  Cache cleared successfully")
        
        elif stats:
            # Show cache stats
            cache_files = list(context_manager.cache_dir.glob('*.json'))
            metadata_file = context_manager.cache_dir / 'metadata.json'
            
            total_size = sum(f.stat().st_size for f in cache_files if f.exists())
            total_size_mb = total_size / (1024 * 1024)
            
            click.echo(f"📊 Cache Statistics:")
            click.echo(f"  📁 Cache directory: {context_manager.cache_dir}")
            click.echo(f"  📄 Cached files: {len(cache_files)}")
            click.echo(f"  💾 Total size: {total_size_mb:.2f} MB")
            
            if metadata_file.exists():
                import json
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    click.echo(f"  ⏰ Entries with TTL: {len(metadata)}")
                except:
                    pass
        
        else:
            # Default: cleanup expired entries
            context_manager.file_cache.cleanup_expired()
            click.echo("🧹 Expired cache entries cleaned up")
    
    except Exception as e:
        click.echo(f"❌ Error managing cache: {format_error_message(e)}", err=True)