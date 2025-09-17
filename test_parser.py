#!/usr/bin/env python3
"""
Test script for Chinese Switch Parser

This script tests the parser with the provided test switch.
"""

import sys
import time
from advanced_parser import AdvancedChineseSwitchParser
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_connection():
    """Test basic connection to the switch."""
    console.print(Panel.fit(
        "[bold blue]Testing Chinese Switch Parser[/bold blue]\n"
        "Testing connection to: http://10.41.8.33",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = AdvancedChineseSwitchParser('http://10.41.8.33')
    
    # Test connection
    console.print("\n[bold]Testing connection...[/bold]")
    if parser.connect():
        console.print("[green]✓ Connection successful![/green]")
        
        # Test data extraction
        console.print("\n[bold]Testing data extraction...[/bold]")
        
        # Get system info
        console.print("  • Getting system information...")
        system_info = parser.get_system_info_advanced()
        console.print(f"    Model: {system_info.model}")
        console.print(f"    Firmware: {system_info.firmware_version}")
        console.print(f"    IP: {system_info.ip_address}")
        
        # Get port status
        console.print("  • Getting port status...")
        port_status = parser.get_port_status_advanced()
        console.print(f"    Found {len(port_status)} ports")
        
        # Get VLAN info
        console.print("  • Getting VLAN information...")
        vlan_info = parser.get_vlan_info()
        console.print(f"    Found {len(vlan_info)} VLANs")
        
        # Test comprehensive data
        console.print("  • Getting comprehensive data...")
        data = parser.get_comprehensive_data()
        console.print(f"    Data keys: {list(data.keys())}")
        
        # Test export
        console.print("  • Testing data export...")
        export_file = parser.export_data('test_export.json')
        if export_file:
            console.print(f"    ✓ Data exported to: {export_file}")
        
        console.print("\n[green]✓ All tests passed![/green]")
        return True
    else:
        console.print("[red]✗ Connection failed[/red]")
        return False

def test_web_interface():
    """Test web interface startup."""
    console.print("\n[bold]Testing web interface...[/bold]")
    
    try:
        from web_interface import app
        console.print("  • Web interface module loaded successfully")
        console.print("  • Flask app created successfully")
        console.print("[green]✓ Web interface test passed![/green]")
        return True
    except ImportError as e:
        console.print(f"[red]✗ Web interface test failed: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Web interface test failed: {e}[/red]")
        return False

def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold green]Chinese Switch Parser Test Suite[/bold green]\n"
        "Running comprehensive tests...",
        border_style="green"
    ))
    
    tests = [
        ("Connection Test", test_connection),
        ("Web Interface Test", test_web_interface),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        console.print(f"\n[bold]{test_name}:[/bold]")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            console.print(f"[red]✗ {test_name} failed with error: {e}[/red]")
    
    # Summary
    console.print(f"\n[bold]Test Summary:[/bold]")
    console.print(f"  Passed: {passed}/{total}")
    
    if passed == total:
        console.print("[green]✓ All tests passed![/green]")
        return 0
    else:
        console.print("[red]✗ Some tests failed[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())

