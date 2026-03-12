#!/usr/bin/env python3
"""
Test All Departments - Verify multi-department configuration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence


def test_all_departments():
    """Test that all departments are accessible"""
    
    print("\n" + "="*70)
    print("🚀 TESTING ALL DEPARTMENTS")
    print("="*70)
    
    pi = PortfolioIntelligence()
    
    departments = ['proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal']
    
    print("\n📊 Loading all portfolio items...")
    all_projects = pi.get_all_projects()
    
    print(f"\n✅ Total projects across all departments: {len(all_projects)}")
    
    print("\n" + "="*70)
    print("DEPARTMENT BREAKDOWN")
    print("="*70)
    
    for dept in departments:
        print(f"\n🏢 {dept.upper()}")
        print("-" * 70)
        
        try:
            summary = pi.get_department_summary(dept)
            
            print(f"   Total Projects: {summary['total_projects']}")
            print(f"   At Risk: {summary['at_risk_count']}")
            print(f"   Green: {summary['green_count']}")
            print(f"   Yellow: {summary['yellow_count']}")
            print(f"   Red: {summary['red_count']}")
            print(f"   OKR Aligned: {summary['okr_aligned_count']} ({summary['okr_alignment_percentage']}%)")
            
            if summary['total_projects'] > 0:
                print(f"\n   Sample Projects:")
                for proj in summary['projects'][:3]:
                    status_icon = "🟢" if proj['status_color'] == 'green' else "🟡" if proj['status_color'] == 'yellow' else "🔴" if proj['status_color'] == 'red' else "⚪"
                    print(f"     {status_icon} {proj['project_name']}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*70)
    print("🎯 TESTING OKR PROGRESS ACROSS DEPARTMENTS")
    print("="*70)
    
    for dept in departments:
        print(f"\n🏢 {dept.upper()} OKRs")
        print("-" * 70)
        
        try:
            okr_progress = pi.get_department_okr_progress(dept)
            
            print(f"   Total OKRs: {len(okr_progress)}")
            
            for okr in okr_progress[:3]:  # Show first 3 OKRs
                print(f"\n   🎯 {okr['okr_name']}")
                print(f"      Contributing Projects: {okr['contributing_projects']}")
                print(f"      At Risk: {okr['at_risk_projects']}")
                print(f"      Key Results: {okr['key_results_count']}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*70)
    print("🚨 PORTFOLIO-WIDE RISK ANALYSIS")
    print("="*70)
    
    risks = pi.identify_risks()
    
    print(f"\n   Total Risk Signals: {risks['total_risk_signals']}")
    print(f"   At-Risk Projects: {risks['at_risk_projects']['count']}")
    
    # Group risks by department
    dept_risks = {}
    for proj in risks['at_risk_projects']['projects']:
        dept = proj['department']
        if dept not in dept_risks:
            dept_risks[dept] = []
        dept_risks[dept].append(proj)
    
    print(f"\n   Risks by Department:")
    for dept, projs in sorted(dept_risks.items()):
        print(f"     {dept}: {len(projs)} at-risk projects")
    
    print("\n" + "="*70)
    print("✅ ALL DEPARTMENT TESTS COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    test_all_departments()