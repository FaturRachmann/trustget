"""
Unit tests for TrustGet trust engine.
"""

import pytest
from trustget.trust import (
    TrustEngine,
    TrustReport,
    TrustFactor,
    RiskLevel,
)


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_from_score_critical(self):
        assert RiskLevel.from_score(0) == RiskLevel.CRITICAL
        assert RiskLevel.from_score(39) == RiskLevel.CRITICAL

    def test_from_score_high(self):
        assert RiskLevel.from_score(40) == RiskLevel.HIGH
        assert RiskLevel.from_score(59) == RiskLevel.HIGH

    def test_from_score_medium(self):
        assert RiskLevel.from_score(60) == RiskLevel.MEDIUM
        assert RiskLevel.from_score(79) == RiskLevel.MEDIUM

    def test_from_score_low(self):
        assert RiskLevel.from_score(80) == RiskLevel.LOW
        assert RiskLevel.from_score(100) == RiskLevel.LOW

    def test_emoji(self):
        assert RiskLevel.CRITICAL.emoji == "🔴"
        assert RiskLevel.HIGH.emoji == "🟠"
        assert RiskLevel.MEDIUM.emoji == "🟡"
        assert RiskLevel.LOW.emoji == "🟢"

    def test_color(self):
        assert RiskLevel.CRITICAL.color == "bold red"
        assert RiskLevel.HIGH.color == "orange1"
        assert RiskLevel.MEDIUM.color == "yellow"
        assert RiskLevel.LOW.color == "green"


class TestTrustFactor:
    """Tests for TrustFactor."""

    def test_points_when_applied(self):
        factor = TrustFactor(
            name="HTTPS",
            description="Secure connection",
            weight=20,
            applied=True,
        )
        assert factor.points == 20

    def test_points_when_not_applied(self):
        factor = TrustFactor(
            name="HTTPS",
            description="Secure connection",
            weight=20,
            applied=False,
        )
        assert factor.points == 0

    def test_display_weight_positive(self):
        factor = TrustFactor(name="Test", description="Test", weight=20)
        assert factor.display_weight == "+20"

    def test_display_weight_negative(self):
        factor = TrustFactor(name="Test", description="Test", weight=-15)
        assert factor.display_weight == "-15"

    def test_to_dict(self):
        factor = TrustFactor(
            name="HTTPS",
            description="Secure connection",
            weight=20,
            applied=True,
            reason="Using HTTPS",
        )
        data = factor.to_dict()
        assert data["name"] == "HTTPS"
        assert data["weight"] == 20
        assert data["applied"] is True
        assert data["points"] == 20


class TestTrustReport:
    """Tests for TrustReport."""

    def test_default_values(self):
        report = TrustReport(url="https://example.com/file.tar.gz")
        assert report.score == 0
        assert report.risk_level == RiskLevel.MEDIUM
        assert len(report.factors) == 0

    def test_summary(self):
        report = TrustReport(url="https://example.com/file.tar.gz", score=90, risk_level=RiskLevel.LOW)
        assert "LOW" in report.summary
        assert "90" in report.summary

    def test_positive_factors(self):
        report = TrustReport(
            url="https://example.com/file.tar.gz",
            factors=[
                TrustFactor("HTTPS", "Secure", 20, applied=True),
                TrustFactor("Unknown Domain", "Unknown", -20, applied=True),
            ],
        )
        positive = report.positive_factors
        assert len(positive) == 1
        assert positive[0].name == "HTTPS"

    def test_negative_factors(self):
        report = TrustReport(
            url="https://example.com/file.tar.gz",
            factors=[
                TrustFactor("HTTPS", "Secure", 20, applied=True),
                TrustFactor("Unknown Domain", "Unknown", -20, applied=True),
            ],
        )
        negative = report.negative_factors
        assert len(negative) == 1
        assert negative[0].name == "Unknown Domain"

    def test_to_dict(self):
        report = TrustReport(url="https://example.com/file.tar.gz", score=75)
        data = report.to_dict()
        assert data["url"] == "https://example.com/file.tar.gz"
        assert data["score"] == 75
        assert "risk_level" in data


