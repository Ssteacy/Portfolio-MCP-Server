"""
Portfolio Intelligence Logic
Core business logic for analyzing portfolio data from Monday.com
"""

import json
from typing import Dict, List, Optional
from core.monday_client import MondayClient
from core.models import LeadFollowBreakdown


class PortfolioIntelligence:
    """Main class for portfolio analysis and intelligence"""
    
    def __init__(self):
        self.client = MondayClient()
        self._portfolio_cache = {}
        self._okr_cache = {}
    
    def _get_all_portfolio_items(self, refresh: bool = False) -> List[Dict]:
        """
        Get all portfolio items across all departments
        
        Args:
            refresh: Force refresh from API instead of using cache
        
        Returns:
            List of all portfolio items with department metadata
        """
        if self._portfolio_cache and not refresh:
            return self._portfolio_cache
        
        all_items = []
        
        for board_type in self.client.get_all_portfolio_boards():
            department = self.client.get_department_from_board_type(board_type)
            
            try:
                items = self.client.get_board_items(board_type)
                
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
        status_json = self._get_column_json(item, 'status')
        if status_json:
            label = status_json.get('label', 'No status')
            # Map Monday.com color indices to names
            color_map = {0: 'gray', 1: 'green', 2: 'yellow', 3: 'red'}
            color_index = status_json.get('index', 0)
            color = color_map.get(color_index, 'gray')
            return label, color
        return 'No status', 'gray'
    
    def _is_at_risk(self, status_color: str) -> bool:
        """Determine if a project is at risk based on status color"""
        return status_color in ['yellow', 'red']
    
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
    
    def _get_okr_column_ids(self, project: Dict) -> List[str]:
        """
        Dynamically find OKR column IDs by looking for columns with 'objective' or 'key result' in the title
        
        Args:
            project: The Monday.com item with column_values
        
        Returns:
            List of column IDs that are OKR-related
        """
        okr_column_ids = []
        
        for col_val in project.get('column_values', []):
            # Check if this is a board_relation column
            if col_val.get('type') == 'board_relation':
                col_id = col_val['id']
                # OKR columns have IDs like 'board_relation_mkxv5m0t' and contain 'objective' or 'key result' keywords
                # We'll check all board_relation columns
                if col_id.startswith('board_relation'):
                    okr_column_ids.append(col_id)
        
        return okr_column_ids
    
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
        
        # Parse OKR links (check all 4 OKR columns)
        okr_links = []
        for okr_col in self._get_okr_column_ids(project):
            okr_links.extend(self._parse_board_relation(project, okr_col))
        
        return {
            'project_name': project['name'],
            'project_id': project['id'],
            'department': project.get('_department', 'unknown'),
            'status': status_label,
            'status_color': status_color,
            'at_risk': self._is_at_risk(status_color),
            'owner': self._get_column_value(project, 'people') or 'Unassigned',
            'target_date': self._get_column_value(project, 'date4') or 'No date set',
            'okr_aligned': len(okr_links) > 0,
            'okr_count': len(okr_links),
            'okr_links': okr_links,
            'portfolio_tier': self._get_column_value(project, 'dropdown') or 'None',
            'theme': self._get_column_value(project, 'dropdown8') or 'None',
            'path_to_green': self._get_column_value(project, 'long_text') or 'Not documented',
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
        
        # Get linked follow projects from board_relation9 column
        follow_project_ids = self._parse_board_relation(project, 'board_relation9')
        
        # Fetch details for each follow project
        follow_projects = []
        for follow_id in follow_project_ids:
            follow_item = self.client.get_item_by_id(follow_id)
            if follow_item:
                status_label, _ = self._parse_status(follow_item)
                follow_projects.append({
                    'id': follow_item['id'],
                    'name': follow_item['name'],
                    'status': status_label,
                    'owner': self._get_column_value(follow_item, 'people') or 'Unassigned'
                })
        
        return LeadFollowBreakdown(
            lead_project=project['name'],
            lead_project_id=project['id'],
            follow_projects=follow_projects,
            total_follow_count=len(follow_projects)
        )
    
    def get_okr_contributing_projects(self, okr_id: str) -> List[Dict]:
        """
        Get all projects that are linked to a specific OKR
        
        Args:
            okr_id: The Monday.com item ID of the OKR
        
        Returns:
            List of projects contributing to this OKR
        """
        all_projects = self._get_all_portfolio_items()
        okr_map = self._get_all_okr_items()
        
        contributing_projects = []
        
        for project in all_projects:
            # Check all 4 OKR link columns
            okr_links = []
            for okr_col in self._get_okr_column_ids(project):
                okr_links.extend(self._parse_board_relation(project, okr_col))
            
            # Check if this project links to the target OKR (or its subitems)
            if okr_id in okr_links:
                status_label, status_color = self._parse_status(project)
                
                # Get the OKR names this project links to
                okr_names = []
                for linked_okr_id in okr_links:
                    if linked_okr_id in okr_map:
                        okr_item = okr_map[linked_okr_id]
                        if okr_item.get('_parent_okr'):
                            # This is a Key Result
                            okr_names.append(f"{okr_item['_parent_okr']} → {okr_item['name']}")
                        else:
                            # This is an Objective
                            okr_names.append(okr_item['name'])
                
                contributing_projects.append({
                    'project_id': project['id'],
                    'project_name': project['name'],
                    'department': project.get('_department', 'unknown'),
                    'status': status_label,
                    'status_color': status_color,
                    'at_risk': self._is_at_risk(status_color),
                    'owner': self._get_column_value(project, 'people') or 'Unassigned',
                    'okr_links': okr_names
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
            
            if self._is_at_risk(status_color):
                # Parse OKR links
                okr_links = []
                for okr_col in self._get_okr_column_ids(project):
                    okr_links.extend(self._parse_board_relation(project, okr_col))
                
                at_risk_projects.append({
                    'id': project['id'],
                    'name': project['name'],
                    'department': project.get('_department', 'unknown'),
                    'status': status_label,
                    'status_color': status_color,
                    'owner': self._get_column_value(project, 'people') or 'Unassigned',
                    'okr_aligned': len(okr_links) > 0,
                    'path_to_green': self._get_column_value(project, 'long_text') or 'Not documented'
                })
        
        # TODO: Add capacity/overallocation analysis when we implement capacity board parsing
        
        return {
            'total_risk_signals': len(at_risk_projects),
            'at_risk_projects': {
                'count': len(at_risk_projects),
                'projects': at_risk_projects
            },
            'overallocated_people': {
                'count': 0,
                'people': []
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
            ok_items = self.client.get_board_items(board_type)
        except ValueError:
            raise ValueError(f"Unknown department: {department}")
        
        okr_summary = []
        
        for okr in ok_items:
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
            
            # Calculate OKR alignment
            okr_links = []
            for okr_col in self._get_okr_column_ids(project):
                okr_links.extend(self._parse_board_relation(project, okr_col))
            
            result.append({
                'project_id': project['id'],
                'project_name': project['name'],
                'department': project.get('_department', 'unknown'),
                'status': status_label,
                'status_color': status_color,
                'at_risk': self._is_at_risk(status_color),
                'owner': self._get_column_value(project, 'people') or 'Unassigned',
                'target_date': self._get_column_value(project, 'date4') or 'No date set',
                'portfolio_tier': self._get_column_value(project, 'dropdown') or 'None',
                'theme': self._get_column_value(project, 'dropdown8') or 'None',
                'okr_aligned': len(okr_links) > 0,
                'okr_count': len(okr_links)
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