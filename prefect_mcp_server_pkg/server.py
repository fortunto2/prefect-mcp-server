#!/usr/bin/env python

"""
Prefect MCP Server (using FastMCP)
--------------------------------
MCP server integrating with the Prefect API for managing workflows,
using FastMCP from the 'mcp' package and official prefect-client.
"""

import os
import sys
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from prefect.client.orchestration import get_client
from prefect.client.schemas.objects import Flow, FlowRun, Deployment

from mcp.server.fastmcp import FastMCP, Context

# Prefect API Settings
PREFECT_API_URL = os.environ.get("PREFECT_API_URL", "http://localhost:4200/api")
PREFECT_API_KEY = os.environ.get("PREFECT_API_KEY", "")


# --- API Client Lifespan Management ---
@asynccontextmanager
async def prefect_api_lifespan(
    server: FastMCP,
) -> AsyncIterator[Dict[str, Any]]:
    """Async context manager to initialize and clean up the Prefect API client."""
    print("Initializing Prefect API Client for MCP server...", file=sys.stderr)

    # Set environment variables for the client if provided
    if PREFECT_API_URL:
        os.environ["PREFECT_API_URL"] = PREFECT_API_URL
    if PREFECT_API_KEY:
        os.environ["PREFECT_API_KEY"] = PREFECT_API_KEY

    # No need to pre-initialize the client, we will create it in each tool
    yield {}


# --- MCP Server Definition with FastMCP ---
mcp_server = FastMCP(
    name="prefect",  # Server name
    version="1.0.0",  # Server version
    lifespan=prefect_api_lifespan,  # Specify the context manager
)

# --- Tool Definitions with @mcp.tool() decorator ---


@mcp_server.tool()
async def list_flows(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Get a list of flows from the Prefect API.

    Args:
        limit: Maximum number of flows to return (default 20).
    """
    async with get_client() as client:
        flows = await client.read_flows(limit=limit)
        return {"flows": [flow.model_dump() for flow in flows]}


@mcp_server.tool()
async def list_flow_runs(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Get a list of flow runs from the Prefect API.

    Args:
        limit: Maximum number of flow runs to return (default 20).
    """
    async with get_client() as client:
        flow_runs = await client.read_flow_runs(limit=limit)
        return {"flow_runs": [run.model_dump() for run in flow_runs]}


@mcp_server.tool()
async def list_deployments(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Get a list of deployments from the Prefect API.

    Args:
        limit: Maximum number of deployments to return (default 20).
    """
    async with get_client() as client:
        deployments = await client.read_deployments(limit=limit)
        return {"deployments": [deployment.model_dump() for deployment in deployments]}


@mcp_server.tool()
async def filter_flows(ctx: Context, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Filter flows based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"flows": {"tags": {"all_": ["production"]}}}
    """
    async with get_client() as client:
        flows = await client.read_flows(filter=filter_criteria)
        return {"flows": [flow.model_dump() for flow in flows]}


@mcp_server.tool()
async def filter_flow_runs(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter flow runs based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"flow_runs": {"state": {"type": {"any_": ["FAILED", "CRASHED"]}}}}
    """
    async with get_client() as client:
        flow_runs = await client.read_flow_runs(filter=filter_criteria)
        return {"flow_runs": [run.model_dump() for run in flow_runs]}


@mcp_server.tool()
async def filter_deployments(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter deployments based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"deployments": {"is_schedule_active": {"eq_": true}}}
    """
    async with get_client() as client:
        deployments = await client.read_deployments(filter=filter_criteria)
        return {"deployments": [deployment.model_dump() for deployment in deployments]}


@mcp_server.tool()
async def create_flow_run(
    ctx: Context, deployment_id: str, parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new flow run for the specified deployment.

    Args:
        deployment_id: ID of the deployment to create a run for.
        parameters: Dictionary with parameters for the flow run (optional).
    """
    if not deployment_id:
        return {"error": "Missing required argument: deployment_id"}

    from prefect.deployments import run_deployment

    # Создаем flow run с помощью функции run_deployment
    result = await run_deployment(
        name=deployment_id,  # В документации это "name", а не "deployment_id"
        parameters=parameters or {},
        timeout=0,  # Без ожидания завершения
    )

    return {"flow_run_id": str(result)}


def main_run():
    print("Starting Prefect MCP Server using FastMCP...", file=sys.stderr)
    print(f"Prefect API URL: {PREFECT_API_URL}", file=sys.stderr)
    if PREFECT_API_KEY:
        print("Using Prefect API Key: YES", file=sys.stderr)
    else:
        print("Using Prefect API Key: NO", file=sys.stderr)

    # mcp.run() starts the server and handles the stdio transport
    mcp_server.run()


# --- Main entry point for running the server ---
if __name__ == "__main__":
    main_run()
