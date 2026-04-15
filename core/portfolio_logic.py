"""
Portfolio Intelligence Logic
Core business logic for analyzing portfolio data from Monday.com
"""

import json
import os
from typing import Dict, List, Optional
from core.monday_client import MondayClient

import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Global in-memory cache
_CACHE = {
    'portfolios': {},  # {department: {board_id, items, last_refresh}}
    'okrs': {},        # {department: {board_id, objectives, key_results, last_refresh}}
    'metadata': {
        'cache_created': None,
        'ttl_seconds': 600,  # 10 minutes
        'total_portfolios': 0,
        'total_okrs': 0
    }
}

def _is_cache_valid() -> bool:
    """Check if cache exists and is within TTL"""
    if not _CACHE['metadata']['cache_created']:
        return False
    
    elapsed = time.time() - _CACHE['metadata']['cache_created']
    return elapsed < _CACHE['metadata']['ttl_seconds']

def _ensure_cache_fresh(monday_client) -> None:
    """
    Ensure cache is loaded and fresh.
    Refreshes if cache is stale or empty.
    """
    if not _is_cache_valid():
        _refresh_cache(monday_client)

def _refresh_cache(monday_client) -> Dict:
    """
    Fetch ALL portfolio and OKR data for all 8 boards
    This is the ONLY method that calls the Monday API
    """
    print("🔄 Refreshing cache...")
    start_time = time.time()
    
    # Portfolio board types
    portfolio_types = [
        'company_portfolio',
        'proddev_portfolio',
        'secit_portfolio',
        'finops_portfolio',
        'field_portfolio',
        'people_portfolio',
        'marketing_portfolio',
        'legal_portfolio'
    ]

    # OKR board types
    okr_types = [
        'company_okr',
        'proddev_okr',
        'secit_okr',
        'finops_okr',
        'field_okr',
        'people_okr',
        'marketing_okr',
        'legal_okr'
    ]
    
    # Fetch all portfolios
    total_portfolio_items = 0
    total_portfolio_subitems = 0
    for board_type in portfolio_types:
        try:
            data = monday_client.get_complete_portfolio_data(board_type)
            department = data['department']
            _CACHE['portfolios'][department] = {
                'board_id': data['board_id'],
                'board_name': data['board_name'],
                'items': data['items'],
                'total_items': data['total_items'],
                'total_subitems': data['total_subitems'],
                'last_refresh': time.time()
            }
            total_portfolio_items += data['total_items']
            total_portfolio_subitems += data['total_subitems']
            print(f"  ✅ {department}: {data['total_items']} items, {data['total_subitems']} subitems")
        except Exception as e:
            print(f"  ❌ Failed to fetch {board_type}: {e}")
            # Continue with other boards even if one fails
    
    # Fetch all OKRs
    total_objectives = 0
    total_key_results = 0
    for board_type in okr_types:
        try:
            data = monday_client.get_complete_okr_data(board_type)
            department = data['department']
            _CACHE['okrs'][department] = {
                'board_id': data['board_id'],
                'board_name': data['board_name'],
                'objectives': data['objectives'],
                'key_results': data['key_results'],
                'total_objectives': data['total_objectives'],
                'total_key_results': data['total_key_results'],
                'last_refresh': time.time()
            }
            total_objectives += data['total_objectives']
            total_key_results += data['total_key_results']
            print(f"  ✅ {department} OKRs: {data['total_objectives']} objectives, {data['total_key_results']} key results")
        except Exception as e:
            print(f"  ❌ Failed to fetch {board_type}: {e}")
    
    # Update metadata
    _CACHE['metadata']['cache_created'] = time.time()
    _CACHE['metadata']['total_portfolios'] = len(_CACHE['portfolios'])
    _CACHE['metadata']['total_okrs'] = len(_CACHE['okrs'])
    
    elapsed = time.time() - start_time
    print(f"✅ Cache refreshed in {elapsed:.2f}s")
    print(f"   📊 Total: {total_portfolio_items} projects, {total_portfolio_subitems} subitems, {total_objectives} objectives, {total_key_results} key results")
    
    return _CACHE

def get_cached_data(monday_client) -> Dict:
    """
    Get cached data, refreshing if necessary
    This is the entry point for all tools
    """
    if not _is_cache_valid():
        _refresh_cache(monday_client)
    
    return _CACHE

