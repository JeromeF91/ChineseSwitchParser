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
@click.option('--rename-vlan', help='Rename VLAN with specified ID (format: id:name)')
@click.option('--vlan-membership', is_flag=True, help='Show per-port VLAN membership (VM-S100-0800MS)')
@click.option('--port-vlan-add', help='Add a port to a VLAN (format: portIdx:vlanId[:tagged|untagged|forbidden], 0-based port index; VM-S100-0800MS)')
@click.option('--port-vlan-remove', help='Remove a port from a VLAN (format: portIdx:vlanId; VM-S100-0800MS)')
@click.option('--enable-ssh', is_flag=True, help='Enable SSH on the switch')
@click.option('--disable-ssh', is_flag=True, help='Disable SSH on the switch')
@click.option('--save-config', is_flag=True, help='Save configuration to flash memory')
@click.option('--list-models', is_flag=True, help='List all available switch models')
def main(url, username, password, model, mac_delay, export, create_vlan, delete_vlan, rename_vlan, vlan_membership, port_vlan_add, port_vlan_remove, enable_ssh, disable_ssh, save_config, list_models):
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
        
        if rename_vlan:
            vlan_id, vlan_name = rename_vlan.split(':', 1)
            if not hasattr(switch, '_update_vlan_name'):
                console.print("[red]❌ VLAN rename not supported for this model[/red]")
                return
            console.print(f"\n[bold yellow]Renaming VLAN {vlan_id} to '{vlan_name}'...[/bold yellow]")
            success = switch._update_vlan_name(int(vlan_id), vlan_name)
            console.print(f"[green]✅ VLAN {vlan_id} renamed![/green]" if success else f"[red]❌ Failed to rename VLAN {vlan_id}[/red]")
            return
        
        if vlan_membership:
            if not hasattr(switch, 'get_vlan_membership'):
                console.print("[red]❌ VLAN membership listing not supported for this model[/red]")
                return
            console.print(f"\n[bold yellow]Per-port VLAN membership:[/bold yellow]")
            for port in switch.get_vlan_membership():
                console.print(f"  port[{port['port']}] mode={port['mode']} {port['admin_vlans']}")
            return
        
        if port_vlan_add:
            if not hasattr(switch, 'add_port_to_vlan'):
                console.print("[red]❌ Port VLAN membership writes not supported for this model[/red]")
                return
            parts = port_vlan_add.split(':')
            if len(parts) not in (2, 3):
                console.print("[red]Format: portIdx:vlanId[:tagged|untagged|forbidden][/red]")
                return
            port_idx, vlan_id = int(parts[0]), int(parts[1])
            kind = parts[2] if len(parts) == 3 else 'tagged'
            if kind not in ('tagged', 'untagged', 'forbidden'):
                console.print("[red]Kind must be tagged, untagged or forbidden[/red]")
                return
            if kind == 'forbidden':
                # forbidden = 'F' entry; use the full-set API for this rare case
                current = switch._port_membership(port_idx)
                wanted = {(vid, k) for vid, k in current if vid != vlan_id}
                wanted.add((vlan_id, 'F'))
                success = switch.set_port_vlan_membership(port_idx, sorted(wanted))
            else:
                success = switch.add_port_to_vlan(port_idx, vlan_id, tagged=(kind == 'tagged'))
            if success:
                console.print(f"[green]✅ Port {port_idx} added to VLAN {vlan_id} ({kind})![/green]")
                console.print("[dim]Run --save-config to persist to flash.[/dim]")
            else:
                console.print(f"[red]❌ Failed to add port {port_idx} to VLAN {vlan_id}[/red]")
            return
        
        if port_vlan_remove:
            if not hasattr(switch, 'remove_port_from_vlan'):
                console.print("[red]❌ Port VLAN membership writes not supported for this model[/red]")
                return
            parts = port_vlan_remove.split(':')
            if len(parts) != 2:
                console.print("[red]Format: portIdx:vlanId[/red]")
                return
            success = switch.remove_port_from_vlan(int(parts[0]), int(parts[1]))
            if success:
                console.print(f"[green]✅ Port {parts[0]} removed from VLAN {parts[1]}![/green]")
                console.print("[dim]Run --save-config to persist to flash.[/dim]")
            else:
                console.print(f"[red]❌ Failed to remove port {parts[0]} from VLAN {parts[1]}[/red]")
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
