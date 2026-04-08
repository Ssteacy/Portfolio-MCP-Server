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
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from core.portfolio_logic import PortfolioIntelligence

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

# Initialize portfolio intelligence
logger.info("📊 Initializing PortfolioIntelligence...")
pi = PortfolioIntelligence()
logger.info("✅ PortfolioIntelligence initialized")


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
            description="Identify all risk signals across the portfolio including at-risk projects (red/yellow status) and overallocated people (>70% capacity). Can filter by department.",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Filter by department: 'company', 'proddev', 'secit', 'finops', 'field', 'people', 'marketing', 'legal'. Leave empty for all departments.",
                        "enum": ["", "company", "proddev", "secit", "finops", "field", "people", "marketing", "legal"],
                        "default": ""
                    }
                },
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
        ),
        Tool(
            name="get_portfolio_schema",
            description="Get the structure and schema of the Monday.com portfolio system including boards, relationships, and column definitions. Use this to understand what data is available and how it's connected.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_data",
            description="Flexible query tool to get raw portfolio data with relationships. Returns structured data that can be filtered and analyzed. Use this for custom queries not covered by specialized tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Data scope to retrieve",
                        "enum": ["all", "projects", "okrs", "people", "capacity"],
                        "default": "all"
                    },
                    "departments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by departments (e.g., ['proddev', 'secit']). Empty = all departments.",
                        "default": []
                    },
                    "include_relationships": {
                        "type": "boolean",
                        "description": "Include relationship mappings (projects→OKRs, projects→people, etc.)",
                        "default": True
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"🔧 call_tool invoked: {name} with arguments: {arguments}")
    
    try:
        if name == "get_project_status":
            logger.info(f"📊 Handling get_project_status")
            project_name = arguments.get("project_name")
            if not project_name:
                logger.warning("❌ project_name is missing")
                return [TextContent(type="text", text="Error: project_name is required")]
            
            logger.info(f"🔍 Looking up project: {project_name}")
            result = pi.get_project_status(project_name)
            if not result:
                logger.warning(f"❌ Project not found: {project_name}")
                return [TextContent(type="text", text=f"Project '{project_name}' not found")]
            
            logger.info(f"✅ Found project: {result['project_name']}")
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
            logger.info(f"✅ Returning response for {result['project_name']}")
            return [TextContent(type="text", text=response)]
        
        elif name == "get_lead_follow_breakdown":
            logger.info(f"📊 Handling get_lead_follow_breakdown")
            project_name = arguments.get("project_name")
            if not project_name:
                logger.warning("❌ project_name is missing")
                return [TextContent(type="text", text="Error: project_name is required")]
            
            logger.info(f"🔍 Looking up lead/follow for: {project_name}")
            result = pi.get_lead_follow_breakdown(project_name)
            if not result:
                logger.warning(f"❌ Project not found: {project_name}")
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
            department = arguments.get("department", "")
            result = pi.identify_risks()
            
            # Filter by department if specified
            if department:
                result['at_risk_projects']['projects'] = [
                    p for p in result['at_risk_projects']['projects'] 
                    if p.get('department') == department
                ]
                result['at_risk_projects']['count'] = len(result['at_risk_projects']['projects'])
                
                result['overallocated_people']['people'] = [
                    p for p in result['overallocated_people']['people']
                    if p.get('department') == department
                ]
                result['overallocated_people']['count'] = len(result['overallocated_people']['people'])
                
                result['total_risk_signals'] = result['at_risk_projects']['count'] + result['overallocated_people']['count']
            
            # Group projects by department
            projects_by_dept = {}
            for proj in result['at_risk_projects']['projects']:
                dept = proj['department'] if proj['department'] else 'company'
                if dept not in projects_by_dept:
                    projects_by_dept[dept] = []
                projects_by_dept[dept].append(proj)
            
            # Format the response
            dept_filter_text = f" in {department.upper()}" if department else ""
            response = f"""**Portfolio Risk Analysis{dept_filter_text}**

🚨 **Total Risk Signals:** {result['total_risk_signals']}

📊 **At-Risk Projects:** {result['at_risk_projects']['count']}
👥 **Overallocated People:** {result['overallocated_people']['count']}

"""
            # Show projects grouped by department
            for dept in sorted(projects_by_dept.keys()):
                projects = projects_by_dept[dept]
                response += f"\n**{dept.upper()} - {len(projects)} at-risk project(s):**\n"
                
                for proj in projects:
                    response += f"\n⚠️  **{proj['name']}** ({proj['status']})"
                    response += f"\n   Owner: {proj['owner']}"
                    
                    # Show OKR names if available
                    if proj.get('okr_names') and len(proj['okr_names']) > 0:
                        response += f"\n   OKRs: {', '.join(proj['okr_names'][:2])}"
                        if len(proj['okr_names']) > 2:
                            response += f" (+{len(proj['okr_names']) - 2} more)"
                    else:
                        response += f"\n   OKR Aligned: No"
                    
                    if proj['path_to_green'] and proj['path_to_green'] != 'Not documented':
                        response += f"\n   Path to Green: {proj['path_to_green'][:100]}..."
                    response += "\n"
            
            if result['overallocated_people']['count'] > 0:
                response += "\n**Overallocated People:**\n"
                for person in result['overallocated_people']['people']:
                    response += f"\n⚠️  **{person['name']}** - {person['capacity']}% allocated"
                    response += f"\n   Department: {person['department']}"
                    response += f"\n   Projects: {', '.join(person['projects'][:3])}"
                    if len(person['projects']) > 3:
                        response += f" (+{len(person['projects']) - 3} more)"
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
        
        elif name == "get_portfolio_schema":
            # Return the schema/structure of the portfolio system
            schema = {
                "boards": {
                    "portfolios": {
                        "description": "Project portfolio boards tracking initiatives across departments",
                        "departments": ["company (top-level/cross-functional)", "proddev", "secit", "finops", "field", "people", "marketing", "legal"],
                        "key_columns": [
                            "name", 
                            "status", 
                            "owner", 
                            "okr_links", 
                            "lead_project", 
                            "follow_projects", 
                            "path_to_green (action plan for at-risk projects to get back on track)"
                        ],
                        "subitems": "Used for two purposes: 1) Lead/Follow project relationships (identified by having multiple mirror/lookup columns), 2) Project milestones (fewer mirror columns). Not always clearly distinguished."
                    },
                    "okrs": {
                        "description": "OKR boards tracking objectives and key results",
                        "departments": ["company (top-level)", "proddev", "secit", "finops", "field", "people", "marketing", "legal"],
                        "key_columns": ["name", "type (Objective/Key Result)", "linked_projects"]
                    },
                    "capacity": {
                        "description": "People capacity boards tracking allocation across projects",
                        "departments": ["proddev", "secit", "finops", "field", "people", "marketing", "legal"],
                        "key_columns": ["person_name", "project_allocations", "total_capacity"],
                        "risk_threshold": "People with >70% capacity are considered overallocated"
                    }
                },
                "relationships": {
                    "projects_to_okrs": "Projects link to OKRs via okr_link columns",
                    "projects_to_projects": "Lead projects link to follow projects via subitems (identified by mirror columns)",
                    "projects_to_people": "Projects link to people via capacity boards",
                    "okrs_to_projects": "OKRs link back to contributing projects"
                },
                "status_values": {
                    "green": "On track",
                    "yellow": "At risk - needs attention",
                    "red": "Critical - blocked or significantly delayed (also at risk)",
                    "blue": "Completed (also called 'Done')",
                    "gray": "Not started",
                    "pink": "Cancelled or deprioritized"
                }
            }
            
            response = f"""**Monday.com Portfolio System Schema**

📋 **Available Boards:**

**Portfolio Boards** (Project tracking)
- Departments: 
  • company (top-level/cross-functional portfolio)
  • proddev, secit, finops, field, people, marketing, legal (department portfolios)
- Key Data: 
  • Status, Owner, OKR Links
  • Lead/Follow relationships (via subitems with mirror columns)
  • Milestones (via subitems with fewer mirror columns)
  • Path to Green (action plan for at-risk projects)

**OKR Boards** (Objectives & Key Results)
- Departments: company (top-level), proddev, secit, finops, field, people, marketing, legal
- Key Data: OKR name, Type (Objective/KR), Linked projects

**Capacity Boards** (People allocation)
- Departments: proddev, secit, finops, field, people, marketing, legal
- Key Data: Person name, Project allocations, Total capacity
- Risk Threshold: People with >70% capacity are considered overallocated

🔗 **Relationships:**
- Projects → OKRs (via okr_link columns)
- Projects → Projects (Lead/Follow via subitems - identified by mirror/lookup columns)
- Projects → People (via capacity boards)
- OKRs → Projects (reverse lookup)

📊 **Status Values:**
- 🟢 Green: On track
- 🟡 Yellow: At risk - needs attention
- 🔴 Red: Critical - blocked or significantly delayed
- 🔵 Blue: Completed (also called "Done")
- ⚪ Gray: Not Started
- 🩷 Pink: Cancelled or deprioritized

**Note:**
- "At risk" projects include both Yellow and Red statuses
- "Completed", "done", and "blue" all refer to the same status
- "Cancelled" and "deprioritized" both use Pink status

🎯 **Complete OKR List** (Current as of Q1 FY27 - updated 2026-04-08):
*For the most current OKR list, use get_portfolio_data with scope='okr'*

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

🔗 **Lead/Follow Project Examples:**

**Business Transformation: Ops Cloud Pricing & Packaging** (company)
  └─ [LEAD] ProdDev: OpsCloud Pricing & Packaging
  └─ [FOLLOW] Finance Contribution
  └─ [FOLLOW] Corporate Strategy Contribution

**Project 270** (company)
  └─ [LEAD] Field P270
  └─ [FOLLOW] Enterprise Customer Lifecycle Marketing
  └─ [FOLLOW] CTO: P270 Dashboards & Data

**PD Advance + Agents Enhancements & Usage** (company)
  └─ [LEAD] ProdDev: SRE Agent
  └─ [LEAD] ProdDev: Scribe Agent
  └─ [LEAD] ProdDev: Shift Agent

*Note: Lead/Follow subitems typically have 4+ mirror/lookup columns. Milestone subitems have fewer. Prefixes like [LEAD], [FOLLOW], [MS] are user conventions and not always reliable.*

📝 **Example Queries:**
- "Show me all red projects in proddev"
- "Which projects are contributing to KR3 in the company portfolio?"
- "What's the lead/follow breakdown for OpsCloud Pricing & Packaging?"
- "Show me overallocated people in secit"
- "Identify all at-risk projects across the company portfolio"
- "Get OKR progress for marketing department"
- "Show me all completed projects in people department"

💡 **Available Tools:**
- `get_portfolio_schema` - View this schema (you just used it!)
- `get_portfolio_data` - Flexible queries across departments/scopes/statuses
- `identify_risks` - Find at-risk projects and overallocated people (filterable by department)
- `get_okr_contributing_projects` - Projects aligned to specific OKRs
- `get_project_status` - Deep dive on a specific project
- `get_lead_follow_breakdown` - Project hierarchy details
- `get_department_okr_progress` - Department OKR rollup view
"""
            return [TextContent(type="text", text=response)]
        
        elif name == "get_portfolio_data":
            scope = arguments.get("scope", "all")
            departments = arguments.get("departments", [])
            include_relationships = arguments.get("include_relationships", True)
            
            result = {
                "scope": scope,
                "departments_filter": departments if departments else "all",
                "data": {}
            }
            
            # Get projects
            if scope in ["all", "projects"]:
                all_projects = pi._get_all_portfolio_items()
                
                # Filter by departments if specified
                if departments:
                    all_projects = [p for p in all_projects if p.get('_department') in departments]
                
                # Format project data
                projects_data = []
                for proj in all_projects:
                    status_label, status_color = pi._parse_status(proj)
                    
                    project_data = {
                        "id": proj['id'],
                        "name": proj['name'],
                        "department": proj.get('_department'),
                        "status": status_label,
                        "status_color": status_color,
                        "owner": pi._get_column_value(proj, pi.col_owner) or 'Unassigned',
                        "path_to_green": pi._get_column_value(proj, pi.col_path_to_green)
                    }
                    
                    # Add relationships if requested
                    if include_relationships:
                        okr_links = []
                        okr_names = []
                        okr_map = pi._get_all_okr_items()
                        
                        for okr_col in pi._get_okr_column_ids(proj):
                            linked_ids = pi._parse_board_relation(proj, okr_col)
                            okr_links.extend(linked_ids)
                            
                            for okr_id in linked_ids:
                                okr_item = okr_map.get(okr_id)
                                if okr_item:
                                    okr_names.append(okr_item['name'])
                        
                        project_data["okr_ids"] = okr_links
                        project_data["okr_names"] = okr_names
                    
                    projects_data.append(project_data)
                
                result["data"]["projects"] = {
                    "count": len(projects_data),
                    "items": projects_data
                }
            
            # Get OKRs
            if scope in ["all", "okrs"]:
                okr_map = pi._get_all_okr_items()
                okrs_data = []
                
                for okr_id, okr in okr_map.items():
                    okr_data = {
                        "id": okr_id,
                        "name": okr['name'],
                        "department": okr.get('_department')
                    }
                    okrs_data.append(okr_data)
                
                # Filter by departments if specified
                if departments:
                    okrs_data = [o for o in okrs_data if o.get('department') in departments]
                
                result["data"]["okrs"] = {
                    "count": len(okrs_data),
                    "items": okrs_data
                }
            
            # Format as readable text
            response = f"""**Portfolio Data Query Results**

📊 **Scope:** {scope}
🏢 **Departments:** {', '.join(departments) if departments else 'All'}
🔗 **Relationships:** {'Included' if include_relationships else 'Excluded'}

"""
            
            if "projects" in result["data"]:
                response += f"\n**Projects:** {result['data']['projects']['count']} found\n"
                for proj in result["data"]["projects"]["items"][:20]:  # Show first 20
                    response += f"\n• **{proj['name']}** ({proj['status']})"
                    response += f"\n  Dept: {proj['department']} | Owner: {proj['owner']}"
                    if include_relationships and proj.get('okr_names'):
                        response += f"\n  OKRs: {', '.join(proj['okr_names'][:2])}"
                    response += "\n"
                
                if result["data"]["projects"]["count"] > 20:
                    response += f"\n... and {result['data']['projects']['count'] - 20} more projects\n"
            
            if "okrs" in result["data"]:
                response += f"\n**OKRs:** {result['data']['okrs']['count']} found\n"
                for okr in result["data"]["okrs"]["items"][:10]:  # Show first 10
                    response += f"\n• {okr['name']} ({okr['department']})\n"
                
                if result["data"]["okrs"]["count"] > 10:
                    response += f"\n... and {result['data']['okrs']['count'] - 10} more OKRs\n"
            
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