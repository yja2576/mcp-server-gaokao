import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

import mcp.types as types
import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from mcp_server_gaokao.tools import QueryMajorInfo

query_major_info_tool = QueryMajorInfo()
tools_map = {query_major_info_tool.name: query_major_info_tool}

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # 输出到控制台
)


def create_mcp_server(return_format: str) -> Server:
    """
    创建并返回一个 MCP 服务器实例。
    """
    server = Server(name="gaokao-server")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=query_major_info_tool.name,
                description=query_major_info_tool.description,
                inputSchema=query_major_info_tool.parameters,
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            tool = tools_map[name]
        except Exception as e:
            text = str(e)
        else:
            result = tool.execute(**arguments, return_format=return_format)
            if result.success:
                text = f"{result.name}工具调用成功！返回内容如下：\n{result.content}"
            else:
                text = f"{result.name}工具调用失败！错误信息如下：\n{result.content}"
        return [types.TextContent(type="text", text=text)]

    return server


async def stdio_run(server: Server):
    """
    启动 MCP 服务器，使用标准输入输出 (stdio) 传输协议。
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def sse_run(server: Server, port: int):
    """
    启动 MCP 服务器，使用 Server-Sent Events (SSE) 传输协议。
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (
            read_stream,
            write_stream,
        ):
            await server.run(read_stream, write_stream, server.create_initialization_options())
        return Response()

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    uvicorn.run(starlette_app, host="127.0.0.1", port=port)


def streamable_http_run(server: Server, port: int, json_response):
    """
    启动 MCP 服务器，使用可流式传输的 HTTP 协议。
    """
    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logging.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logging.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )
    uvicorn.run(starlette_app, host="127.0.0.1", port=port)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MCP Server Gaokao")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="The transport protocol to use for the server: 'stdio', 'sse', or 'streamable-http'. Default is 'stdio'.",
    )
    parser.add_argument(
        "--return_format",
        choices=["json", "markdown"],
        default="json",
        help="The format of the return value from the tool: 'json' or 'markdown'. Default is 'json'.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="The port to run the server on. Default is 8000.",
    )
    parser.add_argument(
        "--json_response",
        action="store_true",
        help="Enable JSON responses instead of SSE streams.",
    )
    args = parser.parse_args()
    logging.info("Starting mcp-server-gaokao......")
    server = create_mcp_server(return_format=args.return_format)
    if args.transport == "stdio":
        asyncio.run(stdio_run(server))
    elif args.transport == "sse":
        sse_run(server, port=args.port)
    elif args.transport == "streamable-http":
        streamable_http_run(server, port=args.port, json_response=args.json_response)
