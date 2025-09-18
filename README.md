# Chinese Switch Parser

A modular and comprehensive parser for Chinese network switch administrative interfaces. This tool extracts configuration data, status information, and provides VLAN management capabilities across multiple switch models.

## 🚀 Features

- **Modular Architecture**: Support for multiple switch models with unified interface
- **Auto-Detection**: Automatically detects switch model type from web interface
- **VLAN Management**: Create, delete, and manage VLANs across different switch types
- **MAC Vendor Resolution**: Automatic MAC address to vendor lookup with rate limiting
- **Multiple Interface Options**: Command-line tool, web interface, and Python API
- **Advanced Authentication**: Supports JSON API and HTML form-based authentication
- **Comprehensive Data Extraction**: System info, port status, VLAN configuration, MAC tables, port configuration
- **Real-time Monitoring**: Live data updates and monitoring capabilities
- **Multiple Export Formats**: JSON, CSV, and Excel export options
- **Sleek Presentation**: Beautiful terminal and web interfaces with rich formatting
- **Error Handling**: Robust error handling and logging

## 📋 Supported Switch Models

| **Model** | **Interface Type** | **Authentication** | **VLAN Management** | **MAC Lookup** | **Port Config** |
|-----------|-------------------|-------------------|-------------------|----------------|----------------|
| **VM-S100-0800MS** | JSON API | Form POST | ✅ Full Support | ✅ With Rate Limiting | ✅ Speed/Duplex/VLAN |
| **SL-SWTG124AS** | HTML CGI | MD5 Cookie | ✅ Full Support | ✅ With Rate Limiting | ✅ Speed/Duplex/VLAN |
| **SL-SWTGW218AS** | HTML CGI | MD5 Cookie | ✅ Full Support | ✅ With Rate Limiting | ✅ Speed/Duplex/VLAN |

## 🛠 Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### List Available Switch Models

```bash
python3 modular_parser.py --list-models
```

### Basic Data Extraction

```bash
# Auto-detect switch model (recommended)
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin

# Specify switch model manually
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms
python3 modular_parser.py --url http://10.41.8.35 --username admin --password admin --model sl-swtg124as
```

### VLAN Management

```bash
# Create VLAN 99 with name "testIAC"
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --create-vlan "99:testIAC"

# Delete VLAN 99
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --delete-vlan "99"
```

### Export Data

```bash
# Export with custom filename
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --export my_switch_data

# Export with MAC vendor lookup delay
python3 modular_parser.py --url http://10.41.8.35 --username admin --password admin --model sl-swtg124as --mac-delay 2.0 --export sl_switch_data
```

## 📖 Usage Examples

### Command Line Interface

```bash
# Basic connection with auto-detection
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin

# Create VLAN and export data (auto-detection)
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --create-vlan "100:Production" --export production_vlan

# Delete VLAN (auto-detection)
python3 modular_parser.py --url http://10.41.8.35 --username admin --password admin --delete-vlan "100"

# Extract data with port configuration details
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --export switch_with_port_config
```

### Python API

```python
from switch_models import get_model, get_model_with_detection

# Auto-detect switch model (recommended)
switch = get_model_with_detection('http://10.41.8.33', 'admin', 'admin')

# Or specify model manually
switch = get_model('vm-s100-0800ms')('http://10.41.8.33', 'admin', 'admin')

# Authenticate and extract data
if switch.authenticate():
    data = switch.extract_all_data()
    switch.display_data(data)
    
    # Create VLAN
    switch.create_vlan(99, "testIAC")
    
    # Delete VLAN
    switch.delete_vlan(99)
```

## 🔍 Auto-Detection

The parser can automatically detect the switch model by analyzing the web interface. This eliminates the need to manually specify the `--model` parameter in most cases.

### How Auto-Detection Works

1. **Web Interface Analysis**: The parser examines the login page and other endpoints
2. **Model Indicators**: Looks for specific CSS files, JavaScript libraries, and HTML patterns
3. **Fallback Detection**: Tries multiple endpoints if initial detection fails
4. **Model Mapping**: Maps detected patterns to supported switch models

### Detection Indicators

| **Switch Model** | **Detection Indicators** |
|------------------|-------------------------|
| **VM-S100-0800MS** | `login-box.css`, `jquery.confirmon.css`, `ie=emulateie10`, `cgi/set.cgi` |
| **SL-SWTG124AS** | `md5.js`, `vlan.cgi?page=static`, `login.cgi`, model name in HTML |
| **SL-SWTGW218AS** | `sl-swtgw218as`, `slswtgw218as`, `login.cgi`, `md5.js` |

### Using Auto-Detection

```bash
# Auto-detect and connect
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin

# Manual model specification (if auto-detection fails)
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms
```

## 🔧 Command Line Options

