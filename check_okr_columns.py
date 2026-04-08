from core.monday_client import MondayClient
import json

mc = MondayClient()

# Get all portfolio board IDs
for dept, board_id in mc.boards.items():
    print(f"\n{'='*60}")
    print(f"{dept} Portfolio (ID: {board_id})")
    print('='*60)

    query = f"""
    query {{
      boards(ids: [{board_id}]) {{
        name
        columns {{
          id
          title
          type
        }}
      }}
    }}
    """

    result = mc.query(query)

    # Find board_relation columns
    if result and 'data' in result and 'boards' in result['data']:
        board = result['data']['boards'][0]
        okr_columns = [col for col in board['columns'] if col['type'] == 'board_relation']

        print(f"\nOKR Columns ({len(okr_columns)}):")
        for col in okr_columns:
            print(f"  - {col['title']}: {col['id']}")