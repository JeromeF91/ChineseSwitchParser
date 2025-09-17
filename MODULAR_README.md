# Modular Chinese Switch Parser

A modular parser system for Chinese network switches that supports multiple switch models with a unified interface.

## 🏗️ Architecture

The parser is organized into a modular structure:

```
switch_models/
├── __init__.py          # Model registry and factory
├── base.py              # Base switch model class
├── vm_s100_0800ms.py    # VM-S100-0800MS specific implementation
├── template.py          # Template for new models
├── config.py            # Configuration system
└── configs/             # Model configuration files
    └── vm-s100-0800ms.json
```

## 🚀 Quick Start

### Using the Modular Parser

```bash
# List available models
python3 modular_parser.py --list-models

# Parse a VM-S100-0800MS switch
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms

# Parse with custom MAC lookup delay
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --mac-delay 2.0

# Export data to file
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --export my_switch_data
```

## 📋 Available Models

- **vm-s100-0800ms**: VM-S100-0800MS switch (default)
- **vms1000800ms**: Alias for VM-S100-0800MS

## 🔧 Adding New Switch Models

### Method 1: Using the Template

1. Copy the template file:
   ```bash
   cp switch_models/template.py switch_models/your_model.py
   ```

2. Modify the template for your switch:
   - Update `get_model_name()` with your switch model name
   - Update `get_api_endpoints()` with your switch's API endpoints
   - Update `get_login_endpoint()` with your switch's login endpoint
   - Implement `authenticate()` method for your switch's authentication
   - Add any model-specific data processing methods

3. Register your model in `switch_models/__init__.py`:
   ```python
   from .your_model import YourModelClass
   
   MODELS = {
       'vm-s100-0800ms': VMS1000800MS,
       'your-model': YourModelClass,  # Add this line
       'default': VMS1000800MS
   }
   ```

### Method 2: Using Configuration Files

1. Create a configuration file in `switch_models/configs/your-model.json`:
   ```json
   {
     "model_name": "Your Model Name",
     "api_endpoints": {
       "system_info": "api/system",
       "port_info": "api/ports"
     },
     "login_endpoint": "api/login",
     "authentication_method": "form",
     "features": {
       "vlan_support": true,
       "mac_table_support": false
     }
   }
   ```

2. Create a model class that uses the configuration:
   ```python
   from .base import BaseSwitchModel
   from .config import ModelConfig
   
   class YourModel(BaseSwitchModel):
       def __init__(self, url, username, password, mac_lookup_delay=1.0):
           super().__init__(url, username, password, mac_lookup_delay)
           self.config = ModelConfig().get_model_config('your-model')
       
       def get_model_name(self):
           return self.config['model_name']
       
       def get_api_endpoints(self):
           return self.config['api_endpoints']
       
       # ... implement other methods
   ```

## 🎯 Features

### Base Switch Model Features
- **Authentication**: Common authentication patterns
- **MAC Vendor Lookup**: Resolve MAC addresses to vendors with rate limiting
- **Data Export**: Export data to JSON files
- **Rich Display**: Beautiful terminal output with progress indicators
- **Error Handling**: Comprehensive error handling and logging

### VM-S100-0800MS Specific Features
- **VLAN Management**: Extract VLAN configuration and port assignments
- **MAC Address Tables**: Dynamic and static MAC address extraction
- **Port Statistics**: Port count, bandwidth, and status information
- **System Information**: CPU, memory, and system details
- **Syslog**: System log extraction

## 🔧 Configuration

### Model Configuration Files

Each model can have a JSON configuration file in `switch_models/configs/`:

```json
{
  "model_name": "Model Name",
  "api_endpoints": {
    "endpoint_name": "api/path"
  },
  "login_endpoint": "api/login",
  "authentication_method": "form|json|basic",
  "features": {
    "vlan_support": true,
    "mac_table_support": true,
    "port_statistics": true,
    "system_info": true
  }
}
```

### CLI Options

- `--url`: Switch URL (required)
- `--username`: Username for authentication (required)
- `--password`: Password for authentication (required)
- `--model`: Switch model to use (default: vm-s100-0800ms)
- `--mac-delay`: Delay between MAC vendor lookups in seconds (default: 1.0)
- `--export`: Export data to JSON file (optional)
- `--list-models`: List all available models

## 🧪 Testing

Test the modular parser with your switch:

```bash
# Test with VM-S100-0800MS
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --export test_output

# Test with different MAC delay
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms --mac-delay 3.0
```

## 📝 Example Output

The parser provides rich terminal output with:
- Progress indicators for data extraction
- Formatted tables for VLAN and MAC information
- Color-coded status messages
- Cache statistics for MAC vendor lookups

## 🔄 Migration from Legacy Parser

To migrate from the old `final_parser.py`:

1. Use the same command-line arguments
2. Add `--model vm-s100-0800ms` to specify the model
3. The output format remains the same

```bash
# Old way
python3 final_parser.py --url http://10.41.8.33 --username admin --password admin

# New way
python3 modular_parser.py --url http://10.41.8.33 --username admin --password admin --model vm-s100-0800ms
```

## 🤝 Contributing

To add support for a new switch model:

1. Study the existing VM-S100-0800MS implementation
2. Use the template to create your model class
3. Test with your switch
4. Add configuration file if needed
5. Update documentation

## 📚 API Reference

### BaseSwitchModel

- `authenticate()`: Authenticate with the switch
- `get_data(endpoint)`: Get data from an API endpoint
- `extract_all_data()`: Extract all available data
- `display_data(data)`: Display data in formatted output
- `export_data(data, filename)`: Export data to JSON file

### Model-Specific Methods

Each model can implement additional methods for:
- Data processing
- Custom display formatting
- Model-specific authentication
- Specialized feature extraction
