"""
Unit tests for TrustGet utility functions.
"""

import pytest
from pathlib import Path
from trustget.utils import (
    get_filename_from_url,
    get_filename_from_content_disposition,
    format_size,
    format_speed,
    format_duration,
    detect_hash_algorithm,
    is_github_releases_url,
    parse_github_url,
    truncate_string,
    safe_filename,
)


class TestGetFilenameFromUrl:
    """Tests for get_filename_from_url."""

    def test_simple_url(self):
        url = "https://example.com/file.tar.gz"
        assert get_filename_from_url(url) == "file.tar.gz"

    def test_url_with_query_params(self):
        url = "https://example.com/file.tar.gz?token=abc123"
        assert get_filename_from_url(url) == "file.tar.gz"

    def test_url_with_encoded_filename(self):
        url = "https://example.com/my%20file.tar.gz"
        assert get_filename_from_url(url) == "my file.tar.gz"

    def test_url_without_filename(self):
        url = "https://example.com/"
        result = get_filename_from_url(url)
        assert result.startswith("download_")

    def test_nested_path(self):
        url = "https://example.com/path/to/file.tar.gz"
        assert get_filename_from_url(url) == "file.tar.gz"


class TestGetFilenameFromContentDisposition:
    """Tests for get_filename_from_content_disposition."""

    def test_simple_filename(self):
        header = 'attachment; filename="file.tar.gz"'
        assert get_filename_from_content_disposition(header) == "file.tar.gz"

    def test_filename_without_quotes(self):
        header = "attachment; filename=file.tar.gz"
        assert get_filename_from_content_disposition(header) == "file.tar.gz"

    def test_utf8_filename(self):
        header = "attachment; filename*=UTF-8''my%20file.tar.gz"
        assert get_filename_from_content_disposition(header) == "my file.tar.gz"

    def test_no_header(self):
        assert get_filename_from_content_disposition(None) is None

    def test_empty_header(self):
        assert get_filename_from_content_disposition("") is None


class TestFormatSize:
    """Tests for format_size."""

    def test_bytes(self):
        assert format_size(0) == "0 B"
        assert format_size(500) == "500 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.0 KB"
        assert format_size(2048) == "2.0 KB"

    def test_megabytes(self):
        assert format_size(1048576) == "1.0 MB"
        assert format_size(5242880) == "5.0 MB"

    def test_gigabytes(self):
        assert format_size(1073741824) == "1.0 GB"


class TestFormatSpeed:
    """Tests for format_speed."""

    def test_speed_format(self):
        assert format_speed(1048576) == "1.0 MB/s"
        assert format_speed(1024) == "1.0 KB/s"


class TestFormatDuration:
    """Tests for format_duration."""

    def test_seconds(self):
        assert format_duration(0.5) == "0.5s"
        assert format_duration(5) == "5s"
        assert format_duration(59) == "59s"

    def test_minutes(self):
        assert format_duration(120) == "2m 0s"
        assert format_duration(150) == "2m 30s"

    def test_hours(self):
        assert format_duration(3600) == "1h 0m"
        assert format_duration(7200) == "2h 0m"


class TestDetectHashAlgorithm:
    """Tests for detect_hash_algorithm."""

    def test_md5(self):
        # MD5 is 32 hex chars
        assert detect_hash_algorithm("d41d8cd98f00b204e9800998ecf8427e") == "md5"

    def test_sha1(self):
        # SHA1 is 40 hex chars
        assert detect_hash_algorithm("da39a3ee5e6b4b0d3255bfef95601890afd80709") == "sha1"

    def test_sha256(self):
        # SHA256 is 64 hex chars
        assert detect_hash_algorithm(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ) == "sha256"

    def test_sha512(self):
        # SHA512 is 128 hex chars
        assert detect_hash_algorithm(
            "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce"
            "47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        ) == "sha512"

    def test_invalid_length(self):
        assert detect_hash_algorithm("invalid") is None


class TestIsGithubReleasesUrl:
    """Tests for is_github_releases_url."""

    def test_valid_releases_url(self):
        url = "https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz"
        assert is_github_releases_url(url) is True

    def test_http_releases_url(self):
        url = "http://github.com/cli/cli/releases/download/v2.40.0/file.tar.gz"
        assert is_github_releases_url(url) is True

    def test_not_releases_url(self):
        url = "https://example.com/file.tar.gz"
        assert is_github_releases_url(url) is False

    def test_github_but_not_releases(self):
        url = "https://github.com/user/repo/raw/main/file.tar.gz"
        assert is_github_releases_url(url) is False


class TestParseGithubUrl:
    """Tests for parse_github_url."""

    def test_valid_releases_url(self):
        url = "https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz"
        result = parse_github_url(url)
        assert result is not None
        assert result["owner"] == "cli"
        assert result["repo"] == "cli"
        assert result["tag"] == "v2.40.0"
        assert result["filename"] == "gh_2.40.0_linux_amd64.tar.gz"

    def test_invalid_url(self):
        url = "https://example.com/file.tar.gz"
        assert parse_github_url(url) is None


class TestTruncateString:
    """Tests for truncate_string."""

    def test_no_truncation_needed(self):
        assert truncate_string("short", 50) == "short"

    def test_truncation(self):
        result = truncate_string("a" * 100, 50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_custom_suffix(self):
        result = truncate_string("a" * 100, 50, suffix=" [more]")
        assert result.endswith(" [more]")


class TestSafeFilename:
    """Tests for safe_filename."""

    def test_safe_filename(self):
        assert safe_filename("file.tar.gz") == "file.tar.gz"

    def test_unsafe_characters(self):
        assert safe_filename("file<>name.tar.gz") == "file__name.tar.gz"

    def test_long_filename(self):
        long_name = "a" * 300 + ".tar.gz"
        result = safe_filename(long_name)
        assert len(result) <= 255

    def test_leading_trailing_dots(self):
        assert safe_filename(".hidden.") == "hidden"
