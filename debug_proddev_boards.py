#!/usr/bin/env python3
"""Debug ProdDev board loading issue"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.monday_client import MondayClient

client = MondayClient()

print("Testing board access...\n")

boards_to_test = [
    ('proddev_portfolio', '1476720991'),
    ('proddev_okr', '1476720990'),
    ('company_okr', '1476720989'),
]

for board_name, board_id in boards_to_test:
    print(f"🔍 Testing {board_name} (ID: {board_id})")
    print("-" * 60)
    
    try:
        # Make raw GraphQL request
        query = f"""
        query {{
          boards(ids: {board_id}) {{
            id
            name
            items_page(limit: 5) {{
              items {{
                id
                name
              }}
            }}
          }}
        }}
        """
        
        result = client._make_request(query)
        
        # Check response structure
        if 'data' in result and 'boards' in result['data']:
            boards = result['data']['boards']
            print(f"   Boards returned: {len(boards)}")
            
            if len(boards) == 0:
                print(f"   ❌ Board not found or no access!")
            else:
                board = boards[0]
                items = board['items_page']['items']
                print(f"   ✅ Board name: {board['name']}")
                print(f"   ✅ Items found: {len(items)}")
                
                if len(items) > 0:
                    print(f"   Sample item: {items[0]['name']}")
        else:
            print(f"   ❌ Unexpected response structure: {result}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()