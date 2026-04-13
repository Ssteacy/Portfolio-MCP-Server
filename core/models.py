from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StatusColor(Enum):
    """Monday.com status colors"""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    GREY = "grey"
    BLUE = "blue"
    ORANGE = "orange"


# OKR Column Mappings - maps board_relation column IDs to OKR types
OKR_COLUMN_MAPPINGS = {
    'company_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0efvmg': 'company_kr',
    },
    'proddev_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0pnjk4': 'company_kr',
        'board_relation_mm0pp1zv': 'dept_objective',
        'board_relation_mm0pntcx': 'dept_kr',
    },
    'secit_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0eyrk5': 'company_kr',
        'board_relation_mm0e1nwb': 'dept_objective',
        'board_relation_mm0e9ydq': 'dept_kr',
    },
    'finops_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0epkcf': 'company_kr',
        'board_relation_mm0e4fe3': 'dept_objective',
        'board_relation_mm0e57sy': 'dept_kr',
    },
    'field_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0esg2h': 'company_kr',
        'board_relation_mm0eq60r': 'dept_objective',
        'board_relation_mm0ejhbb': 'dept_kr',
    },
    'people_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0e754a': 'company_kr',
        'board_relation_mm0e54k5': 'dept_objective',
        'board_relation_mm0exydn': 'dept_kr',
    },
    'marketing_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0ezyy8': 'company_kr',
        'board_relation_mm0exaj1': 'dept_objective',
        'board_relation_mm0ezk54': 'dept_kr',
    },
    'legal_portfolio': {
        'board_relation_mkxv5m0t': 'company_objective',
        'board_relation_mm0ex15n': 'company_kr',
        'board_relation_mm0ezxz0': 'dept_objective',
        'board_relation_mm0e60jy': 'dept_kr',
    },
}


@dataclass
class ProjectStatus:
    """Represents a portfolio project/program"""
    id: str
    name: str
    overall_status: Optional[str]
    status_color: Optional[str]
    owner: List[str]
    editors: List[str]
    target_date: Optional[str]
    path_to_green: Optional[str]
    portfolio_tier: Optional[str]
    theme: Optional[str]
    category: Optional[str]
    term_vector: Optional[str]
    
    # OKR linkages
    company_objectives: List[str]
    company_key_results: List[str]
    proddev_objectives: List[str]
    proddev_key_results: List[str]
    
    # Lead/Follow
    subitems: List[Dict[str, Any]]
    
    # Metadata
    board_id: str
    raw_data: Dict[str, Any]
    
    def is_at_risk(self) -> bool:
        """Check if project is at risk based on status"""
        if self.status_color:
            return self.status_color.lower() in ['red', 'yellow', 'orange']
        return False
    
    def has_okr_alignment(self) -> bool:
        """Check if project is aligned to any OKR"""
        return bool(
            self.company_objectives or 
            self.company_key_results or 
            self.proddev_objectives or 
            self.proddev_key_results
        )
    
    def get_all_okr_links(self) -> List[str]:
        """Get all OKR item IDs this project links to"""
        return (
            self.company_objectives + 
            self.company_key_results + 
            self.proddev_objectives + 
            self.proddev_key_results
        )


@dataclass
class OKRItem:
    """Represents an OKR (Objective or Key Result)"""
    id: str
    name: str
    status: Optional[str]
    status_color: Optional[str]
    owner: List[str]
    target_date: Optional[str]
    board_id: str
    raw_data: Dict[str, Any]


@dataclass
class CapacityAllocation:
    """Represents capacity allocation for an individual"""
    id: str
    person_name: str
    project_name: str
    allocation_percentage: Optional[float]
    project_id: Optional[str]
    raw_data: Dict[str, Any]
    
    def is_overallocated(self, threshold: float = 70.0) -> bool:
        """Check if person is over-allocated"""
        if self.allocation_percentage:
            return self.allocation_percentage > threshold
        return False


@dataclass
class LeadFollowBreakdown:
    """Lead/Follow project breakdown"""
    lead_project: str
    lead_project_id: str
    lead_department: str  
    follow_projects: List[Dict]
    total_follow_count: int