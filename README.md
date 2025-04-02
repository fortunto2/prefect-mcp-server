# Prefect MCP Server

This repository provides a Prefect MCP server configuration using the `prefect-mcp-server` package with a reliable running mechanism via `uvx`. The configuration is tailored for use with the Cursor IDE.

## Prerequisites

- Python 3.9 or newer.
- A preferred virtual environment tool (such as uv) for managing Python environments.
- Prefect 3 (see [Prefect Documentation](https://docs.prefect.io/v3/get-started/install) for installation instructions).

## Installation

Create and activate your virtual environment, then install Prefect MCP Server:

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -U prefect-mcp-server
```

## Configuration

The server is configured via the `.cursor/mcp.json` file. The updated configuration is as follows:

```json
{
  "mcpServers": {
    "prefect": {
      "command": "uvx",
      "args": [
        "prefect-mcp-server"
      ],
      "env": {}
    }
  }
}
```

This configuration ensures that the server uses the `uvx` command with the exact package version installed via `uv pip install`. This approach provides enhanced reliability and consistency in your development environment.

## Environment Variables

Set the following environment variables to configure your Prefect environment. You can create a file named `.env` in the project root with entries such as:

```bash
PREFECT_API_URL=http://localhost:4200/api
```

Additionally, if needed, set other environment variables like `PREFECT_API_KEY` to authenticate with your Prefect server or Prefect Cloud.

## Running the Server

To start the server, you can run the following command:

```bash
uv run <script>
```

Alternatively, if you are using the Cursor IDE with its configuration, the server will be automatically invoked with the command specified in `.cursor/mcp.json`.

## Documentation

Detailed documentation on the Prefect MCP Server functionality and usage is available in the [docs/prefect_mcp_documentation.md](docs/prefect_mcp_documentation.md) file. The documentation includes:

- Complete list of available tools and their parameters
- Instructions for installation and configuration
- Examples of usage with different MCP clients
- Prefect 3.0 compatibility information

## Cursor Rules

This repository includes Cursor Rules for working with the Prefect MCP Server, located in the `.cursor/rules/` directory. These rules provide contextual help and guidance when working with Prefect MCP in the Cursor IDE.

## Additional Information

- For further details on Prefect installation and usage, please refer to the [Prefect Documentation](https://docs.prefect.io/).
- For information about the Model Context Protocol (MCP), see the [MCP Documentation](https://modelcontextprotocol.io/).
- Use `uv run` for running scripts within the configured environment as recommended by Cursor.

Happy coding! 