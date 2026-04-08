"""
Portfolio Intelligence Logic
Core business logic for analyzing portfolio data from Monday.com
"""

import json
import os
from typing import Dict, List, Optional
from core.monday_client import MondayClient
from core.models import LeadFollowBreakdown


class PortfolioIntelligence:
    """Main class for portfolio analysis and intelligence"""
    
    def __init__(self):
        self.client = MondayClient()
        self._portfolio_cache = {}
        self._okr_cache = {}
        
        # Column ID mappings from environment
        self.col_owner = os.getenv('COLUMN_OWNER', 'person')
        self.col_editor = os.getenv('COLUMN_EDITOR', 'multiple_person_mkt3t62e')
        self.col_status = os.getenv('COLUMN_STATUS', 'status')
        self.col_path_to_green = os.getenv('COLUMN_PATH_TO_GREEN', '18390087085__long_text_mky296ss')
        self.col_portfolio_tier = os.getenv('COLUMN_PORTFOLIO_TIER', 'dropdown_mksq3s8t')
        self.col_theme = os.getenv('COLUMN_THEME', 'dropdown_mm16pfa8')
        self.col_product = os.getenv('COLUMN_PRODUCT', 'dropdown_mm1tknya')
        self.col_target_date = os.getenv('COLUMN_TARGET_DATE', 'date4')
    
    def _get_all_portfolio_items(self, refresh: bool = False) -> List[Dict]:
        """
        Get all portfolio items across all departments with OKR links
        
        Args:
            refresh: Force refresh from API instead of using cache
        
        Returns:
            List of all portfolio items with department metadata and parsed OKR links
        """
        if self._portfolio_cache and not refresh:
            return self._portfolio_cache
        
        all_items = []
        
        for board_type in self.client.get_all_portfolio_boards():
            department = self.client.get_department_from_board_type(board_type)
            
            try:
                # Use the new optimized method with linked_items
                items = self.client.get_portfolio_items_with_okrs(board_type)
                
                # Add department metadata to each item
                for item in items:
                    item['_department'] = department
                    item['_board_type'] = board_type
                
                all_items.extend(items)
                print(f"✅ Loaded {len(items)} items from {department} portfolio")
            
            except Exception as e:
                print(f"⚠️  Warning: Could not load {board_type}: {e}")
                continue
        
        self._portfolio_cache = all_items
        return all_items
    
    def _get_all_okr_items(self, refresh: bool = False) -> Dict[str, Dict]:
        """
        Get all OKR items across all departments, structured as a lookup map
        
        Returns:
            Dict mapping item_id -> {item data with objectives and key results}
        """
        if self._okr_cache and not refresh:
            return self._okr_cache
        
        okr_map = {}
        
        for board_type in self.client.get_all_okr_boards():
            department = self.client.get_department_from_board_type(board_type)
            
            try:
                items = self.client.get_board_items(board_type)
                
                for item in items:
                    item['_department'] = department
                    item['_board_type'] = board_type
                    okr_map[item['id']] = item
                    
                    # Also add subitems (Key Results) to the map
                    if item.get('subitems'):
                        for subitem in item['subitems']:
                            subitem['_parent_okr'] = item['name']
                            subitem['_department'] = department
                            subitem['_board_type'] = board_type
                            okr_map[subitem['id']] = subitem
                
                print(f"✅ Loaded {len(items)} OKRs from {department}")
            
            except Exception as e:
                print(f"⚠️  Warning: Could not load {board_type}: {e}")
                continue
        
        self._okr_cache = okr_map
        return okr_map
    
    def find_okr_by_name(self, okr_name: str, department: Optional[str] = None) -> Optional[Dict]:
        """
        Find an OKR by name (partial match) across all OKR boards
        
        Args:
            okr_name: OKR name to search for (partial match)
            department: Optional department filter
        
        Returns:
            Matching OKR item or None
        """
        okr_map = self._get_all_okr_items()
        
        # Filter by department if specified
        if department:
            dept_lower = department.lower()
            okr_map = {k: v for k, v in okr_map.items() 
                      if v.get('_department', '').lower() == dept_lower}
        
        # Search for matching OKR
        okr_name_lower = okr_name.lower()
        for okr_id, okr_item in okr_map.items():
            if okr_name_lower in okr_item['name'].lower():
                return {'id': okr_id, **okr_item}
        
        return None
    
    def _get_column_value(self, item: Dict, column_id: str) -> Optional[str]:
        """Extract a column value by ID from an item"""
        for col in item.get('column_values', []):
            if col['id'] == column_id:
                return col.get('text', '')
        return None
    
    def _get_column_json(self, item: Dict, column_id: str) -> Optional[Dict]:
        """Extract a column's JSON value by ID"""
        for col in item.get('column_values', []):
            if col['id'] == column_id:
                value_str = col.get('value')
                if value_str:
                    try:
                        return json.loads(value_str)
                    except json.JSONDecodeError:
                        return None
        return None
    
    def _parse_status(self, item: Dict) -> tuple[str, str]:
        """Parse status column to get label and color"""
        # First, find the status column to get the text
        status_text = 'No status'
        status_col = None
        
        for col in item.get('column_values', []):
            if col['id'] == self.col_status:
                status_col = col
                status_text = col.get('text', 'No status')
                break
        
        # Now parse the JSON for the color
        if status_col and status_col.get('value'):
            try:
                status_json = json.loads(status_col['value'])
                # Map Monday.com color indices to names
                color_map = {0: 'gray', 1: 'green', 2: 'yellow', 3: 'red'}
                color_index = status_json.get('index', 0)
                color = color_map.get(color_index, 'gray')
                return status_text, color
            except:
                pass
        
        return status_text, 'gray'
    
    def _is_at_risk(self, status_text: str) -> bool:
        """Determine if a project is at risk based on status text"""
        at_risk_statuses = ['Red', 'Yellow']
        return status_text in at_risk_statuses
    
    def _get_okr_links_from_item(self, project: Dict) -> List[str]:
        """
        Extract OKR link names from a project item (uses pre-parsed okr_links)
        
        Args:
            project: The Monday.com item with okr_links already parsed
        
        Returns:
            List of OKR names this project links to
        """
        okr_links = project.get('okr_links', {})
        
        all_okr_names = []
        all_okr_names.extend(okr_links.get('company_objectives', []))
        all_okr_names.extend(okr_links.get('company_key_results', []))
        all_okr_names.extend(okr_links.get('dept_objectives', []))
        all_okr_names.extend(okr_links.get('dept_key_results', []))
        
        return all_okr_names
    
    def _parse_board_relation(self, item: Dict, column_id: str) -> List[str]:
        """
        Parse board relation column to extract linked item IDs
        
        Args:
            item: The Monday.com item
            column_id: The column ID to parse
        
        Returns:
            List of linked item IDs
        """
        for col in item.get('column_values', []):
            if col['id'] == column_id:
                # Check for linked_item_ids (new approach)
                if 'linked_item_ids' in col and col['linked_item_ids']:
                    return col['linked_item_ids']
                
                # Fallback to parsing value JSON
                value_str = col.get('value')
                if value_str:
                    try:
                        value_json = json.loads(value_str)
                        if 'linkedPulseIds' in value_json:
                            return [str(pid) for pid in value_json['linkedPulseIds']]
                    except json.JSONDecodeError:
                        pass
        
        return []
    
    def _find_project_by_name(self, project_name: str, items: List[Dict] = None) -> Optional[Dict]:
        """
        Find a project by name (supports partial matching)
        
        Args:
            project_name: Name or partial name of the project
            items: Optional list of items to search (defaults to all portfolio items)
        
        Returns:
            Matching project item or None
        """
        if items is None:
            items = self._get_all_portfolio_items()
        
        project_name_lower = project_name.lower()
        
        # First try exact match
        for item in items:
            if item['name'].lower() == project_name_lower:
                return item
        
        # Then try partial match
        for item in items:
            if project_name_lower in item['name'].lower():
                return item
        
        return None
    
    def get_project_status(self, project_name: str) -> Optional[Dict]:
        """
        Get detailed status information for a specific project
        
        Args:
            project_name: Name of the project (supports partial matching)
        
        Returns:
            Dictionary with project status details or None if not found
        """
        project = self._find_project_by_name(project_name)
        
        if not project:
            return None
        
        status_label, status_color = self._parse_status(project)
        
        # Get OKR links from pre-parsed data
        okr_names = self._get_okr_links_from_item(project)
        
        return {
            'project_name': project['name'],
            'project_id': project['id'],
            'department': project.get('_department', 'unknown'),
            'status': status_label,
            'status_color': status_color,
            'at_risk': self._is_at_risk(status_label),
            'owner': self._get_column_value(project, self.col_owner) or 'Unassigned',
            'target_date': self._get_column_value(project, self.col_target_date) or 'No date set',
            'okr_aligned': len(okr_names) > 0,
            'okr_count': len(okr_names),
            'okr_names': okr_names,  # Now returns actual OKR names instead of IDs
            'portfolio_tier': self._get_column_value(project, self.col_portfolio_tier) or 'None',
            'theme': self._get_column_value(project, self.col_theme) or 'None',
            'path_to_green': self._get_column_value(project, self.col_path_to_green) or 'Not documented',
            'subitem_count': len(project.get('subitems', []))
        }
    
    def get_lead_follow_breakdown(self, project_name: str) -> Optional[LeadFollowBreakdown]:
        """
        Get the lead/follow project breakdown for a specific project
        
        Args:
            project_name: Name of the lead project
        
        Returns:
            LeadFollowBreakdown object or None if project not found
        """
        project = self._find_project_by_name(project_name)
        
        if not project:
            return None
        
        # Follow projects are ALL subitems of the lead project
        # (The board_relation link is often not maintained due to human error)
        follow_projects = []
        for subitem in project.get('subitems', []):
            status_label, _ = self._parse_status(subitem)
            follow_projects.append({
                'id': subitem['id'],
                'name': subitem['name'],
                'status': status_label,
                'owner': self._get_column_value(subitem, self.col_owner) or 'Unassigned',
                'department': project.get('_department', 'unknown'),
                'parent_project': project['name']
            })
        
        return LeadFollowBreakdown(
            lead_project=project['name'],
            lead_project_id=project['id'],
            lead_department=project.get('_department', 'unknown'),
            follow_projects=follow_projects,
            total_follow_count=len(follow_projects)
        )
    
    def get_okr_contributing_projects(self, okr_id: str) -> List[Dict]:
        """
        Get all projects that are linked to a specific OKR
        
        Args:
            okr_id: The Monday.com item ID of the OKR (Objective or Key Result)
        
        Returns:
            List of projects contributing to this OKR
        """
        all_projects = self._get_all_portfolio_items()
        okr_map = self._get_all_okr_items()
        
        # Get the target OKR name
        target_okr = okr_map.get(okr_id)
        if not target_okr:
            return []
        
        target_okr_name = target_okr['name']
        
        # Also collect Key Result names if this is an Objective
        target_okr_names = {target_okr_name}
        for subitem in target_okr.get('subitems', []):
            target_okr_names.add(subitem['name'])
        
        contributing_projects = []
        
        for project in all_projects:
            # Get OKR names this project links to
            okr_names = self._get_okr_links_from_item(project)
            
            # Check if any of the project's OKR links match our target
            matching_okrs = [name for name in okr_names if name in target_okr_names]
            
            if matching_okrs:
                status_label, status_color = self._parse_status(project)
                
                contributing_projects.append({
                    'project_id': project['id'],
                    'project_name': project['name'],
                    'department': project.get('_department', 'unknown'),
                    'status': status_label,
                    'status_color': status_color,
                    'at_risk': self._is_at_risk(status_label),
                    'owner': self._get_column_value(project, self.col_owner) or 'Unassigned',
                    'okr_links': matching_okrs
                })
        
        return contributing_projects
    
    def identify_risks(self) -> Dict:
        """
        Identify all risk signals across the entire portfolio
        
        Returns:
            Dictionary with categorized risk information
        """
        all_projects = self._get_all_portfolio_items()
        
        at_risk_projects = []
        
        for project in all_projects:
            status_label, status_color = self._parse_status(project)
            
            if self._is_at_risk(status_label):
                # Get OKR names from pre-parsed data
                okr_names = self._get_okr_links_from_item(project)
                
                at_risk_projects.append({
                    'id': project['id'],
                    'name': project['name'],
                    'department': project.get('_department', 'unknown'),
                    'status': status_label,
                    'status_color': status_color,
                    'owner': self._get_column_value(project, self.col_owner) or 'Unassigned',
                    'okr_aligned': len(okr_names) > 0,
                    'okr_names': okr_names,
                    'path_to_green': self._get_column_value(project, self.col_path_to_green) or 'Not documented'
                })
        
        # Analyze capacity/overallocation
        overallocated_people = []
        person_capacity = {}  # {person_name: {'total': X, 'projects': [...]}}
        
        # Get all capacity boards
        capacity_boards = self.client.get_all_capacity_boards()
        
        for board_type in capacity_boards:
            try:
                items = self.client.get_board_items(board_type)
                department = board_type.replace('_capacity', '')
                
                for item in items:
                    # Skip template/empty items
                    if item['name'] == 'Portfolio Item Name':
                        continue
                    
                    # Get person name
                    person_col = next((c for c in item['column_values'] if c['id'] == 'person'), None)
                    if not person_col or not person_col.get('text'):
                        continue
                    
                    person_name = person_col['text']
                    
                    # Get capacity percentage
                    capacity_col = next((c for c in item['column_values'] if c['type'] == 'numbers'), None)
                    if not capacity_col or not capacity_col.get('text'):
                        continue
                    
                    try:
                        capacity_pct = float(capacity_col['text'])
                    except (ValueError, TypeError):
                        continue
                    
                    # Initialize person if not seen before
                    if person_name not in person_capacity:
                        person_capacity[person_name] = {
                            'total': 0,
                            'projects': [],
                            'department': department
                        }
                    
                    # Add to their total
                    person_capacity[person_name]['total'] += capacity_pct
                    person_capacity[person_name]['projects'].append({
                        'name': item['name'],
                        'capacity': capacity_pct
                    })
            except Exception as e:
                print(f"⚠️  Warning: Could not load capacity board {board_type}: {e}")
                continue
        
        # Find overallocated people (>70%)
        for person_name, data in person_capacity.items():
            if data['total'] > 70:
                overallocated_people.append({
                    'name': person_name,
                    'capacity': round(data['total'], 1),
                    'projects': [p['name'] for p in data['projects']],
                    'department': data['department']
                })
        
        # Sort by capacity (highest first)
        overallocated_people.sort(key=lambda x: x['capacity'], reverse=True)
        
        return {
            'total_risk_signals': len(at_risk_projects) + len(overallocated_people),
            'at_risk_projects': {
                'count': len(at_risk_projects),
                'projects': at_risk_projects
            },
            'overallocated_people': {
                'count': len(overallocated_people),
                'people': overallocated_people
            }
        }
    
    def get_department_okr_progress(self, department: str = 'proddev') -> List[Dict]:
        """
        Get OKR progress summary for a specific department
        
        Args:
            department: Department name (proddev, secit, finops, field, people, marketing, legal, company)
        
        Returns:
            List of OKRs with their contributing projects and progress
        """
        # Get the OKR board for this department
        board_type = f"{department}_okr"
        
        try:
            okr_items = self.client.get_board_items(board_type)
        except ValueError:
            raise ValueError(f"Unknown department: {department}")
        
        okr_summary = []
        
        for okr in okr_items:
            # Get all projects contributing to this OKR
            contributing_projects = self.get_okr_contributing_projects(okr['id'])
            
            # Count at-risk projects
            at_risk_count = sum(1 for p in contributing_projects if p.get('at_risk', False))
            
            # Count key results (subitems)
            key_results_count = len(okr.get('subitems', []))
            
            okr_summary.append({
                'okr_id': okr['id'],
                'okr_name': okr['name'],
                'department': department,
                'contributing_projects': len(contributing_projects),
                'at_risk_projects': at_risk_count,
                'key_results_count': key_results_count,
                'projects': contributing_projects
            })
        
        return okr_summary
    
    def get_all_projects(self, department: Optional[str] = None) -> List[Dict]:
        """
        Get all projects, optionally filtered by department
        
        Args:
            department: Optional department filter
        
        Returns:
            List of all projects with basic info
        """
        all_projects = self._get_all_portfolio_items()
        
        if department:
            all_projects = [p for p in all_projects if p.get('_department') == department]
        
        result = []
        for project in all_projects:
            status_label, status_color = self._parse_status(project)
            
            # Get OKR names from pre-parsed data
            okr_names = self._get_okr_links_from_item(project)
            
            result.append({
                'project_id': project['id'],
                'project_name': project['name'],
                'department': project.get('_department', 'unknown'),
                'status': status_label,
                'status_color': status_color,
                'at_risk': self._is_at_risk(status_label),
                'owner': self._get_column_value(project, self.col_owner) or 'Unassigned',
                'target_date': self._get_column_value(project, self.col_target_date) or 'No date set',
                'portfolio_tier': self._get_column_value(project, self.col_portfolio_tier) or 'None',
                'theme': self._get_column_value(project, self.col_theme) or 'None',
                'okr_aligned': len(okr_names) > 0,
                'okr_count': len(okr_names)
            })
        
        return result
    
    def get_department_summary(self, department: str) -> Dict:
        """
        Get a high-level summary for a specific department
        
        Args:
            department: Department name
        
        Returns:
            Summary statistics for the department
        """
        projects = self.get_all_projects(department=department)
        
        total_projects = len(projects)
        at_risk_projects = [p for p in projects if p['at_risk']]
        green_projects = [p for p in projects if p['status_color'] == 'green']
        yellow_projects = [p for p in projects if p['status_color'] == 'yellow']
        red_projects = [p for p in projects if p['status_color'] == 'red']
        
        # Get OKR alignment
        okr_aligned = [p for p in projects if p.get('okr_aligned', False)]
        
        return {
            'department': department,
            'total_projects': total_projects,
            'at_risk_count': len(at_risk_projects),
            'green_count': len(green_projects),
            'yellow_count': len(yellow_projects),
            'red_count': len(red_projects),
            'okr_aligned_count': len(okr_aligned),
            'okr_alignment_percentage': round(len(okr_aligned) / total_projects * 100, 1) if total_projects > 0 else 0,
            'projects': projects
        }