#!/usr/bin/env python

"""
Prefect MCP Server (using FastMCP)
--------------------------------
MCP server integrating with the Prefect API for managing workflows,
using FastMCP from the 'mcp' package and official prefect-client.
"""

import os
import sys
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from uuid import UUID

from prefect.client.orchestration import get_client
from prefect.client.schemas.objects import Flow, FlowRun, Deployment
from prefect.client.schemas.filters import FlowFilter, FlowRunFilter, DeploymentFilter

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
mcp = FastMCP(
    name="prefect",  # Server name
    version="1.0.0",  # Server version
    lifespan=prefect_api_lifespan,  # Specify the context manager
)

# ------------------------------------------------------------------------
# Flow CRUD Operations
# ------------------------------------------------------------------------


@mcp.tool()
async def get_flow_by_id(ctx: Context, flow_id: str) -> Dict[str, Any]:
    """Get a flow by its ID.

    Args:
        flow_id: ID of the flow to retrieve.
    """
    if not flow_id:
        return {"error": "Missing required argument: flow_id"}

    async with get_client() as client:
        try:
            flow = await client.read_flow(UUID(flow_id))
            return {"flow": flow.model_dump()}
        except Exception as e:
            return {"error": f"Failed to get flow: {str(e)}"}


@mcp.tool()
async def get_flow_by_name(ctx: Context, name: str) -> Dict[str, Any]:
    """Get a flow by its name.

    Args:
        name: Name of the flow to retrieve.
    """
    if not name:
        return {"error": "Missing required argument: name"}

    async with get_client() as client:
        try:
            # Use correct flow_filter parameter
            flow_filter = FlowFilter(name={"equals": name})
            flows = await client.read_flows(flow_filter=flow_filter)

            if not flows:
                return {"error": f"No flow found with name: {name}"}

            # Return the first matching flow
            return {"flow": flows[0].model_dump()}
        except Exception as e:
            return {"error": f"Failed to get flow: {str(e)}"}


