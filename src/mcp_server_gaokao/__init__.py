# Corresponding to the following configuration in the pyproject.toml:
# [tool.poetry.scripts]
# mcp-server-gaokao = "mcp_server_gaokao:main"
from mcp_server_gaokao.server import main

__all__ = ["main"]
