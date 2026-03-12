#!/usr/bin/env python3
"""Test _get_okr_column_ids method"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence

intel = PortfolioIntelligence()

print("🔍 Testing _get_okr_column_ids method...\n")
print("="*70)

# Get a project
projects = intel._get_all_portfolio_items()
test_project = next((p for p in projects if p['name'] == 'OpsCloud Pricing & Packaging'), None)

if test_project:
    print(f"📦 Testing with: {test_project['name']}\n")
    
    # Test the method
    okr_column_ids = intel._get_okr_column_ids(test_project)
    
    print(f"✅ Found {len(okr_column_ids)} OKR columns:")
    for col_id in okr_column_ids:
        print(f"   - {col_id}")
    
    print(f"\n🔍 Now testing _parse_board_relation for each column:\n")
    
    for col_id in okr_column_ids:
        linked_ids = intel._parse_board_relation(test_project, col_id)
        if linked_ids:
            print(f"   ✅ {col_id}: {len(linked_ids)} links → {linked_ids}")
        else:
            print(f"   ⚪ {col_id}: empty")
    
    print(f"\n🎯 Now testing get_project_status:\n")
    status = intel.get_project_status('OpsCloud Pricing & Packaging')
    print(f"   OKR Aligned: {status['okr_aligned']}")
    print(f"   OKR Count: {status['okr_count']}")
    print(f"   OKR Links: {status['okr_links']}")
else:
    print("❌ Project not found")