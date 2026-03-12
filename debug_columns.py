#!/usr/bin/env python3
"""
Debug ALL columns to find board relations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence
import json


def debug_all_columns():
    """Show ALL columns for first project"""
    pi = PortfolioIntelligence()
    
    items = pi.client.get_board_items('portfolio')
    
    print("=" * 70)
    print("🔍 DEBUGGING ALL COLUMNS - FIRST PROJECT")
    print("=" * 70)
    
    if items:
        first_item = items[0]
        print(f"\n📊 Project: {first_item['name']}\n")
        
        print("ALL COLUMNS (showing everything):")
        print("-" * 70)
        
        for col in first_item['column_values']:
            print(f"\nColumn ID: {col['id']}")
            print(f"Type: {col['type']}")
            print(f"Text: '{col.get('text', '')}'")
            
            value = col.get('value', '')
            if value:
                if len(value) < 200:
                    print(f"Value: {value}")
                else:
                    print(f"Value: {value[:200]}... (truncated)")
            else:
                print(f"Value: (empty)")
        
        print("\n" + "=" * 70)
        print("🔍 BOARD_RELATION TYPE COLUMNS")
        print("=" * 70)
        
        board_relation_cols = [col for col in first_item['column_values'] 
                               if col['type'] == 'board_relation']
        
        if board_relation_cols:
            print(f"\nFound {len(board_relation_cols)} board_relation columns:\n")
            for col in board_relation_cols:
                print(f"  Column ID: {col['id']}")
                print(f"  Text: '{col.get('text', '')}'")
                print(f"  Value: '{col.get('value', '')}'")
                print()
        else:
            print("\n❌ NO board_relation columns found!")
            print("The GraphQL query might not be returning this data.")
    
    print("\n" + "=" * 70)
    print("📋 ALL PORTFOLIO PROJECTS")
    print("=" * 70)
    
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['name']}")


if __name__ == "__main__":
    debug_all_columns()