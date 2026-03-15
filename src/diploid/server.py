"""MCP server entry point for Diploid.

Exposes debate tools via the Model Context Protocol, allowing MCP clients
to initiate debates, submit positions, and retrieve convergence results.

Tools exposed:
- debate/start: Begin a new debate session with a decision prompt
- debate/position: Submit a position from a session
- debate/challenge: Submit a challenge to the other session's position
- debate/converge: Trigger convergence analysis
- debate/status: Get current state of a debate
- debate/history: Retrieve past debates and their outcomes
"""

from mcp.server import Server


def create_server() -> Server:
    """Create and configure the Diploid MCP server.

    Returns:
        Configured MCP Server instance with all debate tools registered.
    """
    pass


async def run() -> None:
    """Run the Diploid MCP server.

    Starts the server on stdio transport, ready to accept
    connections from MCP clients.
    """
    pass
