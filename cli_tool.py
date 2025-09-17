#!/usr/bin/env python3
"""
CLI Tool for Chinese Switch Parser

A command-line interface for the Chinese switch parser with various options.
"""

import click
import json
import sys
from pathlib import Path
from advanced_parser import AdvancedChineseSwitchParser
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.group()
def cli():
    """Chinese Switch Parser CLI Tool"""
    pass

@cli.command()
@click.option('--url', default='http://10.41.8.33', help='Switch base URL')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
@click.option('--output', '-o', help='Output file for data export')
@click.option('--format', 'output_format', type=click.Choice(['json', 'csv', 'table']), default='table', help='Output format')
def connect(url, username, password, output, output_format):
    """Connect to switch and display information."""
    
    console.print(Panel.fit(
        "[bold blue]Chinese Switch Parser CLI[/bold blue]\n"
        f"Connecting to: {url}",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = AdvancedChineseSwitchParser(url, username, password)
    
    # Connect to switch
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Connecting to switch...", total=None)
        
        if not parser.connect():
            console.print("[red]Failed to connect to switch. Exiting.[/red]")
            sys.exit(1)
        
        progress.update(task, description="Connected successfully")
    
    # Get comprehensive data
    console.print("\n[bold]Gathering switch data...[/bold]")
    data = parser.get_comprehensive_data()
    
    # Display or export data
    if output_format == 'table':
        parser.display_comprehensive_data(data)
    elif output_format == 'json':
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                # Convert dataclasses to dictionaries
                export_data = data.copy()
                if export_data.get('system_info'):
                    export_data['system_info'] = export_data['system_info'].__dict__
                if export_data.get('port_status'):
                    export_data['port_status'] = [port.__dict__ for port in export_data['port_status']]
                if export_data.get('vlan_info'):
                    export_data['vlan_info'] = [vlan.__dict__ for vlan in export_data['vlan_info']]
                
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Data exported to: {output}[/green]")
        else:
            console.print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    elif output_format == 'csv':
        if not output:
            console.print("[red]CSV format requires --output option[/red]")
            sys.exit(1)
        
        import pandas as pd
        
        # Convert data to CSV format
        csv_data = {}
        
        if data.get('system_info'):
            system_info = data['system_info']
            csv_data['system'] = [{
                'Property': 'Model', 'Value': system_info.model
            }, {
                'Property': 'Firmware Version', 'Value': system_info.firmware_version
            }, {
                'Property': 'Uptime', 'Value': system_info.uptime
            }, {
                'Property': 'MAC Address', 'Value': system_info.mac_address
            }, {
                'Property': 'IP Address', 'Value': system_info.ip_address
            }]
        
        if data.get('port_status'):
            csv_data['ports'] = [port.__dict__ for port in data['port_status']]
        
        if data.get('vlan_info'):
            csv_data['vlans'] = [vlan.__dict__ for vlan in data['vlan_info']]
        
        # Write to Excel file with multiple sheets
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, sheet_data in csv_data.items():
                if sheet_data:
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        console.print(f"[green]Data exported to: {output}[/green]")

@cli.command()
@click.option('--url', default='http://10.41.8.33', help='Switch base URL')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
@click.option('--interval', default=30, help='Refresh interval in seconds')
def monitor(url, username, password, interval):
    """Monitor switch in real-time."""
    
    console.print(Panel.fit(
        "[bold blue]Chinese Switch Parser - Real-time Monitor[/bold blue]\n"
        f"Monitoring: {url}\n"
        f"Refresh interval: {interval}s",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = AdvancedChineseSwitchParser(url, username, password)
    
    # Connect to switch
    if not parser.connect():
        console.print("[red]Failed to connect to switch. Exiting.[/red]")
        sys.exit(1)
    
    console.print("[green]Connected successfully. Starting monitoring...[/green]")
    console.print("Press Ctrl+C to stop monitoring.\n")
    
    try:
        import time
        while True:
            # Clear screen
            console.clear()
            
            # Get and display data
            data = parser.get_comprehensive_data()
            parser.display_comprehensive_data(data)
            
            # Wait for next refresh
            time.sleep(interval)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user.[/yellow]")

@cli.command()
@click.option('--url', default='http://10.41.8.33', help='Switch base URL')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
def discover(url, username, password):
    """Discover switch capabilities and endpoints."""
    
    console.print(Panel.fit(
        "[bold blue]Chinese Switch Parser - Discovery Mode[/bold blue]\n"
        f"Discovering: {url}",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = AdvancedChineseSwitchParser(url, username, password)
    
    # Connect to switch
    if not parser.connect():
        console.print("[red]Failed to connect to switch. Exiting.[/red]")
        sys.exit(1)
    
    # Display discovered endpoints
    console.print("\n[bold]Discovered Endpoints:[/bold]")
    for endpoint in sorted(parser.discovered_endpoints):
        console.print(f"  • {endpoint}")
    
    # Get basic system info
    console.print("\n[bold]Basic System Information:[/bold]")
    system_info = parser.get_system_info_advanced()
    console.print(f"  Model: {system_info.model}")
    console.print(f"  Firmware: {system_info.firmware_version}")
    console.print(f"  IP Address: {system_info.ip_address}")

@cli.command()
def web():
    """Start web interface."""
    
    console.print(Panel.fit(
        "[bold blue]Chinese Switch Parser - Web Interface[/bold blue]\n"
        "Starting web server...",
        border_style="blue"
    ))
    
    try:
        from web_interface import app
        console.print("[green]Web interface starting at http://localhost:5000[/green]")
        app.run(debug=False, host='0.0.0.0', port=5000)
    except ImportError:
        console.print("[red]Web interface not available. Please install Flask.[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli()

