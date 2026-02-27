"""
URL scanner for automatic checksum file detection.

Scans directory URLs for checksum files like:
- .sha256, .sha512, .md5, .sha1
- checksums.txt, SHA256SUMS, SHA512SUMS, MD5SUMS
- B2SUMS, .sig, .asc (signatures)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from urllib.parse import urljoin, urlparse

import requests

from trustget.utils import detect_hash_algorithm


class ChecksumFileType(Enum):
    """Types of checksum files."""

    SHA256 = auto()
    SHA512 = auto()
    SHA1 = auto()
    MD5 = auto()
    GENERIC = auto()
    SIGNATURE = auto()


@dataclass
class ChecksumEntry:
    """A single checksum entry from a checksum file."""

    hash_value: str
    filename: str
    algorithm: str
    line_number: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "hash": self.hash_value,
            "filename": self.filename,
            "algorithm": self.algorithm,
            "line_number": self.line_number,
        }


@dataclass
class ChecksumFile:
    """A checksum file found during scanning."""

    url: str
    filename: str
    file_type: ChecksumFileType
    content: str
    entries: list[ChecksumEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "filename": self.filename,
            "file_type": self.file_type.name,
            "entries": [e.to_dict() for e in self.entries],
        }

    def get_entry_for_file(self, target_filename: str) -> ChecksumEntry | None:
        """Get checksum entry for a specific filename."""
        target_lower = target_filename.lower()
        for entry in self.entries:
            if entry.filename.lower() == target_lower:
                return entry
        return None


@dataclass
class ScanResult:
    """Result of scanning a URL directory."""

    base_url: str
    checksum_files: list[ChecksumFile] = field(default_factory=list)
    signature_files: list[str] = field(default_factory=list)
    scanned_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "base_url": self.base_url,
            "checksum_files": [f.to_dict() for f in self.checksum_files],
            "signature_files": self.signature_files,
            "scanned_urls": self.scanned_urls,
        }

    def has_checksum_for(self, filename: str) -> bool:
        """Check if any checksum file contains entry for filename."""
        for cf in self.checksum_files:
            if cf.get_entry_for_file(filename):
                return True
        return False

    def get_checksum_for(self, filename: str) -> ChecksumEntry | None:
        """Get checksum entry for filename (priority: SHA256 > SHA512 > others)."""
        # Priority order
        priority = [
            ChecksumFileType.SHA256,
            ChecksumFileType.SHA512,
            ChecksumFileType.SHA1,
            ChecksumFileType.MD5,
            ChecksumFileType.GENERIC,
        ]

        for file_type in priority:
            for cf in self.checksum_files:
                if cf.file_type == file_type:
                    entry = cf.get_entry_for_file(filename)
                    if entry:
                        return entry
        return None


class Scanner:
    """
    Scanner for finding checksum files in URL directories.

    Supports:
    - GitHub Releases asset scanning
    - Directory listing parsing (Apache, Nginx)
    - Common checksum file naming patterns
    """

    # Checksum file patterns
    CHECKSUM_PATTERNS = [
        # Extension-based
        (r"\.sha256$", ChecksumFileType.SHA256),
        (r"\.sha512$", ChecksumFileType.SHA512),
        (r"\.sha1$", ChecksumFileType.SHA1),
        (r"\.md5$", ChecksumFileType.MD5),
        (r"\.asc$", ChecksumFileType.SIGNATURE),
        (r"\.sig$", ChecksumFileType.SIGNATURE),
        # Name-based
        (r"^SHA256SUMS$", ChecksumFileType.SHA256),
        (r"^SHA512SUMS$", ChecksumFileType.SHA512),
        (r"^SHA1SUMS$", ChecksumFileType.SHA1),
        (r"^MD5SUMS$", ChecksumFileType.MD5),
        (r"^B2SUMS$", ChecksumFileType.SHA512),  # BLAKE2b
        (r"^checksums\.txt$", ChecksumFileType.GENERIC),
        (r"^CHECKSUMS$", ChecksumFileType.GENERIC),
        (r"^checksums$", ChecksumFileType.GENERIC),
    ]

    # Patterns to skip
    SKIP_PATTERNS = [
        r"\.asc\.sha256$",  # Signature of checksum file
        r"\.sig\.sha256$",
        r"^\.+$",  # Directory navigation
        r"^#",  # Comments in listings
    ]

    DEFAULT_TIMEOUT = 10
    USER_AGENT = "TrustGet/0.1.0 (https://github.com/FaturRachmann/trustget)"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize scanner.

        Args:
            timeout: HTTP request timeout
        """
        self.timeout = timeout
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": self.USER_AGENT})
        return self._session

    def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> Scanner:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _get_checksum_file_type(self, filename: str) -> ChecksumFileType | None:
        """Determine checksum file type from filename."""
        filename_lower = filename.lower()

        for pattern, file_type in self.CHECKSUM_PATTERNS:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return file_type
        return None

    def _should_skip(self, filename: str) -> bool:
        """Check if file should be skipped."""
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False

    def _parse_checksum_content(self, content: str, url: str) -> list[ChecksumEntry]:
        """
        Parse checksum file content.

        Supports formats:
        - GNU coreutils: hash  filename
        - hash filename
        - filename: hash
        """
        entries = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try different formats
            entry = self._parse_checksum_line(line, line_num)
            if entry:
                entries.append(entry)

        return entries

    def _parse_checksum_line(self, line: str, line_num: int) -> ChecksumEntry | None:
        """Parse a single checksum line."""
        line = line.strip()

        # Format 1: GNU coreutils (hash  filename) or (hash *filename)
        # The space after hash can be single or double
        match = re.match(r"^([a-fA-F0-9]+)\s+[\*]?(.+)$", line)
        if match:
            hash_value = match.group(1).lower()
            filename = match.group(2).strip()
            algorithm = detect_hash_algorithm(hash_value) or "unknown"
            return ChecksumEntry(
                hash_value=hash_value,
                filename=filename,
                algorithm=algorithm,
                line_number=line_num,
            )

        # Format 2: filename: hash
        match = re.match(r"^(.+):\s*([a-fA-F0-9]+)$", line)
        if match:
            filename = match.group(1).strip()
            hash_value = match.group(2).lower()
            algorithm = detect_hash_algorithm(hash_value) or "unknown"
            return ChecksumEntry(
                hash_value=hash_value,
                filename=filename,
                algorithm=algorithm,
                line_number=line_num,
            )

        return None

    def _fetch_url(self, url: str) -> tuple[str | None, int]:
        """
        Fetch URL content.

        Returns:
            Tuple of (content, status_code)
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.text, response.status_code
            return None, response.status_code
        except requests.RequestException:
            return None, 0

    def _scan_github_release(self, base_url: str, owner: str, repo: str, tag: str) -> ScanResult:
        """Scan GitHub Release assets for checksum files."""
        result = ScanResult(base_url=base_url)

        # GitHub API URL for release assets
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"

        try:
            response = self.session.get(api_url, timeout=self.timeout)
            if response.status_code != 200:
                return result

            release_data = response.json()
            assets = release_data.get("assets", [])

            for asset in assets:
                asset_name = asset.get("name", "")
                asset_url = asset.get("browser_download_url", "")

                if self._should_skip(asset_name):
                    continue

                file_type = self._get_checksum_file_type(asset_name)
                if not file_type:
                    continue

                if file_type == ChecksumFileType.SIGNATURE:
                    result.signature_files.append(asset_url)
                else:
                    # Fetch checksum file content
                    content, status = self._fetch_url(asset_url)
                    if content:
                        entries = self._parse_checksum_content(content, asset_url)
                        checksum_file = ChecksumFile(
                            url=asset_url,
                            filename=asset_name,
                            file_type=file_type,
                            content=content,
                            entries=entries,
                        )
                        result.checksum_files.append(checksum_file)
                        result.scanned_urls.append(asset_url)

        except requests.RequestException:
            pass

        return result

    def _scan_directory_listing(self, base_url: str) -> ScanResult:
        """Scan HTML directory listing for checksum files."""
        result = ScanResult(base_url=base_url)

        try:
            response = self.session.get(base_url, timeout=self.timeout)
            if response.status_code != 200:
                return result

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return result

            html = response.text

            # Extract links from HTML
            # Common patterns: Apache, Nginx directory listings
            link_pattern = r'href=["\']([^"\']+)[\"\']'
            links = re.findall(link_pattern, html)

            for link in links:
                # Skip parent directory links
                if link.startswith("?") or link == "../" or link == "/":
                    continue

                # Build absolute URL
                full_url = urljoin(base_url, link)
                filename = urlparse(full_url).path.split("/")[-1]

                if self._should_skip(filename):
                    continue

                result.scanned_urls.append(full_url)

                file_type = self._get_checksum_file_type(filename)
                if not file_type:
                    continue

                if file_type == ChecksumFileType.SIGNATURE:
                    result.signature_files.append(full_url)
                else:
                    # Fetch and parse checksum file
                    content, status = self._fetch_url(full_url)
                    if content:
                        entries = self._parse_checksum_content(content, full_url)
                        checksum_file = ChecksumFile(
                            url=full_url,
                            filename=filename,
                            file_type=file_type,
                            content=content,
                            entries=entries,
                        )
                        result.checksum_files.append(checksum_file)

        except requests.RequestException:
            pass

        return result

    def _scan_inline_checksum(self, url: str) -> ScanResult:
        """Check for inline checksum file (e.g., file.tar.gz.sha256)."""
        result = ScanResult(base_url=url)

        file_type = self._get_checksum_file_type(url)
        if not file_type or file_type == ChecksumFileType.SIGNATURE:
            return result

        content, status = self._fetch_url(url)
        if content:
            entries = self._parse_checksum_content(content, url)
            filename = urlparse(url).path.split("/")[-1]
            checksum_file = ChecksumFile(
                url=url,
                filename=filename,
                file_type=file_type,
                content=content,
                entries=entries,
            )
            result.checksum_files.append(checksum_file)
            result.scanned_urls.append(url)

        return result

    def scan(self, url: str, target_filename: str | None = None) -> ScanResult:
        """
        Scan URL directory for checksum files.

        Args:
            url: URL to scan (can be file URL or directory URL)
            target_filename: Optional target filename to optimize search

        Returns:
            ScanResult with found checksum files
        """
        from trustget.utils import is_github_releases_url, parse_github_url

        # Strategy 1: Check for inline checksum (file.ext.sha256)
        inline_url = f"{url}.sha256"
        inline_result = self._scan_inline_checksum(inline_url)
        if inline_result.checksum_files:
            return inline_result

        # Also try .sha512
        inline_url = f"{url}.sha512"
        inline_result = self._scan_inline_checksum(inline_url)
        if inline_result.checksum_files:
            return inline_result

        # Strategy 2: GitHub Releases
        if is_github_releases_url(url):
            parsed = parse_github_url(url)
            if parsed:
                # Get base releases URL
                base_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}/releases"
                return self._scan_github_release(
                    base_url,
                    parsed["owner"],
                    parsed["repo"],
                    parsed["tag"],
                )

        # Strategy 3: Directory listing
        # Get directory URL from file URL
        parsed = urlparse(url)
        path = parsed.path
        if "/" in path:
            dir_path = path.rsplit("/", 1)[0] + "/"
            dir_url = f"{parsed.scheme}://{parsed.netloc}{dir_path}"
            return self._scan_directory_listing(dir_url)

        return ScanResult(base_url=url)

    def scan_for_file(self, url: str, filename: str) -> ChecksumEntry | None:
        """
        Scan and get checksum entry for specific file.

        Args:
            url: Base URL or file URL
            filename: Target filename

        Returns:
            ChecksumEntry if found, None otherwise
        """
        result = self.scan(url, filename)
        return result.get_checksum_for(filename)
