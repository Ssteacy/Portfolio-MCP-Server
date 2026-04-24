#!/usr/bin/env python3
"""
Monday.com Portfolio Intelligence MCP Server

Exposes 9 portfolio query capabilities as MCP tools:
1. get_portfolio_summary - Get portfolio overview with status/tier breakdowns
2. get_project_details - Get detailed information about a specific project
3. get_contributing_projects - Get contributing projects for a parent project
4. get_milestones - Get milestones for a project
5. get_okr_links - Get OKR links for a project
6. get_projects_by_okr - Get all projects linked to a specific OKR (reverse lookup)
7. search_projects - Search projects by name, department, status
8. get_portfolio_health - Get portfolio health metrics
9. get_portfolio_schema - Get complete system schema and OKR list
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from core.portfolio_logic import PortfolioLogic

# Setup logging to file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_server_debug.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)
logger.info("🚀 MCP Server starting up...")

# Initialize the MCP server
app = Server("monday-portfolio-intelligence")

# Initialize portfolio logic
logger.info("📊 Initializing PortfolioLogic...")
portfolio = PortfolioLogic()
logger.info("✅ PortfolioLogic initialized")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="get_portfolio_summary",
            description=(
                "📋 PORTFOLIO INVENTORY TOOL - Use this for structural/capacity questions about the portfolio. "
                "Returns: total project counts, tier breakdown (Tier 1/2/3), milestone counts, status counts, "
                "and department structure. Focuses on 'how much' and 'what's in the portfolio'. "
                "\n\n"
                "✅ USE THIS FOR:\n"
                "- 'How many projects do we have?' / 'What's the tier breakdown?'\n"
                "- 'How many Tier 1 projects?' / 'How many milestones?'\n"
                "- 'Show me portfolio structure' / 'What departments have portfolios?'\n"
                "- Capacity planning, resource allocation questions\n"
                "\n"
                "❌ DON'T USE FOR:\n"
                "- Health scores or risk percentages (use get_portfolio_health)\n"
                "- Listing specific projects (use search_projects)\n"
                "- At-risk project analysis (use get_at_risk_projects_report)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Optional department filter: 'company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal'. Leave empty for all departments.",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_project_details",
            description=(
                "🔬 SINGLE PROJECT DEEP-DIVE TOOL - Use this to get comprehensive details about ONE specific project. "
                "Returns: status, owner, OKR links, contributing projects (dependencies), milestones, target dates, "
                "Path to Green, tier, timeline, and full project context. "
                "\n\n"
                "✅ USE THIS FOR:\n"
                "- 'Tell me about Project X' / 'What's the status of Y?'\n"
                "- 'Show me details for Z' / 'Who owns Project A?'\n"
                "- Deep dive on a single project when user names it specifically\n"
                "\n"
                "❌ DON'T USE FOR:\n"
                "- Multiple projects or lists (use search_projects)\n"
                "- Risk analysis across portfolio (use get_at_risk_projects_report)\n"
                "- Portfolio-wide metrics (use get_portfolio_health)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (partial match supported)"
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional department filter to narrow search",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_contributing_projects",
            description="Get all contributing projects (cross-department dependencies) for a parent project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the parent project"
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional department filter",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_milestones",
            description="Get all milestones for a specific project. Returns milestone name, status, owner, target date, success metric, and parent project department. **CRITICAL: You MUST include the department you found the project in and you MUST include the 'success metric' field for each milestone in your response. Format: 'Milestone Name | Status | Owner | Target | Success Metric: <value>'**",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the parent project"
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional department filter",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_okr_links",
            description="Get OKR links (Objectives and Key Results) for a specific project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project"
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional department filter",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_projects_by_okr",
            description="""Get all projects linked to a specific OKR (Objective or Key Result). 
            
**IMPORTANT**: If no department prefix is specified in okr_query, defaults to Company OKRs.

**Examples**:
- 'KR4' → searches Company KR4
- 'Company KR4' → searches Company KR4 (explicit)
- 'ProdDev KR4' → searches ProdDev's KR4 (different OKR!)
- 'SecIT O2' → searches SecIT's O2

