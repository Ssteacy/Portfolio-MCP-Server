#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence
import json

pi = PortfolioIntelligence()

# Get all portfolio items
print("Loading portfolio data...")
all_items = pi._get_all_portfolio_items()

print(f"\n🔍 Checking status columns for at-risk projects:\n")

# Check the at-risk projects
target_names = ['Incident dot uh-oh', 'SeanTestFinOps', 'Permissions/Roles (ReBAC, RBAC)']

for item in all_items:
    if item['name'] in target_names:
        print("=" * 80)
        print(f"📦 {item['name']}")
        
        # Find status column
        for col in item.get('column_values', []):
            if col['id'] == 'status':
                print(f"\n   Raw column data:")
                print(f"   - text: {col.get('text')}")
                print(f"   - value: {col.get('value')}")
                
                if col.get('value'):
                    try:
                        value_json = json.loads(col['value'])
                        print(f"\n   Parsed JSON:")
                        print(f"   {json.dumps(value_json, indent=6)}")
                    except Exception as e:
                        print(f"   Error parsing JSON: {e}")
                break
        
        # Also show what _parse_status returns
        status_text, status_color = pi._parse_status(item)
        print(f"\n   _parse_status() returns:")
        print(f"   - text: {status_text}")
        print(f"   - color: {status_color}")
        print()