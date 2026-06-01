from fastmcp import Context, FastMCP

from src.core.handlers import tool_handler

example_router = FastMCP("example")


@example_router.tool()
@tool_handler
async def echo(message: str, ctx: Context) -> str:
    """Echo a message back. Replace with your first real tool."""
    return f"Echo: {message}"