### Main Options
- `--url`: Switch base URL (required)
- `--username`: Login username (required)
- `--password`: Login password (required)
- `--model`: Switch model (optional, auto-detects if not specified)
- `--mac-delay`: Delay between MAC vendor lookups in seconds (default: 1.0)
- `--export`: Export data to JSON file (optional)
- `--create-vlan`: Create VLAN with format "id:name" (optional)
- `--delete-vlan`: Delete VLAN by ID (optional)
- `--list-models`: List all available switch models

### Available Models
- `vm-s100-0800ms`: VM-S100-0800MS (JSON API)
- `sl-swtg124as`: SL-SWTG124AS (HTML Interface)
- `sl-swtgw218as`: SL-SWTGW218AS (HTML Interface)
- `vms1000800ms`: Alias for VM-S100-0800MS
- `slswtg124as`: Alias for SL-SWTG124AS
- `slswtgw218as`: Alias for SL-SWTGW218AS

## 📊 Data Structure

### System Information
- Model name and firmware version
- Uptime and MAC address
- IP configuration (IP, subnet, gateway)
- System metrics (CPU, memory, temperature)

### Port Status
- Port ID and status (up/down)
- Speed and duplex settings
- VLAN assignment
- Traffic statistics (bytes, packets)
- Port descriptions

### Port Configuration
- **Speed/Duplex Settings**: Auto-negotiation, manual speed/duplex configuration
- **Link Status**: Real-time port up/down status
- **Flow Control**: Flow control settings and status
- **VLAN Assignments**: Tagged and untagged VLAN memberships per port
- **PVID Configuration**: Port VLAN ID assignments
- **Port Mode**: Access/trunk port configurations

### VLAN Information
- VLAN ID and name
- Status and member ports
- VLAN descriptions
- Port assignments (tagged/untagged)

### MAC Address Tables
- Dynamic MAC addresses
- Static MAC addresses
- Vendor resolution with caching
- Port and VLAN assignments

## 🏗 Architecture

### Modular Design

```
ChineseSwitchParser/
├── switch_models/
│   ├── __init__.py          # Model registry and factory
│   ├── base.py              # Base switch model class
│   ├── vm_s100_0800ms.py    # VM-S100-0800MS implementation
│   ├── sl_swtg124as.py      # SL-SWTG124AS implementation
│   ├── template.py          # Template for new models
│   ├── config.py            # Configuration management
│   └── configs/             # Model-specific configurations
├── modular_parser.py        # Main CLI tool
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### Adding New Switch Models

1. Create a new model class in `switch_models/`
2. Inherit from `BaseSwitchModel`
3. Implement required methods:
   - `authenticate()`
   - `extract_all_data()`
   - `create_vlan()` (optional)
   - `delete_vlan()` (optional)
4. Register the model in `switch_models/__init__.py`
5. Create configuration file in `switch_models/configs/`

## 🔍 Troubleshooting

### Connection Issues
- Verify the switch URL is accessible
- Check username/password credentials
- Ensure the switch supports web-based management
- Try different authentication methods

### VLAN Management Issues
- Ensure you have administrative privileges
- Check VLAN ID is within valid range (1-4094)
- Verify VLAN name doesn't conflict with existing VLANs
- Some switches may require specific port assignments

### MAC Vendor Lookup Issues
- Check internet connectivity for vendor lookups
- Adjust `--mac-delay` if experiencing rate limiting
- Vendor data is cached to improve performance
- Some MAC addresses may not be in the vendor database

### Data Extraction Issues
- Some switches may have different API structures
- Check the model-specific implementation
- Use the discovery mode to explore switch capabilities
- Review logs for detailed error messages

## 🧪 Testing

The parser has been tested with the following switches:

- **VM-S100-0800MS**: `http://10.41.8.33` (JSON API)
- **SL-SWTG124AS**: `http://10.41.8.35` (HTML Interface)
- **SL-SWTGW218AS**: `http://10.41.8.36` (HTML Interface)

## 🤝 Contributing

This parser is designed to be extensible. To add support for new switch types:

1. Create a new model class in `switch_models/`
2. Implement the required methods from `BaseSwitchModel`
3. Add authentication logic specific to the switch
4. Implement data extraction methods
5. Add VLAN management if supported
6. Register the model in the factory
7. Create configuration file
8. Test thoroughly with the target switch

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Use the discovery mode to explore switch capabilities
4. Check the model-specific implementation
5. Verify switch compatibility with supported models

## 🎯 Roadmap

- [x] Implement switch discovery and auto-detection
- [ ] Add more switch models
- [ ] Implement port configuration management
- [ ] Add SNMP support
- [ ] Create web interface for VLAN management
- [ ] Add configuration backup/restore
- [ ] Add support for switch clusters/stacks