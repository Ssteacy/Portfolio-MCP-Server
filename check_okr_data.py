#!/usr/bin/env python3
"""Check if OKR columns have actual links"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.monday_client import MondayClient

client = MondayClient()

print("🔍 Checking OKR column data in ProdDev Portfolio...\n")
print("="*70)

board_id = "18400640667"

query = f"""
query {{
  boards(ids: {board_id}) {{
    items_page(limit: 10) {{
      items {{
        id
        name
        column_values {{
          id
          type
          text
          ... on BoardRelationValue {{
            display_value
            linked_item_ids
          }}
        }}
      }}
    }}
  }}
}}
"""

result = client._make_request(query)
items = result['data']['boards'][0]['items_page']['items']

print(f"📦 Checking {len(items)} items for OKR links...\n")

for item in items:
    print(f"🎯 {item['name']}")
    
    has_links = False
    for col_val in item['column_values']:
        if col_val['type'] == 'board-relation':
            linked_ids = col_val.get('linked_item_ids', [])
            if linked_ids:
                has_links = True
                print(f"   ✅ Column {col_val['id']}: {len(linked_ids)} links")
                print(f"      IDs: {linked_ids[:3]}")
    
    if not has_links:
        print(f"   ❌ No OKR links found")
    
    print()