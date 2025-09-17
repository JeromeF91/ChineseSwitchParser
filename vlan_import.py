#!/usr/bin/env python3
"""
VLAN Import Script
Imports VLANs from source switch to destination switch
"""

import json
import time
from switch_models import get_model_with_detection
from rich.console import Console

console = Console()

def import_vlans(source_url, dest_url, username, password):
    """Import VLANs from source switch to destination switch."""
    
    # Source VLANs to import
    vlans_to_import = [
        (105, "TOR01-WAN1"),
        (106, "TOR01-WAN2"),
        (110, "TOR01-Management"),
        (120, "TOR01-NetMgmt"),
        (130, "TOR01-Storage"),
        (140, "TOR01-Workstations"),
        (150, "TOR01-Servers"),
        (160, "ServersDMZ"),
        (170, "TOR01-CCTV"),
        (180, "TOR01-IOT"),
        (190, "TOR01-GuestWifi")
    ]
    
    console.print(f"\n[bold blue]VLAN Import Process[/bold blue]")
    console.print(f"Source: {source_url}")
    console.print(f"Destination: {dest_url}")
    console.print(f"VLANs to import: {len(vlans_to_import)}")
    
    # Create destination switch instance with auto-detection
    dest_switch = get_model_with_detection(dest_url, username, password)
    
    # Authenticate with destination switch
    console.print(f"\n[bold yellow]Authenticating with destination switch...[/bold yellow]")
    if not dest_switch.authenticate():
        console.print("[red]❌ Failed to authenticate with destination switch[/red]")
        return False
    
    console.print("[green]✅ Authentication successful[/green]")
    
    # Import each VLAN
    success_count = 0
    failed_vlans = []
    
    for vlan_id, vlan_name in vlans_to_import:
        console.print(f"\n[bold yellow]Creating VLAN {vlan_id}: {vlan_name}...[/bold yellow]")
        
        try:
            success = dest_switch.create_vlan(vlan_id, vlan_name)
            if success:
                console.print(f"[green]✅ VLAN {vlan_id} created successfully[/green]")
                success_count += 1
            else:
                console.print(f"[red]❌ Failed to create VLAN {vlan_id}[/red]")
                failed_vlans.append((vlan_id, vlan_name))
        except Exception as e:
            console.print(f"[red]❌ Error creating VLAN {vlan_id}: {str(e)}[/red]")
            failed_vlans.append((vlan_id, vlan_name))
        
        # Small delay between VLAN creations
        time.sleep(1)
    
    # Summary
    console.print(f"\n[bold blue]Import Summary[/bold blue]")
    console.print(f"✅ Successfully created: {success_count}/{len(vlans_to_import)} VLANs")
    
    if failed_vlans:
        console.print(f"[red]❌ Failed VLANs:[/red]")
        for vlan_id, vlan_name in failed_vlans:
            console.print(f"  - VLAN {vlan_id}: {vlan_name}")
    
    return success_count == len(vlans_to_import)

if __name__ == "__main__":
    # Configuration
    source_url = "http://10.41.8.34"
    dest_url = "http://10.41.8.35"
    username = "admin"
    password = "admin"
    
    console.print("[bold green]VLAN Import Tool[/bold green]")
    console.print("This tool will import VLANs from source switch to destination switch")
    
    # Confirm before proceeding
    try:
        confirm = input("\nProceed with VLAN import? (y/N): ").strip().lower()
        if confirm != 'y':
            console.print("[yellow]Import cancelled by user[/yellow]")
            exit(0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Import cancelled by user[/yellow]")
        exit(0)
    
    # Run import
    success = import_vlans(source_url, dest_url, username, password)
    
    if success:
        console.print("\n[bold green]🎉 All VLANs imported successfully![/bold green]")
    else:
        console.print("\n[bold red]⚠️  Some VLANs failed to import. Check the summary above.[/bold red]")
