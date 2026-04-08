#!/usr/bin/env python3
"""
Debug script to check the actual status values for at-risk projects
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence
import json

# Initialize
pi = PortfolioIntelligence()

# Get at-risk projects
print("=" * 80)
print("🔍 DEBUGGING AT-RISK PROJECT STATUSES")
print("=" * 80)

risks = pi.identify_risks()

print(f"\n📋 Risk data keys: {risks.keys()}")
print(f"📋 Total risk signals: {risks.get('total_risk_signals', 'N/A')}")

# Check the structure
at_risk_projects = risks.get('at_risk_projects', [])
print(f"📋 At-risk projects type: {type(at_risk_projects)}")
print(f"📋 At-risk projects content: {at_risk_projects}")
print()

# Let's just iterate through all portfolio items and check their status
print("=" * 80)
print("🔍 CHECKING ALL PROJECTS WITH RED/YELLOW STATUS")
print("=" * 80)

for board_name, items in pi.monday_client.portfolio_items.items():
    for item in items:
        # Parse the status
        status_text, status_color = pi._parse_status(item)
        
        # Only show red/yellow or items flagged as at-risk
        if status_color in ['red', 'yellow'] or pi._is_at_risk(item):
            print("-" * 80)
            print(f"📦 Project: {item['name']}")
            print(f"   Board: {board_name}")
            print(f"   Parsed Status: {status_text} ({status_color})")
            print(f"   At Risk: {pi._is_at_risk(item)}")
            
            # Find the status column
            status_col = None
            for col in item.get('column_values', []):
                if col['id'] == 'status':
                    status_col = col
                    break
            
            if status_col:
                print(f"\n   📋 RAW STATUS COLUMN DATA:")
                print(f"      Column ID: {status_col['id']}")
                print(f"      Type: {status_col['type']}")
                print(f"      Text: {status_col.get('text', 'N/A')}")
                
                # Parse the value JSON
                try:
                    value_json = json.loads(status_col['value']) if status_col['value'] else None
                    print(f"      Value JSON: {json.dumps(value_json, indent=8)}")
                except:
                    print(f"      Value (raw): {status_col['value']}")
            else:
                print(f"   ❌ No 'status' column found!")
                print(f"   Available columns: {[col['id'] for col in item.get('column_values', [])]}")
            
            print()

print("=" * 80)
print("✅ DEBUG COMPLETE")
print("=" * 80)