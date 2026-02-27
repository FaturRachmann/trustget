"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory."""
    return tmp_path


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """Create a sample file for testing."""
    filepath = tmp_path / "sample.txt"
    filepath.write_text("Sample content for testing")
    return filepath


@pytest.fixture
def sample_checksum_file(tmp_path: Path) -> Path:
    """Create a sample checksum file."""
    filepath = tmp_path / "checksums.txt"
    # SHA256 of "Sample content for testing"
    content = """abc123def456  sample.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  empty.txt"""
    filepath.write_text(content)
    return filepath
