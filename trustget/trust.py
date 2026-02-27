"""
Trust Score Engine for TrustGet.

Transparent security scoring system with auditable factors.
Not a black box - every score is explainable.

Scoring: 0-100
Risk Levels:
- CRITICAL (<40): Abort download
- HIGH (40-59): Confirm with user
- MEDIUM (60-79): Proceed with warning
- LOW (80-100): Safe to proceed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from trustget.github import GitHubClient
from trustget.utils import is_github_releases_url, parse_github_url


class RiskLevel(Enum):
    """Risk level classification."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @classmethod
    def from_score(cls, score: int) -> RiskLevel:
        """Get risk level from trust score."""
        if score < 40:
            return cls.CRITICAL
        elif score < 60:
            return cls.HIGH
        elif score < 80:
            return cls.MEDIUM
        else:
            return cls.LOW

    @property
    def emoji(self) -> str:
        """Get emoji for risk level."""
        emojis = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
        }
        return emojis.get(self, "⚪")

    @property
    def color(self) -> str:
        """Get Rich color string for risk level."""
        colors = {
            RiskLevel.CRITICAL: "bold red",
            RiskLevel.HIGH: "orange1",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.LOW: "green",
        }
        return colors.get(self, "white")


@dataclass
class TrustFactor:
    """A single factor contributing to trust score."""

    name: str
    description: str
    weight: int  # Positive or negative points
    applied: bool = False
    reason: str = ""

    @property
    def points(self) -> int:
        """Get points if factor was applied."""
        return self.weight if self.applied else 0

    @property
    def display_weight(self) -> str:
        """Get formatted weight for display."""
        if self.weight > 0:
            return f"+{self.weight}"
        return str(self.weight)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "applied": self.applied,
            "reason": self.reason,
            "points": self.points,
        }


@dataclass
class TrustReport:
    """Complete trust analysis report."""

    url: str
    score: int = 0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    factors: list[TrustFactor] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def max_score(self) -> int:
        """Calculate maximum possible score."""
        return sum(f.weight for f in self.factors if f.weight > 0)

    @property
    def positive_factors(self) -> list[TrustFactor]:
        """Get factors with positive weight that were applied."""
        return [f for f in self.factors if f.applied and f.weight > 0]

    @property
    def negative_factors(self) -> list[TrustFactor]:
        """Get factors with negative weight that were applied."""
        return [f for f in self.factors if f.applied and f.weight < 0]

    @property
    def summary(self) -> str:
        """Get one-line summary."""
        return f"{self.risk_level.emoji} {self.risk_level.value} ({self.score}/100)"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "score": self.score,
            "risk_level": self.risk_level.value,
            "factors": [f.to_dict() for f in self.factors],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "summary": self.summary,
        }


# Default domain reputation database
# These are trusted sources that get bonus points
KNOWN_DOMAINS = {
    # Code hosting
    "github.com": 10,
    "gitlab.com": 10,
    "bitbucket.org": 5,
    # Linux/Unix
    "kernel.org": 15,
    "gnu.org": 15,
    "debian.org": 15,
    "ubuntu.com": 15,
    "redhat.com": 15,
    "fedoraproject.org": 12,
    "archlinux.org": 12,
    # Apache
    "apache.org": 15,
    "apache.com": 15,
    # Python
    "python.org": 15,
    "pypi.org": 12,
    "pypi.io": 12,
    # Node.js
    "nodejs.org": 15,
    "npmjs.com": 10,
    # Go
    "go.dev": 15,
    "golang.org": 15,
    # Rust
    "rust-lang.org": 15,
    "crates.io": 12,
    # Container
    "docker.com": 12,
    "docker.io": 12,
    # Cloud
    "aws.amazon.com": 12,
    "azure.microsoft.com": 12,
    "cloud.google.com": 12,
    # Other trusted
    "mozilla.org": 15,
    "firefox.com": 12,
    "google.com": 10,
    "microsoft.com": 10,
    "apple.com": 10,
    "cloudflare.com": 12,
}


