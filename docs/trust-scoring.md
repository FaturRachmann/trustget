# Trust Scoring Guide

This document explains the TrustGet Trust Score system in detail.

## Overview

The Trust Score is a transparent security scoring system that evaluates the safety of a download URL. It's not a black box — every score is explainable and auditable.

## Scoring System

### Score Range: 0–100

The score is calculated by summing weighted factors. Positive factors increase the score, negative factors decrease it.

### Risk Levels

| Score Range | Risk Level | Recommendation |
|-------------|------------|----------------|
| 0–39 | 🔴 CRITICAL | Abort download |
| 40–59 | 🟠 HIGH | Confirm with user |
| 60–79 | 🟡 MEDIUM | Proceed with warning |
| 80–100 | 🟢 LOW | Safe to proceed |

## Trust Factors

### Positive Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| **HTTPS Connection** | +20 | URL uses HTTPS protocol |
| **Checksum Available** | +10 | Checksum file found in release assets or directory |
| **Checksum Verified** | +25 | File hash matches expected checksum |
| **GPG Signature** | +25 | Valid GPG signature verified |
| **Known Domain** | +10 | Domain is in trusted allowlist |
| **Maintainer Verified** | +20 | Release created by repository owner |
| **Repo Age > 1 Year** | +7 | Repository established for over a year |
| **Recent Release** | +10 | Release published within 30 days |

### Negative Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| **HTTP Redirect** | -10 | Redirect to different domain |
| **Unknown Domain** | -20 | Domain not in trusted allowlist |
| **No Checksum** | -15 | No checksum file found |
| **Repo < 3 Months** | -20 | Repository is very new |
| **Pre-release** | -10 | Draft or pre-release version |

## Known Domains

TrustGet maintains a built-in database of trusted domains:

### Code Hosting
- github.com (+10)
- gitlab.com (+10)
- bitbucket.org (+5)

### Linux/Unix
- kernel.org (+15)
- gnu.org (+15)
- debian.org (+15)
- ubuntu.com (+15)
- redhat.com (+15)
- fedoraproject.org (+12)
- archlinux.org (+12)

### Package Managers
- pypi.org (+12)
- npmjs.com (+10)
- crates.io (+12)

### Language Official Sites
- python.org (+15)
- nodejs.org (+15)
- go.dev (+15)
- rust-lang.org (+15)

### Cloud Providers
- aws.amazon.com (+12)
- azure.microsoft.com (+12)
- cloud.google.com (+12)

### Other Trusted
- mozilla.org (+15)
- google.com (+10)
- microsoft.com (+10)
- cloudflare.com (+12)

## Example Calculations

### Example 1: GitHub Release (Trusted)

```
URL: https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz

Factors:
✓ HTTPS connection              +20
✓ Known domain (github.com)     +10
✓ Checksum verified             +25
✓ Maintainer verified           +20
✓ Repo age > 1 year             +7
✓ Recent release                +10
────────────────────────────────────
Total Score:                    92/100
Risk Level: 🟢 LOW
```

### Example 2: Unknown HTTP Source

```
URL: http://random-site.com/file.tar.gz

Factors:
✗ HTTPS connection               0 (not applied)
✗ Unknown domain                -20
✗ No checksum                   -15
────────────────────────────────────
Total Score:                    -35 → 0 (clamped)
Risk Level: 🔴 CRITICAL
```

### Example 3: Medium Risk

```
URL: https://new-project.io/download/file.tar.gz

Factors:
✓ HTTPS connection              +20
✗ Unknown domain                -20
✗ No checksum                   -15
✓ Checksum available            +10
────────────────────────────────────
Total Score:                    -5 → 0 (clamped)
Risk Level: 🔴 CRITICAL
```

## Customization

### Adding Custom Trusted Domains

```python
from trustget.trust import TrustEngine

engine = TrustEngine()
engine.add_known_domain("my-company.com", 15)
```

### Custom Scoring Weights

```python
from trustget.trust import TrustEngine

engine = TrustEngine(weights={
    "https": 25,  # Increase HTTPS weight
    "unknown_domain": -30,  # Stricter on unknown domains
})
```

### Policy File

Create a policy file at `~/.config/trustget/policy.json`:

```json
{
  "weights": {
    "https": 20,
    "checksum_verified": 30
  },
  "known_domains": {
    "internal.company.com": 20
  },
  "min_trust_score": 60
}
```

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Download with TrustGet
  run: |
    trustget --json ${{ env.DOWNLOAD_URL }} | jq '.trust.score' | \
      xargs -I {} test {} -ge 80
```

### Minimum Trust Score

```bash
# Fail if trust score is below 80
trustget trust https://example.com/file.tar.gz --min-score 80
```

## Limitations

1. **Not Antivirus** — Trust Score doesn't detect malware
2. **Domain-Based** — Relies on domain reputation, not content analysis
3. **No Zero-Day Protection** — New domains may be incorrectly flagged
4. **GitHub-Centric** — Best support for GitHub Releases

## Best Practices

1. **Always Verify** — Use `--no-verify` only for trusted sources
2. **Check Trust Report** — Review factors, not just the score
3. **Update Domain List** — Add your organization's domains
4. **Use in CI/CD** — Set minimum trust score for automated downloads

## FAQ

**Q: Why is my trusted domain flagged as unknown?**

A: Add it to your custom domain list or contribute to the built-in database.

**Q: Can I disable trust scoring?**

A: Use `--force` to bypass trust checks, but this is not recommended.

**Q: How often is the domain list updated?**

A: The built-in list is updated with each release. Custom lists are local.

**Q: Does TrustGet phone home?**

A: No. Only GitHub API is called for GitHub Releases URLs.
