"""
Monday.com API Client
Handles all interactions with the Monday.com GraphQL API
"""

import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class MondayClient:
    """Client for interacting with Monday.com API"""
    
    def __init__(self):
        self.api_token = os.getenv('MONDAY_API_TOKEN')
        if not self.api_token:
            raise ValueError("MONDAY_API_TOKEN not found in environment variables")
        
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        
        # Board configuration - all departments
        self.boards = {
            # Company-wide
            'company_okr': os.getenv('COMPANY_OKR_BOARD_ID'),
            'company_portfolio': os.getenv('COMPANY_PORTFOLIO_BOARD_ID'),
            'company_clean_agreements': os.getenv('COMPANY_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # Product Development
            'proddev_okr': os.getenv('PRODDEV_OKR_BOARD_ID'),
            'proddev_portfolio': os.getenv('PRODDEV_PORTFOLIO_BOARD_ID'),
            'proddev_capacity': os.getenv('PRODDEV_CAPACITY_BOARD_ID'),
            'proddev_clean_agreements': os.getenv('PRODDEV_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # Security and IT
            'secit_okr': os.getenv('SECIT_OKR_BOARD_ID'),
            'secit_portfolio': os.getenv('SECIT_PORTFOLIO_BOARD_ID'),
            'secit_capacity': os.getenv('SECIT_CAPACITY_BOARD_ID'),
            'secit_clean_agreements': os.getenv('SECIT_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # Finance and Operations
            'finops_okr': os.getenv('FINOPS_OKR_BOARD_ID'),
            'finops_portfolio': os.getenv('FINOPS_PORTFOLIO_BOARD_ID'),
            'finops_capacity': os.getenv('FINOPS_CAPACITY_BOARD_ID'),
            'finops_clean_agreements': os.getenv('FINOPS_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # Field
            'field_okr': os.getenv('FIELD_OKR_BOARD_ID'),
            'field_portfolio': os.getenv('FIELD_PORTFOLIO_BOARD_ID'),
            'field_capacity': os.getenv('FIELD_CAPACITY_BOARD_ID'),
            'field_clean_agreements': os.getenv('FIELD_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # People
            'people_okr': os.getenv('PEOPLE_OKR_BOARD_ID'),
            'people_portfolio': os.getenv('PEOPLE_PORTFOLIO_BOARD_ID'),
            'people_capacity': os.getenv('PEOPLE_CAPACITY_BOARD_ID'),
            'people_clean_agreements': os.getenv('PEOPLE_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # Marketing and Commercial
            'marketing_okr': os.getenv('MARKETING_OKR_BOARD_ID'),
            'marketing_portfolio': os.getenv('MARKETING_PORTFOLIO_BOARD_ID'),
            'marketing_capacity': os.getenv('MARKETING_CAPACITY_BOARD_ID'),
            'marketing_clean_agreements': os.getenv('MARKETING_CLEAN_AGREEMENTS_BOARD_ID'),
            
            # Legal
            'legal_okr': os.getenv('LEGAL_OKR_BOARD_ID'),
            'legal_portfolio': os.getenv('LEGAL_PORTFOLIO_BOARD_ID'),
            'legal_capacity': os.getenv('LEGAL_CAPACITY_BOARD_ID'),
            'legal_clean_agreements': os.getenv('LEGAL_CLEAN_AGREEMENTS_BOARD_ID'),
        }
        
        # Department mapping for easy lookup
        self.departments = {
            'company': ['company_okr', 'company_portfolio', 'company_clean_agreements'],
            'proddev': ['proddev_okr', 'proddev_portfolio', 'proddev_capacity', 'proddev_clean_agreements'],
            'secit': ['secit_okr', 'secit_portfolio', 'secit_capacity', 'secit_clean_agreements'],
            'finops': ['finops_okr', 'finops_portfolio', 'finops_capacity', 'finops_clean_agreements'],
            'field': ['field_okr', 'field_portfolio', 'field_capacity', 'field_clean_agreements'],
            'people': ['people_okr', 'people_portfolio', 'people_capacity', 'people_clean_agreements'],
            'marketing': ['marketing_okr', 'marketing_portfolio', 'marketing_capacity', 'marketing_clean_agreements'],
            'legal': ['legal_okr', 'legal_portfolio', 'legal_capacity', 'legal_clean_agreements'],
        }
        
        # Validate required boards are configured
        required_boards = ['company_okr', 'proddev_okr', 'proddev_portfolio']
        missing = [b for b in required_boards if not self.boards.get(b)]
        if missing:
            raise ValueError(f"Missing required board IDs: {missing}")
    
    def get_all_portfolio_boards(self) -> List[str]:
        """Get all portfolio board types across all departments"""
        return [
            'company_portfolio',
            'proddev_portfolio',
            'secit_portfolio',
            'finops_portfolio',
            'field_portfolio',
            'people_portfolio',
            'marketing_portfolio',
            'legal_portfolio'
        ]
    
    def get_all_okr_boards(self) -> List[str]:
        """Get all OKR board types across all departments"""
        return [
            'company_okr',
            'proddev_okr',
            'secit_okr',
            'finops_okr',
            'field_okr',
            'people_okr',
            'marketing_okr',
            'legal_okr'
        ]
    
    def get_all_capacity_boards(self) -> List[str]:
        """Get all capacity board types across all departments"""
        return [
            'proddev_capacity',
            'secit_capacity',
            'finops_capacity',
            'field_capacity',
            'people_capacity',
            'marketing_capacity',
            'legal_capacity'
        ]
    
    def get_all_clean_agreements_boards(self) -> List[str]:
        """Get all clean agreements board types across all departments"""
        return [
            'proddev_clean_agreements',
            'secit_clean_agreements',
            'finops_clean_agreements',
            'field_clean_agreements',
            'people_clean_agreements',
            'marketing_clean_agreements',
            'legal_clean_agreements'
        ]
    
    def get_department_boards(self, department: str) -> Dict[str, str]:
        """Get all board types for a specific department"""
        if department not in self.departments:
            raise ValueError(f"Unknown department: {department}. Valid: {list(self.departments.keys())}")
        
        board_types = self.departments[department]
        return {bt: self.boards[bt] for bt in board_types if self.boards.get(bt)}
    
    def get_department_from_board_type(self, board_type: str) -> Optional[str]:
        """Get department name from a board type (e.g., 'proddev_portfolio' -> 'proddev')"""
        for dept, board_types in self.departments.items():
            if board_type in board_types:
                return dept
        return None
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Make a GraphQL request to Monday.com API"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(
            self.api_url,
            json=payload,
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Monday.com API error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data
    
    def get_board_items(self, board_type: str, limit: int = 500) -> List[Dict]:
        """
        Fetch all items from a specific board
        
        Args:
            board_type: Key from self.boards (e.g., 'proddev_portfolio', 'secit_okr')
            limit: Maximum number of items to fetch
        
        Returns:
            List of items with their column values
        """
        board_id = self.boards.get(board_type)
        if not board_id:
            raise ValueError(f"Board type '{board_type}' not configured or board ID not set")
        
        query = f"""
        query {{
        boards(ids: {board_id}) {{
            items_page(limit: {limit}) {{
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
                subitems {{
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
        }}
        """
        
        result = self._make_request(query)
        items = result['data']['boards'][0]['items_page']['items']
        
        return items
    
    def get_board_columns(self, board_type: str) -> List[Dict]:
        """
        Fetch column metadata for a specific board
        
        Args:
            board_type: Key from self.boards (e.g., 'proddev_portfolio')
        
        Returns:
            List of columns with id, title, and type
        """
        board_id = self.boards.get(board_type)
        if not board_id:
            raise ValueError(f"Board type '{board_type}' not configured or board ID not set")
        
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
        
        result = self._make_request(query)
        return result['data']['boards'][0]['columns']
    
    def get_okr_column_ids(self, board_type: str) -> Dict[str, str]:
        """
        Detect OKR-related board_relation columns for a portfolio board
        
        Args:
            board_type: Portfolio board type (e.g., 'proddev_portfolio')
        
        Returns:
            Dict mapping column purpose to column ID:
            {
                'company_objective': 'board_relation_mkxv5m0t',
                'company_key_result': 'board_relation_mm0pnjk4',
                'dept_objective': 'board_relation_mm0pp1zv',
                'dept_key_result': 'board_relation_mm0pntcx'
            }
        """
        columns = self.get_board_columns(board_type)
        okr_columns = {}
        
        # Get department name from board type
        dept = self.get_department_from_board_type(board_type)
        
        for col in columns:
            if col['type'] != 'board_relation':
                continue
            
            title_lower = col['title'].lower()
            
            # Company Objective (always the same ID across all boards)
            if 'company' in title_lower and 'objective' in title_lower:
                okr_columns['company_objective'] = col['id']
            
            # Company Key Result(s)
            elif 'company' in title_lower and ('key result' in title_lower or 'kr' in title_lower):
                okr_columns['company_key_result'] = col['id']
            
            # Department-specific Objective
            elif dept and dept in title_lower and 'objective' in title_lower:
                okr_columns['dept_objective'] = col['id']
            
            # Department-specific Key Result
            elif dept and dept in title_lower and ('key result' in title_lower or 'kr' in title_lower):
                okr_columns['dept_key_result'] = col['id']
            
            # Handle special cases like "Sec and IT"
            elif 'sec and it' in title_lower or 'sec&it' in title_lower:
                if 'objective' in title_lower:
                    okr_columns['dept_objective'] = col['id']
                elif 'key result' in title_lower or 'kr' in title_lower:
                    okr_columns['dept_key_result'] = col['id']
        
        return okr_columns
    
    def get_portfolio_items_with_okrs(self, board_type: str, limit: int = 100) -> List[Dict]:
        """
        Fetch portfolio items with OKR links efficiently using linked_items
        
        Args:
            board_type: Portfolio board type (e.g., 'proddev_portfolio')
            limit: Maximum items per page
        
        Returns:
            List of items with parsed OKR information
        """
        board_id = self.boards.get(board_type)
        if not board_id:
            raise ValueError(f"Board type '{board_type}' not configured")
        
        # Get OKR column IDs for this board
        okr_cols = self.get_okr_column_ids(board_type)
        
        # Build column_ids list for the query
        column_ids = [
            'name',
            'status',
            okr_cols.get('company_objective'),
            okr_cols.get('company_key_result'),
            okr_cols.get('dept_objective'),
            okr_cols.get('dept_key_result')
        ]
        # Filter out None values
        column_ids = [cid for cid in column_ids if cid]
        column_ids_str = ', '.join([f'"{cid}"' for cid in column_ids])
        
        query = f"""
        query {{
        boards(ids: [{board_id}]) {{
            items_page(limit: {limit}) {{
            cursor
            items {{
                id
                name
                column_values(ids: [{column_ids_str}]) {{
                id
                text
                type
                ... on BoardRelationValue {{
                    linked_items {{
                    id
                    name
                    }}
                }}
                }}
                subitems {{
                id
                name
                column_values {{
                    id
                    text
                    value
                    type
                }}
                }}
            }}
            }}
        }}
        }}
        """
        
        result = self._make_request(query)
        items_page = result['data']['boards'][0]['items_page']
        items = items_page['items']
        
        # Parse OKR links from linked_items
        for item in items:
            item['okr_links'] = {
                'company_objectives': [],
                'company_key_results': [],
                'dept_objectives': [],
                'dept_key_results': []
            }
            
            for col_val in item['column_values']:
                col_id = col_val['id']
                
                # Extract linked OKR names
                if col_val.get('linked_items'):
                    okr_names = [li['name'] for li in col_val['linked_items']]
                    
                    if col_id == okr_cols.get('company_objective'):
                        item['okr_links']['company_objectives'] = okr_names
                    elif col_id == okr_cols.get('company_key_result'):
                        item['okr_links']['company_key_results'] = okr_names
                    elif col_id == okr_cols.get('dept_objective'):
                        item['okr_links']['dept_objectives'] = okr_names
                    elif col_id == okr_cols.get('dept_key_result'):
                        item['okr_links']['dept_key_results'] = okr_names
        
        return items
    
    def get_complete_portfolio_data(self, board_type: str, limit: int = 100) -> Dict:
        """
        Fetch ALL data for a portfolio board in one comprehensive query
        
        Args:
            board_type: Portfolio board type (e.g., 'proddev_portfolio')
            limit: Maximum items per page (default 100)
        
        Returns:
            Dict with structure:
            {
                'board_id': str,
                'board_name': str,
                'department': str,
                'items': List[Dict],  # All parent items with nested subitems
                'total_items': int,
                'total_subitems': int
            }
        """
        board_id = self.boards.get(board_type)
        if not board_id:
            raise ValueError(f"Board type '{board_type}' not configured or board ID not set")
        
        department = self.get_department_from_board_type(board_type)
        
        query = f"""
        query {{
        boards(ids: [{board_id}]) {{
            id
            name
            items_page(limit: {limit}) {{
            cursor
            items {{
                id
                name
                created_at
                column_values {{
                id
                type
                text
                value
                ... on StatusValue {{
                    label
                    index
                }}
                ... on PeopleValue {{
                    persons_and_teams {{
                    id
                    kind
                    }}
                }}
                ... on DateValue {{
                    date
                }}
                ... on BoardRelationValue {{
                    display_value
                    linked_item_ids
                    linked_items {{
                    id
                    name
                    }}
                }}
                }}
                subitems {{
                id
                name
                column_values {{
                    id
                    type
                    text
                    value
                    ... on StatusValue {{
                    label
                    index
                    }}
                    ... on MirrorValue {{
                    display_value
                    }}
                    ... on BoardRelationValue {{
                    display_value
                    linked_item_ids
                    linked_items {{
                        id
                        name
                    }}
                    }}
                    ... on PeopleValue {{
                    persons_and_teams {{
                        id
                        kind
                    }}
                    }}
                    ... on DateValue {{
                    date
                    }}
                }}
                }}
            }}
            }}
        }}
        }}
        """
        
        result = self._make_request(query)
        board_data = result['data']['boards'][0]
        items = board_data['items_page']['items']
        
        # Count subitems
        total_subitems = sum(len(item.get('subitems', [])) for item in items)
        
        return {
            'board_id': board_data['id'],
            'board_name': board_data['name'],
            'department': department,
            'items': items,
            'total_items': len(items),
            'total_subitems': total_subitems
        }    
    
    def get_complete_okr_data(self, board_type: str, limit: int = 100) -> Dict:
        """
        Fetch ALL OKR data (Objectives + Key Results) in one query
        
        Args:
            board_type: OKR board type (e.g., 'proddev_okr')
            limit: Maximum items per page (default 100)
        
        Returns:
            Dict with structure:
            {
                'board_id': str,
                'board_name': str,
                'department': str,
                'objectives': List[Dict],  # Parent items (Objectives)
                'key_results': List[Dict],  # Subitems (Key Results)
                'total_objectives': int,
                'total_key_results': int
            }
        """
        board_id = self.boards.get(board_type)
        if not board_id:
            raise ValueError(f"Board type '{board_type}' not configured or board ID not set")
        
        department = self.get_department_from_board_type(board_type)
        
        query = f"""
        query {{
        boards(ids: [{board_id}]) {{
            id
            name
            items_page(limit: {limit}) {{
            cursor
            items {{
                id
                name
                created_at
                column_values {{
                id
                type
                text
                value
                }}
                subitems {{
                id
                name
                column_values {{
                    id
                    type
                    text
                    value
                }}
                }}
            }}
            }}
        }}
        }}
        """
        
        result = self._make_request(query)
        board_data = result['data']['boards'][0]
        items = board_data['items_page']['items']
        
        # Separate objectives (parent items) and key results (subitems)
        objectives = []
        key_results = []
        
        for item in items:
            # Add objective
            objective = {
                'id': item['id'],
                'name': item['name'],
                'created_at': item['created_at'],
                'column_values': item['column_values']
            }
            objectives.append(objective)
            
            # Add key results with parent reference
            for subitem in item.get('subitems', []):
                key_result = {
                    'id': subitem['id'],
                    'name': subitem['name'],
                    'parent_objective_id': item['id'],
                    'parent_objective_name': item['name'],
                    'column_values': subitem['column_values']
                }
                key_results.append(key_result)
        
        return {
            'board_id': board_data['id'],
            'board_name': board_data['name'],
            'department': department,
            'objectives': objectives,
            'key_results': key_results,
            'total_objectives': len(objectives),
            'total_key_results': len(key_results)
        }
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Fetch a specific item by its ID"""
        query = f"""
        query {{
          items(ids: {item_id}) {{
            id
            name
            board {{
              id
              name
            }}
            column_values {{
              id
              title
              text
              value
              type
              ... on BoardRelationValue {{
                linked_item_ids
                display_value
              }}
            }}
            subitems {{
              id
              name
              column_values {{
                id
                text
                value
                type
              }}
            }}
          }}
        }}
        """
        
        result = self._make_request(query)
        items = result['data']['items']
        
        return items[0] if items else None