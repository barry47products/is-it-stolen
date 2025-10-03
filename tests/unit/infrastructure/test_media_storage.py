"""Unit tests for media storage."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from src.infrastructure.media.exceptions import MediaStorageError
from src.infrastructure.media.storage import LocalMediaStorage, MediaStorage


class TestLocalMediaStorage:
    """Test local filesystem media storage."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_dir: Path) -> MediaStorage:
        """Create storage instance for testing."""
        return LocalMediaStorage(base_path=temp_dir)

    async def test_stores_media_file(
        self, storage: LocalMediaStorage, temp_dir: Path
    ) -> None:
        """Should store media file and return file path."""
        # Arrange
        content = b"test image content"
        filename = "test_image.jpg"

        # Act
        file_path = await storage.store(content, filename)

        # Assert
        assert file_path.startswith(str(temp_dir))
        assert file_path.endswith(".jpg")
        stored_file = Path(file_path)
        assert stored_file.exists()
        assert stored_file.read_bytes() == content

    async def test_retrieves_stored_media(
        self, storage: LocalMediaStorage, temp_dir: Path
    ) -> None:
        """Should retrieve previously stored media."""
        # Arrange
        content = b"test image content"
        filename = "test_image.jpg"
        file_path = await storage.store(content, filename)

        # Act
        retrieved_content = await storage.retrieve(file_path)

        # Assert
        assert retrieved_content == content

    async def test_deletes_stored_media(
        self, storage: LocalMediaStorage, temp_dir: Path
    ) -> None:
        """Should delete stored media file."""
        # Arrange
        content = b"test image content"
        filename = "test_image.jpg"
        file_path = await storage.store(content, filename)

        # Act
        await storage.delete(file_path)

        # Assert
        assert not Path(file_path).exists()

    async def test_raises_error_when_retrieving_nonexistent_file(
        self, storage: LocalMediaStorage
    ) -> None:
        """Should raise MediaStorageError when file doesn't exist."""
        # Arrange
        nonexistent_path = "/nonexistent/path/file.jpg"

        # Act & Assert
        with pytest.raises(MediaStorageError) as exc_info:
            await storage.retrieve(nonexistent_path)

        assert "Failed to retrieve media" in str(exc_info.value)

    async def test_raises_error_when_deleting_nonexistent_file(
        self, storage: LocalMediaStorage
    ) -> None:
        """Should raise MediaStorageError when deleting nonexistent file."""
        # Arrange
        nonexistent_path = "/nonexistent/path/file.jpg"

        # Act & Assert
        with pytest.raises(MediaStorageError) as exc_info:
            await storage.delete(nonexistent_path)

        assert "Failed to delete media" in str(exc_info.value)

    async def test_generates_unique_filenames_for_same_original_name(
        self, storage: LocalMediaStorage, temp_dir: Path
    ) -> None:
        """Should generate unique filenames for multiple files with same name."""
        # Arrange
        content1 = b"first image"
        content2 = b"second image"
        filename = "test.jpg"

        # Act
        path1 = await storage.store(content1, filename)
        path2 = await storage.store(content2, filename)

        # Assert
        assert path1 != path2
        assert Path(path1).exists()
        assert Path(path2).exists()
        assert Path(path1).read_bytes() == content1
        assert Path(path2).read_bytes() == content2

    async def test_exists_returns_true_for_existing_file(
        self, storage: LocalMediaStorage, temp_dir: Path
    ) -> None:
        """Should return True when file exists."""
        # Arrange
        content = b"test content"
        file_path = await storage.store(content, "test.jpg")

        # Act
        exists = await storage.exists(file_path)

        # Assert
        assert exists is True

    async def test_exists_returns_false_for_nonexistent_file(
        self, storage: LocalMediaStorage
    ) -> None:
        """Should return False when file doesn't exist."""
        # Arrange
        nonexistent_path = "/nonexistent/file.jpg"

        # Act
        exists = await storage.exists(nonexistent_path)

        # Assert
        assert exists is False

    async def test_raises_error_when_storing_to_invalid_path(
        self, storage: LocalMediaStorage
    ) -> None:
        """Should raise MediaStorageError when storage path is invalid."""
        # Arrange
        content = b"test content"

        # Patch Path.write_bytes to raise PermissionError
        with patch.object(
            Path, "write_bytes", side_effect=PermissionError("No permission")
        ):
            # Act & Assert
            with pytest.raises(MediaStorageError) as exc_info:
                await storage.store(content, "test.jpg")

            assert "Failed to store media" in str(exc_info.value)

    async def test_exists_returns_false_on_exception(
        self, storage: LocalMediaStorage
    ) -> None:
        """Should return False when exists() encounters an exception."""
        # Arrange - Patch Path.exists to raise an exception
        with patch.object(Path, "exists", side_effect=OSError("Permission denied")):
            # Act
            exists = await storage.exists("/some/path")

            # Assert
            assert exists is False
