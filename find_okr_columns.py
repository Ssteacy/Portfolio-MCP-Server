#!/usr/bin/env python3
"""Find OKR column names across all portfolio boards"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.monday_client import MondayClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MondayClient()

portfolio_boards = {
    'proddev': os.getenv('PRODDEV_PORTFOLIO_BOARD_ID'),
    'secit': os.getenv('SECIT_PORTFOLIO_BOARD_ID'),
    'finops': os.getenv('FINOPS_PORTFOLIO_BOARD_ID'),
    'field': os.getenv('FIELD_PORTFOLIO_BOARD_ID'),
    'people': os.getenv('PEOPLE_PORTFOLIO_BOARD_ID'),
    'marketing': os.getenv('MARKETING_PORTFOLIO_BOARD_ID'),
    'legal': os.getenv('LEGAL_PORTFOLIO_BOARD_ID'),
}

print("🔍 Finding OKR-related columns across all portfolio boards...\n")
print("="*70)

for dept, board_id in portfolio_boards.items():
    if not board_id:
        print(f"\n📋 {dept.upper()} Portfolio")
        print("-"*70)
        print(f"  ⚠️  Board ID not set in .env")
        continue
        
    print(f"\n📋 {dept.upper()} Portfolio (ID: {board_id})")
    print("-"*70)
    
    query = f"""
    query {{
      boards(ids: {board_id}) {{
        columns {{
          id
          title
          type
        }}
      }}
    }}
    """
    
    try:
        result = client._make_request(query)
        board = result['data']['boards'][0]
        
        # Look for columns with "OKR", "objective", "key result" in the name
        okr_columns = [col for col in board['columns'] 
                       if any(keyword in col['title'].lower() 
                             for keyword in ['okr', 'objective', 'key result', 'kr'])]
        
        if okr_columns:
            for col in okr_columns:
                print(f"  ✅ {col['title']:40} [{col['type']}] (ID: {col['id']})")
        else:
            print(f"  ❌ No OKR-related columns found")
    except Exception as e:
        print(f"  ❌ Error: {e}")