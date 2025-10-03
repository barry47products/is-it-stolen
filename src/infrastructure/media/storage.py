"""Media storage implementations."""

from pathlib import Path
from typing import Protocol
from uuid import uuid4

from src.infrastructure.media.exceptions import MediaStorageError


class MediaStorage(Protocol):
    """Protocol for media storage backends."""

    async def store(self, content: bytes, filename: str) -> str:
        """Store media content and return file path."""
        ...  # pragma: no cover

    async def retrieve(self, file_path: str) -> bytes:
        """Retrieve media content by file path."""
        ...  # pragma: no cover

    async def delete(self, file_path: str) -> None:
        """Delete media file."""
        ...  # pragma: no cover

    async def exists(self, file_path: str) -> bool:
        """Check if media file exists."""
        ...  # pragma: no cover


class LocalMediaStorage:
    """Local filesystem media storage implementation."""

    def __init__(self, base_path: Path) -> None:
        """Initialize local media storage.

        Args:
            base_path: Base directory for storing media files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def store(self, content: bytes, filename: str) -> str:
        """Store media content locally.

        Args:
            content: Media file content as bytes
            filename: Original filename (used for extension)

        Returns:
            Absolute path to stored file

        Raises:
            MediaStorageError: If storage fails
        """
        try:
            # Generate unique filename with original extension
            extension = Path(filename).suffix
            unique_name = f"{uuid4()}{extension}"
            file_path = self.base_path / unique_name

            # Write content to file
            file_path.write_bytes(content)

            return str(file_path.absolute())
        except Exception as e:
            raise MediaStorageError(f"Failed to store media: {e}") from e

    async def retrieve(self, file_path: str) -> bytes:
        """Retrieve media content from local storage.

        Args:
            file_path: Path to media file

        Returns:
            Media file content as bytes

        Raises:
            MediaStorageError: If retrieval fails
        """
        try:
            path = Path(file_path)
            return path.read_bytes()
        except Exception as e:
            raise MediaStorageError(f"Failed to retrieve media: {e}") from e

    async def delete(self, file_path: str) -> None:
        """Delete media file from local storage.

        Args:
            file_path: Path to media file

        Raises:
            MediaStorageError: If deletion fails
        """
        try:
            path = Path(file_path)
            path.unlink()
        except Exception as e:
            raise MediaStorageError(f"Failed to delete media: {e}") from e

    async def exists(self, file_path: str) -> bool:
        """Check if media file exists in local storage.

        Args:
            file_path: Path to media file

        Returns:
            True if file exists, False otherwise
        """
        try:
            path = Path(file_path)
            return path.exists()
        except Exception:
            return False
