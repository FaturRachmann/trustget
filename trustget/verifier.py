"""
File verification module for hash and GPG signature verification.

Supports:
- SHA256, SHA512, SHA1, MD5 hash verification
- GPG signature verification
- Batch verification
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import gnupg

from trustget.scanner import ChecksumEntry, Scanner
from trustget.utils import compute_hash, detect_hash_algorithm


class VerificationStatus(Enum):
    """Status of verification."""

    VERIFIED = auto()
    MISMATCH = auto()
    NOT_FOUND = auto()
    ERROR = auto()
    SKIPPED = auto()


@dataclass
class VerificationResult:
    """Result of a verification operation."""

    status: VerificationStatus
    filepath: Path
    algorithm: str | None = None
    expected_hash: str | None = None
    actual_hash: str | None = None
    source: str | None = None  # Source of checksum (file, inline, etc.)
    error: str | None = None
    gpg_verified: bool = False
    gpg_key_id: str | None = None
    gpg_key_status: str | None = None

    @property
    def is_verified(self) -> bool:
        """Check if verification succeeded."""
        return self.status == VerificationStatus.VERIFIED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "status": self.status.name,
            "filepath": str(self.filepath),
            "algorithm": self.algorithm,
            "expected_hash": self.expected_hash,
            "actual_hash": self.actual_hash,
            "source": self.source,
            "error": self.error,
            "gpg_verified": self.gpg_verified,
            "gpg_key_id": self.gpg_key_id,
            "gpg_key_status": self.gpg_key_status,
        }


@dataclass
class BatchVerificationResult:
    """Result of batch verification."""

    results: list[VerificationResult] = field(default_factory=list)
    total: int = 0
    verified: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return self.verified / self.total * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "verified": self.verified,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": self.success_rate,
        }


class VerificationError(Exception):
    """Exception raised for verification errors."""

    def __init__(self, message: str, filepath: Path | None = None):
        self.message = message
        self.filepath = filepath
        super().__init__(self.message)


class Verifier:
    """
    File verification engine.

    Features:
    - Multi-algorithm hash verification (SHA256, SHA512, SHA1, MD5)
    - GPG signature verification
    - Auto-detection of checksum files
    - Batch verification support
    """

    SUPPORTED_ALGORITHMS = ["sha256", "sha512", "sha1", "md5"]
    DEFAULT_ALGORITHM = "sha256"

    def __init__(self, gpg_home: str | None = None, timeout: int = 10):
        """
        Initialize verifier.

        Args:
            gpg_home: Custom GPG home directory
            timeout: HTTP timeout for fetching checksums
        """
        self.gpg_home = gpg_home
        self.timeout = timeout
        self._scanner: Scanner | None = None
        self._gpg: gnupg.GPG | None = None

    @property
    def scanner(self) -> Scanner:
        """Get or create scanner."""
        if self._scanner is None:
            self._scanner = Scanner(timeout=self.timeout)
        return self._scanner

    @property
    def gpg(self) -> gnupg.GPG:
        """Get or create GPG instance."""
        if self._gpg is None:
            self._gpg = gnupg.GPG(gnupghome=self.gpg_home)
        return self._gpg

    def close(self) -> None:
        """Close resources."""
        if self._scanner:
            self._scanner.close()
        if self._gpg:
            pass  # GPG doesn't need explicit cleanup

    def __enter__(self) -> Verifier:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def verify_hash(
        self,
        filepath: Path,
        expected_hash: str,
        algorithm: str | None = None,
    ) -> VerificationResult:
        """
        Verify file hash against expected value.

        Args:
            filepath: Path to file to verify
            expected_hash: Expected hash value
            algorithm: Hash algorithm (auto-detected if None)

        Returns:
            VerificationResult with verification status
        """
        if not filepath.exists():
            return VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                filepath=filepath,
                error=f"File not found: {filepath}",
            )

        # Auto-detect algorithm if not specified
        if algorithm is None:
            algorithm = detect_hash_algorithm(expected_hash)
            if algorithm is None:
                return VerificationResult(
                    status=VerificationStatus.ERROR,
                    filepath=filepath,
                    error="Could not detect hash algorithm",
                )

        algorithm = algorithm.lower()

        if algorithm not in self.SUPPORTED_ALGORITHMS:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                filepath=filepath,
                error=f"Unsupported algorithm: {algorithm}",
            )

        try:
            actual_hash = compute_hash(filepath, algorithm)
        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                filepath=filepath,
                error=f"Failed to compute hash: {e}",
            )

        if actual_hash.lower() == expected_hash.lower():
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                filepath=filepath,
                algorithm=algorithm,
                expected_hash=expected_hash.lower(),
                actual_hash=actual_hash.lower(),
            )
        else:
            return VerificationResult(
                status=VerificationStatus.MISMATCH,
                filepath=filepath,
                algorithm=algorithm,
                expected_hash=expected_hash.lower(),
                actual_hash=actual_hash.lower(),
            )

    def verify_with_entry(
        self,
        filepath: Path,
        entry: ChecksumEntry,
    ) -> VerificationResult:
        """
        Verify file using ChecksumEntry.

        Args:
            filepath: Path to file to verify
            entry: ChecksumEntry with expected hash

        Returns:
            VerificationResult with verification status
        """
        result = self.verify_hash(filepath, entry.hash_value, entry.algorithm)
        result.source = f"{entry.filename}:{entry.line_number}"
        return result

    def verify_auto(
        self,
        filepath: Path,
        source_url: str | None = None,
    ) -> VerificationResult:
        """
        Automatically verify file using available checksum sources.

        Args:
            filepath: Path to file to verify
            source_url: Optional source URL for scanning checksums

        Returns:
            VerificationResult with verification status
        """
        filename = filepath.name

        # Strategy 1: Check for local checksum file
        local_checksums = [
            filepath.parent / f"{filename}.sha256",
            filepath.parent / f"{filename}.sha512",
            filepath.parent / f"{filename}.md5",
            filepath.parent / "SHA256SUMS",
            filepath.parent / "SHA512SUMS",
            filepath.parent / "MD5SUMS",
            filepath.parent / "checksums.txt",
        ]

        for checksum_file in local_checksums:
            if checksum_file.exists():
                result = self.verify_with_checksum_file(filepath, checksum_file)
                if result.status != VerificationStatus.NOT_FOUND:
                    result.source = str(checksum_file)
                    return result

        # Strategy 2: Scan URL for checksums
        if source_url:
            entry = self.scanner.scan_for_file(source_url, filename)
            if entry:
                result = self.verify_with_entry(filepath, entry)
                result.source = entry.filename
                return result

        return VerificationResult(
            status=VerificationStatus.NOT_FOUND,
            filepath=filepath,
            error="No checksum file found",
        )

    def verify_with_checksum_file(
        self,
        filepath: Path,
        checksum_file: Path,
        algorithm: str | None = None,
    ) -> VerificationResult:
        """
        Verify file against a checksum file.

        Args:
            filepath: Path to file to verify
            checksum_file: Path to checksum file
            algorithm: Hash algorithm (auto-detect from file if None)

        Returns:
            VerificationResult with verification status
        """
        if not checksum_file.exists():
            return VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                filepath=filepath,
                error=f"Checksum file not found: {checksum_file}",
            )

        filename = filepath.name

        try:
            content = checksum_file.read_text(encoding="utf-8")
        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                filepath=filepath,
                error=f"Failed to read checksum file: {e}",
            )

        # Parse checksum file
        from trustget.scanner import Scanner

        scanner = Scanner()
        entries = scanner._parse_checksum_content(content, str(checksum_file))

        # Find entry for our file
        target_lower = filename.lower()
        for entry in entries:
            if entry.filename.lower() == target_lower:
                result = self.verify_with_entry(filepath, entry)
                result.source = checksum_file.name
                return result

        # Also try matching by hash if filename doesn't match
        # (some checksum files only contain one entry)
        if len(entries) == 1:
            entry = entries[0]
            if algorithm is None or entry.algorithm == algorithm:
                result = self.verify_with_entry(filepath, entry)
                result.source = checksum_file.name
                return result

        return VerificationResult(
            status=VerificationStatus.NOT_FOUND,
            filepath=filepath,
            error=f"No checksum entry found for {filename}",
        )

    def verify_gpg(
        self,
        filepath: Path,
        signature_file: Path | None = None,
        key_servers: list[str] | None = None,
    ) -> VerificationResult:
        """
        Verify GPG signature of file.

        Args:
            filepath: Path to file to verify
            signature_file: Path to signature file (.asc, .sig)
            key_servers: List of key servers for key lookup

        Returns:
            VerificationResult with GPG verification status
        """
        if not filepath.exists():
            return VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                filepath=filepath,
                error=f"File not found: {filepath}",
            )

        # Auto-detect signature file
        if signature_file is None:
            for ext in [".asc", ".sig", ".gpg"]:
                sig_path = Path(f"{filepath}{ext}")
                if sig_path.exists():
                    signature_file = sig_path
                    break

        if signature_file is None or not signature_file.exists():
            return VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                filepath=filepath,
                error="No signature file found",
            )

        try:
            # Verify signature
            with open(filepath, "rb") as f:
                verified = self.gpg.verify_file(f, signature_file)

            if verified.valid:
                return VerificationResult(
                    status=VerificationStatus.VERIFIED,
                    filepath=filepath,
                    gpg_verified=True,
                    gpg_key_id=verified.key_id,
                    gpg_key_status="valid" if verified.valid else "invalid",
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.MISMATCH,
                    filepath=filepath,
                    gpg_verified=True,
                    gpg_key_id=verified.key_id,
                    gpg_key_status="invalid",
                    error="GPG signature verification failed",
                )

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                filepath=filepath,
                error=f"GPG verification error: {e}",
            )

    def verify_batch(
        self,
        files: list[tuple[Path, str | ChecksumEntry]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BatchVerificationResult:
        """
        Verify multiple files.

        Args:
            files: List of (filepath, hash_or_entry) tuples
            progress_callback: Optional callback(current, total)

        Returns:
            BatchVerificationResult with all results
        """
        results: list[VerificationResult] = []
        verified = 0
        failed = 0
        skipped = 0

        for i, (filepath, hash_or_entry) in enumerate(files):
            if progress_callback:
                progress_callback(i + 1, len(files))

            if isinstance(hash_or_entry, str):
                result = self.verify_hash(filepath, hash_or_entry)
            else:
                result = self.verify_with_entry(filepath, hash_or_entry)

            results.append(result)

            if result.status == VerificationStatus.VERIFIED:
                verified += 1
            elif result.status == VerificationStatus.SKIPPED:
                skipped += 1
            else:
                failed += 1

        return BatchVerificationResult(
            results=results,
            total=len(files),
            verified=verified,
            failed=failed,
            skipped=skipped,
        )

    def verify_checksum_string(
        self,
        filepath: Path,
        checksum_string: str,
    ) -> VerificationResult:
        """
        Verify file against a checksum string (e.g., from command line).

        Args:
            filepath: Path to file to verify
            checksum_string: Checksum string in format "hash  filename" or just "hash"

        Returns:
            VerificationResult with verification status
        """
        checksum_string = checksum_string.strip()

        # Parse checksum string
        parts = checksum_string.split()
        if len(parts) >= 1:
            hash_value = parts[0]
        else:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                filepath=filepath,
                error="Invalid checksum string",
            )

        return self.verify_hash(filepath, hash_value)
