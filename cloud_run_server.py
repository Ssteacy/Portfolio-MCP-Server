#!/usr/bin/env python3
"""
Cloud Run HTTP wrapper for Monday.com Portfolio MCP Server
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import logging
from flask import Flask, request, jsonify
from core.portfolio_logic import PortfolioLogic

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize portfolio logic
logger.info("📊 Initializing PortfolioLogic...")
portfolio = PortfolioLogic()
logger.info("✅ PortfolioLogic initialized")

# Define available tools
TOOLS = {
    "get_portfolio_summary": {
        "handler": portfolio.get_portfolio_summary,
        "params": ["department"]
    },
    "get_project_details": {
        "handler": portfolio.get_project_details,
        "params": ["project_name", "department"]
    },
    "get_project_comments": {
        "handler": portfolio.get_project_comments,
        "params": ["project_name", "department"]
    },
    "get_contributing_projects": {
        "handler": portfolio.get_contributing_projects,
        "params": ["project_name"]
    },
    "get_milestones": {
        "handler": portfolio.get_milestones,
        "params": ["project_name", "department"]
    },
    "get_okr_links": {
        "handler": portfolio.get_okr_links,
        "params": ["project_name", "department"]
    },
    "get_projects_by_okr": {
        "handler": portfolio.get_projects_by_okr,
        "params": ["okr_name"]
    },
    "search_projects": {
        "handler": portfolio.search_projects,
        "params": ["query", "department", "status", "tier"]
    },
    "get_portfolio_health": {
        "handler": portfolio.get_portfolio_health,
        "params": ["department"]
    }
}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "monday-portfolio-mcp"}), 200

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools"""
    tools = [
        {
            "name": name,
            "parameters": info["params"]
        }
        for name, info in TOOLS.items()
    ]
    return jsonify({"tools": tools}), 200

@app.route('/tools/<tool_name>', methods=['POST'])
def call_tool(tool_name):
    """Call a specific tool"""
    if tool_name not in TOOLS:
        return jsonify({"error": f"Tool '{tool_name}' not found"}), 404

    try:
        # Get arguments from request
        args = request.get_json() or {}

        # Call the tool handler
        handler = TOOLS[tool_name]["handler"]
        result = handler(**args)

        return jsonify({"result": result}), 200

    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        "service": "Monday.com Portfolio Intelligence MCP Server",
        "version": "1.0",
        "endpoints": {
            "GET /health": "Health check",
            "GET /tools": "List available tools",
            "POST /tools/<tool_name>": "Call a specific tool"
        },
        "available_tools": list(TOOLS.keys())
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Starting MCP HTTP server on port {port}")
    app.run(host='0.0.0.0', port=port)
