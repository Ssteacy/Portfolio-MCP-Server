#!/usr/bin/env python3
"""Debug raw GraphQL response for OKR columns"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.monday_client import MondayClient
import json

client = MondayClient()

print("🔍 Checking raw GraphQL response for OKR columns...\n")
print("="*70)

board_id = "18400640667"

# Use the exact same query as get_board_items
query = f"""
query {{
  boards(ids: {board_id}) {{
    items_page(limit: 5) {{
      items {{
        id
        name
        column_values {{
          id
          text
          value
          type
          ... on BoardRelationValue {{
            linked_item_ids
            display_value
          }}
        }}
      }}
    }}
  }}
}}
"""

result = client._make_request(query)
items = result['data']['boards'][0]['items_page']['items']

print(f"🔍 Checking all board_relation columns:\n")

for item in items:
    print(f"🎯 {item['name']}")
    
    found_any = False
    for col_val in item['column_values']:
        if col_val['type'] == 'board_relation':  # Fixed: underscore not hyphen
            found_any = True
            linked_ids = col_val.get('linked_item_ids', [])
            if linked_ids:
                print(f"   ✅ Column {col_val['id']}: {len(linked_ids)} links")
                print(f"      Display: {col_val.get('display_value', 'None')}")
            else:
                print(f"   ⚪ Column {col_val['id']}: empty")
    
    if not found_any:
        print(f"   ❌ No board_relation columns found")
    print()