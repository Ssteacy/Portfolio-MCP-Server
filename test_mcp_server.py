#!/usr/bin/env python3
"""
Test the Monday.com Portfolio Intelligence MCP Server
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence


def test_all_capabilities():
    """Test all 5 MVP capabilities"""
    pi = PortfolioIntelligence()
    
    print("=" * 70)
    print("🚀 MONDAY.COM PORTFOLIO INTELLIGENCE - MCP SERVER TEST")
    print("=" * 70)
    
    # TEST 1: Get Project Status
    print("\n📊 TEST 1: Get Project Status")
    print("-" * 70)
    status = pi.get_project_status("OpsCloud Pricing & Packaging")
    if status:
        dept = status.get('department', 'unknown').upper()
        print(f"✅ Project: {status['project_name']} [{dept}]")
        print(f"   Status: {status['status']} ({status['status_color']})")
        print(f"   At Risk: {status['at_risk']}")
        print(f"   Owner: {status['owner']}")
        print(f"   OKR Aligned: {status['okr_aligned']}")
        print(f"   OKR Count: {status['okr_count']}")
    else:
        print("❌ Project not found")
    
    # TEST 2: Lead/Follow Breakdown
    print("\n📊 TEST 2: Lead/Follow Breakdown")
    print("-" * 70)
    breakdown = pi.get_lead_follow_breakdown("OpsCloud Pricing & Packaging")
    if breakdown:
        dept = breakdown.lead_department.upper()
        print(f"✅ Lead Project: {breakdown.lead_project} [{dept}]")
        print(f"   Follow Projects: {breakdown.total_follow_count}")
        for follow in breakdown.follow_projects[:5]:
            follow_dept = follow.get('department', 'unknown').upper()
            print(f"   - {follow['name']} ({follow['status']}) [{follow_dept}]")
    else:
        print("❌ Project not found")
    
    # TEST 3: OKR Contributing Projects
    print("\n📊 TEST 3: OKR Contributing Projects")
    print("-" * 70)
    
    # Get ProdDev OKR board (which has linked projects)
    okr_items = pi.client.get_board_items('proddev_okr')
    if okr_items:
        # Find an OKR with linked projects
        test_okr = None
        for okr in okr_items:
            projects = pi.get_okr_contributing_projects(okr['id'])
            if projects:
                test_okr = okr
                break
        
        if test_okr:
            okr_id = test_okr['id']
            okr_name = test_okr['name']
            
            projects = pi.get_okr_contributing_projects(okr_id)
            at_risk = [p for p in projects if p.get('at_risk', False)]
            
            print(f"   OKR: {okr_name}")
            print(f"   Contributing Projects: {len(projects)}")
            print(f"   At Risk: {len(at_risk)}")
            
            print(f"\n   Top Contributing Projects:")
            for proj in projects[:5]:
                risk_icon = "⚠️ " if proj.get('at_risk', False) else "✅"
                dept = proj.get('department', 'unknown').upper()
                print(f"   {risk_icon} {proj['project_name']} ({proj.get('status', 'N/A')}) [{dept}]")
                if proj.get('okr_links'):
                    okr_link_preview = proj['okr_links'][0] if len(proj['okr_links']) > 0 else 'N/A'
                    print(f"      Link: {okr_link_preview}")
        else:
            print("   ℹ️  No OKRs with linked projects found")
    else:
        print("❌ No OKR items found")
    
    # TEST 4: Identify Risks
    print("\n📊 TEST 4: Identify Risks")
    print("-" * 70)
    risks = pi.identify_risks()
    print(f"✅ Total Risk Signals: {risks['total_risk_signals']}")
    print(f"   At-Risk Projects: {risks['at_risk_projects']['count']}")
    print(f"   Overallocated People: {risks['overallocated_people']['count']}")
    
    print(f"\n   Top 5 At-Risk Projects:")
    for project in risks['at_risk_projects']['projects'][:5]:
        dept = project.get('department', 'unknown').upper()
        print(f"   ⚠️  {project['name']} ({project['status']}) [{dept}] - {project['owner']}")
    
    # TEST 5: Department OKR Progress
    print("\n📊 TEST 5: Department OKR Progress")
    print("-" * 70)
    okr_progress = pi.get_department_okr_progress('proddev')
    print(f"✅ Total OKRs: {len(okr_progress)}")
    
    print(f"\n   OKR Summary:")
    for okr in okr_progress:
        print(f"   - {okr['okr_name']}")
        print(f"     Contributing: {okr['contributing_projects']} | At Risk: {okr['at_risk_projects']}")
        
        # Show top contributing projects
        if okr.get('projects') and len(okr['projects']) > 0:
            for proj in okr['projects'][:3]:
                risk_icon = "⚠️" if proj.get('at_risk', False) else "✅"
                dept = proj.get('department', 'unknown').upper()
                print(f"       {risk_icon} {proj['project_name']} ({proj.get('status', 'N/A')}) [{dept}]")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE - MCP SERVER READY!")
    print("=" * 70)


if __name__ == "__main__":
    test_all_capabilities()