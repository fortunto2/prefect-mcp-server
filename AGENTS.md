# Repository Guidelines

## Project Structure & Module Organization
- `prefect_mcp_server_pkg/` contains the runtime package; `server.py` exposes all MCP tools and the console entry point defined in `pyproject.toml`.
- `docs/prefect_mcp_documentation.md` captures user-facing behavior; update it alongside feature changes.
- `Makefile`, `pyproject.toml`, and `uv.lock` manage builds and dependencies; never edit `uv.lock` by hand.
- `dist/` is generated output from packaging; remove artifacts with `make clean` before committing.

## Build, Test, and Development Commands
- `make build` (wraps `uv build`) packages the project for distribution and refreshes `dist/`.
- `make test` runs `pytest`; use it before every push even if no dedicated tests exist yet.
- `uv run prefect-mcp-server --help` exercises the CLI entry point locally. Provide `PREFECT_API_URL` and `PREFECT_API_KEY` in your shell when hitting a live Prefect instance.
- `make clean` clears build outputs to ensure reproducible artifacts.

## Coding Style & Naming Conventions
- Follow existing 4-space indentation and type-hinted async APIs as shown in `prefect_mcp_server_pkg/server.py`.
- Use `snake_case` for functions/tools (`get_flow_by_id`) and `SCREAMING_SNAKE_CASE` for module-level constants (`PREFECT_API_URL`).
- Prefer descriptive docstrings and in-line logging over comments; keep responses JSON-serializable for MCP clients.
- Run `uv run python -m compileall prefect_mcp_server_pkg` if you need a quick syntax check without tests.

## Testing Guidelines
- Tests should live under `tests/` and mirror tool modules (e.g., `tests/test_flows.py`).
- Name tests `test_<behavior>` and mock Prefect clients to avoid contacting real services.
- Use `pytest.mark.asyncio` for coroutine-based cases and assert on serialized dictionaries returned to MCP.
- Aim to exercise error paths (missing IDs, Prefect API failures) before feature merges.

## Commit & Pull Request Guidelines
- Use focused commit headers similar to existing history (`Fix: Use correct filter parameters…`) and limit scopes to a single concern.
- Reference related Prefect tickets or MCP issues in the body and note environment variables touched.
- Pull requests should include: summary of changes, testing commands executed, configuration prerequisites, and screenshots or terminal snippets when behavior is user-visible.
- Keep PRs small; coordinate larger efforts with maintainers via an outline in the description.

## Agent Integration Notes
- Document any new MCP tools or prompts in both `README.md` and `docs/` so client agents can surface them.
- When adding environment variables, list them in the README and provide sane defaults to avoid agent startup regressions.