class PortfolioLogic:
    """Main class for portfolio analysis using cached data"""
    
    def __init__(self):
        self.client = MondayClient()
    
    def _get_cache(self) -> Dict:
        """Get cached data (refreshes if needed)"""
        return get_cached_data(self.client)
    
    def _get_column_value(self, column_values: List[Dict], column_id: str) -> Optional[str]:
        """Extract column value by ID"""
        for col in column_values:
            if col['id'] == column_id:
                return col.get('text') or col.get('value')
        return None
    
    def _parse_status(self, column_values: List[Dict]) -> str:
        """Parse status column"""
        status_text = self._get_column_value(column_values, 'status')
        return status_text if status_text else 'Not Set'
    
    def _parse_owner(self, column_values: List[Dict]) -> str:
        """Parse owner column"""
        owner_text = self._get_column_value(column_values, 'person')
        return owner_text if owner_text else 'Unassigned'
    
    def _parse_subitem_mirror_column(self, column_values: List[Dict], column_id: str) -> str:
        """Parse mirror column value from subitem"""
        for col in column_values:
            if col.get('id') == column_id:
                display_value = col.get('display_value', '').strip()
                return display_value if display_value else 'Not Set'
        return 'Not Set'
    
    def _get_okr_links(self, column_values: List[Dict]) -> set:
        """
        Extract all OKR item IDs from OKR link columns
        
        Returns:
            Set of linked OKR item IDs
        """
        okr_ids = set()
        
        # OKR link column IDs (adjust these to match your actual column IDs)
        okr_columns = [
            'board_relation__1',  # Company Objectives
            'board_relation0__1', # Company Key Results
            'board_relation1__1', # Department Objectives
            'board_relation2__1'  # Department Key Results
        ]
        
        for col in column_values:
            if col['id'] in okr_columns:
                # Parse linked_items from the column
                value = col.get('value')
                if value:
                    try:
                        parsed = json.loads(value) if isinstance(value, str) else value
                        if isinstance(parsed, dict) and 'linkedPulseIds' in parsed:
                            for linked_id in parsed['linkedPulseIds']:
                                okr_ids.add(str(linked_id['linkedPulseId']))
                    except:
                        pass
        
        return okr_ids
    
    def _parse_path_to_green(self, column_values: List[Dict]) -> str:
        """Parse path to green column"""
        ptg = self._get_column_value(column_values, '18390087085__long_text_mky296ss')
        return ptg if ptg else 'Not provided'
    
    def _parse_okr_links(self, column_values: List[Dict]) -> List[str]:
        """Parse OKR links from ALL board_relation columns"""
        from core.models import OKR_COLUMN_MAPPINGS
        
        okr_names = []
        
        # Get all OKR column IDs from mappings
        all_okr_columns = set()
        for portfolio_mapping in OKR_COLUMN_MAPPINGS.values():
            all_okr_columns.update(portfolio_mapping.keys())
        
        for col in column_values:
            # Check if this is an OKR column (board_relation type and in our mappings)
            if col.get('type') == 'board_relation' and col.get('id') in all_okr_columns:
                # Use display_value instead of parsing linkedPulseIds
                display_value = col.get('display_value', '')
                if display_value:
                    # Split by comma in case multiple OKRs are linked in one column
                    okr_names.extend([okr.strip() for okr in display_value.split(',')])
        
        return okr_names
    
    def _parse_milestone_column(self, column_values: List[Dict], column_type: str) -> str:
        """Parse milestone-specific columns by type (since IDs have board prefix)"""
        for col in column_values:
            col_type = col.get('type')
            
            # Match by type instead of ID
            if column_type == 'status' and col_type == 'status':
                return col.get('text', 'Not Set')
            elif column_type == 'people' and col_type == 'people':
                return col.get('text', 'Unassigned')
            elif column_type == 'date' and col_type == 'date':
                return col.get('text', 'Not Set')
            elif column_type == 'text' and col_type == 'text':
                return col.get('text', 'Not Set')
        
        return 'Not Set'
    
    def _is_milestone(self, subitem: Dict) -> bool:
        """Check if subitem is a milestone"""
        for col in subitem.get('column_values', []):
            # Check by type instead of ID (checkbox type is 'checkbox')
            if col.get('type') == 'checkbox':
                # Check the text value (simpler than parsing JSON)
                text = col.get('text', '')
                if text == 'v' or text.lower() == 'checked':
                    return True
                # Also check the value JSON as fallback
                value = col.get('value')
                if value:
                    try:
                        data = json.loads(value)
                        if data.get('checked') == True:
                            return True
                    except:
                        pass
        return False
    
    def _get_contributing_project_link(self, subitem: Dict) -> Optional[str]:
        """Get contributing project link from board_relation column"""
        for col in subitem.get('column_values', []):
            # Check if it's a board_relation type and has a display_value
            if col.get('type') == 'board_relation':
                display_value = col.get('display_value', '')
                if display_value:
                    # Return the display_value (the linked project name)
                    return display_value
        return None
    
    def _normalize_okr_query(self, query: str) -> str:
        """Normalize OKR query to handle common variations"""
        import re
        
        query = query.strip()
        
        # Replace leading zeros with letter O (e.g., "01" → "O1", "Company 01" → "Company O1")
        query = re.sub(r'\b0(\d+)\b', r'O\1', query)
        
        # Handle "Objective 1" → "O1"
        query = re.sub(r'\bObjective\s+(\d+)\b', r'O\1', query, flags=re.IGNORECASE)
        
        # Handle "Key Result 3" → "KR3"
        query = re.sub(r'\bKey\s+Result\s+(\d+)\b', r'KR\1', query, flags=re.IGNORECASE)
        
        return query
    
    def get_portfolio_summary(self, department: Optional[str] = None) -> Dict:
        """
        Get portfolio summary from cache
        
        Args:
            department: Optional department filter (e.g., 'proddev', 'secit')
        
        Returns:
            Dict with portfolio summary
        """
        cache = self._get_cache()
        
        if department:
            dept_lower = department.lower()
            if dept_lower not in cache['portfolios']:
                return {
                    'error': f"Department '{department}' not found",
                    'available_departments': list(cache['portfolios'].keys())
                }
            
            dept_data = cache['portfolios'][dept_lower]
            return {
                'department': dept_lower,
                'board_name': dept_data['board_name'],
                'total_projects': dept_data['total_items'],
                'total_subitems': dept_data['total_subitems'],
                'status_breakdown': self._get_status_breakdown(dept_data['items']),
                'tier_breakdown': self._get_tier_breakdown(dept_data['items'])
            }
        else:
            # All portfolios
            total_projects = sum(d['total_items'] for d in cache['portfolios'].values())
            total_subitems = sum(d['total_subitems'] for d in cache['portfolios'].values())
            
            all_items = []
            for dept_data in cache['portfolios'].values():
                all_items.extend(dept_data['items'])
            
            return {
                'total_portfolios': cache['metadata']['total_portfolios'],
                'total_projects': total_projects,
                'total_subitems': total_subitems,
                'departments': list(cache['portfolios'].keys()),
                'status_breakdown': self._get_status_breakdown(all_items),
                'tier_breakdown': self._get_tier_breakdown(all_items)
            }
    
    def _get_status_breakdown(self, items: List[Dict]) -> Dict[str, int]:
        """Get status breakdown from items"""
        breakdown = {}
        for item in items:
            status = self._parse_status(item['column_values'])
            breakdown[status] = breakdown.get(status, 0) + 1
        return breakdown
    
    def _get_tier_breakdown(self, items: List[Dict]) -> Dict[str, int]:
        """Get tier breakdown from items"""
        breakdown = {}
        for item in items:
            tier = self._get_column_value(item['column_values'], 'dropdown_mksq3s8t')
            tier = tier if tier else 'Not Set'
            breakdown[tier] = breakdown.get(tier, 0) + 1
        return breakdown
    
    def get_project_details(self, project_name: str, department: Optional[str] = None) -> Dict:
        """
        Get detailed project information from cache
        
        Args:
            project_name: Name of the project (partial match supported)
            department: Optional department filter
        
        Returns:
            Dict with project details
        """
        cache = self._get_cache()
        
        # Search for project
        departments_to_search = [department.lower()] if department else cache['portfolios'].keys()
        
        matches = []
        for dept in departments_to_search:
            if dept not in cache['portfolios']:
                continue
            
            for item in cache['portfolios'][dept]['items']:
                if project_name.lower() in item['name'].lower():
                    matches.append({
                        'department': dept,
                        'item': item
                    })
        
        if not matches:
            return {'error': f"No projects found matching '{project_name}'"}
        
        if len(matches) > 1:
            return {
                'error': f"Multiple projects found matching '{project_name}'",
                'matches': [{'name': m['item']['name'], 'department': m['department']} for m in matches]
            }
        
        # Single match found
        match = matches[0]
        item = match['item']
        
        # Count contributing projects and milestones
        contributing_projects = []
        milestones = []
        for subitem in item.get('subitems', []):
            if self._is_milestone(subitem):
                milestones.append(subitem['name'])
            else:
                link = self._get_contributing_project_link(subitem)
                if link:
                    contributing_projects.append(link)
        
        return {
            'name': item['name'],
            'department': match['department'],
            'status': self._parse_status(item['column_values']),
            'owner': self._parse_owner(item['column_values']),
            'path_to_green': self._parse_path_to_green(item['column_values']),
            'tier': self._get_column_value(item['column_values'], 'dropdown_mksq3s8t') or 'Not Set',
            'target_date': self._get_column_value(item['column_values'], 'date4') or 'Not Set',
            'okr_links': self._parse_okr_links(item['column_values']),
            'total_subitems': len(item.get('subitems', [])),
            'contributing_projects_count': len(contributing_projects),
            'milestones_count': len(milestones)
        }
    
    def get_contributing_projects(self, project_name: str, department: Optional[str] = None) -> Dict:
        """
        Get contributing projects for a given project from cache
        
        Args:
            project_name: Name of the parent project
            department: Optional department filter
        
        Returns:
            Dict with contributing projects
        """
        cache = self._get_cache()
        
        # Find the project
        departments_to_search = [department.lower()] if department else cache['portfolios'].keys()
        
        parent_item = None
        parent_dept = None
        for dept in departments_to_search:
            if dept not in cache['portfolios']:
                continue
            
            for item in cache['portfolios'][dept]['items']:
                if project_name.lower() in item['name'].lower():
                    parent_item = item
                    parent_dept = dept
                    break
            if parent_item:
                break
        
        if not parent_item:
            return {'error': f"Project '{project_name}' not found"}
        
        # Extract contributing projects (non-milestone subitems)
        contributing_projects = []
        for subitem in parent_item.get('subitems', []):
            if not self._is_milestone(subitem):
                link = self._get_contributing_project_link(subitem)
                if link:
                    contributing_projects.append({
                        'name': link,
                        'status': self._parse_subitem_mirror_column(subitem['column_values'], 'lookup_mm0esz60'),
                        'owner': self._parse_subitem_mirror_column(subitem['column_values'], 'lookup_mm0ek9bc'),
                        'target_date': self._parse_subitem_mirror_column(subitem['column_values'], 'lookup_mm0eq0da'),
                        'path_to_green': self._parse_subitem_mirror_column(subitem['column_values'], 'lookup_mm1474t8'),
                        'success_metrics': self._parse_subitem_mirror_column(subitem['column_values'], 'lookup_mm1vjwfn')
                    })
        
        return {
            'parent_project': parent_item['name'],
            'department': parent_dept,
            'contributing_projects': contributing_projects,
            'total_count': len(contributing_projects)
        }
    
    def get_milestones(self, project_name: str, department: Optional[str] = None) -> Dict:
        """
        Get milestones for a given project from cache
        
        Args:
            project_name: Name of the parent project
            department: Optional department filter
        
        Returns:
            Dict with milestones
        """
        cache = self._get_cache()
        
        # Find the project
        departments_to_search = [department.lower()] if department else cache['portfolios'].keys()
        
        parent_item = None
        parent_dept = None
        for dept in departments_to_search:
            if dept not in cache['portfolios']:
                continue
            
            for item in cache['portfolios'][dept]['items']:
                if project_name.lower() in item['name'].lower():
                    parent_item = item
                    parent_dept = dept
                    break
            if parent_item:
                break
        
        if not parent_item:
            return {'error': f"Project '{project_name}' not found"}
        
        # Extract milestones
        milestones = []
        for subitem in parent_item.get('subitems', []):
            if self._is_milestone(subitem):
                milestones.append({
                    'name': subitem['name'],
                    'status': self._parse_milestone_column(subitem['column_values'], 'status'),
                    'owner': self._parse_milestone_column(subitem['column_values'], 'people'),
                    'target_date': self._parse_milestone_column(subitem['column_values'], 'date'),
                    'success_metric': self._parse_milestone_column(subitem['column_values'], 'text')
                })
        
        return {
            'parent_project': parent_item['name'],
            'department': parent_dept,
            'milestones': milestones,
            'total_count': len(milestones)
        }
    
    def get_okr_links(self, project_name: str, department: Optional[str] = None) -> Dict:
        """
        Get OKR links for a given project from cache
        
        Args:
            project_name: Name of the project
            department: Optional department filter
        
        Returns:
            Dict with OKR links
        """
        cache = self._get_cache()
        
        # Find the project
        departments_to_search = [department.lower()] if department else cache['portfolios'].keys()
        
        parent_item = None
        parent_dept = None
        for dept in departments_to_search:
            if dept not in cache['portfolios']:
                continue
            
            for item in cache['portfolios'][dept]['items']:
                if project_name.lower() in item['name'].lower():
                    parent_item = item
                    parent_dept = dept
                    break
            if parent_item:
                break
        
        if not parent_item:
            return {'error': f"Project '{project_name}' not found"}
        
        okr_links = self._parse_okr_links(parent_item['column_values'])
        
        return {
            'project': parent_item['name'],
            'department': parent_dept,
            'okr_links': okr_links,
            'total_count': len(okr_links)
        }
    
    def search_projects(self, query: str, department: Optional[str] = None, status: Optional[str] = None) -> Dict:
        """
        Search projects from cache
        
        Args:
            query: Search query (matches project name)
            department: Optional department filter
            status: Optional status filter
        
        Returns:
            Dict with search results
        """
        cache = self._get_cache()
        
        departments_to_search = [department.lower()] if department else cache['portfolios'].keys()
        
        results = []
        for dept in departments_to_search:
            if dept not in cache['portfolios']:
                continue
            
            for item in cache['portfolios'][dept]['items']:
                # Name match
                if query.lower() not in item['name'].lower():
                    continue
                
                # Status filter
                item_status = self._parse_status(item['column_values'])
                if status and status.lower() not in item_status.lower():
                    continue
                
                results.append({
                    'name': item['name'],
                    'department': dept,
                    'status': item_status,
                    'owner': self._parse_owner(item['column_values']),
                    'tier': self._get_column_value(item['column_values'], 'dropdown_mksq3s8t') or 'Not Set'
                })
        
        return {
            'query': query,
            'filters': {
                'department': department,
                'status': status
            },
            'results': results,
            'total_count': len(results)
        }
    
    def _check_other_departments_for_okr(self, okr_query: str, exclude_results: list) -> Dict[str, Dict[str, any]]:
        """
        Check if other departments have projects linked to the same OKR query.
        Used for smart hybrid OKR search.
        
        Args:
            okr_query: The OKR search term (e.g., 'KR4')
            exclude_results: List of projects already found (to avoid duplicates)
        
        Returns:
            Dict mapping department names to {'count': int, 'okr_name': str}
        """
        from core.models import OKR_COLUMN_MAPPINGS
        
        cache = self._get_cache()
        other_matches = {}
        
        # Extract project IDs we've already found
        exclude_ids = {proj.get('name') + proj.get('department') for proj in exclude_results}
        
        # Search all departments
        all_departments = ['company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal']
        
        for dept in all_departments:
            if dept not in cache['portfolios']:
                continue
            
            dept_count = 0
            dept_okr_name = None
            portfolio = cache['portfolios'][dept]
            portfolio_type = f"{dept}_portfolio"
            column_mapping = OKR_COLUMN_MAPPINGS.get(portfolio_type, {})
            
            for item in portfolio['items']:
                # Skip if we already counted this project
                item_id = item.get('name') + dept
                if item_id in exclude_ids:
                    continue
                
                # Check if this project links to the OKR query
                for col in item.get('column_values', []):
                    if col.get('type') == 'board_relation':
                        display_value = col.get('display_value', '')
                        col_id = col.get('id')
                        
                        # Determine the OKR type for this column
                        col_okr_type = column_mapping.get(col_id)
                        
                        # Only count if this is a DEPARTMENT OKR column (not company)
                        # We want to find departments that have their OWN KR4, not projects linking to Company KR4
                        if col_okr_type not in ['dept_objective', 'dept_kr']:
                            continue
                        
                        if display_value and okr_query.lower() in display_value.lower():
                            # Capture ONLY the matching OKR line (not all linked OKRs)
                            # Only capture the OKR name once (from the first matching project)
                            if not dept_okr_name:
                                # Split by newline and comma to handle both formats
                                import re
                                # Split by newlines first, then by commas
                                lines = []
                                for line in display_value.split('\n'):
                                    lines.extend([l.strip() for l in line.split(',')])
                                
                                for line in lines:
                                    line_stripped = line.strip()
                                    # Check if the line contains the OKR query as a word boundary
                                    # This matches "KR2" in "KR2 - ..." or "Company KR2 - ..." but not "KR27"
                                    if re.search(rf'\b{re.escape(okr_query)}\b', line_stripped, re.IGNORECASE):
                                        dept_okr_name = line_stripped
                                        break
                            dept_count += 1
                            break  # Count each project only once
            
            if dept_count > 0:
                other_matches[dept] = {
                    'count': dept_count,
                    'okr_name': dept_okr_name
                }
        
        return other_matches
    
    def get_projects_by_okr(self, okr_query: str, department: str = None) -> Dict[str, Any]:
        """
        Get all projects linked to a specific OKR (reverse lookup).
        
        Args:
            okr_query: OKR identifier with optional department prefix
                    Examples: 'O1', 'Company O1', 'ProdDev KR3', 'KR2'
            department: Optional department filter for projects
        
        Returns:
            Dictionary with OKR name, department filter, total count, and matching projects
        """
        from core.models import OKR_COLUMN_MAPPINGS
        
        cache = self._get_cache()
        
        # Normalize the query to handle common variations
        okr_query = self._normalize_okr_query(okr_query)
        
        # Parse the OKR query to determine scope and search term
        okr_query_lower = okr_query.lower().strip()
        
        # Determine OKR scope (company vs department) and type (objective vs KR)
        okr_scope = None  # 'company_objective', 'company_kr', 'dept_objective', 'dept_kr'
        search_term = okr_query  # What to search for in display_value
        target_department = None  # Which department's OKRs to search (for dept objectives/KRs)
        
        # Check for explicit department prefix
        if okr_query_lower.startswith('company '):
            search_term = okr_query[8:].strip()  # Remove 'company ' prefix
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'company_kr'
            else:
                okr_scope = 'company_objective'
        elif okr_query_lower.startswith('proddev '):
            search_term = okr_query[8:].strip()
            target_department = 'proddev'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        elif okr_query_lower.startswith('secit '):
            search_term = okr_query[6:].strip()
            target_department = 'secit'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        elif okr_query_lower.startswith('finops '):
            search_term = okr_query[7:].strip()
            target_department = 'finops'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        elif okr_query_lower.startswith('field '):
            search_term = okr_query[6:].strip()
            target_department = 'field'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        elif okr_query_lower.startswith('people '):
            search_term = okr_query[7:].strip()
            target_department = 'people'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        elif okr_query_lower.startswith('marketing '):
            search_term = okr_query[10:].strip()
            target_department = 'marketing'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        elif okr_query_lower.startswith('legal '):
            search_term = okr_query[6:].strip()
            target_department = 'legal'
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'dept_kr'
            else:
                okr_scope = 'dept_objective'
        
        # DEFAULT TO COMPANY if no department prefix was specified
        if okr_scope is None and target_department is None:
            # Determine if it's an objective or KR based on the search term
            if 'kr' in search_term.lower() or 'key result' in search_term.lower():
                okr_scope = 'company_kr'
            else:
                okr_scope = 'company_objective'
        
        results = []
        matched_okr_name = None
        
        # Search through all portfolios
        for dept_name, portfolio in cache['portfolios'].items():
            # Apply department filter if specified (for projects, not OKRs)
            if department and dept_name.lower() != department.lower():
                continue
            
            # Get the portfolio board type (e.g., 'proddev_portfolio')
            portfolio_type = f"{dept_name.lower()}_portfolio"
            column_mapping = OKR_COLUMN_MAPPINGS.get(portfolio_type, {})
            
            for item in portfolio['items']:
                # Track matched OKR links for this project
                matched_links = []
                
                for col in item.get('column_values', []):
                    # Check if it's a board_relation column with display_value
                    if col.get('type') == 'board_relation':
                        col_id = col.get('id')
                        display_value = col.get('display_value', '')
                        
                        if not display_value:
                            continue
                        
                        # Determine the OKR type for this column
                        col_okr_type = column_mapping.get(col_id)
                        
                        # Check if this column matches our scope filter
                        scope_match = True
                        if okr_scope:
                            # If we have a scope, the column must match
                            if col_okr_type != okr_scope:
                                scope_match = False
                            
                            # For dept objectives/KRs, also check department match
                            if okr_scope in ['dept_objective', 'dept_kr'] and target_department:
                                # Only match if this is the target department's portfolio
                                if dept_name.lower() != target_department.lower():
                                    scope_match = False
                        
                        # Check if the search term matches and scope is correct
                        if scope_match and search_term.lower() in display_value.lower():
                            matched_links.append(display_value)
                            if not matched_okr_name:
                                # Add department prefix for clarity
                                dept_prefix = "Company" if okr_scope in ['company_objective', 'company_kr'] else target_department.title() if target_department else "Company"
                                matched_okr_name = f"{dept_prefix} {display_value}"
                
                # If we found matching OKR links, add this project to results
                if matched_links:
                    results.append({
                        'name': item.get('name', 'Unnamed'),
                        'department': dept_name,
                        'status': self._parse_status(item.get('column_values', [])),
                        'owner': self._parse_owner(item.get('column_values', [])),
                        'tier': self._get_column_value(item.get('column_values', []), 'dropdown_mksq3s8t') or 'Not Set',
                        'okr_links': ', '.join(matched_links)
                    })
        
        if not results:
            return {
                'error': f"No projects found linked to OKR matching '{okr_query}'. Try a different search term (e.g., 'O1', 'Company KR3', 'ProdDev O2')."
            }
        
        # Check for other departments with matching OKRs (smart hybrid)
        other_matches = self._check_other_departments_for_okr(search_term, results)
        
        # Determine which department to exclude from other_matches
        dept_to_exclude = None
        if target_department:
            # User specified a department OKR (e.g., "ProdDev KR4")
            dept_to_exclude = target_department
        elif department:
            # User filtered by department (e.g., department="proddev")
            dept_to_exclude = department.lower()
        elif not target_department:
            # No department specified, we defaulted to company
            dept_to_exclude = 'company'
        
        # Remove the current department from other_matches
        if dept_to_exclude and dept_to_exclude in other_matches:
            del other_matches[dept_to_exclude]
        
        return {
            'okr_name': matched_okr_name or okr_query,
            'okr_scope': okr_scope or 'all',
            'target_department': target_department,
            'department_filter': department,
            'total_count': len(results),
            'projects': results,
            'other_matches': other_matches  # New field for smart hybrid
        }
    
    def get_portfolio_health(self, department: Optional[str] = None) -> Dict:
        """
        Get portfolio health metrics from cache
        
        Args:
            department: Optional department filter
        
        Returns:
            Dict with health metrics
        """
        cache = self._get_cache()
        
        departments_to_analyze = [department.lower()] if department else cache['portfolios'].keys()
        
        all_items = []
        for dept in departments_to_analyze:
            if dept not in cache['portfolios']:
                continue
            all_items.extend(cache['portfolios'][dept]['items'])
        
        if not all_items:
            return {'error': 'No projects found'}
        
        # Calculate health metrics
        total = len(all_items)
        status_counts = {}
        for item in all_items:
            status = self._parse_status(item['column_values'])
            status_counts[status] = status_counts.get(status, 0) + 1
        
        green = status_counts.get('Green', 0)
        yellow = status_counts.get('Yellow', 0)
        red = status_counts.get('Red', 0)
        
        health_score = ((green * 100) + (yellow * 50) + (red * 0)) / total if total > 0 else 0
        
        return {
            'department': department if department else 'All',
            'total_projects': total,
            'status_breakdown': status_counts,
            'health_score': round(health_score, 2),
            'green_percentage': round((green / total * 100), 2) if total > 0 else 0,
            'yellow_percentage': round((yellow / total * 100), 2) if total > 0 else 0,
            'red_percentage': round((red / total * 100), 2) if total > 0 else 0
        }