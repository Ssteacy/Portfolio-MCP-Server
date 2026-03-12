#!/usr/bin/env python3
"""
Diagnostic script to see what each function actually returns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence
import json

pi = PortfolioIntelligence()

print("=" * 70)
print("DIAGNOSTIC: Checking return types")
print("=" * 70)

# 1. get_project_status
print("\n1. get_project_status:")
status = pi.get_project_status("OpsCloud Pricing & Packaging")
print(f"   Type: {type(status)}")
print(f"   Keys: {status.keys() if isinstance(status, dict) else 'N/A'}")
print(f"   Sample: {status}")

# 2. get_lead_follow_breakdown
print("\n2. get_lead_follow_breakdown:")
breakdown = pi.get_lead_follow_breakdown("OpsCloud Pricing & Packaging")
print(f"   Type: {type(breakdown)}")
if hasattr(breakdown, '__dict__'):
    print(f"   Attributes: {breakdown.__dict__}")
else:
    print(f"   Value: {breakdown}")

# 3. get_okr_contributing_projects
print("\n3. get_okr_contributing_projects:")
okr_items = pi.client.get_board_items('company_okr')
if okr_items:
    projects = pi.get_okr_contributing_projects(okr_items[0]['id'])
    print(f"   Type: {type(projects)}")
    print(f"   Length: {len(projects)}")
    if projects:
        print(f"   First item type: {type(projects[0])}")
        print(f"   First item: {projects[0]}")

# 4. identify_risks
print("\n4. identify_risks:")
risks = pi.identify_risks()
print(f"   Type: {type(risks)}")
print(f"   Length: {len(risks)}")
if risks:
    print(f"   First item type: {type(risks[0])}")
    print(f"   First item: {risks[0]}")

# 5. get_department_okr_progress
print("\n5. get_department_okr_progress:")
okr_progress = pi.get_department_okr_progress('proddev')
print(f"   Type: {type(okr_progress)}")
print(f"   Length: {len(okr_progress)}")
if okr_progress:
    print(f"   First item type: {type(okr_progress[0])}")
    print(f"   First item keys: {okr_progress[0].keys() if isinstance(okr_progress[0], dict) else 'N/A'}")
    print(f"   First item: {okr_progress[0]}")