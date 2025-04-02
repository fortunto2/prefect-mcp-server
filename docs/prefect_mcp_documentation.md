# Prefect MCP Server Documentation

## Overview

Prefect MCP Server is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides integration with the Prefect API. It allows AI assistants and MCP clients to interact with Prefect workflows, deployments, and flow runs through standardized MCP tools.

The server implements the full MCP specification and provides a comprehensive set of CRUD operations for managing Prefect entities.

## Features

The Prefect MCP server provides the following capabilities:

### Flow Operations
- Get flow by ID or name
- List all flows with pagination
- Search flows by name and tags
- Filter flows with custom criteria

### Flow Run Operations
- Get flow run by ID
- List flow runs with pagination
- Search flow runs by state
- Cancel flow runs
- Create new flow runs from deployments

### Deployment Operations
- Get deployment by ID or name
- List deployments with pagination
- Search deployments by schedule status
- Filter deployments with custom criteria

## Installation

Install the package from PyPI:

```bash
pip install prefect-mcp-server
```

Alternatively, install using [uv](https://docs.astral.sh/uv):

```bash
uv pip install prefect-mcp-server
```

## Getting Started

### Running the Server

You can run the server directly from the command line:

```bash
prefect-mcp-server
```

### Environment Configuration

The server can be configured using the following environment variables:

- `PREFECT_API_URL`: URL of the Prefect API (default: "http://localhost:4200/api")
- `PREFECT_API_KEY`: API key for the Prefect API (optional)

### Using with MCP Inspector

To test the server with the MCP Inspector:

```bash
mcp dev prefect_mcp_server_pkg/server.py
```

### Using with Claude Desktop

To install the server in Claude Desktop:

```bash
mcp install prefect_mcp_server_pkg/server.py
```

## Tool Reference

### Flow Operations

#### get_flow_by_id
Get a flow by its ID.

**Parameters:**
- `flow_id` (str): ID of the flow to retrieve.

**Returns:**
- Dictionary containing the flow details or an error message.

#### get_flow_by_name
Get a flow by its name.

**Parameters:**
- `name` (str): Name of the flow to retrieve.

**Returns:**
- Dictionary containing the flow details or an error message.

#### list_flows
Get a list of flows from the Prefect API.

**Parameters:**
- `limit` (int, optional): Maximum number of flows to return. Default: 20.
- `offset` (int, optional): Number of flows to skip. Default: 0.

**Returns:**
- Dictionary containing the list of flows and the count.

#### search_flows
Search for flows by name and/or tags.

**Parameters:**
- `name` (str, optional): Optional name to search for (case-insensitive contains match).
- `tags` (List[str], optional): Optional list of tags to filter by.
- `limit` (int, optional): Maximum number of flows to return. Default: 20.

**Returns:**
- Dictionary containing the matching flows and the count.

### Flow Run Operations

#### get_flow_run_by_id
Get a flow run by its ID.

**Parameters:**
- `flow_run_id` (str): ID of the flow run to retrieve.

**Returns:**
- Dictionary containing the flow run details or an error message.

#### list_flow_runs
Get a list of flow runs from the Prefect API.

**Parameters:**
- `limit` (int, optional): Maximum number of flow runs to return. Default: 20.
- `offset` (int, optional): Number of flow runs to skip. Default: 0.
- `flow_id` (str, optional): Optional ID of the flow to filter runs by.

**Returns:**
- Dictionary containing the list of flow runs and the count.

#### search_flow_runs_by_state
Search for flow runs by state.

**Parameters:**
- `state_type` (str, optional): Optional state type (e.g., "COMPLETED", "FAILED", "CRASHED").
- `state_name` (str, optional): Optional state name (e.g., "Completed", "Failed").
- `limit` (int, optional): Maximum number of flow runs to return. Default: 20.

**Returns:**
- Dictionary containing the matching flow runs and the count.

#### cancel_flow_run
Cancel a flow run.

**Parameters:**
- `flow_run_id` (str): ID of the flow run to cancel.

**Returns:**
- Dictionary indicating success or failure.

### Deployment Operations

#### get_deployment_by_id
Get a deployment by its ID.

**Parameters:**
- `deployment_id` (str): ID of the deployment to retrieve.

**Returns:**
- Dictionary containing the deployment details or an error message.

#### get_deployment_by_name
Get a deployment by its name.

**Parameters:**
- `name` (str): Name of the deployment to retrieve, in format "flow_name/deployment_name".

**Returns:**
- Dictionary containing the deployment details or an error message.

#### list_deployments
Get a list of deployments from the Prefect API.

**Parameters:**
- `limit` (int, optional): Maximum number of deployments to return. Default: 20.
- `offset` (int, optional): Number of deployments to skip. Default: 0.
- `flow_id` (str, optional): Optional ID of the flow to filter deployments by.

**Returns:**
- Dictionary containing the list of deployments and the count.

#### search_deployments_by_status
Search for deployments by schedule status.

**Parameters:**
- `is_schedule_active` (bool, optional): Filter deployments by whether their schedule is active.
- `limit` (int, optional): Maximum number of deployments to return. Default: 20.

**Returns:**
- Dictionary containing the matching deployments and the count.

#### create_flow_run_from_deployment
Create a new flow run for the specified deployment.

**Parameters:**
- `deployment_id` (str): ID of the deployment or name in format 'flow_name/deployment_name'.
- `parameters` (Dict[str, Any], optional): Dictionary with parameters for the flow run.
- `name` (str, optional): Optional name for the flow run.
- `timeout` (int, optional): Timeout in seconds, 0 means no waiting for completion. Default: 0.

**Returns:**
- Dictionary containing the flow run ID or an error message.

### Filter Operations

#### filter_flows
Filter flows based on specified criteria.

**Parameters:**
- `filter_criteria` (Dict[str, Any]): Dictionary with filter criteria according to Prefect API.

**Returns:**
- Dictionary containing the matching flows.

#### filter_flow_runs
Filter flow runs based on specified criteria.

**Parameters:**
- `filter_criteria` (Dict[str, Any]): Dictionary with filter criteria according to Prefect API.

**Returns:**
- Dictionary containing the matching flow runs.

#### filter_deployments
Filter deployments based on specified criteria.

**Parameters:**
- `filter_criteria` (Dict[str, Any]): Dictionary with filter criteria according to Prefect API.

**Returns:**
- Dictionary containing the matching deployments.

## Prefect 3.0 Compatibility

As of version 1.1.2, the server fully supports Prefect 3.0 and its updated API. The main changes include:

- Updated parameter names for the filters in client methods:
  - `flow_filter=` instead of `filter=`
  - `flow_run_filter=` instead of `filter=`
  - `deployment_filter=` instead of `filter=`

## Development

### Project Structure

```
prefect_mcp/
├── prefect_mcp_server_pkg/
│   └── server.py       # Main server implementation
└── pyproject.toml      # Project metadata and dependencies
```

### Building and Publishing

The package is built and published to PyPI using GitHub Actions triggered by version tags.

To create a new release:

1. Update the version in `pyproject.toml`
2. Commit the changes
3. Create and push a new tag matching the version (e.g., `v1.1.2`)

## License

This project is licensed under the MIT License. 