@mcp.tool()
async def list_flows(ctx: Context, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Get a list of flows from the Prefect API.

    Args:
        limit: Maximum number of flows to return (default 20).
        offset: Number of flows to skip (default 0).
    """
    async with get_client() as client:
        flows = await client.read_flows(limit=limit, offset=offset)
        return {"flows": [flow.model_dump() for flow in flows], "count": len(flows)}


@mcp.tool()
async def search_flows(
    ctx: Context,
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Search for flows by name and/or tags.

    Args:
        name: Optional name to search for (case-insensitive contains match).
        tags: Optional list of tags to filter by.
        limit: Maximum number of flows to return (default 20).
    """
    filter_dict = {}

    if name:
        filter_dict["name"] = {"contains": name}

    if tags:
        filter_dict["tags"] = {"all_": tags}

    async with get_client() as client:
        flow_filter = FlowFilter(**filter_dict)
        flows = await client.read_flows(flow_filter=flow_filter, limit=limit)
        return {"flows": [flow.model_dump() for flow in flows], "count": len(flows)}


# ------------------------------------------------------------------------
# Flow Run CRUD Operations
# ------------------------------------------------------------------------


@mcp.tool()
async def get_flow_run_by_id(ctx: Context, flow_run_id: str) -> Dict[str, Any]:
    """Get a flow run by its ID.

    Args:
        flow_run_id: ID of the flow run to retrieve.
    """
    if not flow_run_id:
        return {"error": "Missing required argument: flow_run_id"}

    async with get_client() as client:
        try:
            flow_run = await client.read_flow_run(UUID(flow_run_id))
            return {"flow_run": flow_run.model_dump()}
        except Exception as e:
            return {"error": f"Failed to get flow run: {str(e)}"}


@mcp.tool()
async def list_flow_runs(
    ctx: Context, limit: int = 20, offset: int = 0, flow_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get a list of flow runs from the Prefect API.

    Args:
        limit: Maximum number of flow runs to return (default 20).
        offset: Number of flow runs to skip (default 0).
        flow_id: Optional ID of the flow to filter runs by.
    """
    filter_dict = {}

    if flow_id:
        filter_dict["flow_id"] = {"equals": flow_id}

    async with get_client() as client:
        flow_run_filter = FlowRunFilter(**filter_dict) if filter_dict else None
        flow_runs = await client.read_flow_runs(
            flow_run_filter=flow_run_filter, limit=limit, offset=offset
        )
        return {
            "flow_runs": [run.model_dump() for run in flow_runs],
            "count": len(flow_runs),
        }


@mcp.tool()
async def search_flow_runs_by_state(
    ctx: Context,
    state_type: Optional[str] = None,
    state_name: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Search for flow runs by state.

    Args:
        state_type: Optional state type (e.g., "COMPLETED", "FAILED", "CRASHED").
        state_name: Optional state name (e.g., "Completed", "Failed").
        limit: Maximum number of flow runs to return (default 20).
    """
    filter_dict = {}

    if state_type:
        filter_dict["state"] = {"type": {"equals": state_type}}

    if state_name:
        filter_dict["state"] = {"name": {"equals": state_name}}

    async with get_client() as client:
        flow_run_filter = FlowRunFilter(**filter_dict) if filter_dict else None
        flow_runs = await client.read_flow_runs(
            flow_run_filter=flow_run_filter, limit=limit
        )
        return {
            "flow_runs": [run.model_dump() for run in flow_runs],
            "count": len(flow_runs),
        }


@mcp.tool()
async def cancel_flow_run(ctx: Context, flow_run_id: str) -> Dict[str, Any]:
    """Cancel a flow run.

    Args:
        flow_run_id: ID of the flow run to cancel.
    """
    if not flow_run_id:
        return {"error": "Missing required argument: flow_run_id"}

    async with get_client() as client:
        try:
            result = await client.cancel_flow_run(UUID(flow_run_id))
            return {"success": True, "result": str(result)}
        except Exception as e:
            return {"error": f"Failed to cancel flow run: {str(e)}"}


# ------------------------------------------------------------------------
# Deployment CRUD Operations
# ------------------------------------------------------------------------


@mcp.tool()
async def get_deployment_by_id(ctx: Context, deployment_id: str) -> Dict[str, Any]:
    """Get a deployment by its ID.

    Args:
        deployment_id: ID of the deployment to retrieve.
    """
    if not deployment_id:
        return {"error": "Missing required argument: deployment_id"}

    async with get_client() as client:
        try:
            deployment = await client.read_deployment(UUID(deployment_id))
            return {"deployment": deployment.model_dump()}
        except Exception as e:
            return {"error": f"Failed to get deployment: {str(e)}"}


@mcp.tool()
async def get_deployment_by_name(ctx: Context, name: str) -> Dict[str, Any]:
    """Get a deployment by its name.

    Args:
        name: Name of the deployment to retrieve, in format "flow_name/deployment_name".
    """
    if not name:
        return {"error": "Missing required argument: name"}

    if "/" not in name:
        return {"error": "Name should be in format 'flow_name/deployment_name'"}

    async with get_client() as client:
        try:
            flow_name, deployment_name = name.split("/", 1)

            # Use filters to find deployment by name
            deployment_filter = DeploymentFilter(
                name={"equals": deployment_name}, flow_name={"equals": flow_name}
            )
            deployments = await client.read_deployments(
                deployment_filter=deployment_filter
            )

            if not deployments:
                return {"error": f"No deployment found with name: {name}"}

            # Return the first matching deployment
            return {"deployment": deployments[0].model_dump()}
        except Exception as e:
            return {"error": f"Failed to get deployment: {str(e)}"}


@mcp.tool()
async def list_deployments(
    ctx: Context, limit: int = 20, offset: int = 0, flow_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get a list of deployments from the Prefect API.

    Args:
        limit: Maximum number of deployments to return (default 20).
        offset: Number of deployments to skip (default 0).
        flow_id: Optional ID of the flow to filter deployments by.
    """
    filter_dict = {}

    if flow_id:
        filter_dict["flow_id"] = {"equals": flow_id}

    async with get_client() as client:
        deployment_filter = DeploymentFilter(**filter_dict) if filter_dict else None
        deployments = await client.read_deployments(
            deployment_filter=deployment_filter, limit=limit, offset=offset
        )
        return {
            "deployments": [depl.model_dump() for depl in deployments],
            "count": len(deployments),
        }


@mcp.tool()
async def search_deployments_by_status(
    ctx: Context, is_schedule_active: Optional[bool] = None, limit: int = 20
) -> Dict[str, Any]:
    """Search for deployments by schedule status.

    Args:
        is_schedule_active: Filter deployments by whether their schedule is active.
        limit: Maximum number of deployments to return (default 20).
    """
    filter_dict = {}

    if is_schedule_active is not None:
        filter_dict["is_schedule_active"] = {"equals": is_schedule_active}

    async with get_client() as client:
        deployment_filter = DeploymentFilter(**filter_dict) if filter_dict else None
        deployments = await client.read_deployments(
            deployment_filter=deployment_filter, limit=limit
        )
        return {
            "deployments": [depl.model_dump() for depl in deployments],
            "count": len(deployments),
        }


@mcp.tool()
async def create_flow_run_from_deployment(
    ctx: Context,
    deployment_id: str,
    parameters: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
    timeout: int = 0,
) -> Dict[str, Any]:
    """Create a new flow run for the specified deployment.

    Args:
        deployment_id: ID of the deployment or name in format 'flow_name/deployment_name'.
        parameters: Dictionary with parameters for the flow run (optional).
        name: Optional name for the flow run.
        timeout: Timeout in seconds, 0 means no waiting for completion (default 0).
    """
    if not deployment_id:
        return {"error": "Missing required argument: deployment_id"}

    from prefect.deployments import run_deployment

    try:
        # Создаем flow run с помощью функции run_deployment
        result = await run_deployment(
            name=deployment_id,  # В документации это "name", а не "deployment_id"
            parameters=parameters or {},
            timeout=timeout,
            flow_run_name=name,
        )

        return {"flow_run_id": str(result)}
    except Exception as e:
        return {"error": f"Failed to create flow run: {str(e)}"}


# ------------------------------------------------------------------------
# Legacy Support / Backwards Compatibility
# ------------------------------------------------------------------------


@mcp.tool()
async def filter_flows(ctx: Context, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Filter flows based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"flows": {"tags": {"all_": ["production"]}}}
    """
    async with get_client() as client:
        flow_filter = FlowFilter(**filter_criteria)
        flows = await client.read_flows(flow_filter=flow_filter)
        return {"flows": [flow.model_dump() for flow in flows]}


@mcp.tool()
async def filter_flow_runs(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter flow runs based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"flow_runs": {"state": {"type": {"any_": ["FAILED", "CRASHED"]}}}}
    """
    async with get_client() as client:
        flow_run_filter = FlowRunFilter(**filter_criteria)
        flow_runs = await client.read_flow_runs(flow_run_filter=flow_run_filter)
        return {"flow_runs": [run.model_dump() for run in flow_runs]}


@mcp.tool()
async def filter_deployments(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter deployments based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"deployments": {"is_schedule_active": {"eq_": true}}}
    """
    async with get_client() as client:
        deployment_filter = DeploymentFilter(**filter_criteria)
        deployments = await client.read_deployments(deployment_filter=deployment_filter)
        return {"deployments": [deployment.model_dump() for deployment in deployments]}


@mcp.tool()
async def create_flow_run(
    ctx: Context, deployment_id: str, parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new flow run for the specified deployment (Legacy).

    Args:
        deployment_id: ID of the deployment to create a run for.
        parameters: Dictionary with parameters for the flow run (optional).
    """
    return await create_flow_run_from_deployment(ctx, deployment_id, parameters)


def main_run():
    print("Starting Prefect MCP Server using FastMCP...", file=sys.stderr)
    print(f"Prefect API URL: {PREFECT_API_URL}", file=sys.stderr)
    if PREFECT_API_KEY:
        print("Using Prefect API Key: YES", file=sys.stderr)
    else:
        print("Using Prefect API Key: NO", file=sys.stderr)

    # mcp.run() starts the server and handles the stdio transport
    mcp.run()


# --- Main entry point for running the server ---
if __name__ == "__main__":
    main_run()
