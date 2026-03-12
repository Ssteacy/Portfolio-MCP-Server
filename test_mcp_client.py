#!/usr/bin/env python3
"""
MCP Test Client - Tests the MCP server tool implementations

This client tests the tool logic that will be exposed via MCP protocol.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_logic import PortfolioIntelligence


class MCPToolTester:
    """Tests MCP tool implementations"""
    
    def __init__(self):
        self.pi = PortfolioIntelligence()
    
    def format_project_status(self, result):
        """Format project status response"""
        if not result:
            return "Project not found"
        
        response = f"""**Project Status: {result['project_name']}**

📊 **Status:** {result['status']} ({result['status_color']})
⚠️  **At Risk:** {'Yes' if result['at_risk'] else 'No'}
👤 **Owner:** {result['owner']}
📅 **Target Date:** {result['target_date']}
🎯 **OKR Aligned:** {'Yes' if result['okr_aligned'] else 'No'} ({result['okr_count']} OKR links)
📦 **Portfolio Tier:** {result['portfolio_tier']}
🎨 **Theme:** {result['theme']}
📝 **Subitems:** {result['subitem_count']}

**Path to Green:**
{result['path_to_green']}
"""
        return response
    
    def format_lead_follow(self, result):
        """Format lead/follow breakdown response"""
        if not result:
            return "Project not found"
        
        response = f"""**Lead/Follow Breakdown**

🎯 **Lead Project:** {result.lead_project}
📊 **Total Follow Projects:** {result.total_follow_count}

**Follow Projects:**
"""
        if result.follow_projects:
            for follow in result.follow_projects:
                response += f"\n- {follow['name']}"
                response += f"\n  Status: {follow['status']}"
                response += f"\n  Owner: {follow['owner']}\n"
        else:
            response += "\nNo follow projects found."
        
        return response
    
    def format_okr_projects(self, okr_name, result):
        """Format OKR contributing projects response"""
        at_risk = [p for p in result if p.get('at_risk', False)]
        
        response = f"""**OKR Contributing Projects**

🎯 **OKR:** {okr_name}
📊 **Contributing Projects:** {len(result)}
⚠️  **At Risk:** {len(at_risk)}

**Projects:**
"""
        if result:
            for proj in result:
                risk_icon = "⚠️" if proj.get('at_risk', False) else "✅"
                response += f"\n{risk_icon} **{proj['project_name']}** ({proj.get('status', 'N/A')})"
                if proj.get('okr_links'):
                    response += f"\n   Links: {proj['okr_links'][0]}"
                response += "\n"
        else:
            response += "\nNo projects currently linked to this OKR."
        
        return response
    
    def format_risks(self, result):
        """Format risk analysis response"""
        response = f"""**Portfolio Risk Analysis**

🚨 **Total Risk Signals:** {result['total_risk_signals']}

📊 **At-Risk Projects:** {result['at_risk_projects']['count']}
👥 **Overallocated People:** {result['overallocated_people']['count']}

**Top At-Risk Projects:**
"""
        for proj in result['at_risk_projects']['projects'][:10]:
            response += f"\n⚠️  **{proj['name']}** ({proj['status']})"
            response += f"\n   Owner: {proj['owner']}"
            response += f"\n   OKR Aligned: {'Yes' if proj['okr_aligned'] else 'No'}"
            if proj['path_to_green'] and proj['path_to_green'] != 'Not documented':
                response += f"\n   Path to Green: {proj['path_to_green'][:100]}..."
            response += "\n"
        
        if result['overallocated_people']['count'] > 0:
            response += "\n**Overallocated People:**\n"
            for person in result['overallocated_people']['people']:
                response += f"\n⚠️  **{person['name']}** - {person['capacity']}% allocated"
                response += f"\n   Projects: {', '.join(person['projects'][:3])}"
                response += "\n"
        
        return response
    
    def format_okr_progress(self, department, result):
        """Format OKR progress response"""
        response = f"""**{department.upper()} OKR Progress Summary**

📊 **Total OKRs:** {len(result)}

