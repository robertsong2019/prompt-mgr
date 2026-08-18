"""CLI interface for prompt-mgr."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import Optional

from .manager import PromptManager
from .utils import parse_variable_assignments, format_template_table


console = Console()


@click.group()
def main():
    """Prompt Manager - A lightweight CLI tool for managing AI prompt templates."""
    pass


@main.command()
@click.argument("name")
@click.option("--content", "-c", required=True, help="Template content")
@click.option("--tags", "-t", help="Comma-separated tags")
@click.option("--description", "-d", help="Template description")
def add(name: str, content: str, tags: Optional[str], description: Optional[str]):
    """Add a new template."""
    try:
        manager = PromptManager()
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        
        template = manager.add_template(
            name=name,
            content=content,
            tags=tag_list,
            description=description,
        )
        
        console.print(f"[green]✓[/green] Template added: {name}")
        console.print(f"  Tags: {', '.join(template.tags) or 'none'}")
        console.print(f"  Variables: {', '.join(template.extract_variables()) or 'none'}")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list(tags: Optional[str], format: str):
    """List all templates."""
    manager = PromptManager()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    templates = manager.list_templates(tags=tag_list)
    
    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return
    
    if format == "json":
        import json
        data = [t.to_dict() for t in templates]
        console.print(json.dumps(data, indent=2))
    else:
        console.print(format_template_table(templates))


@main.command()
@click.argument("query", required=False)
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
def search(query: Optional[str], tags: Optional[str]):
    """Search templates."""
    manager = PromptManager()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    templates = manager.search_templates(query=query or "", tags=tag_list)
    
    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return
    
    console.print(format_template_table(templates))


@main.command()
@click.argument("name")
def show(name: str):
    """Show template details."""
    manager = PromptManager()
    template = manager.get_template(name)
    
    if not template:
        console.print(f"[red]Error:[/red] Template not found: {name}")
        raise click.Abort()
    
    console.print(Panel(
        template.content,
        title=f"[bold]{template.name}[/bold]",
        subtitle=f"Tags: {', '.join(template.tags) or 'none'}",
    ))
    
    if template.description:
        console.print(f"\n[bold]Description:[/bold] {template.description}")
    
    variables = template.extract_variables()
    if variables:
        console.print(f"\n[bold]Variables:[/bold] {', '.join(variables)}")
    
    console.print(f"\n[bold]Created:[/bold] {template.created_at}")
    console.print(f"[bold]Updated:[/bold] {template.updated_at}")


@main.command()
@click.argument("name")
@click.option("--content", "-c", help="New template content")
@click.option("--tags", "-t", help="New tags (comma-separated)")
@click.option("--description", "-d", help="New description")
def edit(name: str, content: Optional[str], tags: Optional[str], description: Optional[str]):
    """Edit a template."""
    try:
        manager = PromptManager()
        
        # Check if template exists
        if not manager.get_template(name):
            console.print(f"[red]Error:[/red] Template not found: {name}")
            raise click.Abort()
        
        # Parse tags if provided
        tag_list = [t.strip() for t in tags.split(",")] if tags is not None else None
        
        # Update template
        template = manager.update_template(
            name=name,
            content=content,
            tags=tag_list,
            description=description,
        )
        
        console.print(f"[green]✓[/green] Template updated: {name}")
        console.print(f"  Tags: {', '.join(template.tags) or 'none'}")
        console.print(f"  Variables: {', '.join(template.extract_variables()) or 'none'}")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(name: str, yes: bool):
    """Delete a template."""
    manager = PromptManager()
    
    # Check if template exists
    if not manager.get_template(name):
        console.print(f"[red]Error:[/red] Template not found: {name}")
        raise click.Abort()
    
    # Confirm deletion
    if not yes:
        if not click.confirm(f"Delete template '{name}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return
    
    # Delete template
    if manager.delete_template(name):
        console.print(f"[green]✓[/green] Template deleted: {name}")
    else:
        console.print(f"[red]Error:[/red] Could not delete template: {name}")


@main.command()
@click.argument("name")
@click.option("--vars", "-v", help="Variable assignments as comma-separated list (key=value,key2=value2)")
def render(name: str, vars):
    """Render a template with variables."""
    try:
        manager = PromptManager()
        
        # Parse variables - split comma-separated vars
        if vars:
            # Split comma-separated values
            var_list = [v.strip() for v in vars.split(',')]
            variables = parse_variable_assignments(var_list)
        else:
            variables = {}
        
        # Render template
        result = manager.render_template(name, variables)
        
        console.print(Panel(
            result,
            title=f"[bold]Rendered: {name}[/bold]",
        ))
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.option("--limit", "-n", default=10, help="Number of recent templates")
def recent(limit: int):
    """Show recently updated templates."""
    manager = PromptManager()
    templates = manager.recent_templates(n=limit)
    
    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return
    
    console.print(format_template_table(templates))


@main.command()
@click.option("--output", "-o", type=click.Path(), default="templates.json", help="Output file")
def export(output: str):
    """Export templates to JSON."""
    manager = PromptManager()
    output_path = Path(output)
    
    manager.export_templates(output_path)
    console.print(f"[green]✓[/green] Templates exported to: {output_path}")


@main.command()
@click.option("--input", "-i", type=click.Path(exists=True), required=True, help="Input file")
@click.option("--overwrite", "-o", is_flag=True, help="Overwrite existing templates")
def import_cmd(input: str, overwrite: bool):
    """Import templates from JSON."""
    try:
        manager = PromptManager()
        input_path = Path(input)
        
        count = manager.import_templates(input_path, overwrite=overwrite)
        console.print(f"[green]✓[/green] Imported {count} templates")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


# Rename the command to avoid conflict with Python's import
main.add_command(import_cmd, "import")


if __name__ == "__main__":
    main()
