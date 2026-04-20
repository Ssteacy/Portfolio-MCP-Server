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
import logging

logger = logging.getLogger(__name__)

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
        """Extract column value by ID - handles JSON format for long_text columns"""
        for col in column_values:
            if col['id'] == column_id:
                text_value = col.get('text')
                raw_value = col.get('value')
                
                # Prefer 'text' if available
                if text_value:
                    return text_value
                
                # Handle JSON format in 'value' (common for long_text columns when empty/recently edited)
                if raw_value and isinstance(raw_value, str) and raw_value.strip().startswith('{'):
                    try:
                        import json
                        data = json.loads(raw_value)
                        # Extract 'text' field from JSON
                        extracted_text = data.get('text', '').strip()
                        return extracted_text if extracted_text else None
                    except (json.JSONDecodeError, AttributeError, KeyError):
                        # If JSON parsing fails, return raw value as-is
                        pass
                
                return raw_value
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

    def _get_days_in_current_status(self, project_id: str, current_status: str, board_id: str) -> int:
        """
        Calculate how many days a project has been in its current status
        
        Args:
            project_id: The project's item ID
            current_status: The current status value (e.g., 'Red', 'Yellow')
            board_id: The board ID to query activity logs
        
        Returns:
            Number of days in current status, or 90+ if beyond log retention
        """
        from datetime import datetime, timedelta
        
        try:
            # Query activity logs for the last 90 days, filtered to this specific item
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(days=90)
            
            from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            logs_data = self.client.get_activity_logs(
                board_id=board_id,
                from_date=from_date_str,
                to_date=to_date_str,
                item_ids=[project_id],  # Filter to this specific item
                column_ids=["status"],   # Only get status changes
                limit=100
            )
            
            # Find the most recent status change (any status change, not just TO current status)
            most_recent_status_change = None
            most_recent_status_value = None
            
            for log in logs_data.get('activity_logs', []):
                if log.get('event') != 'update_column_value':
                    continue
                
                try:
                    data = json.loads(log['data']) if isinstance(log['data'], str) else log['data']
                except:
                    continue
                
                # Verify this is a status column change
                if data.get('column_id') != 'status':
                    continue
                
                # Parse the change date
                try:
                    change_date_str = log.get('created_at', '')
                    
                    # Monday.com returns timestamps as a long string where first 10 digits = Unix seconds
                    if change_date_str.isdigit() and len(change_date_str) >= 10:
                        from datetime import timezone
                        # Take first 10 digits as seconds since epoch
                        timestamp_seconds = int(change_date_str[:10])
                        change_date = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc).replace(tzinfo=None)
                    else:
                        # Fallback: ISO 8601 format
                        if '.' in change_date_str:
                            change_date = datetime.strptime(change_date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                        else:
                            change_date = datetime.strptime(change_date_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                except Exception as e:
                    logger.warning(f"Failed to parse date {log.get('created_at')}: {e}")
                    continue
                
                # Track the most recent status change
                if not most_recent_status_change or change_date > most_recent_status_change:
                    most_recent_status_change = change_date
                    # Extract the new status value
                    value_data = data.get('value', {})
                    if isinstance(value_data, str):
                        try:
                            value_data = json.loads(value_data)
                        except:
                            pass
                    most_recent_status_value = value_data.get('label', {}).get('text') if isinstance(value_data, dict) else None
            
            # Calculate days since most recent status change
            if most_recent_status_change:
                # Verify the most recent change matches current status
                if most_recent_status_value == current_status:
                    days_diff = (datetime.utcnow() - most_recent_status_change).days
                    return days_diff
                else:
                    # Most recent change was to a different status - something is wrong
                    # This means the project changed status AFTER our activity log window
                    # or the current status is stale
                    logger.warning(f"Project {project_id}: Most recent status change was to '{most_recent_status_value}', but current status is '{current_status}'")
                    return 0  # Assume very recent change
            else:
                # No status change found in last 90 days - been in this status for 90+ days
                return 90
        
        except Exception as e:
            logger.error(f"Error calculating days in status for project {project_id}: {e}")
            return 0

    def _get_contributing_projects_for_report(self, project_id: str) -> List[Dict[str, str]]:
        """
        Find all projects that depend on this project (contributing projects)
        
        Args:
            project_id: The project's item ID
        
        Returns:
            List of dicts with project name and department
        """
        cache = self._get_cache()
        contributing = []
        
        # Search all portfolios for subitems that link to this project
        for dept_name, portfolio in cache['portfolios'].items():
            for item in portfolio['items']:
                for subitem in item.get('subitems', []):
                    # Skip milestones
                    if self._is_milestone(subitem):
                        continue
                    
                    # Check if this subitem links to our project
                    for col in subitem.get('column_values', []):
                        if col.get('type') == 'board_relation':
                            value = col.get('value')
                            if value:
                                try:
                                    parsed = json.loads(value) if isinstance(value, str) else value
                                    if isinstance(parsed, dict) and 'linkedPulseIds' in parsed:
                                        for linked in parsed['linkedPulseIds']:
                                            if str(linked.get('linkedPulseId')) == str(project_id):
                                                contributing.append({
                                                    'name': item['name'],
                                                    'department': dept_name
                                                })
                                                break
                                except:
                                    pass
        
        return contributing

    def get_at_risk_projects_report(
        self,
        status_filter: Optional[List[str]] = None,
        group_by: str = "department",
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get at-risk projects report with escalation context
        
        Args:
            status_filter: List of statuses to include (default: ["Red"])
                        Options: ["Red"], ["Yellow"], ["Red", "Yellow"]
            group_by: How to group results - "department" or "okr" (default: "department")
            department: Optional department filter
        
        Returns:
            Dict with at-risk projects grouped and enriched with escalation context
        """
        from datetime import datetime
        
        # Default to Red only
        if not status_filter:
            status_filter = ["Red"]
        
        # Validate group_by
        if group_by not in ["department", "okr"]:
            return {'error': f"Invalid group_by value: {group_by}. Must be 'department' or 'okr'"}
        
        cache = self._get_cache()
        
        # Determine which departments to search
        departments_to_search = [department.lower()] if department else cache['portfolios'].keys()
        
        # Collect all at-risk projects
        at_risk_projects = []
        
        for dept in departments_to_search:
            if dept not in cache['portfolios']:
                continue
            
            portfolio = cache['portfolios'][dept]
            board_id = portfolio['board_id']
            
            for item in portfolio['items']:
                status = self._parse_status(item['column_values'])
                
                # Check if status matches filter
                if status not in status_filter:
                    continue
                
                # Get project details
                project_id = item['id']
                tier = self._get_column_value(item['column_values'], 'dropdown_mksq3s8t') or 'Not Set'
                
                # Calculate days in current status
                days_in_status = self._get_days_in_current_status(project_id, status, board_id)
                # Format days in status for display
                if days_in_status == 0:
                    days_text = "< 1 day"
                elif days_in_status >= 90:
                    days_text = "90+ days"
                else:
                    days_text = f"{days_in_status} days"
                
                # Get contributing projects (who depends on this)
                contributing = self._get_contributing_projects_for_report(project_id)
                
                # Get OKR links
                okr_links = self._parse_okr_links(item['column_values'])
                
                at_risk_projects.append({
                    'name': item['name'],
                    'id': project_id,
                    'department': dept,
                    'status': status,
                    'tier': tier,
                    'owner': self._parse_owner(item['column_values']),
                    'target_date': self._get_column_value(item['column_values'], 'date4') or 'Not Set',
                    'path_to_green': self._parse_path_to_green(item['column_values']),
                    'okr_links': okr_links,
                    'days_in_status': days_in_status,
                    'days_in_status_text': days_text,
                    'contributing_projects': contributing
                })
        
        if not at_risk_projects:
            return {
                'message': f"No projects found with status: {', '.join(status_filter)}",
                'filters': {
                    'status_filter': status_filter,
                    'department': department,
                    'group_by': group_by
                },
                'total_count': 0
            }
        
        # Sort projects: Tier 1 first, then by days_in_status (longest first)
        tier_order = {'Department -Tier 1': 1, 'Department -Tier 2': 2, 'Department -Tier 3': 3, 'Not Set': 4}
        at_risk_projects.sort(
            key=lambda p: (tier_order.get(p['tier'], 99), -p['days_in_status'])
        )
        
        # Group projects
        grouped = {}
        
        if group_by == "department":
            for proj in at_risk_projects:
                dept_key = proj['department']
                if dept_key not in grouped:
                    grouped[dept_key] = []
                grouped[dept_key].append(proj)
        
        elif group_by == "okr":
            for proj in at_risk_projects:
                if proj['okr_links']:
                    for okr in proj['okr_links']:
                        if okr not in grouped:
                            grouped[okr] = []
                        grouped[okr].append(proj)
                else:
                    # Projects with no OKR links
                    if 'No OKR Links' not in grouped:
                        grouped['No OKR Links'] = []
                    grouped['No OKR Links'].append(proj)
        
        # Format output
        formatted_groups = []
        for group_name, projects in grouped.items():
            formatted_groups.append({
                'group_name': group_name,
                'project_count': len(projects),
                'projects': projects
            })
        
        # Calculate summary stats
        tier_1_count = sum(1 for p in at_risk_projects if 'Tier 1' in p['tier'])
        long_red_count = sum(1 for p in at_risk_projects if p['days_in_status'] > 30)
        
        return {
            'report_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'filters': {
                'status_filter': status_filter,
                'department': department,
                'group_by': group_by
            },
            'summary': {
                'total_at_risk': len(at_risk_projects),
                'tier_1_count': tier_1_count,
                'long_duration_count': long_red_count,
                'departments_affected': len(set(p['department'] for p in at_risk_projects))
            },
            'groups': formatted_groups
        }

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
    
    def get_portfolio_changes(
        self,
        days_back: int = 30,
        department: Optional[str] = None,
        change_types: Optional[List[str]] = None,
        include_subitems: bool = False
    ) -> Dict:
        """
        Get portfolio changes from activity logs
        
        Args:
            days_back: Number of days to look back (default 30)
            department: Optional department filter
            change_types: Optional list of change types to filter:
                ['status', 'new', 'deleted', 'dates', 'okr_links', 'path_to_green', 'moved', 'owner', 'tier']
            include_subitems: Include subitem changes (milestones) - NOT YET IMPLEMENTED
        
        Returns:
            Dict with changes grouped by project
        """
        from datetime import datetime, timedelta
        import json
        
        # Calculate date range
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days_back)
        
        from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Determine which boards to query
        if department:
            dept_lower = department.lower()
            board_type = f"{dept_lower}_portfolio"
            board_id = self.client.boards.get(board_type)
            if not board_id:
                return {'error': f"Department '{department}' not found or board not configured"}
            boards_to_query = [(dept_lower, board_id)]
        else:
            # Query all portfolio boards
            boards_to_query = []
            for dept in ['company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal']:
                board_type = f"{dept}_portfolio"
                board_id = self.client.boards.get(board_type)
                if board_id:
                    boards_to_query.append((dept, board_id))
        
        # Column IDs we care about
        TRACKED_COLUMNS = {
            'status': 'Overall Status',
            'date4': 'Target Date',
            '18397281142__timerange_mm217rjj': 'Timeline',
            '18390087085__long_text_mky296ss': 'Path to Green',
            'person': 'Owner(s)',
            'dropdown_mksq3s8t': 'Portfolio Tier',
            'text4': 'Portfolio Tier (alt)',
            # OKR columns (board_relation type)
            'board_relation_mkxv5m0t': 'Company Objective',
            'board_relation_mm0pnjk4': 'Company Key Results',
            'board_relation_mm0pp1zv': 'Prod Dev Objective',
            'board_relation_mm0pntcx': 'Prod Dev Key Result',
        }
        
        # Event types we care about
        TRACKED_EVENTS = {
            'update_column_value': 'updated',
            'create_pulse': 'created',
            'delete_pulse': 'deleted',
            'move_pulse_from_group': 'moved'
        }
        
        # Collect all changes
        all_changes = []
        
        for dept, board_id in boards_to_query:
            try:
                logs_data = self.client.get_activity_logs(
                    board_id=board_id,
                    from_date=from_date_str,
                    to_date=to_date_str,
                    limit=250
                )
                
                for log in logs_data['activity_logs']:
                    event = log['event']
                    
                    # Skip events we don't track
                    if event not in TRACKED_EVENTS:
                        continue
                    
                    # Parse the data JSON
                    try:
                        data = json.loads(log['data'])
                    except:
                        continue
                    
                    pulse_id = data.get('pulse_id')
                    pulse_name = data.get('pulse_name')
                    
                    if not pulse_id or not pulse_name:
                        continue
                    
                    # Determine change type
                    change_type = None
                    change_field = None
                    old_value = None
                    new_value = None
                    
                    if event == 'create_pulse':
                        change_type = 'new'
                        change_field = 'Project Created'
                        new_value = pulse_name
                    
                    elif event == 'delete_pulse':
                        change_type = 'deleted'
                        change_field = 'Project Deleted'
                        old_value = pulse_name
                    
                    elif event == 'move_pulse_from_group':
                        change_type = 'moved'
                        source_group = data.get('source_group', {}).get('title', 'Unknown')
                        dest_group = data.get('dest_group', {}).get('title', 'Unknown')
                        change_field = 'Group'
                        old_value = source_group
                        new_value = dest_group
                    
                    elif event == 'update_column_value':
                        column_id = data.get('column_id')
                        column_title = data.get('column_title', 'Unknown')
                        column_type = data.get('column_type')
                        
                        # Determine change type based on column
                        if column_id == 'status':
                            change_type = 'status'
                            change_field = 'Overall Status'
                            old_value = data.get('previous_value', {}).get('label', {}).get('text') if data.get('previous_value') else None
                            new_value = data.get('value', {}).get('label', {}).get('text') if data.get('value') else None
                        
                        elif column_id in ['date4', '18397281142__timerange_mm217rjj']:
                            change_type = 'dates'
                            change_field = column_title
                            
                            if column_id == 'date4':
                                old_value = data.get('previous_value', {}).get('date') if data.get('previous_value') else None
                                new_value = data.get('value', {}).get('date') if data.get('value') else None
                            else:  # Timeline
                                prev = data.get('previous_value', {})
                                curr = data.get('value', {})
                                old_value = f"{prev.get('from')} to {prev.get('to')}" if prev and prev.get('from') else None
                                new_value = f"{curr.get('from')} to {curr.get('to')}" if curr and curr.get('from') else None
                        
                        elif column_id == '18390087085__long_text_mky296ss':
                            change_type = 'path_to_green'
                            change_field = 'Path to Green'
                            old_value = data.get('previous_value', {}).get('value') if data.get('previous_value') else None
                            new_value = data.get('value', {}).get('value') if data.get('value') else None
                        
                        elif column_type == 'board-relation':
                            change_type = 'okr_links'
                            change_field = column_title
                            old_value = data.get('previous_textual_value')
                            new_value = data.get('textual_value')
                        
                        elif column_id == 'person':
                            change_type = 'owner'
                            change_field = 'Owner(s)'
                            old_value = None  # Not easily parseable from activity log
                            new_value = data.get('textual_value')
                        
                        elif column_id in ['dropdown_mksq3s8t', 'text4']:
                            change_type = 'tier'
                            change_field = 'Portfolio Tier'
                            old_value = data.get('previous_textual_value')
                            new_value = data.get('textual_value') or (data.get('value', {}).get('chosenValues', [{}])[0].get('name') if data.get('value') else None)
                    
                    # Apply change_types filter
                    if change_types and change_type not in change_types:
                        continue
                    
                    # Add to changes
                    if change_type:
                        # Debug: log the raw data for OKR changes
                        if change_type == 'okr_links':
                            logger.info(f"OKR change debug - column: {column_title}, prev: {data.get('previous_textual_value')}, curr: {data.get('textual_value')}, full data: {data}")

                        all_changes.append({
                            'project_id': str(pulse_id),
                            'project_name': pulse_name,
                            'department': dept,
                            'change_type': change_type,
                            'field': change_field,
                            'old_value': old_value,
                            'new_value': new_value,
                            'timestamp': log['created_at'],
                            'user_id': log.get('user_id')
                        })
            
            except Exception as e:
                logger.error(f"Error fetching activity logs for {dept}: {e}")
                continue
        
        # Resolve all user IDs to names
        all_user_ids = list(set([c['user_id'] for c in all_changes if c.get('user_id')]))
        user_map = self.client.get_users(all_user_ids)
        
        # Group changes by project
        changes_by_project = {}
        for change in all_changes:
            project_key = f"{change['project_name']} ({change['department']})"
            if project_key not in changes_by_project:
                changes_by_project[project_key] = {
                    'project_name': change['project_name'],
                    'project_id': change['project_id'],
                    'department': change['department'],
                    'changes': []
                }
            
            # Simplified change record: what, from, to, who
            changes_by_project[project_key]['changes'].append({
                'what': change['field'],
                'from': change['old_value'],
                'to': change['new_value'],
                'who': user_map.get(change['user_id'], 'Unknown')
            })
        
        # Sort projects by number of changes (descending)
        sorted_projects = sorted(
            changes_by_project.values(),
            key=lambda x: len(x['changes']),
            reverse=True
        )
        
        # Identify critical changes
        critical_changes = []
        for proj in sorted_projects:
            for change in proj['changes']:
                # Critical: Status changed to Red or Yellow
                if 'Status' in change['what'] and change['to'] in ['Red', 'Yellow']:
                    critical_changes.append({
                        'project': proj['project_name'],
                        'reason': f"Status changed to {change['to']}",
                        'who': change['who']
                    })
                
                # Critical: OKR link removed
                if 'Objective' in change['what'] or 'Key Result' in change['what']:
                    if change['from'] and not change['to']:
                        critical_changes.append({
                            'project': proj['project_name'],
                            'reason': f"OKR link removed: {change['from']}",
                            'who': change['who']
                        })
                
                # Critical: Project deleted
                if change['what'] == 'Project Deleted':
                    critical_changes.append({
                        'project': proj['project_name'],
                        'reason': 'Project deleted',
                        'who': change['who']
                    })
        
        return {
            'date_range': {
                'from': from_date_str,
                'to': to_date_str,
                'days_back': days_back
            },
            'filters': {
                'department': department,
                'change_types': change_types
            },
            'total_changes': len(all_changes),
            'total_projects_changed': len(sorted_projects),
            'projects': sorted_projects,
            'critical_changes': critical_changes
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