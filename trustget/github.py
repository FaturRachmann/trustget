"""
GitHub Release API integration for TrustGet.

Features:
- Auto-detect GitHub Release URLs
- Fetch release metadata (tag, publisher, date, notes)
- Scan release assets for checksum files
- Verify release authenticity
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import requests

from trustget.utils import parse_github_url


@dataclass
class GitHubAsset:
    """GitHub Release asset."""

    name: str
    url: str
    size: int
    download_count: int
    content_type: str
    created_at: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "size": self.size,
            "download_count": self.download_count,
            "content_type": self.content_type,
            "created_at": self.created_at,
        }


@dataclass
class GitHubRelease:
    """GitHub Release information."""

    tag_name: str
    name: str
    body: str
    html_url: str
    published_at: str
    created_at: str
    draft: bool
    prerelease: bool
    author: dict[str, Any]
    assets: list[GitHubAsset] = field(default_factory=list)
    owner: str = ""
    repo: str = ""

    @property
    def is_draft(self) -> bool:
        """Check if release is a draft."""
        return self.draft

    @property
    def is_prerelease(self) -> bool:
        """Check if release is a pre-release."""
        return self.prerelease

    @property
    def published_date(self) -> datetime:
        """Get published date as datetime."""
        return datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))

    @property
    def age_days(self) -> int:
        """Calculate release age in days."""
        now = datetime.now(UTC)
        published = self.published_date
        return (now - published).days

    @property
    def is_recent(self) -> bool:
        """Check if release was published within 30 days."""
        return self.age_days < 30

    @property
    def is_old(self) -> bool:
        """Check if release is older than 2 years."""
        return self.age_days > 730

    @property
    def author_login(self) -> str:
        """Get author login name."""
        return self.author.get("login", "unknown")

    @property
    def short_body(self) -> str:
        """Get first 3 lines of release body."""
        lines = self.body.strip().split("\n")[:3]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "tag_name": self.tag_name,
            "name": self.name,
            "body": self.body,
            "html_url": self.html_url,
            "published_at": self.published_at,
            "created_at": self.created_at,
            "draft": self.draft,
            "prerelease": self.prerelease,
            "author": self.author,
            "assets": [a.to_dict() for a in self.assets],
            "owner": self.owner,
            "repo": self.repo,
            "age_days": self.age_days,
        }


@dataclass
class GitHubRepo:
    """GitHub Repository information."""

    owner: str
    name: str
    description: str
    created_at: str
    updated_at: str
    stargazers_count: int
    watchers_count: int
    language: str | None
    default_branch: str
    private: bool
    archived: bool

    @property
    def age_days(self) -> int:
        """Calculate repo age in days."""
        now = datetime.now(UTC)
        created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        return (now - created).days

    @property
    def is_new(self) -> bool:
        """Check if repo is less than 6 months old."""
        return self.age_days < 180

    @property
    def is_established(self) -> bool:
        """Check if repo is older than 1 year."""
        return self.age_days > 365

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "owner": self.owner,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stargazers_count": self.stargazers_count,
            "watchers_count": self.watchers_count,
            "language": self.language,
            "default_branch": self.default_branch,
            "private": self.private,
            "archived": self.archived,
            "age_days": self.age_days,
        }


class GitHubError(Exception):
    """Exception raised for GitHub API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class GitHubClient:
    """
    GitHub API client for TrustGet.

    Features:
    - Fetch release metadata
    - Get repository information
    - Scan assets for checksum files
    - Token-based authentication for higher rate limits
    """

    API_BASE = "https://api.github.com"
    DEFAULT_TIMEOUT = 10
    RATE_LIMIT_UNAUTHENTICATED = 60  # requests per hour
    RATE_LIMIT_AUTHENTICATED = 5000  # requests per hour

    def __init__(self, token: str | None = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, from env if not provided)
            timeout: HTTP request timeout
        """
        self.timeout = timeout
        self.token = token or os.getenv("TRUSTGET_GITHUB_TOKEN")
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session with auth."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "User-Agent": "TrustGet/0.1.0 (https://github.com/FaturRachmann/trustget)",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
            )
            if self.token:
                self._session.headers["Authorization"] = f"Bearer {self.token}"
        return self._session

    def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _request(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make authenticated request to GitHub API."""
        url = f"{self.API_BASE}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 403:
                # Check rate limit
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if int(remaining) == 0:
                    raise GitHubError(
                        "GitHub API rate limit exceeded. "
                        "Set TRUSTGET_GITHUB_TOKEN for higher limits.",
                        status_code=403,
                    )

            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            if e.response is not None:
                raise GitHubError(
                    f"GitHub API error: {e.response.status_code}",
                    status_code=e.response.status_code,
                ) from e
            raise GitHubError(f"GitHub API error: {e}") from e

    def get_release(
        self,
        owner: str,
        repo: str,
        tag: str,
    ) -> GitHubRelease:
        """
        Get release information by tag.

        Args:
            owner: Repository owner
            repo: Repository name
            tag: Release tag name

        Returns:
            GitHubRelease with release information
        """
        endpoint = f"/repos/{owner}/{repo}/releases/tags/{tag}"
        data = self._request(endpoint)

        assets = [
            GitHubAsset(
                name=asset["name"],
                url=asset["browser_download_url"],
                size=asset["size"],
                download_count=asset["download_count"],
                content_type=asset["content_type"],
                created_at=asset["created_at"],
            )
            for asset in data.get("assets", [])
        ]

        return GitHubRelease(
            tag_name=data["tag_name"],
            name=data["name"] or data["tag_name"],
            body=data["body"] or "",
            html_url=data["html_url"],
            published_at=data["published_at"],
            created_at=data["created_at"],
            draft=data["draft"],
            prerelease=data["prerelease"],
            author=data["author"],
            assets=assets,
            owner=owner,
            repo=repo,
        )

    def get_latest_release(self, owner: str, repo: str) -> GitHubRelease:
        """
        Get latest release information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            GitHubRelease with latest release information
        """
        endpoint = f"/repos/{owner}/{repo}/releases/latest"
        data = self._request(endpoint)

        assets = [
            GitHubAsset(
                name=asset["name"],
                url=asset["browser_download_url"],
                size=asset["size"],
                download_count=asset["download_count"],
                content_type=asset["content_type"],
                created_at=asset["created_at"],
            )
            for asset in data.get("assets", [])
        ]

        return GitHubRelease(
            tag_name=data["tag_name"],
            name=data["name"] or data["tag_name"],
            body=data["body"] or "",
            html_url=data["html_url"],
            published_at=data["published_at"],
            created_at=data["created_at"],
            draft=data["draft"],
            prerelease=data["prerelease"],
            author=data["author"],
            assets=assets,
            owner=owner,
            repo=repo,
        )

    def get_repo(self, owner: str, repo: str) -> GitHubRepo:
        """
        Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            GitHubRepo with repository information
        """
        endpoint = f"/repos/{owner}/{repo}"
        data = self._request(endpoint)

        return GitHubRepo(
            owner=data["owner"]["login"],
            name=data["name"],
            description=data["description"] or "",
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            stargazers_count=data["stargazers_count"],
            watchers_count=data["watchers_count"],
            language=data["language"],
            default_branch=data["default_branch"],
            private=data["private"],
            archived=data["archived"],
        )

    def get_release_from_url(self, url: str) -> GitHubRelease | None:
        """
        Get release information from GitHub Releases URL.

        Args:
            url: GitHub Releases download URL

        Returns:
            GitHubRelease or None if URL is not valid
        """
        parsed = parse_github_url(url)
        if not parsed:
            return None

        return self.get_release(parsed["owner"], parsed["repo"], parsed["tag"])

    def is_maintainer(self, release: GitHubRelease) -> bool:
        """
        Check if release was created by a repository maintainer.

        This checks if the release author is the same as the repo owner
        or has write access to the repository.

        Args:
            release: GitHubRelease to check

        Returns:
            True if author is a maintainer
        """
        # Simple check: author login matches owner
        if release.author_login.lower() == release.owner.lower():
            return True

        # Check if author is in the organization (for org repos)
        # This would require additional API calls
        # For now, we consider same login as maintainer
        return False

    def find_checksum_asset(
        self,
        release: GitHubRelease,
        target_filename: str,
    ) -> GitHubAsset | None:
        """
        Find checksum asset for a target file in release assets.

        Args:
            release: GitHubRelease to search
            target_filename: Target filename to find checksum for

        Returns:
            GitHubAsset for checksum file or None
        """
        target_lower = target_filename.lower()

        # Patterns to look for
        patterns = [
            f"{target_lower}.sha256",
            f"{target_lower}.sha512",
            f"{target_lower}.md5",
            f"{target_lower}.asc",
            f"{target_lower}.sig",
        ]

        for asset in release.assets:
            asset_name = asset.name.lower()

            # Direct match
            if asset_name in patterns:
                return asset

            # Checksum file containing multiple entries
            if asset_name in ["sha256sums", "sha512sums", "md5sums", "checksums.txt"]:
                return asset

        return None

    def get_checksum_content(self, asset: GitHubAsset) -> str | None:
        """
        Download checksum file content from asset.

        Args:
            asset: GitHubAsset for checksum file

        Returns:
            Checksum file content or None
        """
        try:
            response = self.session.get(asset.url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    def get_rate_limit_info(self) -> dict:
        """
        Get current rate limit information.

        Returns:
            Dict with rate limit info
        """
        try:
            endpoint = "/rate_limit"
            data = self._request(endpoint)
            return data.get("resources", {}).get("core", {})
        except GitHubError:
            return {}

    def is_authenticated(self) -> bool:
        """Check if client is authenticated with a token."""
        return self.token is not None

    def get_release_info_for_url(self, url: str) -> dict:
        """
        Get comprehensive release info for a GitHub Releases URL.

        Args:
            url: GitHub Releases download URL

        Returns:
            Dict with release, repo, and analysis info
        """
        parsed = parse_github_url(url)
        if not parsed:
            return {}

        try:
            release = self.get_release(parsed["owner"], parsed["repo"], parsed["tag"])
            repo = self.get_repo(parsed["owner"], parsed["repo"])

            return {
                "release": release.to_dict(),
                "repo": repo.to_dict(),
                "is_maintainer": self.is_maintainer(release),
                "is_prerelease": release.is_prerelease,
                "is_draft": release.is_draft,
                "is_recent": release.is_recent,
                "is_old": release.is_old,
                "repo_age_days": repo.age_days,
                "repo_is_established": repo.is_established,
                "repo_is_new": repo.is_new,
            }
        except GitHubError as e:
            return {"error": str(e), "status_code": e.status_code}
