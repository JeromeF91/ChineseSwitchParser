#!/usr/bin/env python3
"""
Test script to demonstrate auto-detection functionality
"""

from switch_models import detect_switch_model, get_model_with_detection
from rich.console import Console

console = Console()

def test_auto_detection():
    """Test auto-detection on known switches."""
    
    # Test switches
    test_switches = [
        ("10.41.8.33", "VM-S100-0800MS"),
        ("10.41.8.34", "SL-SWTG124AS"),
        ("10.41.8.35", "SL-SWTG124AS")
    ]
    
    console.print("[bold blue]🔍 Testing Auto-Detection Feature[/bold blue]")
    console.print()
    
    for url, expected_model in test_switches:
        console.print(f"[bold yellow]Testing {url} (expected: {expected_model})[/bold yellow]")
        
        try:
            # Test detection
            detected = detect_switch_model(f"http://{url}")
            
            if detected:
                if detected.lower() in expected_model.lower() or expected_model.lower() in detected.lower():
                    console.print(f"[green]✅ Correctly detected: {detected}[/green]")
                else:
                    console.print(f"[yellow]⚠️  Detected: {detected} (expected: {expected_model})[/yellow]")
            else:
                console.print(f"[red]❌ Detection failed[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
        
        console.print()

def test_full_workflow():
    """Test full workflow with auto-detection."""
    
    console.print("[bold blue]🚀 Testing Full Workflow with Auto-Detection[/bold blue]")
    console.print()
    
    # Test with VM-S100-0800MS
    console.print("[bold yellow]Testing VM-S100-0800MS workflow...[/bold yellow]")
    try:
        switch = get_model_with_detection("http://10.41.8.33", "admin", "admin")
        console.print(f"[green]✅ Switch instance created: {switch.model_name}[/green]")
        
        # Test authentication
        if switch.authenticate():
            console.print("[green]✅ Authentication successful[/green]")
        else:
            console.print("[red]❌ Authentication failed[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    
    console.print()
    
    # Test with SL-SWTG124AS
    console.print("[bold yellow]Testing SL-SWTG124AS workflow...[/bold yellow]")
    try:
        switch = get_model_with_detection("http://10.41.8.35", "admin", "admin")
        console.print(f"[green]✅ Switch instance created: {switch.model_name}[/green]")
        
        # Test authentication
        if switch.authenticate():
            console.print("[green]✅ Authentication successful[/green]")
        else:
            console.print("[red]❌ Authentication failed[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

if __name__ == "__main__":
    test_auto_detection()
    console.print()
    test_full_workflow()
    console.print()
    console.print("[bold green]🎉 Auto-detection testing completed![/bold green]")