class TestTrustEngine:
    """Tests for TrustEngine."""

    @pytest.fixture
    def engine(self) -> TrustEngine:
        """Create TrustEngine instance."""
        return TrustEngine()

    def test_analyze_https_url(self, engine: TrustEngine):
        """Test analysis of HTTPS URL."""
        report = engine.analyze("https://example.com/file.tar.gz")
        https_factor = next(
            (f for f in report.factors if "https" in f.name.lower()),
            None,
        )
        assert https_factor is not None
        assert https_factor.applied is True

    def test_analyze_http_url(self, engine: TrustEngine):
        """Test analysis of HTTP URL."""
        report = engine.analyze("http://example.com/file.tar.gz")
        https_factor = next(
            (f for f in report.factors if "https" in f.name.lower()),
            None,
        )
        assert https_factor is not None
        assert https_factor.applied is False

    def test_analyze_known_domain(self, engine: TrustEngine):
        """Test analysis with known domain."""
        report = engine.analyze("https://github.com/user/repo/releases/download/v1/file.tar.gz")
        domain_factor = next(
            (f for f in report.factors if "domain" in f.name.lower()),
            None,
        )
        assert domain_factor is not None
        assert domain_factor.applied is True
        assert domain_factor.weight > 0

    def test_analyze_unknown_domain(self, engine: TrustEngine):
        """Test analysis with unknown domain."""
        report = engine.analyze("https://unknown-domain-xyz.com/file.tar.gz")
        # Should have unknown_domain penalty
        domain_factors = [f for f in report.factors if "domain" in f.name.lower()]
        assert len(domain_factors) > 0

    def test_analyze_with_checksum_verified(self, engine: TrustEngine):
        """Test analysis with verified checksum."""
        report = engine.analyze(
            "https://example.com/file.tar.gz",
            checksum_verified=True,
        )
        checksum_factor = next(
            (f for f in report.factors if "checksum" in f.name.lower() and "verified" in f.name.lower()),
            None,
        )
        assert checksum_factor is not None
        assert checksum_factor.applied is True
        assert checksum_factor.weight == 25  # Default weight

    def test_analyze_with_checksum_available(self, engine: TrustEngine):
        """Test analysis with available but unverified checksum."""
        report = engine.analyze(
            "https://example.com/file.tar.gz",
            checksum_available=True,
        )
        checksum_factor = next(
            (f for f in report.factors if "checksum" in f.name.lower() and "available" in f.name.lower()),
            None,
        )
        assert checksum_factor is not None
        assert checksum_factor.applied is True

    def test_analyze_no_checksum(self, engine: TrustEngine):
        """Test analysis with no checksum."""
        report = engine.analyze("https://example.com/file.tar.gz")
        no_checksum_factor = next(
            (f for f in report.factors if "no_checksum" in f.name.lower() or "no checksum" in f.name.lower()),
            None,
        )
        assert no_checksum_factor is not None
        assert no_checksum_factor.applied is True

    def test_score_clamped_to_100(self, engine: TrustEngine):
        """Test that score is clamped to maximum 100."""
        report = engine.analyze(
            "https://github.com/user/repo/releases/download/v1/file.tar.gz",
            checksum_verified=True,
            gpg_verified=True,
        )
        assert report.score <= 100

    def test_score_clamped_to_0(self, engine: TrustEngine):
        """Test that score is clamped to minimum 0."""
        # Create custom engine with heavy penalties
        custom_engine = TrustEngine(weights={"unknown_domain": -200})
        report = custom_engine.analyze("https://unknown.com/file.tar.gz")
        assert report.score >= 0

    def test_add_known_domain(self, engine: TrustEngine):
        """Test adding custom known domain."""
        engine.add_known_domain("custom-trusted.com", 15)
        domains = engine.get_known_domains()
        assert "custom-trusted.com" in domains
        assert domains["custom-trusted.com"] == 15

    def test_remove_known_domain(self, engine: TrustEngine):
        """Test removing known domain."""
        engine.remove_known_domain("github.com")
        domains = engine.get_known_domains()
        assert "github.com" not in domains
