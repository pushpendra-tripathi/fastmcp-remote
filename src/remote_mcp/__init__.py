"""remote-mcp — scaffold a production-ready remote MCP server."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("remote-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
