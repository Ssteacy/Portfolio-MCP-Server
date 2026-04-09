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
            description="Get portfolio summary with total projects, status breakdown, and tier breakdown. Can filter by department.",
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
            description="Get detailed information about a specific project including status, owner, OKR links, contributing projects, and milestones.",
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
            description="Get all milestones for a specific project.",
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
            description="Get all projects linked to a specific OKR (Objective or Key Result). Supports partial OKR name matching (e.g., 'KR3', 'Company O1', 'ProdDev KR5', 'Customer Trust').",
            inputSchema={
                "type": "object",
                "properties": {
                    "okr_query": {
                        "type": "string",
                        "description": "OKR identifier or partial name (e.g., 'KR3', 'Company O1', 'ProdDev KR5', 'Customer Trust')"
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional: Filter projects by department",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"]
                    }
                },
                "required": ["okr_query"]
            }
        ),
        Tool(
            name="search_projects",
            description="Search and filter projects. All parameters are optional. Use any combination of: project name query, department filter, and/or status filter. **Use this to find at-risk projects (Red or Yellow status)**. Leave all empty to get all projects.",
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
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_health",
            description="Get aggregate portfolio health metrics including health score, status percentages, and risk indicators. **For listing specific at-risk projects, use search_projects with status='Red' or 'Yellow' instead**. Can filter by department.",
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
            name="get_portfolio_schema",
            description="Get the complete structure and schema of the Monday.com portfolio system including all OKRs, boards, relationships, and column definitions. Use this FIRST to understand what data is available before answering user questions.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
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
                    response += f"  Status: {milestone['status']} | Owner: {milestone['owner']} | Target: {milestone['target_date']}\n\n"
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
            
            return [TextContent(type="text", text=response)]
        
        elif name == "search_projects":
            query = arguments.get("query", "")
            department = arguments.get("department") or None
            status = arguments.get("status") or None
            
            result = portfolio.search_projects(query, department, status)
            
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