#!/usr/bin/env python3
"""Check OKR links in portfolio items"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.monday_client import MondayClient

client = MondayClient()

print("🔍 Checking OKR links in portfolio items...\n")
print("="*70)

# Check a few items from ProdDev portfolio
board_id = "18400640667"

query = f"""
query {{
  boards(ids: {board_id}) {{
    name
    columns {{
      id
      title
      type
    }}
    items_page(limit: 5) {{
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
board = result['data']['boards'][0]

print(f"📋 Board: {board['name']}\n")

# Show all board_relation columns
print("🔗 Board Relation Columns:")
print("-"*70)
relation_columns = [col for col in board['columns'] if col['type'] == 'board-relation']
for col in relation_columns:
    print(f"  {col['id']:30} {col['title']}")

print(f"\n📦 Sample Items:")
print("-"*70)

for item in board['items_page']['items']:
    print(f"\n🎯 {item['name']}")
    
    # Check for board_relation columns with links
    for col_val in item['column_values']:
        if col_val['type'] == 'board-relation':
            linked_ids = col_val.get('linked_item_ids', [])
            if linked_ids:
                # Find column title
                col_title = next((c['title'] for c in board['columns'] if c['id'] == col_val['id']), col_val['id'])
                print(f"   ✅ {col_title}: {len(linked_ids)} links")
                print(f"      IDs: {linked_ids[:3]}{'...' if len(linked_ids) > 3 else ''}")