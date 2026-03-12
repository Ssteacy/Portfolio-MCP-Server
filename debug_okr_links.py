#!/usr/bin/env python3
"""
Debug OKR board relations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence
import json


def debug_okr_links():
    """Debug the OKR board relation columns"""
    pi = PortfolioIntelligence()
    
    items = pi.client.get_board_items('portfolio')
    
    print("=" * 70)
    print("🔍 DEBUGGING OKR BOARD RELATIONS")
    print("=" * 70)
    
    # Find projects with OKR links
    for item in items[:10]:  # Check first 10 projects
        print(f"\n📊 Project: {item['name']}")
        
        okr_columns = [
            'board_relation_mkxv5m0t',  # Company Objective
            'board_relation_mm0pnjk4',  # Company Key Results
            'board_relation_mm0pp1zv',  # Prod Dev Objective
            'board_relation_mm0pntcx'   # Prod Dev Key Result
        ]
        
        has_links = False
        for col in item['column_values']:
            if col['id'] in okr_columns:
                text = col.get('text', '')
                value = col.get('value', '')
                
                if text or value:
                    has_links = True
                    print(f"\n  Column: {col['id']}")
                    print(f"  Text: {text}")
                    if value:
                        print(f"  Value (raw): {value[:300]}")
                        try:
                            parsed = json.loads(value)
                            print(f"  Value (parsed):")
                            print(json.dumps(parsed, indent=4)[:500])
                        except:
                            pass
        
        if not has_links:
            print("  ❌ No OKR links found")
        
        print("-" * 70)


if __name__ == "__main__":
    debug_okr_links()