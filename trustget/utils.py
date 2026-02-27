"""
Shared utility functions for TrustGet.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from platformdirs import user_cache_dir, user_config_dir


def get_filename_from_url(url: str) -> str:
    """Extract filename from URL."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = Path(path).name

    if not filename:
        filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return filename


def get_filename_from_content_disposition(content_disposition: str) -> str | None:
    """Parse filename from Content-Disposition header."""
    if not content_disposition:
        return None

    # RFC 6266: filename*=UTF-8''filename or filename="value"
    match = re.search(r"filename\*=UTF-8\'\'([^;]+)", content_disposition)
    if match:
        return unquote(match.group(1))

    match = re.search(r'filename=["\']?([^"\';]+)["\']?', content_disposition)
    if match:
        return match.group(1)

    return None


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def format_speed(bytes_per_second: float) -> str:
    """Format speed to human-readable string."""
    return f"{format_size(int(bytes_per_second))}/s"


def format_duration(seconds: float) -> str:
    """Format duration to human-readable string."""
    if seconds < 1:
        return f"{seconds:.1f}s"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h {mins}m"


def compute_hash(filepath: Path, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """Compute hash of a file using specified algorithm."""
    hash_func = hashlib.new(algorithm)

    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def detect_hash_algorithm(hash_value: str) -> str | None:
    """Detect hash algorithm from hash value length."""
    hash_lengths = {
        32: "md5",
        40: "sha1",
        64: "sha256",
        128: "sha512",
    }
    # Remove any whitespace and check length
    clean_hash = hash_value.strip()
    return hash_lengths.get(len(clean_hash))


def is_github_releases_url(url: str) -> bool:
    """Check if URL is a GitHub Releases download URL."""
    pattern = r"^https?://github\.com/[^/]+/[^/]+/releases/download/"
    return bool(re.match(pattern, url))


def is_github_url(url: str) -> bool:
    """Check if URL is any GitHub URL."""
    pattern = r"^https?://github\.com/[^/]+/[^/]+"
    return bool(re.match(pattern, url))


def parse_github_url(url: str) -> dict[str, str] | None:
    """Parse GitHub URL to extract owner, repo, tag, and filename."""
    # Try releases URL pattern first
    pattern = r"^https?://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)$"
    match = re.match(pattern, url)

    if match:
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "tag": match.group(3),
            "filename": match.group(4),
            "type": "release",
        }

    # Try general GitHub URL pattern
    pattern = r"^https?://github\.com/([^/]+)/([^/]+)(?:/(tree|blob)/([^/]+)(?:/(.+))?)?$"
    match = re.match(pattern, url)

    if match:
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "type": match.group(3) or "repo",
            "ref": match.group(4) if match.group(4) else "main",
            "path": match.group(5) if match.group(5) else "",
        }

    return None


def get_config_dir() -> Path:
    """Get user config directory."""
    return Path(user_config_dir("trustget"))


def get_cache_dir() -> Path:
    """Get user cache directory."""
    return Path(user_cache_dir("trustget"))


def ensure_dirs() -> None:
    """Ensure config and cache directories exist."""
    get_config_dir().mkdir(parents=True, exist_ok=True)
    get_cache_dir().mkdir(parents=True, exist_ok=True)


def load_json_file(filepath: Path) -> Any:
    """Load JSON from file."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(filepath: Path, data: Any) -> None:
    """Save data to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def is_running_in_ci() -> bool:
    """Check if running in CI environment."""
    ci_env_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "TRAVIS", "CIRCLECI"]
    return any(os.getenv(var) for var in ci_env_vars)


def is_interactive() -> bool:
    """Check if running in interactive terminal."""
    return sys.stdin.isatty() and not is_running_in_ci()


def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string to max length with suffix."""
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def safe_filename(filename: str) -> str:
    """Sanitize filename to be safe for filesystem."""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, "_")
    # Remove control characters
    filename = "".join(c for c in filename if ord(c) >= 32)
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename.strip(". ")
