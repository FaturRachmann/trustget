"""
Unit tests for TrustGet verifier module.
"""

import pytest
from pathlib import Path
from trustget.verifier import (
    Verifier,
    VerificationResult,
    VerificationStatus,
    VerificationError,
)
from trustget.scanner import ChecksumEntry


class TestVerificationResult:
    """Tests for VerificationResult."""

    def test_is_verified_true(self):
        result = VerificationResult(
            status=VerificationStatus.VERIFIED,
            filepath=Path("test.txt"),
        )
        assert result.is_verified is True

    def test_is_verified_false(self):
        result = VerificationResult(
            status=VerificationStatus.MISMATCH,
            filepath=Path("test.txt"),
        )
        assert result.is_verified is False

    def test_to_dict(self):
        result = VerificationResult(
            status=VerificationStatus.VERIFIED,
            filepath=Path("test.txt"),
            algorithm="sha256",
            expected_hash="abc123",
            actual_hash="abc123",
        )
        data = result.to_dict()
        assert data["status"] == "VERIFIED"
        assert data["filepath"] == "test.txt"
        assert data["algorithm"] == "sha256"


class TestVerifier:
    """Tests for Verifier."""

    @pytest.fixture
    def temp_file(self, tmp_path: Path) -> Path:
        """Create a temporary file for testing."""
        filepath = tmp_path / "test.txt"
        filepath.write_text("Hello, World!")
        return filepath

    @pytest.fixture
    def verifier(self) -> Verifier:
        """Create a Verifier instance."""
        return Verifier()

    def test_verify_hash_sha256(self, temp_file: Path, verifier: Verifier):
        """Test SHA256 verification."""
        # SHA256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = verifier.verify_hash(temp_file, expected, "sha256")
        assert result.status == VerificationStatus.VERIFIED
        assert result.algorithm == "sha256"

    def test_verify_hash_mismatch(self, temp_file: Path, verifier: Verifier):
        """Test hash mismatch detection."""
        expected = "0" * 64
        result = verifier.verify_hash(temp_file, expected, "sha256")
        assert result.status == VerificationStatus.MISMATCH
        assert result.expected_hash == expected
        assert result.actual_hash != expected

    def test_verify_hash_file_not_found(self, verifier: Verifier):
        """Test verification of non-existent file."""
        result = verifier.verify_hash(Path("nonexistent.txt"), "abc123", "sha256")
        assert result.status == VerificationStatus.NOT_FOUND
        assert "not found" in result.error.lower()

    def test_verify_hash_auto_detect_algorithm(self, temp_file: Path, verifier: Verifier):
        """Test auto-detection of hash algorithm."""
        # SHA256 hash (64 chars)
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = verifier.verify_hash(temp_file, expected)
        assert result.status == VerificationStatus.VERIFIED
        assert result.algorithm == "sha256"

    def test_verify_with_entry(self, temp_file: Path, verifier: Verifier):
        """Test verification with ChecksumEntry."""
        entry = ChecksumEntry(
            hash_value="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
            filename="test.txt",
            algorithm="sha256",
            line_number=1,
        )
        result = verifier.verify_with_entry(temp_file, entry)
        assert result.status == VerificationStatus.VERIFIED
        assert result.source == "test.txt:1"

    def test_unsupported_algorithm(self, temp_file: Path, verifier: Verifier):
        """Test unsupported algorithm handling."""
        result = verifier.verify_hash(temp_file, "abc123", "blake3")
        assert result.status == VerificationStatus.ERROR
        assert "Unsupported" in result.error