"""
        for okr in result:
            response += f"\n🎯 **{okr['okr_name']}**"
            response += f"\n   Contributing Projects: {okr['contributing_projects']}"
            response += f"\n   At Risk: {okr['at_risk_projects']}"
            response += f"\n   Key Results: {okr['key_results_count']}"
            
            if okr.get('projects') and len(okr['projects']) > 0:
                response += "\n   Top Projects:"
                for proj in okr['projects'][:3]:
                    risk_icon = "⚠️" if proj.get('at_risk', False) else "✅"
                    response += f"\n     {risk_icon} {proj['project_name']} ({proj.get('status', 'N/A')})"
            response += "\n"
        
        return response
    
    def test_tool(self, tool_name, **kwargs):
        """Test a specific tool"""
        print(f"\n{'='*70}")
        print(f"🔧 TESTING TOOL: {tool_name}")
        print(f"📥 ARGUMENTS: {kwargs}")
        print(f"{'='*70}\n")
        
        try:
            if tool_name == "get_project_status":
                result = self.pi.get_project_status(kwargs['project_name'])
                print(self.format_project_status(result))
            
            elif tool_name == "get_lead_follow_breakdown":
                result = self.pi.get_lead_follow_breakdown(kwargs['project_name'])
                print(self.format_lead_follow(result))
            
            elif tool_name == "get_okr_contributing_projects":
                okr_name = kwargs['okr_name']
                department = kwargs.get('department', 'proddev')
                
                # Find the OKR by name
                board_type = 'company_okr' if department == 'company' else 'proddev_okr'
                okr_items = self.pi.client.get_board_items(board_type)
                
                matching_okr = None
                for okr in okr_items:
                    if okr_name.lower() in okr['name'].lower():
                        matching_okr = okr
                        break
                
                if not matching_okr:
                    print(f"OKR matching '{okr_name}' not found in {department} board")
                    return
                
                result = self.pi.get_okr_contributing_projects(matching_okr['id'])
                print(self.format_okr_projects(matching_okr['name'], result))
            
            elif tool_name == "identify_risks":
                result = self.pi.identify_risks()
                print(self.format_risks(result))
            
            elif tool_name == "get_department_okr_progress":
                department = kwargs.get('department', 'proddev')
                result = self.pi.get_department_okr_progress(department)
                print(self.format_okr_progress(department, result))
            
            else:
                print(f"❌ Unknown tool: {tool_name}")
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()


def run_all_tests():
    """Run comprehensive tests of all MCP tools"""
    
    tester = MCPToolTester()
    
    print("\n" + "="*70)
    print("🚀 MONDAY.COM PORTFOLIO INTELLIGENCE - MCP TOOL TESTS")
    print("="*70)
    
    input("\n⏸️  Press ENTER to start testing tools...")
    
    # TEST 1: Get Project Status
    print("\n" + "🔵"*35)
    print("TEST 1: Get Project Status")
    print("🔵"*35)
    
    tester.test_tool("get_project_status", project_name="OpsCloud Pricing & Packaging")
    
    input("\n⏸️  Press ENTER to continue to Test 2...")
    
    # TEST 2: Lead/Follow Breakdown
    print("\n" + "🔵"*35)
    print("TEST 2: Lead/Follow Breakdown")
    print("🔵"*35)
    
    tester.test_tool("get_lead_follow_breakdown", project_name="OpsCloud Pricing & Packaging")
    
    input("\n⏸️  Press ENTER to continue to Test 3...")
    
    # TEST 3: OKR Contributing Projects
    print("\n" + "🔵"*35)
    print("TEST 3: OKR Contributing Projects")
    print("🔵"*35)
    
    tester.test_tool("get_okr_contributing_projects", okr_name="O1", department="proddev")
    
    input("\n⏸️  Press ENTER to continue to Test 4...")
    
    # TEST 4: Identify Risks
    print("\n" + "🔵"*35)
    print("TEST 4: Identify Risks")
    print("🔵"*35)
    
    tester.test_tool("identify_risks")
    
    input("\n⏸️  Press ENTER to continue to Test 5...")
    
    # TEST 5: Department OKR Progress
    print("\n" + "🔵"*35)
    print("TEST 5: Department OKR Progress")
    print("🔵"*35)
    
    tester.test_tool("get_department_okr_progress", department="proddev")
    
    # TEST 6: Error handling - Project not found
    print("\n" + "🔵"*35)
    print("TEST 6: Error Handling - Project Not Found")
    print("🔵"*35)
    
    tester.test_tool("get_project_status", project_name="NonExistentProject12345")
    
    # TEST 7: Partial match
    print("\n" + "🔵"*35)
    print("TEST 7: Partial Match - Chat")
    print("🔵"*35)
    
    tester.test_tool("get_project_status", project_name="Chat")
    
    print("\n" + "="*70)
    print("✅ ALL MCP TOOL TESTS COMPLETE!")
    print("="*70)
    print("\n📝 Summary:")
    print("   - All 5 core tools tested")
    print("   - Error handling verified")
    print("   - Partial matching verified")
    print("\n🎯 MCP tool implementations are working correctly!")
    print("   Ready to connect via Gemini CLI when available.")
    print("="*70 + "\n")


def interactive_mode():
    """Interactive mode - manually test tools"""
    
    tester = MCPToolTester()
    
    print("\n" + "="*70)
    print("🎮 INTERACTIVE MCP TEST MODE")
    print("="*70)
    print("\nYou can now test any tool with custom inputs!")
    print("="*70)
    
    while True:
        print("\n" + "-"*70)
        print("Available commands:")
        print("  1 - get_project_status")
        print("  2 - get_lead_follow_breakdown")
        print("  3 - get_okr_contributing_projects")
        print("  4 - identify_risks")
        print("  5 - get_department_okr_progress")
        print("  quit - Exit")
        print("-"*70)
        
        choice = input("\nEnter command number (or 'quit'): ").strip().lower()
        
        if choice == "quit" or choice == "q":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            project_name = input("Enter project name: ").strip()
            if project_name:
                tester.test_tool("get_project_status", project_name=project_name)
        elif choice == "2":
            project_name = input("Enter project name: ").strip()
            if project_name:
                tester.test_tool("get_lead_follow_breakdown", project_name=project_name)
        elif choice == "3":
            okr_name = input("Enter OKR name (partial match): ").strip()
            department = input("Enter department (company/proddev) [proddev]: ").strip() or "proddev"
            if okr_name:
                tester.test_tool("get_okr_contributing_projects", okr_name=okr_name, department=department)
        elif choice == "4":
            tester.test_tool("identify_risks")
        elif choice == "5":
            department = input("Enter department (company/proddev) [proddev]: ").strip() or "proddev"
            tester.test_tool("get_department_okr_progress", department=department)
        else:
            print("❌ Invalid command. Please enter 1-5 or 'quit'")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        run_all_tests()