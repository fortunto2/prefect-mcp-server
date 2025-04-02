#!/usr/bin/env python

"""
Prefect MCP Server (using FastMCP)
--------------------------------
MCP сервер, интегрирующийся с Prefect API для управления рабочими потоками,
используя FastMCP из пакета 'mcp'.
"""

import os
import sys
import httpx
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator


from mcp.server.fastmcp import FastMCP, Context

# Настройки Prefect API
PREFECT_API_URL = os.environ.get("PREFECT_API_URL", "http://localhost:4200/api")
PREFECT_API_KEY = os.environ.get("PREFECT_API_KEY", "")

# Заголовки для запросов к Prefect API
HEADERS = {
    "Content-Type": "application/json",
}

if PREFECT_API_KEY:
    HEADERS["Authorization"] = f"Bearer {PREFECT_API_KEY}"


class PrefectApiClient:
    """Клиент для взаимодействия с Prefect API."""

    def __init__(self, api_url: str, headers: Dict[str, str]):
        self.api_url = api_url
        self.headers = headers
        # Используем httpx.AsyncClient для асинхронных запросов
        self.client = httpx.AsyncClient(headers=headers, timeout=30.0)
        print(f"PrefectApiClient initialized for {api_url}", file=sys.stderr)

    async def close(self):
        print("Closing PrefectApiClient...", file=sys.stderr)
        await self.client.aclose()
        print("PrefectApiClient closed.", file=sys.stderr)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Универсальный метод для выполнения запросов с обработкой ошибок."""
        url = f"{self.api_url}/{endpoint}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()  # Проверяем статус ответа
            return response.json()
        except httpx.HTTPStatusError as e:
            # Логируем ошибку HTTP
            print(
                f"HTTP Error calling {method} {url}: {e.response.status_code} - {e.response.text}",
                file=sys.stderr,
            )
            # Возвращаем словарь с ошибкой
            return {
                "mcp_error": f"Prefect API Error: HTTP {e.response.status_code}",
                "details": e.response.text,
            }
        except httpx.RequestError as e:
            # Логируем ошибку соединения/запроса
            print(f"Request Error calling {method} {url}: {e}", file=sys.stderr)
            return {"mcp_error": f"Prefect API Request Error: {e}"}
        except Exception as e:
            # Логируем неожиданные ошибки
            print(f"Unexpected Error calling {method} {url}: {e}", file=sys.stderr)
            return {"mcp_error": f"Unexpected Server Error: {e}"}

    # Определяем методы для конкретных эндпоинтов Prefect API
    async def get_flows(self, limit: int = 20) -> Dict[str, Any]:
        return await self._request("GET", "flows", params={"limit": limit})

    async def get_flow_runs(self, limit: int = 20) -> Dict[str, Any]:
        return await self._request("GET", "flow_runs", params={"limit": limit})

    async def get_deployments(self, limit: int = 20) -> Dict[str, Any]:
        return await self._request("GET", "deployments", params={"limit": limit})

    async def filter_flows(self, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
        # Данные для фильтрации передаются в теле POST запроса
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
        # Параметры передаются в теле POST запроса
        data = {"parameters": parameters} if parameters is not None else {}
        return await self._request(
            "POST", f"deployments/{deployment_id}/create_flow_run", json=data
        )


# --- Управление жизненным циклом клиента API ---
@asynccontextmanager
async def prefect_api_lifespan(
    server: FastMCP,
) -> AsyncIterator[Dict[str, PrefectApiClient]]:
    """Асинхронный менеджер контекста для инициализации и очистки клиента Prefect API."""
    print("Initializing Prefect API Client for MCP server...", file=sys.stderr)
    # Создаем экземпляр клиента при старте сервера
    client = PrefectApiClient(PREFECT_API_URL, HEADERS)
    try:
        # Передаем клиент в контекст сервера, доступный для инструментов
        yield {"prefect_client": client}
    finally:
        # Закрываем клиент при остановке сервера
        print("Cleaning up Prefect API Client...", file=sys.stderr)
        await client.close()


# --- Определение MCP сервера с FastMCP ---
mcp_server = FastMCP(
    name="prefect",  # Имя сервера
    version="1.0.0",  # Версия сервера (установлена на 1.0.0)
    lifespan=prefect_api_lifespan,  # Указываем менеджер контекста
)

# --- Определение инструментов с декоратором @mcp.tool() ---


@mcp_server.tool()
async def list_flows(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Получить список потоков (flows) из Prefect API.

    Args:
        limit: Максимальное количество возвращаемых потоков (по умолчанию 20).
    """
    # Получаем клиент из контекста lifespan
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    # Вызываем метод клиента API
    return await client.get_flows(limit=limit)


@mcp_server.tool()
async def list_flow_runs(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Получить список запусков потоков (flow runs) из Prefect API.

    Args:
        limit: Максимальное количество возвращаемых запусков (по умолчанию 20).
    """
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    return await client.get_flow_runs(limit=limit)


@mcp_server.tool()
async def list_deployments(ctx: Context, limit: int = 20) -> Dict[str, Any]:
    """Получить список развертываний (deployments) из Prefect API.

    Args:
        limit: Максимальное количество возвращаемых развертываний (по умолчанию 20).
    """
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    return await client.get_deployments(limit=limit)


@mcp_server.tool()
async def filter_flows(ctx: Context, filter_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Фильтровать потоки по заданным критериям.

    Args:
        filter_criteria: Словарь с критериями фильтрации согласно Prefect API.
                         Пример: {"flows": {"tags": {"all_": ["production"]}}}
    """
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    return await client.filter_flows(filter_criteria)


@mcp_server.tool()
async def filter_flow_runs(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Фильтровать запуски потоков по заданным критериям.

    Args:
        filter_criteria: Словарь с критериями фильтрации согласно Prefect API.
                         Пример: {"flow_runs": {"state": {"type": {"any_": ["FAILED", "CRASHED"]}}}}
    """
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    return await client.filter_flow_runs(filter_criteria)


@mcp_server.tool()
async def filter_deployments(
    ctx: Context, filter_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Фильтровать развертывания по заданным критериям.

    Args:
        filter_criteria: Словарь с критериями фильтрации согласно Prefect API.
                         Пример: {"deployments": {"is_schedule_active": {"eq_": true}}}
    """
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    return await client.filter_deployments(filter_criteria)


@mcp_server.tool()
async def create_flow_run(
    ctx: Context, deployment_id: str, parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Создать новый запуск потока для указанного развертывания.

    Args:
        deployment_id: ID развертывания (deployment), для которого нужно создать запуск.
        parameters: Словарь с параметрами для запуска потока (опционально).
    """
    client: PrefectApiClient = ctx.lifespan_context["prefect_client"]
    # Проверяем наличие обязательного параметра deployment_id
    if not deployment_id:
        return {"mcp_error": "Missing required argument: deployment_id"}
    return await client.create_flow_run(deployment_id, parameters)


# --- Основная точка входа для запуска сервера ---
if __name__ == "__main__":
    print("Starting Prefect MCP Server using FastMCP...", file=sys.stderr)
    print(f"Connecting to Prefect API: {PREFECT_API_URL}", file=sys.stderr)
    if PREFECT_API_KEY:
        print("Using Prefect API Key: YES", file=sys.stderr)
    else:
        print("Using Prefect API Key: NO", file=sys.stderr)

    # mcp.run() запускает сервер и обрабатывает stdio транспорт
    mcp_server.run()
