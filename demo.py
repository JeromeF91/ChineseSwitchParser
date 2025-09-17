#!/usr/bin/env python3
"""
Demo script for Chinese Switch Parser

This script demonstrates the various features of the parser.
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from advanced_parser import AdvancedChineseSwitchParser

console = Console()

def demo_basic_usage():
    """Demonstrate basic parser usage."""
    console.print(Panel.fit(
        "[bold blue]Demo: Basic Parser Usage[/bold blue]\n"
        "Connecting to test switch and extracting data",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = AdvancedChineseSwitchParser('http://10.41.8.33')
    
    # Connect
    if parser.connect():
        console.print("[green]✓ Connected successfully![/green]")
        
        # Get system information
        console.print("\n[bold]System Information:[/bold]")
        system_info = parser.get_system_info_advanced()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Model", system_info.model)
        table.add_row("Firmware", system_info.firmware_version)
        table.add_row("Uptime", system_info.uptime)
        table.add_row("IP Address", system_info.ip_address)
        
        console.print(table)
        
        # Get port status
        console.print("\n[bold]Port Status:[/bold]")
        ports = parser.get_port_status_advanced()
        
        if ports:
            port_table = Table(show_header=True, header_style="bold magenta")
            port_table.add_column("Port", style="cyan")
            port_table.add_column("Status", style="green")
            port_table.add_column("Speed", style="blue")
            port_table.add_column("VLAN", style="yellow")
            
            for port in ports[:5]:  # Show first 5 ports
                status_color = "green" if "up" in port.status.lower() else "red"
                port_table.add_row(
                    port.port_id,
                    f"[{status_color}]{port.status}[/{status_color}]",
                    port.speed,
                    port.vlan
                )
            
            console.print(port_table)
        else:
            console.print("[yellow]No port information available[/yellow]")
        
        return True
    else:
        console.print("[red]✗ Connection failed[/red]")
        return False

def demo_web_interface():
    """Demonstrate web interface."""
    console.print(Panel.fit(
        "[bold blue]Demo: Web Interface[/bold blue]\n"
        "Starting web interface for interactive use",
        border_style="blue"
    ))
    
    try:
        from web_interface import app
        console.print("[green]✓ Web interface available[/green]")
        console.print("To start the web interface, run:")
        console.print("[cyan]python cli_tool.py web[/cyan]")
        console.print("Then open: [cyan]http://localhost:5000[/cyan]")
        return True
    except ImportError:
        console.print("[red]✗ Web interface not available (Flask not installed)[/red]")
        return False

def demo_export_functionality():
    """Demonstrate export functionality."""
    console.print(Panel.fit(
        "[bold blue]Demo: Export Functionality[/bold blue]\n"
        "Exporting switch data to various formats",
        border_style="blue"
    ))
    
    parser = AdvancedChineseSwitchParser('http://10.41.8.33')
    
    if parser.connect():
        console.print("[green]✓ Connected successfully![/green]")
        
        # Export to JSON
        console.print("\n[bold]Exporting to JSON...[/bold]")
        json_file = parser.export_data('demo_export.json')
        if json_file:
            console.print(f"[green]✓ JSON export successful: {json_file}[/green]")
        
        # Get comprehensive data
        console.print("\n[bold]Getting comprehensive data...[/bold]")
        data = parser.get_comprehensive_data()
        
        console.print(f"Data structure:")
        console.print(f"  • System Info: {'✓' if data.get('system_info') else '✗'}")
        console.print(f"  • Port Status: {'✓' if data.get('port_status') else '✗'}")
        console.print(f"  • VLAN Info: {'✓' if data.get('vlan_info') else '✗'}")
        console.print(f"  • QoS Settings: {'✓' if data.get('qos_settings') else '✗'}")
        console.print(f"  • Security Settings: {'✓' if data.get('security_settings') else '✗'}")
        
        return True
    else:
        console.print("[red]✗ Connection failed[/red]")
        return False

def demo_cli_commands():
    """Demonstrate CLI commands."""
    console.print(Panel.fit(
        "[bold blue]Demo: CLI Commands[/bold blue]\n"
        "Available command-line interface options",
        border_style="blue"
    ))
    
    commands = [
        ("Connect and display data", "python cli_tool.py connect --url http://10.41.8.33"),
        ("Export to JSON", "python cli_tool.py connect --url http://10.41.8.33 --output data.json --format json"),
        ("Export to CSV", "python cli_tool.py connect --url http://10.41.8.33 --output data.xlsx --format csv"),
        ("Real-time monitoring", "python cli_tool.py monitor --url http://10.41.8.33 --interval 30"),
        ("Discover endpoints", "python cli_tool.py discover --url http://10.41.8.33"),
        ("Start web interface", "python cli_tool.py web"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Description", style="cyan")
    table.add_column("Command", style="green")
    
    for desc, cmd in commands:
        table.add_row(desc, cmd)
    
    console.print(table)

def main():
    """Run all demos."""
    console.print(Panel.fit(
        "[bold green]Chinese Switch Parser Demo[/bold green]\n"
        "Demonstrating various features and capabilities",
        border_style="green"
    ))
    
    demos = [
        ("Basic Usage", demo_basic_usage),
        ("Web Interface", demo_web_interface),
        ("Export Functionality", demo_export_functionality),
        ("CLI Commands", demo_cli_commands),
    ]
    
    for demo_name, demo_func in demos:
        console.print(f"\n[bold]{'='*50}[/bold]")
        console.print(f"[bold]{demo_name}[/bold]")
        console.print(f"[bold]{'='*50}[/bold]")
        
        try:
            demo_func()
        except Exception as e:
            console.print(f"[red]Demo failed: {e}[/red]")
        
        time.sleep(1)  # Pause between demos
    
    console.print(f"\n[bold]{'='*50}[/bold]")
    console.print("[bold green]Demo Complete![/bold green]")
    console.print(f"[bold]{'='*50}[/bold]")
    
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Try the CLI commands shown above")
    console.print("2. Start the web interface: [cyan]python cli_tool.py web[/cyan]")
    console.print("3. Explore the test switch at: [cyan]http://10.41.8.33[/cyan]")
    console.print("4. Check the README.md for detailed documentation")

if __name__ == "__main__":
    main()

