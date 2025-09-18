#!/usr/bin/env python3
"""
Modular Chinese Switch Parser
Supports multiple switch models with a unified interface.
"""

import click
import json
import time
from switch_models import get_model, list_models as get_available_models, get_model_with_detection
from rich.console import Console

console = Console()


@click.command()
@click.option('--url', help='Switch URL (e.g., http://10.41.8.33)')
@click.option('--username', help='Username for authentication')
@click.option('--password', help='Password for authentication')
@click.option('--model', default=None, help=f'Switch model (available: {", ".join(get_available_models())}). If not specified, will auto-detect.')
@click.option('--mac-delay', default=1.0, help='Delay between MAC vendor lookups in seconds (default: 1.0)')
@click.option('--export', help='Export data to JSON file (optional)')
@click.option('--create-vlan', help='Create VLAN with specified ID and name (format: id:name)')
@click.option('--delete-vlan', help='Delete VLAN with specified ID')
@click.option('--enable-ssh', is_flag=True, help='Enable SSH on the switch')
@click.option('--disable-ssh', is_flag=True, help='Disable SSH on the switch')
@click.option('--save-config', is_flag=True, help='Save configuration to flash memory')
@click.option('--list-models', is_flag=True, help='List all available switch models')
def main(url, username, password, model, mac_delay, export, create_vlan, delete_vlan, enable_ssh, disable_ssh, save_config, list_models):
    """Modular Chinese Switch Parser - Extract data from various switch models."""
    
    if list_models:
        console.print("\n[bold blue]Available Switch Models:[/bold blue]")
        for model_name in get_available_models():
            console.print(f"  • {model_name}")
        return
    
    # Check required parameters when not listing models
    if not url or not username or not password:
        console.print("[red]Error: --url, --username, and --password are required when not using --list-models[/red]")
        return
    
    try:
        # Create switch instance with optional auto-detection
        if model:
            console.print(f"\n[bold blue]Initializing {model.upper()} switch parser...[/bold blue]")
            switch = get_model(model)(url, username, password, mac_delay)
        else:
            console.print(f"\n[bold blue]Initializing switch parser with auto-detection...[/bold blue]")
            switch = get_model_with_detection(url, username, password, None, mac_delay)
        
        # Handle VLAN operations
        if create_vlan:
            vlan_id, vlan_name = create_vlan.split(':', 1)
            console.print(f"\n[bold yellow]Creating VLAN {vlan_id} with name '{vlan_name}'...[/bold yellow]")
            success = switch.create_vlan(int(vlan_id), vlan_name)
            if success:
                console.print(f"[green]✅ VLAN {vlan_id} created successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to create VLAN {vlan_id}[/red]")
            return
        
        if delete_vlan:
            console.print(f"\n[bold yellow]Deleting VLAN {delete_vlan}...[/bold yellow]")
            success = switch.delete_vlan(int(delete_vlan))
            if success:
                console.print(f"[green]✅ VLAN {delete_vlan} deleted successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to delete VLAN {delete_vlan}[/red]")
            return
        
        # Handle SSH operations
        if enable_ssh:
            console.print(f"\n[bold yellow]Enabling SSH on switch...[/bold yellow]")
            success = switch.enable_ssh()
            if success:
                console.print(f"[green]✅ SSH enabled successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to enable SSH[/red]")
            return
        
        if disable_ssh:
            console.print(f"\n[bold yellow]Disabling SSH on switch...[/bold yellow]")
            success = switch.disable_ssh()
            if success:
                console.print(f"[green]✅ SSH disabled successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to disable SSH[/red]")
            return
        
        # Handle save configuration
        if save_config:
            console.print(f"\n[bold yellow]Saving configuration to flash memory...[/bold yellow]")
            success = switch.save_configuration()
            if success:
                console.print(f"[green]✅ Configuration saved successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to save configuration[/red]")
            return
        
        # Extract data
        console.print(f"\n[bold green]Extracting data from {switch.model_name}...[/bold green]")
        data = switch.extract_all_data()
        
        # Display data
        switch.display_data(data)
        
        # Export if requested
        if export:
            filename = switch.export_data(data, export)
            console.print(f"\n[green]Data exported to: {filename}[/green]")
        
        console.print(f"\n[bold green]✅ Data extraction completed successfully![/bold green]")
        
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


if __name__ == '__main__':
    main()