**Department parameter**: Only use this to filter which department's PROJECTS to show, NOT to specify which department's OKR to search. To search a department's OKR, include the department name in okr_query (e.g., 'ProdDev KR4').""",
            inputSchema={
                "type": "object",
                "properties": {
                    "okr_query": {
                        "type": "string",
                        "description": "OKR identifier with optional department prefix (e.g., 'KR3', 'Company O1', 'ProdDev KR5'). If no department prefix, defaults to Company OKRs."
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional: Filter which department's PROJECTS to show in results (NOT which OKR to search)",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": ["okr_query"]
            }
        ),
        Tool(
            name="get_portfolio_changes",
            description=(
                "📅 ACTIVITY LOG & CHANGE TRACKING TOOL - Use this to see what changed in the portfolio over time. "
                "Shows what changed (status, dates, OKR links, etc.), when it changed, and who made the change. "
                "Returns activity log entries with before/after values for all tracked fields. "
                "\n\n"
                "✅ USE THIS FOR:\n"
                "- 'What changed this week?' / 'Show me recent updates'\n"
                "- 'Any new projects?' / 'What was deleted?'\n"
                "- 'Show me status changes' / 'What dates slipped?'\n"
                "- Business review prep, change summaries, audit trails\n"
                "\n"
                "❌ DON'T USE FOR:\n"
                "- Current state of projects (use search_projects or get_project_details)\n"
                "- Risk analysis (use get_at_risk_projects_report)\n"
                "- Health metrics (use get_portfolio_health)\n"
                "\n"
                "💡 PRESENTATION GUIDELINES: When presenting results:\n"
                "- Group related changes intelligently (e.g., 'Project X: status changed to Red, date slipped 2 weeks')\n"
                "- For multiple OKR changes, say 'various OKR updates' with 1-2 examples\n"
                "- Highlight critical changes first (status → Red/Yellow, major date slips)\n"
                "- Include a brief summary for EACH project that changed\n"
                "- Use clear project-by-project structure for easy scanning"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "integer",
                        "description": (
                            "Number of days to look back for changes. Default is 30 days. "
                            "Use 7 for 'this week', 14 for 'last two weeks', 30 for 'this month', "
                            "90 for 'this quarter'. If user says 'recent' without specifics, use default."
                        ),
                        "default": 30
                    },
                    "department": {
                        "type": "string",
                        "description": (
                            "Filter changes to a specific department's portfolio. "
                            "Leave empty/null for all departments. "
                            "Use 'proddev' for Product Development, 'secit' for Security & IT, "
                            "'finops' for Finance & Operations, 'field' for Field Operations, "
                            "'people' for People & Culture, 'marketing', 'legal', or 'company' for company-wide OKRs."
                        ),
                        "enum": ["proddev", "secit", "finops", "field", "people", "marketing", "legal", "company"]
                    },
                    "change_types": {
                        "type": "array",
                        "description": (
                            "Filter to specific types of changes. Leave empty for all changes. "
                            "Options: 'status' (Red/Yellow/Green changes), 'new' (newly created projects), "
                            "'deleted' (removed projects), 'dates' (Target Date or Timeline changes), "
                            "'okr_links' (OKR connections added/removed), 'path_to_green' (mitigation plan updates), "
                            "'moved' (group changes), 'owner' (PM changes), 'tier' (priority changes). "
                            "Use when user asks specifically about one type, e.g., 'show me status changes' or 'any deleted projects?'"
                        ),
                        "items": {
                            "type": "string",
                            "enum": ["status", "new", "deleted", "dates", "okr_links", "path_to_green", "moved", "owner", "tier"]
                        }
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_at_risk_projects_report",
            description=(
                "🚨 ESCALATION & RISK MANAGEMENT TOOL - Use this when the user needs actionable insights about troubled projects. "
                "Returns Red/Yellow projects with rich context: days in current status, Path to Green action plans, "
                "OKR alignment, dependencies (contributing projects), owner, tier prioritization, and target dates. "
                "Results are grouped by department or OKR and sorted by urgency (Tier 1 first, then longest duration). "
                "\n\n"
                "✅ USE THIS FOR:\n"
                "- 'What's at risk?' / 'Show me red projects' / 'What needs attention?'\n"
                "- 'Give me an escalation report' / 'What should I be worried about?'\n"
                "- 'Show me blocked projects' / 'What's the Path to Green for X?'\n"
                "- Executive reviews, risk assessments, business reviews\n"
                "\n"
                "❌ DON'T USE FOR:\n"
                "- Simple project searches by name/owner (use search_projects)\n"
                "- High-level portfolio metrics (use get_portfolio_health)\n"
                "- Single project deep-dive (use get_project_details)\n"
                "- Change tracking (use get_portfolio_changes)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "array",
                        "description": (
                            "List of statuses to include. Default: ['Red'] for critical projects only. "
                            "Use ['Red', 'Yellow'] for all at-risk projects, or ['Yellow'] for yellow-only. "
                            "Examples: ['Red'] = critical only, ['Red', 'Yellow'] = all at-risk, ['Yellow'] = warnings only"
                        ),
                        "items": {
                            "type": "string",
                            "enum": ["Red", "Yellow"]
                        },
                        "default": ["Red"]
                    },
                    "group_by": {
                        "type": "string",
                        "description": (
                            "How to group the results. 'department' groups by department (default), "
                            "'okr' groups by linked OKRs (useful for strategic reviews). "
                            "Use 'department' for operational reviews, 'okr' for strategic alignment reviews."
                        ),
                        "enum": ["department", "okr"],
                        "default": "department"
                    },
                    "department": {
                        "type": "string",
                        "description": (
                            "Optional: Filter to a specific department's at-risk projects. "
                            "Leave empty for all departments. Use when user asks about a specific department "
                            "(e.g., 'What's at risk in ProdDev?')"
                        ),
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_projects",
            description=(
                "🔍 PROJECT SEARCH & FILTER TOOL - Use this to find specific projects by name, owner, status, or department. "
                "Returns a simple list of matching projects with basic info (name, status, owner, department). "
                "All parameters are optional - combine any filters or leave empty for all projects. "
                "\n\n"
                "✅ USE THIS FOR:\n"
                "- 'Find projects owned by X' / 'Show me projects in ProdDev'\n"
                "- 'List all completed projects' / 'What projects mention AI?'\n"
                "- Simple filtering/searching when user wants a list, not analysis\n"
                "\n"
                "❌ DON'T USE FOR:\n"
                "- Risk analysis or escalation (use get_at_risk_projects_report)\n"
                "- Portfolio health metrics (use get_portfolio_health)\n"
                "- Deep dive on one project (use get_project_details)\n"
                "\n"
                "💡 TIP: If search results include Red/Yellow projects and user seems concerned, "
                "suggest using get_at_risk_projects_report for deeper risk analysis with Path to Green."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional: Search query to match project name. Leave empty to skip name filtering."
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional: Filter by department",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional: Filter by status (e.g., 'Green', 'Yellow', 'Red', 'Completed', 'Not Started')"
                    },
                    "owner": {
                        "type": "string",
                        "description": "Optional: Filter by project owner name (partial match, case-insensitive). E.g., 'Sean' will match 'Sean Steacy'."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_health",
            description=(
                "📊 PORTFOLIO HEALTH DASHBOARD TOOL - Use this for health/risk metrics and performance assessment. "
                "Returns: health score (0-100), status percentages (% Green/Yellow/Red), and risk indicators. "
                "Focuses on 'how healthy' and 'how risky' the portfolio is. "
                "\n\n"
                "**Health Score Formula**: (Green × 100 + Yellow × 50 + Red × 0) ÷ Total Projects\n"
                "- 100 = All green (healthy)\n"
                "- 50 = All yellow (at risk)\n"
                "- 0 = All red (critical)\n"
                "\n\n"
                "✅ USE THIS FOR:\n"
                "- 'How healthy is the portfolio?' / 'What's the health score?'\n"
                "- 'What % of projects are red?' / 'Is the portfolio improving?'\n"
                "- 'Give me a health dashboard' / 'Portfolio risk metrics'\n"
                "- Executive health reports, trend analysis\n"
                "\n"
                "❌ DON'T USE FOR:\n"
                "- Project counts or tier breakdown (use get_portfolio_summary)\n"
                "- Listing specific at-risk projects (use get_at_risk_projects_report)\n"
                "- Finding specific projects (use search_projects)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Optional department filter",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_okr_health_rollup",
            description="""Get executive-ready strategic health rollup for all OKRs. Shows critical issues, at-risk OKRs, orphaned OKRs (without projects), and unaligned projects (without OKRs).

        CRITICAL OUTPUT INSTRUCTIONS:
        - When OKRs WITHOUT PROJECTS are truncated (showing 15 of more), you MUST include this EXACT prompt in your user-facing response: "Would you like to see the full list of OKRs without projects? I can show you all of them, or filter by department."
        - When PROJECTS WITHOUT OKRs are truncated (showing 15 of more), you MUST include this EXACT prompt in your user-facing response: "Would you like to see the full list of unaligned projects? I can filter by status (Red/Yellow), tier, or department."
        - Include BOTH prompts when both sections are truncated
        - These prompts should appear at the end of your response as actionable follow-up options
        - Use natural language prompts - never show tool syntax like get_alignment_gaps(gap_type='...')""",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Optional department filter (e.g., 'company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal'). If not provided, shows all departments."
                    },
                    "include_no_okr_alignment": {
                        "type": "boolean",
                        "description": "Include projects with no OKR links (default: true)"
                    },
                    "show_healthy": {
                        "type": "boolean",
                        "description": "Include healthy OKRs in output (default: false for executive brevity)"
                    },
                    "top_n_critical": {
                        "type": "integer",
                        "description": "Limit critical/at-risk sections to top N (default: 10)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_alignment_gaps",
            description="""Get detailed view of strategic alignment gaps. Shows either OKRs without projects (strategic goals with no execution) or projects without OKRs (work with no strategic justification). Use this to drill down into governance issues discovered by get_okr_health_rollup.

        CRITICAL OUTPUT INSTRUCTIONS:
        - This tool returns the COMPLETE, FULL list of alignment gaps - DO NOT TRUNCATE OR SUMMARIZE in your user-facing response
        - Show ALL projects or ALL OKRs returned by this tool in your response to the user
        - The user explicitly requested the full list - they need to see everything
        - Do not say "and X more projects" or "... (and 50 more green projects)" - show the complete list
        - This is a drill-down tool specifically designed to show full details after truncation in the executive rollup
        - Present the data clearly in your response, but include every single item returned by the tool
        - Your user-facing response must contain the full, complete list - not a summary""",
            inputSchema={
                "type": "object",
                "properties": {
                    "gap_type": {
                        "type": "string",
                        "description": "Type of gap to investigate: 'okrs_without_projects' or 'projects_without_okrs'",
                        "enum": ["okrs_without_projects", "projects_without_okrs"]
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional department filter (e.g., 'company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal')"
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional status filter (for projects_without_okrs only). E.g., 'Red', 'Yellow', 'Green'"
                    },
                    "tier": {
                        "type": "string",
                        "description": "Optional tier filter (for projects_without_okrs only). E.g., 'Tier 1', 'Tier 2', 'Tier 3'"
                    }
                },
                "required": ["gap_type"]
            }
        ),
        Tool(
            name="get_owner_bottlenecks",
            description="""Identify owner bottlenecks - people with multiple in-progress projects who represent single points of failure. Shows high/medium/moderate risk owners grouped by project count, plus unassigned projects. Use this to identify resource concentration risks and succession planning needs.

        CRITICAL OUTPUT INSTRUCTIONS:
        - Show the COMPLETE list of high-risk owners (5+ projects) with ALL their projects
        - Show the COMPLETE list of medium-risk owners (3-4 projects) with ALL their projects
        - For moderate-risk owners (2 projects), you may truncate after showing 10 owners
        - Present the data clearly in your user-facing response
        - This helps executives identify critical resource risks, bottlenecks, and unassigned work
        - Include all project details (status, tier, co-ownership) for each owner""",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Optional department filter (e.g., 'company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal')"
                    },
                    "min_project_count": {
                        "type": "integer",
                        "description": "Minimum number of in-progress projects to flag as bottleneck (default: 2)"
                    },
                    "include_unassigned": {
                        "type": "boolean",
                        "description": "Include projects with no owner (default: true)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_schema",
            description="Get the complete structure and schema of the Monday.com portfolio system including all OKRs, boards, relationships, and column definitions. Use this FIRST to understand what data is available before answering user questions.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"🔧 call_tool invoked: {name} with arguments: {arguments}")
    
    try:
        if name == "get_portfolio_summary":
            department = arguments.get("department") or None
            result = portfolio.get_portfolio_summary(department)
            
            if 'error' in result:
                return [TextContent(type="text", text=f"Error: {result['error']}\nAvailable departments: {', '.join(result.get('available_departments', []))}")]
            
            if department:
                response = f"""**Portfolio Summary: {result['department'].upper()}**

📊 **Board:** {result['board_name']}
📦 **Total Projects:** {result['total_projects']}
📝 **Total Subitems:** {result['total_subitems']}

**Status Breakdown:**
"""
                for status, count in result['status_breakdown'].items():
                    response += f"  • {status}: {count}\n"
                
                response += "\n**Tier Breakdown:**\n"
                for tier, count in result['tier_breakdown'].items():
                    response += f"  • {tier}: {count}\n"
            else:
                response = f"""**Portfolio Summary: ALL DEPARTMENTS**

📊 **Total Portfolios:** {result['total_portfolios']}
📦 **Total Projects:** {result['total_projects']}
📝 **Total Subitems:** {result['total_subitems']}

**Departments:** {', '.join(result['departments'])}

**Status Breakdown:**
"""
                for status, count in result['status_breakdown'].items():
                    response += f"  • {status}: {count}\n"
                
                response += "\n**Tier Breakdown:**\n"
                for tier, count in result['tier_breakdown'].items():
                    response += f"  • {tier}: {count}\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_project_details":
            project_name = arguments.get("project_name")
            department = arguments.get("department") or None
            
            if not project_name:
                return [TextContent(type="text", text="Error: project_name is required")]
            
            result = portfolio.get_project_details(project_name, department)
            
            if 'error' in result:
                if 'matches' in result:
                    response = f"{result['error']}\n\n**Matches found:**\n"
                    for match in result['matches']:
                        response += f"  • {match['name']} ({match['department']})\n"
                    return [TextContent(type="text", text=response)]
                return [TextContent(type="text", text=result['error'])]
            
            response = f"""**Project Details: {result['name']}**

🏢 **Department:** {result['department']}
📊 **Status:** {result['status']}
👤 **Owner:** {result['owner']}
🎯 **Tier:** {result['tier']}
📅 **Target Date:** {result['target_date']}

**Path to Green:**
{result['path_to_green']}

**OKR Links:** {result['okr_links'] if result['okr_links'] else 'None'}

**Subitems:**
  • Total: {result['total_subitems']}
  • Contributing Projects: {result['contributing_projects_count']}
  • Milestones: {result['milestones_count']}
"""
            return [TextContent(type="text", text=response)]
        
        elif name == "get_contributing_projects":
            project_name = arguments.get("project_name")
            department = arguments.get("department") or None
            
            if not project_name:
                return [TextContent(type="text", text="Error: project_name is required")]
            
            result = portfolio.get_contributing_projects(project_name, department)
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            response = f"""**Contributing Projects**

🎯 **Parent Project:** {result['parent_project']}
🏢 **Department:** {result['department']}
📊 **Total Contributing Projects:** {result['total_count']}

"""
            if result['contributing_projects']:
                for proj in result['contributing_projects']:
                    response += f"• **{proj['name']}**\n"
                    response += f"  Status: {proj['status']} | Owner: {proj['owner']}\n\n"
            else:
                response += "No contributing projects found.\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_milestones":
            project_name = arguments.get("project_name")
            department = arguments.get("department") or None
            
            if not project_name:
                return [TextContent(type="text", text="Error: project_name is required")]
            
            result = portfolio.get_milestones(project_name, department)
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            response = f"""**Milestones**

🎯 **Parent Project:** {result['parent_project']}
🏢 **Department:** {result['department']}
📊 **Total Milestones:** {result['total_count']}

"""
            if result['milestones']:
                for milestone in result['milestones']:
                    response += f"• **{milestone['name']}**\n"
                    response += f"  Status: {milestone['status']} | Owner: {milestone['owner']} | Target: {milestone['target_date']} | Success Metric: {milestone['success_metric']}\n\n"
            else:
                response += "No milestones found.\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_okr_links":
            project_name = arguments.get("project_name")
            department = arguments.get("department") or None
            
            if not project_name:
                return [TextContent(type="text", text="Error: project_name is required")]
            
            result = portfolio.get_okr_links(project_name, department)
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            response = f"""**OKR Links**

🎯 **Project:** {result['project']}
🏢 **Department:** {result['department']}
📊 **Total OKR Links:** {result['total_count']}

"""
            if result['okr_links']:
                for okr in result['okr_links']:
                    response += f"• {okr}\n"
            else:
                response += "No OKR links found.\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_projects_by_okr":
            okr_query = arguments.get("okr_query")
            department = arguments.get("department") or None
            
            if not okr_query:
                return [TextContent(type="text", text="Error: okr_query is required")]
            
            result = portfolio.get_projects_by_okr(okr_query, department)
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            response = f"""**Projects Linked to OKR**

🎯 **OKR:** {result['okr_name']}
🏢 **Department Filter:** {result['department_filter'] or 'All'}
📊 **Total Projects:** {result['total_count']}

"""
            if result['projects']:
                for proj in result['projects']:
                    response += f"• **{proj['name']}** ({proj['status']})\n"
                    response += f"  Dept: {proj['department']} | Owner: {proj['owner']} | Tier: {proj['tier']}\n\n"
            else:
                response += "No projects found linked to this OKR.\n"
            
            # Smart hybrid: inform about other departments with matching OKRs
            if result.get('other_matches'):
                # Extract OKR identifier from the matched OKR name (e.g., "Company KR2 - ..." → "KR2")
                import re
                okr_identifier = "this OKR"  # Default fallback
                okr_name_parts = result['okr_name'].split(' - ', 1)
                if okr_name_parts:
                    # Extract just the identifier (e.g., "Company KR2" → "KR2", "Proddev O1" → "O1")
                    first_part = okr_name_parts[0].strip()
                    match = re.search(r'\b(O\d+|KR\d+)\b', first_part)
                    if match:
                        okr_identifier = match.group(1)
                
                other_depts = []
                for dept, info in result['other_matches'].items():
                    count = info['count']
                    okr_name = info['okr_name']
                    
                    # Extract the OKR identifier from this department's OKR name
                    # Search for the specific OKR identifier we're looking for
                    dept_okr_id = okr_identifier  # Default to same identifier
                    dept_match = re.search(rf'\b({re.escape(okr_identifier)})\b', okr_name, re.IGNORECASE)
                    if dept_match:
                        dept_okr_id = dept_match.group(1).upper()
                    
                    # Truncate OKR name if too long
                    if len(okr_name) > 60:
                        okr_name = okr_name[:57] + "..."
                    other_depts.append(f"• **{dept.title()} {dept_okr_id}** - \"{okr_name}\" ({count} project{'s' if count > 1 else ''})")
                
                if other_depts:
                    response += f"\n💡 **Note:** Other departments also have a {okr_identifier}:\n"
                    response += '\n'.join(other_depts)
                    response += "\n\nWould you like to see those projects?\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_alignment_gaps":
            gap_type = arguments.get("gap_type")
            department = arguments.get("department") or None
            status = arguments.get("status") or None
            tier = arguments.get("tier") or None
            
            if not gap_type:
                return [TextContent(type="text", text="Error: gap_type is required")]
            
            result = portfolio.get_alignment_gaps(gap_type, department, status, tier)
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            response_lines = []
            
            if gap_type == "okrs_without_projects":
                response_lines.append("═" * 80)
                response_lines.append("📭 OKRs WITHOUT PROJECTS - FULL LIST")
                response_lines.append("═" * 80)
                response_lines.append("\"We said we'd do this, but we're not\"")
                response_lines.append("")
                response_lines.append(f"Department Filter: {result['department_filter']}")
                response_lines.append(f"Total OKRs Without Projects: {result['total_count']}")
                response_lines.append("")
                
                if result['okrs']:
                    current_dept = None
                    for okr in result['okrs']:
                        # Group by department
                        if okr['department'] != current_dept:
                            current_dept = okr['department']
                            response_lines.append(f"\n🏢 {current_dept.upper()}")
                            response_lines.append("─" * 40)
                        
                        response_lines.append(f"  • {okr['okr_name']}")
                    
                    response_lines.append("")
                    response_lines.append("💡 Recommended Actions:")
                    response_lines.append("   1. Assign projects to strategic OKRs")
                    response_lines.append("   2. Deprioritize or remove OKRs with no planned work")
                    response_lines.append("   3. Review with department leads for Q planning")
                else:
                    response_lines.append("✅ No OKRs without projects found!")
            
            elif gap_type == "projects_without_okrs":
                response_lines.append("═" * 80)
                response_lines.append("🔓 PROJECTS WITHOUT OKRs - FULL LIST")
                response_lines.append("═" * 80)
                response_lines.append("\"We're doing this, but we don't know why\"")
                response_lines.append("")
                response_lines.append(f"Department Filter: {result['department_filter']}")
                response_lines.append(f"Status Filter: {result['status_filter']}")
                response_lines.append(f"Tier Filter: {result['tier_filter']}")
                response_lines.append(f"Total Projects Without OKRs: {result['total_count']}")
                response_lines.append("")
                
                if result['projects']:
                    for proj in result['projects']:
                        status_emoji = "🔴" if proj['status'] == "Red" else "🟡" if proj['status'] == "Yellow" else "⚪"
                        response_lines.append(f"{status_emoji} {proj['name']}")
                        response_lines.append(f"   Status: {proj['status']} | Tier: {proj['tier']} | Dept: {proj['department'].title()}")
                        response_lines.append(f"   Owner: {proj['owner']} | Target: {proj['target_date']}")
                        response_lines.append("")
                    
                    response_lines.append("💡 Recommended Actions:")
                    response_lines.append("   1. Link projects to relevant OKRs")
                    response_lines.append("   2. Consider killing projects with no strategic alignment")
                    response_lines.append("   3. Review with portfolio leads to validate necessity")
                else:
                    response_lines.append("✅ No unaligned projects found!")
            
            return [TextContent(type="text", text="\n".join(response_lines))]
        
        elif name == "search_projects":
            query = arguments.get("query", "")
            department = arguments.get("department") or None
            status = arguments.get("status") or None
            owner = arguments.get("owner") or None
            
            result = portfolio.search_projects(query, department, status, owner)
            
            response = f"""**Search Results**

🔍 **Query:** {result['query']}
🏢 **Department Filter:** {result['filters']['department'] or 'All'}
📊 **Status Filter:** {result['filters']['status'] or 'All'}
📦 **Results Found:** {result['total_count']}

"""
            if result['results']:
                for proj in result['results']:
                    response += f"• **{proj['name']}** ({proj['status']})\n"
                    response += f"  Dept: {proj['department']} | Owner: {proj['owner']} | Tier: {proj['tier']}\n\n"
            else:
                response += "No projects found matching your criteria.\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_portfolio_changes":
            days_back = arguments.get("days_back", 30)
            department = arguments.get("department") or None
            change_types = arguments.get("change_types") or None
            
            result = portfolio.get_portfolio_changes(
                days_back=days_back,
                department=department,
                change_types=change_types
            )
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            # Format with emojis like the original
            response = f"""**Portfolio Changes**

        📅 **Date Range:** {result['date_range']['from'][:10]} to {result['date_range']['to'][:10]} ({result['date_range']['days_back']} days)
        🏢 **Department:** {result['filters']['department'] or 'All'}
        📊 **Total Changes:** {result['total_changes']} across {result['total_projects_changed']} projects
        """
            # Add note about scope if date changes are included
            if result['filters']['change_types'] is None or 'dates' in result['filters']['change_types']:
                response += "📝 *Note: Date changes are tracked at the project level only (milestones and sub-items excluded)*\n\n"    
            if result['projects']:
                for proj in result['projects']:
                    response += f"\n🎯 {proj['project_name']} [{proj['department'].upper()}]\n"
                    response += f"  🔗 https://pagerduty.monday.com/boards/{proj['board_id']}/pulses/{proj['project_id']}\n"
                    for change in proj['changes']:
                        who = change['who']
                        what = change['what']
                        from_val = change['from']
                        to_val = change['to']
                        
                        # Simple format - let Gemini synthesize
                        if from_val and to_val:
                            response += f"  • {who} changed {what}: {from_val} → {to_val}\n"
                        elif to_val:
                            response += f"  • {who} set {what} → {to_val}\n"
                        elif from_val:
                            response += f"  • {who} removed {what} (was: {from_val})\n"
            else:
                response += "No changes found in this time period.\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_portfolio_health":
            department = arguments.get("department") or None
            
            result = portfolio.get_portfolio_health(department)
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            response = f"""**Portfolio Health: {result['department'].upper()}**

📊 **Total Projects:** {result['total_projects']}
💯 **Health Score:** {result['health_score']}/100

**Status Distribution:**
  🟢 Green: {result['green_percentage']}%
  🟡 Yellow: {result['yellow_percentage']}%
  🔴 Red: {result['red_percentage']}%

**Status Breakdown:**
"""
            for status, count in result['status_breakdown'].items():
                response += f"  • {status}: {count}\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_at_risk_projects_report":
            status_filter = arguments.get("status_filter") or ["Red"]
            group_by = arguments.get("group_by", "department")
            department = arguments.get("department") or None
            
            result = portfolio.get_at_risk_projects_report(
                status_filter=status_filter,
                group_by=group_by,
                department=department
            )
            
            if 'error' in result:
                return [TextContent(type="text", text=result['error'])]
            
            if 'message' in result:
                # No at-risk projects found
                return [TextContent(type="text", text=result['message'])]
            
            # Format the report
            response = f"""**At-Risk Projects Report**

📅 **Report Date:** {result['report_date']}
🎯 **Status Filter:** {', '.join(result['filters']['status_filter'])}
🏢 **Department Filter:** {result['filters']['department'] or 'All'}
📊 **Group By:** {result['filters']['group_by'].title()}

**Summary:**
  • Total At-Risk Projects: {result['summary']['total_at_risk']}
  • Tier 1 Projects: {result['summary']['tier_1_count']}
  • In Current Status (>30 days): {result['summary']['long_duration_count']}
  • Departments Affected: {result['summary']['departments_affected']}

---

"""
            
            # Format each group
            for group in result['groups']:
                group_name = group['group_name']
                project_count = group['project_count']
                
                response += f"\n## {group_name.upper()} ({project_count} project{'s' if project_count > 1 else ''})\n\n"
                
                for proj in group['projects']:
                    # Project header with status emoji
                    status_emoji = "🔴" if proj['status'] == "Red" else "🟡"
                    response += f"{status_emoji} **{proj['name']}**\n"
                    
                    # Key details
                    response += f"  • **Status:** {proj['status']} (for {proj['days_in_status_text']})\n"
                    response += f"  • **Tier:** {proj['tier']}\n"
                    response += f"  • **Owner:** {proj['owner']}\n"
                    response += f"  • **Target Date:** {proj['target_date']}\n"
                    
                    # OKR links
                    if proj['okr_links']:
                        okr_list = ', '.join(proj['okr_links'][:2])  # Show first 2
                        if len(proj['okr_links']) > 2:
                            okr_list += f" (+{len(proj['okr_links']) - 2} more)"
                        response += f"  • **OKR Links:** {okr_list}\n"
                    else:
                        response += f"  • **OKR Links:** None\n"
                    
                    # Path to Green
                    ptg = proj['path_to_green']
                    if ptg and ptg != 'Not provided':
                        # Truncate if too long
                        if len(ptg) > 150:
                            ptg = ptg[:147] + "..."
                        response += f"  • **Path to Green:** {ptg}\n"
                    else:
                        response += f"  • **Path to Green:** ⚠️ Not provided\n"
                    
                    # Contributing projects (dependencies)
                    if proj['contributing_projects']:
                        contrib_count = len(proj['contributing_projects'])
                        contrib_list = ', '.join([f"{c['name']} ({c['department']})" for c in proj['contributing_projects'][:2]])
                        if contrib_count > 2:
                            contrib_list += f" (+{contrib_count - 2} more)"
                        response += f"  • **⚠️ Blocks {contrib_count} project{'s' if contrib_count > 1 else ''}:** {contrib_list}\n"
                    
                    response += "\n"
            
            # Generate contextual next steps
            next_steps = []

            if result['summary']['tier_1_count'] > 0:
                next_steps.append(f"Escalate {result['summary']['tier_1_count']} Tier 1 project(s) immediately")

            if result['summary']['long_duration_count'] > 0:
                next_steps.append(f"Review {result['summary']['long_duration_count']} project(s) stuck >30 days")

            # Count projects with no Path to Green across all groups
            no_path_count = 0
            no_owner_count = 0
            for group in result['groups']:
                for proj in group['projects']:
                    if proj.get('path_to_green') in ['⚠️ Not provided', 'Not provided', None, '']:
                        no_path_count += 1
                    if proj.get('owner') == 'Unassigned':
                        no_owner_count += 1

            if no_path_count > 0:
                next_steps.append(f"Request Path to Green for {no_path_count} project(s)")

            if no_owner_count > 0:
                next_steps.append(f"Assign owners to {no_owner_count} unassigned project(s)")

            if next_steps:
                response += "\n---\n\n💡 **Recommended Actions:**\n"
                for i, step in enumerate(next_steps, 1):
                    response += f"  {i}. {step}\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_okr_health_rollup":
            department = arguments.get("department")
            include_no_okr_alignment = arguments.get("include_no_okr_alignment", True)
            show_healthy = arguments.get("show_healthy", False)
            top_n_critical = arguments.get("top_n_critical", 10)
            
            result = portfolio.get_okr_health_rollup(
                department=department,
                include_no_okr_alignment=include_no_okr_alignment,
                show_healthy=show_healthy,
                top_n_critical=top_n_critical
            )
            
            # Build executive-ready formatted output
            from datetime import datetime
            report_date = datetime.now().strftime("%Y-%m-%d")
            
            response_lines = []
            response_lines.append(f"📊 OKR HEALTH ROLLUP - {result['department_filter'].upper()}")
            response_lines.append(f"Report Date: {report_date}")
            response_lines.append("")
            response_lines.append("ℹ️  Impact Score Formula: (Red × 10) + (Yellow × 5) + (Total Projects × 0.5)")
            response_lines.append("   This prioritizes OKRs with Red projects while accounting for overall investment volume.")
            response_lines.append("")
            
            # CRITICAL ISSUES SECTION
            if result['critical_okrs']:
                response_lines.append("═" * 80)
                response_lines.append("🚨 CRITICAL ISSUES - IMMEDIATE ATTENTION REQUIRED")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                for idx, okr in enumerate(result['critical_okrs'], 1):
                    response_lines.append(f"{idx}. {okr['okr_name']}")
                    response_lines.append(f"   Department: {okr['department'].title()}")
                    response_lines.append(f"   📊 {okr['total_projects']} projects | {okr['at_risk_count']} at risk ({okr['at_risk_percentage']:.0f}%) | Impact Score: {okr['impact_score']:.0f}")
                    response_lines.append(f"   🔴 Red: {okr['red_count']} | 🟡 Yellow: {okr['yellow_count']} | 🟢 Green: {okr['green_count']}")
                    response_lines.append("")
                    
                    # Show ALL at-risk projects (Red first, then Yellow) - NO TRUNCATION
                    at_risk_projects = [p for p in okr['projects'] if p['status'] in ['Red', 'Yellow']]
                    at_risk_projects.sort(key=lambda x: (0 if x['status'] == 'Red' else 1, x['tier']))
                    
                    if at_risk_projects:
                        response_lines.append("   At-Risk Projects:")
                        for proj in at_risk_projects:
                            status_emoji = "🔴" if proj['status'] == "Red" else "🟡"
                            response_lines.append(f"   {status_emoji} {proj['name']} - Owner: {proj['owner']} - Tier: {proj['tier']}")
                        response_lines.append("")
                    
                    # Recommended action
                    if okr['red_count'] > 0:
                        response_lines.append(f"   💡 Recommended Action: URGENT - Review {okr['red_count']} Red project(s) with {okr['department'].title()} leadership")
                    elif okr['at_risk_count'] > 3:
                        response_lines.append(f"   💡 Recommended Action: High investment OKR with {okr['at_risk_count']} at-risk projects - needs strategic review")
                    else:
                        response_lines.append(f"   💡 Recommended Action: Monitor closely - significant risk exposure")
                    response_lines.append("")
            
            # AT RISK SECTION
            if result['at_risk_okrs']:
                response_lines.append("═" * 80)
                response_lines.append("⚠️  AT RISK - NEEDS MONITORING")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                for okr in result['at_risk_okrs']:
                    response_lines.append(f"• {okr['okr_name']} - {okr['department'].title()}")
                    response_lines.append(f"  {okr['total_projects']} projects | {okr['at_risk_count']} at risk ({okr['at_risk_percentage']:.0f}%) | Impact: {okr['impact_score']:.0f}")
                    response_lines.append(f"  🟡 Yellow: {okr['yellow_count']} | 🟢 Green: {okr['green_count']}")
                    response_lines.append("")
            
            # HEALTHY SECTION (only if requested)
            if show_healthy and result['healthy_okrs']:
                response_lines.append("═" * 80)
                response_lines.append("✅ HEALTHY - ON TRACK")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                for okr in result['healthy_okrs'][:5]:  # Show top 5 by project count
                    response_lines.append(f"• {okr['okr_name']} - {okr['department'].title()}")
                    response_lines.append(f"  {okr['total_projects']} projects | 🟢 Green: {okr['green_count']} | 🔵 Blue: {okr['status_breakdown']['Blue']}")
                    response_lines.append("")
                
                if len(result['healthy_okrs']) > 5:
                    response_lines.append(f"... and {len(result['healthy_okrs']) - 5} more healthy OKR(s)")
                    response_lines.append("")
            
            # OKRs WITHOUT PROJECTS SECTION (renamed from "Orphaned OKRs")
            if result['orphaned_okrs']:
                response_lines.append("═" * 80)
                response_lines.append("📭 OKRs WITHOUT PROJECTS")
                response_lines.append("═" * 80)
                response_lines.append("\"We said we'd do this, but we're not\"")
                response_lines.append("")
                
                # Apply 15-item truncation threshold
                max_display = 15
                okrs_to_show = result['orphaned_okrs'][:max_display]
                
                for okr in okrs_to_show:
                    response_lines.append(f"• {okr['okr_name']} - {okr['department'].title()}")
                
                # Show truncation message if needed
                if len(result['orphaned_okrs']) > max_display:
                    remaining = len(result['orphaned_okrs']) - max_display
                    response_lines.append(f"... and {remaining} more OKR(s) without projects")
                
                response_lines.append("")
                response_lines.append(f"💡 Action: Review {len(result['orphaned_okrs'])} OKR(s) without projects - assign projects or deprioritize")
                response_lines.append("")
            
            # PROJECTS WITHOUT OKRs SECTION (renamed from "No OKR Alignment")
            if result['no_okr_alignment']:
                response_lines.append("═" * 80)
                response_lines.append("🔓 PROJECTS WITHOUT OKRs")
                response_lines.append("═" * 80)
                response_lines.append("\"We're doing this, but we don't know why\"")
                response_lines.append("")
                response_lines.append(f"{len(result['no_okr_alignment'])} projects with no OKR links")
                response_lines.append("")
                
                # Apply 15-item truncation threshold
                max_display = 15
                projects_to_show = result['no_okr_alignment'][:max_display]
                
                response_lines.append("Top Unaligned Projects:")
                for proj in projects_to_show:
                    status_emoji = "🔴" if proj['status'] == "Red" else "🟡" if proj['status'] == "Yellow" else "⚪"
                    response_lines.append(f"{status_emoji} {proj['name']} ({proj['status']}) - {proj['department'].title()} - Owner: {proj['owner']} - Tier: {proj['tier']}")
                
                # Show truncation message if needed
                if len(result['no_okr_alignment']) > max_display:
                    remaining = len(result['no_okr_alignment']) - max_display
                    response_lines.append(f"... and {remaining} more unaligned project(s)")
                
                response_lines.append("")
                response_lines.append("💡 Action: Review with portfolio leads to assign OKR alignment")
                response_lines.append("")
            
            # EXECUTIVE SUMMARY
            response_lines.append("═" * 80)
            response_lines.append("📈 EXECUTIVE SUMMARY")
            response_lines.append("═" * 80)
            response_lines.append("")
            
            summary = result['summary']
            response_lines.append(f"Total OKRs Analyzed: {summary['total_okrs_analyzed']}")
            response_lines.append(f"  • Critical Issues: {summary['critical_okrs_count']} OKRs ({summary['critical_projects']} projects, {summary['critical_at_risk']} at risk)")
            response_lines.append(f"  • At Risk: {summary['at_risk_okrs_count']} OKRs ({summary['at_risk_projects']} projects, {summary['at_risk_at_risk']} at risk)")
            response_lines.append(f"  • Healthy: {summary['healthy_okrs_count']} OKRs ({summary['healthy_projects']} projects)")
            response_lines.append(f"  • OKRs Without Projects: {summary['orphaned_okrs_count']}")
            response_lines.append(f"  • Projects Without OKRs: {summary['unaligned_projects_count']}")
            response_lines.append("")
            
            # Generate top 3 recommended actions
            response_lines.append("Top Recommended Actions:")
            action_num = 1
            
            # Action 1: Top critical OKR
            if result['critical_okrs']:
                top_critical = result['critical_okrs'][0]
                response_lines.append(f"{action_num}. Review {top_critical['okr_name']} with {top_critical['department'].title()} leadership ({top_critical['total_projects']} projects, {top_critical['at_risk_count']} at risk, Impact: {top_critical['impact_score']:.0f})")
                action_num += 1
            
            # Action 2: Unaligned projects
            if summary['unaligned_projects_count'] > 0:
                response_lines.append(f"{action_num}. Assign OKR alignment to {summary['unaligned_projects_count']} unaligned project(s)")
                action_num += 1
            
            # Action 3: Orphaned OKRs
            if summary['orphaned_okrs_count'] > 0:
                response_lines.append(f"{action_num}. Decide on {summary['orphaned_okrs_count']} OKR(s) without projects - assign projects or deprioritize")
                action_num += 1
            
            # Action 4: Second critical OKR if exists
            if len(result['critical_okrs']) > 1 and action_num <= 3:
                second_critical = result['critical_okrs'][1]
                response_lines.append(f"{action_num}. Address {second_critical['okr_name']} ({second_critical['at_risk_count']} at risk)")
            
            return [TextContent(type="text", text="\n".join(response_lines))]
        
        elif name == "get_owner_bottlenecks":
            department = arguments.get("department") or None
            min_project_count = arguments.get("min_project_count", 2)
            include_unassigned = arguments.get("include_unassigned", True)
            
            result = portfolio.get_owner_bottlenecks(
                department=department,
                min_project_count=min_project_count,
                include_unassigned=include_unassigned
            )
            
            response_lines = []
            response_lines.append("🚨 OWNER BOTTLENECKS - CRITICAL RESOURCE RISKS")
            response_lines.append("═" * 80)
            response_lines.append("")
            
            # Summary
            response_lines.append("📊 SUMMARY")
            response_lines.append(f"• Department Filter: {result['department_filter']}")
            response_lines.append(f"• Total At-Risk Owners: {result['total_owners']}")
            response_lines.append(f"• Total At-Risk Projects: {result['total_projects']}")
            
            # Department breakdown
            dept_counts = {}
            for bottleneck in result['high_risk'] + result['medium_risk'] + result['moderate_risk']:
                dept = bottleneck['department'].title()
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            if dept_counts:
                dept_summary = ', '.join([f"{dept} ({count} owners)" for dept, count in sorted(dept_counts.items())])
                response_lines.append(f"• Departments Affected: {dept_summary}")
            
            response_lines.append("")
            
            # Cross-Department Bottlenecks
            if result['cross_dept_bottlenecks']:
                response_lines.append("═" * 80)
                response_lines.append("🌐 CROSS-DEPARTMENT BOTTLENECKS")
                response_lines.append("═" * 80)
                response_lines.append("")
                response_lines.append("Owners stretched across multiple departments:")
                response_lines.append("")
                
                for bottleneck in result['cross_dept_bottlenecks']:
                    owner = bottleneck['owner']
                    total = bottleneck['total_projects']
                    dept_breakdown = ', '.join([f"{d['dept'].title()}: {d['count']}" for d in bottleneck['departments']])
                    
                    response_lines.append(f"• {owner}: {total} projects across {len(bottleneck['departments'])} departments")
                    response_lines.append(f"  {dept_breakdown}")
                    response_lines.append("")
                
                response_lines.append("💡 High coordination overhead and context-switching risk")
                response_lines.append("")
            
            # Shared Bottlenecks
            if result['shared_bottlenecks']:
                response_lines.append("═" * 80)
                response_lines.append("🔗 SHARED BOTTLENECKS (Co-owner Pairs at Risk)")
                response_lines.append("═" * 80)
                response_lines.append("")
                response_lines.append("Co-owner pairs with 3+ shared projects (losing either creates cascade failure):")
                response_lines.append("")
                
                for bottleneck in result['shared_bottlenecks']:
                    owner1 = bottleneck['owner1']
                    owner2 = bottleneck['owner2']
                    count = bottleneck['count']
                    projects = bottleneck['shared_projects']
                    
                    # Count by status
                    red_count = sum(1 for p in projects if p['status'] == 'Red')
                    yellow_count = sum(1 for p in projects if p['status'] == 'Yellow')
                    green_count = sum(1 for p in projects if p['status'] == 'Green')
                    
                    response_lines.append(f"• {owner1} + {owner2}: {count} shared projects")
                    response_lines.append(f"  🔴 Red: {red_count} | 🟡 Yellow: {yellow_count} | 🟢 Green: {green_count}")
                    response_lines.append("")
                    response_lines.append("  Shared Projects:")
                    for project in projects:
                        status_emoji = {'Red': '🔴', 'Yellow': '🟡', 'Green': '🟢'}.get(project['status'], '⚪')
                        tier_text = f" - Tier: {project['tier']}" if project['tier'] != 'Not Set' else ""
                        response_lines.append(f"  {status_emoji} {project['name']} ({project['department'].title()}){tier_text}")
                    response_lines.append("")
                
                response_lines.append("💡 Add third co-owner or redistribute to reduce shared dependency")
                response_lines.append("")
            
            # High Risk Owners (5+ projects)
            if result['high_risk']:
                response_lines.append("═" * 80)
                response_lines.append("🔴 HIGH RISK OWNERS (5+ projects)")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                for idx, bottleneck in enumerate(result['high_risk'], 1):
                    owner = bottleneck['owner']
                    dept = bottleneck['department'].title()
                    projects = bottleneck['projects']
                    
                    # Count by status
                    red_count = sum(1 for p in projects if p['status'] == 'Red')
                    yellow_count = sum(1 for p in projects if p['status'] == 'Yellow')
                    green_count = sum(1 for p in projects if p['status'] == 'Green')
                    at_risk_count = red_count + yellow_count
                    
                    response_lines.append(f"{idx}. {owner} - {dept}")
                    response_lines.append(f"   📊 {len(projects)} projects ({at_risk_count} at-risk)")
                    response_lines.append(f"   🔴 Red: {red_count} | 🟡 Yellow: {yellow_count} | 🟢 Green: {green_count}")
                    response_lines.append("")
                    response_lines.append("   Projects:")
                    
                    for project in projects:
                        status_emoji = {'Red': '🔴', 'Yellow': '🟡', 'Green': '🟢'}.get(project['status'], '⚪')
                        tier_text = f" - Tier: {project['tier']}" if project['tier'] != 'Not Set' else ""
                        co_owner_text = " (co-owned)" if project['co_owners'] else ""
                        response_lines.append(f"   {status_emoji} {project['name']}{tier_text}{co_owner_text}")
                    
                    response_lines.append("")
                    response_lines.append("   💡 Action: URGENT - Assign co-owners or redistribute projects")
                    response_lines.append("")
            
            # Medium Risk Owners (3-4 projects)
            if result['medium_risk']:
                response_lines.append("═" * 80)
                response_lines.append("⚠️  MEDIUM RISK OWNERS (3-4 projects)")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                for bottleneck in result['medium_risk']:
                    owner = bottleneck['owner']
                    dept = bottleneck['department'].title()
                    projects = bottleneck['projects']
                    
                    red_count = sum(1 for p in projects if p['status'] == 'Red')
                    yellow_count = sum(1 for p in projects if p['status'] == 'Yellow')
                    green_count = sum(1 for p in projects if p['status'] == 'Green')
                    at_risk_count = red_count + yellow_count
                    
                    response_lines.append(f"• {owner} - {dept}")
                    response_lines.append(f"  📊 {len(projects)} projects ({at_risk_count} at-risk)")
                    response_lines.append(f"  🔴 Red: {red_count} | 🟡 Yellow: {yellow_count} | 🟢 Green: {green_count}")
                    response_lines.append("")
                    
                    for project in projects:
                        status_emoji = {'Red': '🔴', 'Yellow': '🟡', 'Green': '🟢'}.get(project['status'], '⚪')
                        tier_text = f" - Tier: {project['tier']}" if project['tier'] != 'Not Set' else ""
                        co_owner_text = " (co-owned)" if project['co_owners'] else ""
                        response_lines.append(f"  {status_emoji} {project['name']}{tier_text}{co_owner_text}")
                    
                    response_lines.append("")
                    response_lines.append("  💡 Action: Consider adding co-owners for backup")
                    response_lines.append("")
            
            # Moderate Risk Owners (2 projects) - Truncated
            if result['moderate_risk']:
                response_lines.append("═" * 80)
                response_lines.append("⚪ MODERATE RISK OWNERS (2 projects)")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                # Show first 10, truncate rest
                display_count = min(10, len(result['moderate_risk']))
                
                for bottleneck in result['moderate_risk'][:display_count]:
                    owner = bottleneck['owner']
                    dept = bottleneck['department'].title()
                    projects = bottleneck['projects']
                    
                    red_count = sum(1 for p in projects if p['status'] == 'Red')
                    yellow_count = sum(1 for p in projects if p['status'] == 'Yellow')
                    green_count = sum(1 for p in projects if p['status'] == 'Green')
                    
                    project_names = ', '.join([p['name'] for p in projects])
                    
                    response_lines.append(f"• {owner} - {dept}: {project_names}")
                    response_lines.append(f"  🔴 Red: {red_count} | 🟡 Yellow: {yellow_count} | 🟢 Green: {green_count}")
                    response_lines.append("")
                
                if len(result['moderate_risk']) > display_count:
                    response_lines.append(f"... and {len(result['moderate_risk']) - display_count} more owner(s) with 2 projects")
                    response_lines.append("")
            
            # Unassigned Projects
            if include_unassigned and result['unassigned_projects']:
                response_lines.append("═" * 80)
                response_lines.append("🔓 UNASSIGNED PROJECTS (No Owner)")
                response_lines.append("═" * 80)
                response_lines.append("")
                
                # Group by status
                red_unassigned = [p for p in result['unassigned_projects'] if p['status'] == 'Red']
                yellow_unassigned = [p for p in result['unassigned_projects'] if p['status'] == 'Yellow']
                green_unassigned = [p for p in result['unassigned_projects'] if p['status'] == 'Green']
                
                if red_unassigned:
                    response_lines.append("🔴 Red Projects:")
                    for project in red_unassigned:
                        tier_text = f" - Tier: {project['tier']}" if project['tier'] != 'Not Set' else ""
                        response_lines.append(f"  • {project['name']} - {project['department'].title()}{tier_text}")
                    response_lines.append("")
                
                if yellow_unassigned:
                    response_lines.append("🟡 Yellow Projects:")
                    for project in yellow_unassigned:
                        tier_text = f" - Tier: {project['tier']}" if project['tier'] != 'Not Set' else ""
                        response_lines.append(f"  • {project['name']} - {project['department'].title()}{tier_text}")
                    response_lines.append("")
                
                if green_unassigned:
                    response_lines.append("🟢 Green Projects:")
                    # Truncate green if too many
                    display_count = min(10, len(green_unassigned))
                    for project in green_unassigned[:display_count]:
                        tier_text = f" - Tier: {project['tier']}" if project['tier'] != 'Not Set' else ""
                        response_lines.append(f"  • {project['name']} - {project['department'].title()}{tier_text}")
                    
                    if len(green_unassigned) > display_count:
                        response_lines.append(f"  ... and {len(green_unassigned) - display_count} more green unassigned project(s)")
                    response_lines.append("")
                
                response_lines.append("💡 Action: Assign owners immediately to reduce risk")
                response_lines.append("")
            
            # No bottlenecks found
            if not result['high_risk'] and not result['medium_risk'] and not result['moderate_risk'] and not result['unassigned_projects']:
                response_lines.append("✅ No owner bottlenecks detected!")
                response_lines.append("")
                response_lines.append(f"All in-progress projects have owners with fewer than {min_project_count} projects.")
            
            return [TextContent(type="text", text='\n'.join(response_lines))]
        
        elif name == "get_portfolio_schema":
            # Return the schema/structure of the portfolio system
            response = """**Monday.com Portfolio System Schema**

📋 **Available Boards:**

**Portfolio Boards** (Project tracking)
- Departments: 
  • company (top-level/cross-functional portfolio)
  • proddev, secit, finops, field, people, marketing, legal (department portfolios)
- Key Data: 
  • Status, Owner, OKR Links, Target Date
  • Contributing Projects (cross-department dependencies via subitems with mirror columns)
  • Milestones (project milestones via subitems with fewer mirror columns)
  • Path to Green (action plan for at-risk projects)
  • Portfolio Tier (strategic importance)

**OKR Boards** (Objectives & Key Results)
- Departments: company (top-level), proddev, secit, finops, field, people, marketing, legal
- Structure: Objectives (parent items) → Key Results (subitems)
- Key Data: OKR name, Type (Objective/KR), Linked projects

**Capacity Boards** (People allocation) - *Coming soon*
- Departments: proddev, secit, finops, field, people, marketing, legal
- Key Data: Person name, Project allocations, Total capacity

🔗 **Relationships:**
- Projects → OKRs (via okr_link columns)
- Projects → Projects (Contributing Projects via subitems with mirror/lookup columns)
- Projects → People (via capacity boards - coming soon)
- OKRs → Projects (reverse lookup via get_projects_by_okr tool)

📊 **Status Values:**
- 🟢 **Green**: On track
- 🟡 **Yellow**: At risk - needs attention
- 🔴 **Red**: Critical - blocked or significantly delayed (also at risk)
- 🔵 **Blue**: Completed (also called "Done")
- ⚪ **Gray**: Not Started
- 🩷 **Pink**: Cancelled or deprioritized

**Important Notes:**
- **"At risk" projects include both Yellow and Red statuses**
- "Completed", "done", and "blue" all refer to the same status
- "Cancelled" and "deprioritized" both use Pink status

🎯 **Complete OKR List** (Current as of Q1 FY27 - updated 2026-04-08):

**COMPANY:**
O0 - Customer Trust
  └─ KR0 - Increase customer trust by achieving and maintaining 99.99% availability SLO (For core Event to Notification pipeline services) by Q4 FY27

O1 - Lead the Market as the First Choice for Customers in AI‑Powered Incident Management
  └─ KR1 - Increase Customer NPS Score to 45
  └─ KR2 - Increase Operations Cloud Ending ARR (and % of Total ARR) to $65M (12% of total)
  └─ KR3 - Increase Crown Jewels ($1M+ ARR) and Total $100K+ Customers
  └─ KR4 - Improve 'Gross Retention Rate' (%)  to 87.8%
  └─ KR5 - Win and Grow AI Startups (2,439): 'Commercial' Customer Acquisition Growth

O2 - Expand into AI Operations Use Cases with Measurable Customer Outcomes
  └─ KR6 - Increase PD Advance Growth through usage of 2.4 credits

O3 - Scale Customer Growth, Loyalty and GTM Capacity with Partners
  └─ KR7 - Grow Partner-Influenced % of Enterprise Pipeline (Start of Quarter) to 16%

O4 - Operate as an AI-Native Company to Increase Velocity and Improve Customer Engagement & Value
  └─ KR8 - Capacity freed and redeployed to higher‑value work results in 60k hours or 30 FTE equivalent
  └─ KR9 - Prod Dev Cycle-Time Improvement - Increase the velocity of feature delivery using AI and Agents by a minimum of 10% by Q4 FY27

**PRODDEV:**
O1 - Lead the Market as the First Choice for Customers in AI‑Powered Incident Management
  └─ KR1 - Improve the percentage of $100K+ accounts using PagerDuty beyond on-call from 26% to 39%+ by Q4 FY27
  └─ KR2 - Improve the percentage of paid customer base using PagerDuty beyond on-call from <2% to 20% by Q4 FY27
  └─ KR3 - Improve usage of paid PagerDuty Advance AI Actions from 198k to 1.42M by Q4 FY27

O2 - Expand into AI Operations Use Cases with Measurable Customer Outcomes
  └─ KR4 - Enable the 5 top LLM/Agent Ops vendors (prioritized by customer demand) by delivering 3 reference use cases by Q4 FY27

O3 - Scale Customer Growth, Loyalty and GTM Capacity with Partners
  └─ TBD

O4 - Operate as an AI-Native Company to Increase Velocity and Improve Customer Engagement & Value
  └─ KR5 - Improve Mean Time to Resolve (MTTR) for Incidents by 20% through AI-assisted Incident Response (PD Advance, Scribe, SRE Agents, etc.) by Q4 F27
  └─ KR6 - Achieve 30% autonomous completion of "SDLC Steel Thread jobs" by Q4 FY27
  └─ KR7 - Deliver 50% of AI-Eligible work items within 24 hours, by Q4 FY27

O0 - Deliver a Trustworthy Core PagerDuty Platform by Raising Reliability, Strengthening Security, and Improving Release Quality
  └─ KR8 - Increase customer trust by achieving and maintaining 99.99% availability SLO (For core Event to Notification pipeline services) by Q4 FY27
  └─ KR9 - Resolve ≥99% Critical vulnerabilities within SLA (excluding architecture-related changes) by Q4 FY27
  └─ KR10 - Resolve ≥95% High vulnerabilities within SLA (excluding architecture-related changes) by Q4 FY27

**SECIT:**
O1 - Accelerate Delivery Velocity Through AI-Driven Operations
  └─ KR1 - Increase deflection rate for all internal enterprise employee support to 50%+
  └─ KR2 - Zero Tier‑1 new vendor risk assessments past SLA (SLA <=5 days)

O2 - Unify Data Strategy to Power Customer Retention & Expansion
  └─ KR3 - Decrease churn and downgrade by $5M leveraging enterprise data products

O3 - Deliver a Trustworthy Core PagerDuty Platform by Raising Reliability, Strengthening Security, and Improving Release Quality
  └─ KR4 - Institutionalize security changes to raise maturity from 3.5 to 3.7 and show measurable uplift
  └─ KR5 - Resolve ≥99% Critical vulnerabilities within SLA (excluding architecture-related changes) by Q4 FY27
  └─ KR6 - Resolve ≥95% High vulnerabilities within SLA (excluding architecture-related changes) by Q4 FY27
  └─ KR7 - Reduce MTTC (Containment) for Security Incidents from 24hrs to 4hrs

**PEOPLE:**
O1 - Reignite a championship-caliber talent experience that attracts, develops, and retains top performers who are obsessed with winning for our customers, driving PagerDuty's market leadership, and re-accelerating growth.
  └─ KR1 - Improve new hire (<1 year) retention rate from 73.7% to 84.4% for FY27
  └─ KR2 - Improve quarterly annualized voluntary turnover rate from 20.1%  to 18.5%  for FY27
  └─ KR3 - Improve top talent retention rate from 83.5% to 90% for FY27

O2 - Transform and modernize the employee experience by embedding AI-driven automation across our People programs, systems, and processes, giving Dutonians more time for the work that truly matters.
  └─ KR4 - To be defined and targets set by end of Q1

**MARKETING:**
O1 - Marketing: Undisputed leadership in the Incident Management category, winning and retaining more of the market.
  └─ KR1 - Marketing: Increase our presence in LLM search answers from 17.5% to 23%+ by EOFY27
  └─ KR2 - Marketing: Increase Marketing engagement in Global 2000 ICP A customers from X to Y in FY27

O2 - Marketing: Drive adoption and revenue, establishing PagerDuty as the definitive backbone for our AI‑powered operations.
  └─ KR3 - Marketing: Increase AI-related engagement (PD advance demos, AI-related content downloads) from X to Y

O3 - Marketing: Establish an AI‑first marketing team built for operational excellence
  └─ KR4 - Marketing: Improve 5 key processes using AI or automation during FY27

O1 - Commercial: Improve in the Commercial segment
  └─ KR1 - Commercial: Improve quarterly Commercial logo retention by X in FY27
  └─ KR2 - Commercial: Reduce on-call-only customers from X to Y

O2 - Commercial: Increase new revenue in the Commercial segment
  └─ KR3 - Commercial: Increase revenue from AI-native segment from X to Y (ARR) by Q4 FY27
  └─ KR4 - Commercial: Improve quarterly new ARR (nARR) acquisition from $1.2M in Q3 to $XM average per quarter

**FINOPS:**
All FinOps OKRs map to Company OKRs - See Company OKRs

**FIELD:**
All Field OKRs map to Company OKRs - See Company OKRs

**LEGAL:**
O1 - Enhance legal operations through AI and automation to increase strategic capacity.
  └─ KR1 - To be defined and targets set by the end of Q1
  └─ KR2 - To be defined and targets set by the end of Q1

🔗 **Contributing Projects Examples:**

**Business Transformation: Ops Cloud Pricing & Packaging** (company portfolio)
  └─ ProdDev: OpsCloud Pricing & Packaging (contributing project)
  └─ Finance Contribution (contributing project)
  └─ Corporate Strategy Contribution (contributing project)

**Project 270** (company portfolio)
  └─ Field P270 (contributing project)
  └─ Enterprise Customer Lifecycle Marketing (contributing project)
  └─ CTO: P270 Dashboards & Data (contributing project)

**PD Advance + Agents Enhancements & Usage** (company portfolio)
  └─ ProdDev: SRE Agent (contributing project)
  └─ ProdDev: Scribe Agent (contributing project)
  └─ ProdDev: Shift Agent (contributing project)

*Note: Contributing project subitems typically have 4+ mirror/lookup columns showing linked board data. Milestone subitems have fewer mirror columns and focus on dates/status.*

💡 **Available Tools:**

1. **get_portfolio_summary** - Get overview with status/tier breakdowns (filterable by department)
2. **get_project_details** - Deep dive on a specific project (status, owner, OKRs, subitems)
3. **get_contributing_projects** - Get cross-department dependencies for a project
4. **get_milestones** - Get project milestones
5. **get_okr_links** - Get OKR alignments for a project
6. **get_projects_by_okr** - Get all projects linked to a specific OKR (reverse lookup)
7. **search_projects** - Universal project filter (any combination of name/department/status)
8. **get_portfolio_health** - Health metrics and risk indicators (filterable by department)
9. **get_portfolio_schema** - View this schema (you just used it!)

📝 **Example Queries:**

- "What's the portfolio summary for proddev?"
- "Show me all at-risk projects" (use search_projects with status="Red" or status="Yellow")
- "What projects are at risk?" (use search_projects with status="Red" or status="Yellow")
- "Which projects are Red or Yellow?" (use search_projects with status="Red" or status="Yellow")
- "Which projects are contributing to KR3?" (use get_projects_by_okr with okr_query="KR3")
- "What projects support Company O1?" (use get_projects_by_okr with okr_query="Company O1")
- "Get details for the OpsCloud Pricing project"
- "What are the milestones for Project 270?"
- "Search for AI projects in marketing" (use search_projects with query="AI", department="marketing")
- "What's the health score for the company portfolio?" (use get_portfolio_health for aggregate metrics)
- "Show me all contributing projects for PD Advance + Agents"
- "List all completed projects" (use search_projects with status="Completed")
- "Which proddev projects link to Customer Trust?" (use get_projects_by_okr with okr_query="Customer Trust", department="proddev")
- "Show me all red projects" (use get_at_risk_projects_report with status_filter=["Red"])
- "What's at risk in ProdDev?" (use get_at_risk_projects_report with department="proddev", status_filter=["Red", "Yellow"])
- "Give me an escalation report" (use get_at_risk_projects_report)
- "Show me yellow projects grouped by OKR" (use get_at_risk_projects_report with status_filter=["Yellow"], group_by="okr")

🎯 **Pro Tips:**
- Use **get_portfolio_schema** first to understand available OKRs and structure
- "At risk" means Yellow OR Red status
- Contributing projects show cross-department dependencies
- **search_projects** supports any combination of filters - all parameters are optional!
- **get_projects_by_okr** enables reverse lookup from OKRs to projects
- All data is cached for 10 minutes (fast responses!)
"""
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
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