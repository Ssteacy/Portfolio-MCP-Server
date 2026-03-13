#!/usr/bin/env python3
"""
Monday.com Portfolio Intelligence MCP Server

Exposes 5 query capabilities as MCP tools:
1. get_project_status - Get detailed status of a specific project
2. get_lead_follow_breakdown - Get lead/follow project relationships
3. get_okr_contributing_projects - Get projects contributing to an OKR
4. identify_risks - Identify at-risk projects and overallocated people
5. get_department_okr_progress - Get OKR progress for a department
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from core.portfolio_logic import PortfolioIntelligence

# Initialize the MCP server
app = Server("monday-portfolio-intelligence")

# Initialize portfolio intelligence
pi = PortfolioIntelligence()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="get_project_status",
            description="Get detailed status information for a specific project including status, owner, OKR alignment, and risk indicators",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The name of the project (case-insensitive, partial match supported)"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_lead_follow_breakdown",
            description="Get the lead/follow project breakdown showing which projects are following a lead project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The name of the lead project"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_okr_contributing_projects",
            description="Get all projects contributing to a specific OKR (Objective or Key Result). Returns project details, status, and risk indicators.",
            inputSchema={
                "type": "object",
                "properties": {
                    "okr_name": {
                        "type": "string",
                        "description": "The name of the OKR (Objective or Key Result). Use partial match to find OKRs."
                    },
                    "department": {
                        "type": "string",
                        "description": "Department to search in: 'company' or 'proddev' (default: 'proddev')",
                        "enum": ["company", "proddev"],
                        "default": "proddev"
                    }
                },
                "required": ["okr_name"]
            }
        ),
        Tool(
            name="identify_risks",
            description="Identify all risk signals across the portfolio including at-risk projects (red/yellow status) and overallocated people (>70% capacity)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_department_okr_progress",
            description="Get OKR progress summary for a department showing contributing projects and at-risk counts for each OKR",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Department name: 'company' or 'proddev' (default: 'proddev')",
                        "enum": ["company", "proddev"],
                        "default": "proddev"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "get_project_status":
            project_name = arguments.get("project_name")
            if not project_name:
                return [TextContent(type="text", text="Error: project_name is required")]
            
            result = pi.get_project_status(project_name)
            if not result:
                return [TextContent(type="text", text=f"Project '{project_name}' not found")]
            
            # Format the response
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
            return [TextContent(type="text", text=response)]
        
        elif name == "get_lead_follow_breakdown":
            project_name = arguments.get("project_name")
            if not project_name:
                return [TextContent(type="text", text="Error: project_name is required")]
            
            result = pi.get_lead_follow_breakdown(project_name)
            if not result:
                return [TextContent(type="text", text=f"Project '{project_name}' not found")]
            
            # Format the response
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
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_okr_contributing_projects":
            okr_name = arguments.get("okr_name")
            department = arguments.get("department", "proddev")
            
            if not okr_name:
                return [TextContent(type="text", text="Error: okr_name is required")]
            
            # Find the OKR by name using the new helper
            matching_okr = pi.find_okr_by_name(okr_name, department)
            
            if not matching_okr:
                return [TextContent(type="text", text=f"OKR matching '{okr_name}' not found in {department}")]
            
            result = pi.get_okr_contributing_projects(matching_okr['id'])
            at_risk = [p for p in result if p.get('at_risk', False)]
            
            # Format the response
            response = f"""**OKR Contributing Projects**

        🎯 **OKR:** {matching_okr['name']}
        📊 **Contributing Projects:** {len(result)}
        ⚠️  **At Risk:** {len(at_risk)}

        **Projects:**
        """
            if result:
                for proj in result:
                    risk_icon = "⚠️" if proj.get('at_risk', False) else "✅"
                    response += f"\n{risk_icon} **{proj['project_name']}** ({proj.get('status', 'N/A')})"
                    if proj.get('okr_links'):
                        response += f"\n   Links: {', '.join(proj['okr_links'][:2])}"
                    response += "\n"
            else:
                response += "\nNo projects currently linked to this OKR."
            
            return [TextContent(type="text", text=response)]
        
        elif name == "identify_risks":
            result = pi.identify_risks()
            
            # Format the response
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
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_department_okr_progress":
            department = arguments.get("department", "proddev")
            result = pi.get_department_okr_progress(department)
            
            # Format the response
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
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())