class TrustEngine:
    """
    Trust Score calculation engine.

    Features:
    - Transparent scoring with explainable factors
    - Domain reputation database
    - GitHub Release analysis
    - Configurable scoring weights
    - JSON export for CI/CD integration
    """

    # Default scoring weights (matching blueprint)
    DEFAULT_WEIGHTS = {
        # Positive factors
        "https": 20,
        "checksum_available": 10,
        "checksum_verified": 25,
        "gpg_signed": 25,
        "known_domain": 10,
        "maintainer_verified": 20,
        "repo_age_established": 7,
        "release_recent": 10,
        # Negative factors
        "http_redirect": -10,
        "unknown_domain": -20,
        "no_checksum": -15,
        "repo_new": -20,
        "prerelease": -10,
    }

    def __init__(self, weights: dict[str, int] | None = None):
        """
        Initialize trust engine.

        Args:
            weights: Custom scoring weights (overrides defaults)
        """
        self.weights = {**self.DEFAULT_WEIGHTS, **(weights or {})}
        self._github_client: GitHubClient | None = None
        self._known_domains = {**KNOWN_DOMAINS}

    @property
    def github_client(self) -> GitHubClient:
        """Get or create GitHub client."""
        if self._github_client is None:
            self._github_client = GitHubClient()
        return self._github_client

    def close(self) -> None:
        """Close resources."""
        if self._github_client:
            self._github_client.close()

    def __enter__(self) -> TrustEngine:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _create_factor(
        self,
        name: str,
        weight: int,
        applied: bool = False,
        reason: str = "",
    ) -> TrustFactor:
        """Create a trust factor."""
        descriptions = {
            "https": "Secure HTTPS connection",
            "checksum_available": "Checksum file available",
            "checksum_verified": "Checksum verified successfully",
            "gpg_signed": "GPG signature verified",
            "known_domain": "Known/trusted domain",
            "maintainer_verified": "Release by repository maintainer",
            "repo_age_established": "Repository age > 1 year",
            "release_recent": "Release published < 30 days ago",
            "http_redirect": "HTTP redirect to different domain",
            "unknown_domain": "Unknown domain",
            "no_checksum": "No checksum file found",
            "repo_new": "Repository < 3 months old",
            "prerelease": "Pre-release or draft version",
        }

        return TrustFactor(
            name=name.replace("_", " ").title(),
            description=descriptions.get(name, name),
            weight=weight,
            applied=applied,
            reason=reason,
        )

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _is_https(self, url: str) -> bool:
        """Check if URL uses HTTPS."""
        parsed = urlparse(url)
        return parsed.scheme == "https"

    def _analyze_github_release(
        self,
        url: str,
        report: TrustReport,
    ) -> None:
        """Analyze GitHub Release and add factors."""
        parsed = parse_github_url(url)
        if not parsed:
            return

        try:
            client = self.github_client
            release = client.get_release(parsed["owner"], parsed["repo"], parsed["tag"])
            repo = client.get_repo(parsed["owner"], parsed["repo"])

            # Maintainer verification
            if client.is_maintainer(release):
                report.factors.append(
                    self._create_factor(
                        "maintainer_verified",
                        self.weights["maintainer_verified"],
                        applied=True,
                        reason=f"Release by @{release.author_login} (repo owner)",
                    )
                )

            # Repo age
            if repo.is_established:
                report.factors.append(
                    self._create_factor(
                        "repo_age_established",
                        self.weights["repo_age_established"],
                        applied=True,
                        reason=f"Repository is {repo.age_days} days old",
                    )
                )
            elif repo.is_new:
                report.factors.append(
                    self._create_factor(
                        "repo_new",
                        self.weights["repo_new"],
                        applied=True,
                        reason=f"Repository is only {repo.age_days} days old",
                    )
                )

            # Release recency
            if release.is_recent:
                report.factors.append(
                    self._create_factor(
                        "release_recent",
                        self.weights["release_recent"],
                        applied=True,
                        reason=f"Release published {release.age_days} days ago",
                    )
                )

            # Pre-release / draft warning
            if release.is_prerelease or release.is_draft:
                report.factors.append(
                    self._create_factor(
                        "prerelease",
                        self.weights["prerelease"],
                        applied=True,
                        reason="This is a pre-release or draft version",
                    )
                )

            # Add metadata
            report.metadata["github"] = {
                "owner": parsed["owner"],
                "repo": parsed["repo"],
                "tag": parsed["tag"],
                "release_name": release.name,
                "published_at": release.published_at,
                "repo_age_days": repo.age_days,
                "release_age_days": release.age_days,
                "is_maintainer": client.is_maintainer(release),
            }

        except Exception as e:
            # GitHub API failed, but don't fail the whole analysis
            report.metadata["github_error"] = str(e)

    def analyze(
        self,
        url: str,
        checksum_verified: bool = False,
        checksum_available: bool = False,
        gpg_verified: bool = False,
        redirect_history: list[str] | None = None,
    ) -> TrustReport:
        """
        Analyze URL and calculate trust score.

        Args:
            url: URL to analyze
            checksum_verified: Whether checksum was verified
            checksum_available: Whether checksum file is available
            gpg_verified: Whether GPG signature was verified
            redirect_history: List of URLs in redirect chain

        Returns:
            TrustReport with score and factors
        """
        report = TrustReport(url=url)

        # Factor 1: HTTPS connection
        is_https = self._is_https(url)
        report.factors.append(
            self._create_factor(
                "https",
                self.weights["https"],
                applied=is_https,
                reason="HTTPS connection" if is_https else "HTTP (insecure)",
            )
        )

        # Factor 2: Domain reputation
        domain = self._get_domain(url)
        domain_score = self._known_domains.get(domain)

        if domain_score:
            report.factors.append(
                self._create_factor(
                    "known_domain",
                    self.weights["known_domain"],
                    applied=True,
                    reason=f"Trusted domain: {domain}",
                )
            )
        else:
            report.factors.append(
                self._create_factor(
                    "unknown_domain",
                    self.weights["unknown_domain"],
                    applied=True,
                    reason=f"Unknown domain: {domain}",
                )
            )

        # Factor 3: Checksum availability
        if checksum_verified:
            report.factors.append(
                self._create_factor(
                    "checksum_verified",
                    self.weights["checksum_verified"],
                    applied=True,
                    reason="Checksum verified successfully",
                )
            )
        elif checksum_available:
            report.factors.append(
                self._create_factor(
                    "checksum_available",
                    self.weights["checksum_available"],
                    applied=True,
                    reason="Checksum file available (not yet verified)",
                )
            )
        else:
            report.factors.append(
                self._create_factor(
                    "no_checksum",
                    self.weights["no_checksum"],
                    applied=True,
                    reason="No checksum file found",
                )
            )

        # Factor 4: GPG signature
        if gpg_verified:
            report.factors.append(
                self._create_factor(
                    "gpg_signed",
                    self.weights["gpg_signed"],
                    applied=True,
                    reason="GPG signature verified",
                )
            )

        # Factor 5: Redirect chain
        if redirect_history and len(redirect_history) > 0:
            # Check if any redirect goes to different domain
            base_domain = self._get_domain(url)
            for redirect_url in redirect_history:
                redirect_domain = self._get_domain(redirect_url)
                if redirect_domain != base_domain:
                    report.factors.append(
                        self._create_factor(
                            "http_redirect",
                            self.weights["http_redirect"],
                            applied=True,
                            reason=f"Redirect to different domain: {redirect_domain}",
                        )
                    )
                    break

        # Factor 6: GitHub Release analysis
        if is_github_releases_url(url):
            self._analyze_github_release(url, report)

        # Calculate total score
        score = sum(f.points for f in report.factors)
        # Clamp to 0-100
        report.score = max(0, min(100, score))
        report.risk_level = RiskLevel.from_score(report.score)

        return report

    def analyze_minimal(self, url: str) -> TrustReport:
        """
        Quick trust analysis without verification results.

        Use this for `sg trust <url>` command.

        Args:
            url: URL to analyze

        Returns:
            TrustReport with preliminary score
        """
        return self.analyze(url)

    def add_known_domain(self, domain: str, score: int) -> None:
        """Add domain to known domains database."""
        self._known_domains[domain.lower()] = score

    def remove_known_domain(self, domain: str) -> None:
        """Remove domain from known domains database."""
        self._known_domains.pop(domain.lower(), None)

    def get_known_domains(self) -> dict[str, int]:
        """Get copy of known domains database."""
        return {**self._known_domains}

    def export_report(self, report: TrustReport, filepath: Path) -> None:
        """
        Export trust report to JSON file.

        Args:
            report: TrustReport to export
            filepath: Path to save JSON file
        """
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)

    def import_policy(self, filepath: Path) -> None:
        """
        Import custom policy/scoring weights from file.

        Args:
            filepath: Path to policy JSON file
        """
        import json

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        if "weights" in data:
            self.weights.update(data["weights"])

        if "known_domains" in data:
            for domain, score in data["known_domains"].items():
                self._known_domains[domain.lower()] = score
