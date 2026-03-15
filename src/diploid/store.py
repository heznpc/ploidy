"""Persistence layer for Diploid.

Stores debate history, session contexts, and convergence results
using aiosqlite for async SQLite access. All debate data is persisted
so that future sessions can reference past decisions -- this is how
Session A (the experienced session) accumulates context over time.

Tables:
    debates      -- Debate metadata (id, prompt, status, timestamps)
    sessions     -- Session contexts and roles within a debate
    messages     -- Individual debate messages with phase information
    convergence  -- Convergence results and synthesis outputs
"""

import aiosqlite


class DebateStore:
    """Async SQLite store for debate data.

    Provides CRUD operations for debates, sessions, messages,
    and convergence results.
    """

    def __init__(self, db_path: str = "diploid.db") -> None:
        """Initialize the store.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create database tables if they don't exist.

        Sets up the schema for debates, sessions, messages,
        and convergence results.
        """
        pass

    async def save_debate(self, debate_id: str, prompt: str) -> None:
        """Persist a new debate record.

        Args:
            debate_id: Unique identifier for the debate.
            prompt: The decision prompt for the debate.
        """
        pass

    async def get_debate(self, debate_id: str) -> dict | None:
        """Retrieve a debate by its ID.

        Args:
            debate_id: The debate to look up.

        Returns:
            Debate record as a dict, or None if not found.
        """
        pass

    async def list_debates(self, limit: int = 50) -> list[dict]:
        """List recent debates.

        Args:
            limit: Maximum number of debates to return.

        Returns:
            List of debate records, most recent first.
        """
        pass

    async def close(self) -> None:
        """Close the database connection."""
        pass
