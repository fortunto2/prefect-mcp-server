#!/usr/bin/env python

"""
Prefect MCP Server (using FastMCP)
--------------------------------
MCP server integrating with the Prefect API for managing workflows,
using FastMCP from the 'mcp' package.
"""

import os
import sys
import httpx
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator


from mcp.server.fastmcp import FastMCP, Context

# Prefect API Settings
PREFECT_API_URL = os.environ.get("PREFECT_API_URL", "http://localhost:4200/api")
PREFECT_API_KEY = os.environ.get("PREFECT_API_KEY", "")

# Headers for Prefect API requests
HEADERS = {
    "Content-Type": "application/json",
}

if PREFECT_API_KEY:
    HEADERS["Authorization"] = f"Bearer {PREFECT_API_KEY}"


class PrefectApiClient:
    """Client for interacting with the Prefect API."""

    def __init__(self, api_url: str, headers: Dict[str, str]):
        self.api_url = api_url
        self.headers = headers
        # Use httpx.AsyncClient for asynchronous requests, enable redirects
        self.client = httpx.AsyncClient(
            headers=headers, timeout=30.0, follow_redirects=True
        )
        print(f"PrefectApiClient initialized for {api_url}", file=sys.stderr)

    async def close(self):
        print("Closing PrefectApiClient...", file=sys.stderr)
        await self.client.aclose()
        print("PrefectApiClient closed.", file=sys.stderr)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Universal method for making requests with error handling."""
        url = f"{self.api_url}/{endpoint}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()  # Check response status
            return response.json()
        except httpx.HTTPStatusError as e:
            # Log HTTP error
            print(
                f"HTTP Error calling {method} {url}: {e.response.status_code} - {e.response.text}",
                file=sys.stderr,
            )
            # Return error dictionary
            return {
                "mcp_error": f"Prefect API Error: HTTP {e.response.status_code}",
                "details": e.response.text,
            }
        except httpx.RequestError as e:
            # Log connection/request error
            print(f"Request Error calling {method} {url}: {e}", file=sys.stderr)
            return {"mcp_error": f"Prefect API Request Error: {e}"}
        except Exception as e:
            # Log unexpected errors
            print(f"Unexpected Error calling {method} {url}: {e}", file=sys.stderr)
            return {"mcp_error": f"Unexpected Server Error: {e}"}

    # Define methods for specific Prefect API endpoints
    async def get_flows(self, limit: int = 20) -> Dict[str, Any]:
        # Use POST for listing/filtering as per Prefect API conventions
        return await self._request("POST", "flows/filter", json={"limit": limit})

    async def get_flow_runs(self, limit: int = 20) -> Dict[str, Any]:
        # Use POST for listing/filtering
        return await self._request("POST", "flow_runs/filter", json={"limit": limit})

    async def get_deployments(self, limit: int = 20) -> Dict[str, Any]:
        # Use POST for listing/filtering
        return await self._request("POST", "deployments/filter", json={"limit": limit})

    async def filter_flows(self, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
        # Filter data is sent in the POST request body
        return await self._request("POST", "flows/filter", json=filter_criteria)

    async def filter_flow_runs(self, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "flow_runs/filter", json=filter_criteria)

    async def filter_deployments(
        self, filter_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self._request("POST", "deployments/filter", json=filter_criteria)

    async def create_flow_run(
        self, deployment_id: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Parameters are sent in the POST request body
        data = {"parameters": parameters} if parameters is not None else {}
        return await self._request(
            "POST", f"deployments/{deployment_id}/create_flow_run", json=data
        )


# --- API Client Lifespan Management ---
@asynccontextmanager
async def prefect_api_lifespan(
    server: FastMCP,
) -> AsyncIterator[Dict[str, PrefectApiClient]]:
    """Async context manager to initialize and clean up the Prefect API client."""
    print("Initializing Prefect API Client for MCP server...", file=sys.stderr)
    # Create client instance on server startup
    client = PrefectApiClient(PREFECT_API_URL, HEADERS)
    try:
        # Pass the client into the server context, accessible by tools
        yield {"prefect_client": client}
    finally:
        # Close the client on server shutdown
        print("Cleaning up Prefect API Client...", file=sys.stderr)
        await client.close()


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
    # Get client from lifespan context
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    # Call API client method
    return await client.get_flows(limit=limit)


@mcp_server.tool()
async def list_flow_runs(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Get a list of flow runs from the Prefect API.

    Args:
        limit: Maximum number of flow runs to return (default 20).
    """
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    return await client.get_flow_runs(limit=limit)


@mcp_server.tool()
async def list_deployments(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Get a list of deployments from the Prefect API.

    Args:
        limit: Maximum number of deployments to return (default 20).
    """
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    return await client.get_deployments(limit=limit)


@mcp_server.tool()
async def filter_flows(ctx: Context, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Filter flows based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"flows": {"tags": {"all_": ["production"]}}}
    """
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    return await client.filter_flows(filter_criteria)


@mcp_server.tool()
async def filter_flow_runs(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter flow runs based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"flow_runs": {"state": {"type": {"any_": ["FAILED", "CRASHED"]}}}}
    """
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    return await client.filter_flow_runs(filter_criteria)


@mcp_server.tool()
async def filter_deployments(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter deployments based on specified criteria.

    Args:
        filter_criteria: Dictionary with filter criteria according to Prefect API.
                         Example: {"deployments": {"is_schedule_active": {"eq_": true}}}
    """
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    return await client.filter_deployments(filter_criteria)


@mcp_server.tool()
async def create_flow_run(
    ctx: Context, deployment_id: str, parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new flow run for the specified deployment.

    Args:
        deployment_id: ID of the deployment to create a run for.
        parameters: Dictionary with parameters for the flow run (optional).
    """
    client: PrefectApiClient = ctx.request_context.lifespan_context["prefect_client"]
    # Check for required argument deployment_id
    if not deployment_id:
        return {"mcp_error": "Missing required argument: deployment_id"}
    return await client.create_flow_run(deployment_id, parameters)


def main_run():
    print("Starting Prefect MCP Server using FastMCP...", file=sys.stderr)
    print(f"Connecting to Prefect API: {PREFECT_API_URL}", file=sys.stderr)
    if PREFECT_API_KEY:
        print("Using Prefect API Key: YES", file=sys.stderr)
    else:
        print("Using Prefect API Key: NO", file=sys.stderr)

    # mcp.run() starts the server and handles the stdio transport
    mcp_server.run()


# --- Main entry point for running the server ---
if __name__ == "__main__":
    main_run()
