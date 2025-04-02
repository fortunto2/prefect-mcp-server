# Prefect MCP Server

This repository contains an MCP (Meta Control Protocol) server that integrates with the Prefect API.
It allows controlling Prefect flows, flow runs, and deployments via MCP commands.

The server is built using the `mcp` library (specifically `FastMCP`).

## Features

- List Prefect flows, flow runs, and deployments.
- Filter flows, flow runs, and deployments based on criteria.
- Create new flow runs for specific deployments.
- Uses `httpx` for asynchronous communication with the Prefect API.

## Requirements

- Python 3.8+
- `uv` (for environment management and installation)

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your_github_username>/prefect-mcp-server.git
    cd prefect-mcp-server
    ```

2.  **Create a virtual environment and install dependencies using uv:**
    ```bash
    uv venv
    uv pip install -r requirements.txt
    # or directly from pyproject.toml
    # uv pip install -e . 
    ```
    Activate the environment:
    ```bash
    source .venv/bin/activate 
    ```

3.  **Configure Prefect API:**
    Set the following environment variables (e.g., in a `.env` file or directly):
    ```bash
    export PREFECT_API_URL="http://your-prefect-instance:4200/api" # Replace with your Prefect API URL
    export PREFECT_API_KEY="your_prefect_api_key"              # Optional: Your Prefect API key if required
    ```
    If you are using Prefect Cloud, the URL is typically `https://api.prefect.cloud/api/accounts/{account_id}/workspaces/{workspace_id}`.

4.  **Run the MCP server:**
    ```bash
    python prefect_mcp_server.py
    ```

The server will start and listen for MCP commands on standard input/output.

## Usage

You can interact with the server using an MCP client. Here are examples of commands:

- **List flows:**
  ```json
  {"mcp_command": "list_flows", "params": {"limit": 10}}
  ```

- **List flow runs:**
  ```json
  {"mcp_command": "list_flow_runs", "params": {"limit": 5}}
  ```

- **Create a flow run:**
  ```json
  {
    "mcp_command": "create_flow_run",
    "params": {
      "deployment_id": "your-deployment-id",
      "parameters": {"param1": "value1"}
    }
  }
  ```

Refer to the `prefect_mcp_server.py` script for the full list of available commands and their parameters. 