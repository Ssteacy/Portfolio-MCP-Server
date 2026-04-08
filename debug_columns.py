#!/usr/bin/env python3
"""Debug script to see actual column data"""

import sys
import json
from pathlib import Path

# Add the project to path
project_path = Path('/Users/ssteacy/monday-portfolio-mcp')
sys.path.insert(0, str(project_path))

from core.portfolio_logic import PortfolioIntelligence

pi = PortfolioIntelligence()

# Find the project
project = pi._find_project_by_name("OpsCloud Pricing & Packaging")

if project:
    print(f"Found project: {project['name']}")
    print(f"Department: {project.get('_department')}")
    print(f"\nColumn Values:")
    print("=" * 80)
    
    for col in project.get('column_values', []):
        print(f"\nColumn ID: {col['id']}")
        print(f"Type: {col.get('type', 'N/A')}")
        print(f"Text: {col.get('text', 'N/A')}")
        
        # Try to parse value JSON
        value_str = col.get('value')
        if value_str:
            try:
                value_json = json.loads(value_str)
                print(f"Value JSON: {json.dumps(value_json, indent=2)}")
            except:
                print(f"Value (raw): {value_str}")
        else:
            print("Value: None")
        print("-" * 80)
else:
    print("Project not found!")
#!/usr/bin/env python3
"""Debug script to see actual column data"""

import sys
import json
from pathlib import Path

# Add the project to path
project_path = Path('/Users/ssteacy/monday-portfolio-mcp')
sys.path.insert(0, str(project_path))

from core.portfolio_logic import PortfolioIntelligence

pi = PortfolioIntelligence()

# Find the project
project = pi._find_project_by_name("OpsCloud Pricing & Packaging")

if project:
    print(f"Found project: {project['name']}")
    print(f"Department: {project.get('_department')}")
    print(f"\nColumn Values:")
    print("=" * 80)
    
    for col in project.get('column_values', []):
        print(f"\nColumn ID: {col['id']}")
        print(f"Type: {col.get('type', 'N/A')}")
        print(f"Text: {col.get('text', 'N/A')}")
        
        # Try to parse value JSON
        value_str = col.get('value')
        if value_str:
            try:
                value_json = json.loads(value_str)
                print(f"Value JSON: {json.dumps(value_json, indent=2)}")
            except:
                print(f"Value (raw): {value_str}")
        else:
            print("Value: None")
        print("-" * 80)
else:
    print("Project not found!")
