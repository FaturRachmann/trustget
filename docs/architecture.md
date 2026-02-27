# TrustGet Architecture

This document describes the architecture of TrustGet, a secure file downloader with automatic verification.

## Overview

TrustGet is designed with the following principles:

1. **Single Responsibility** — Each module has one clear purpose
2. **Testability** — Components can be tested in isolation
3. **Composability** — Modules can be combined flexibly
4. **Zero Config** — Works out of the box with sensible defaults

## Module Dependencies

```
cli.py (entry point)
  ├── downloader.py ──▶ utils.py
  ├── verifier.py ──▶ scanner.py
  ├── github.py ──▶ verifier.py
  ├── trust.py ◀───── all modules above
  ├── reporter.py ◀── trust.py + verifier.py
  └── sandbox.py (optional)
```

## Core Modules

### `cli.py` — Command-Line Interface

**Responsibility:** User interaction, command parsing, orchestration

- Uses `click` for command parsing
- Coordinates download → verify → trust analysis flow
- Handles exit codes and error messages
- Supports JSON output for CI/CD integration

### `downloader.py` — Streaming Downloader

**Responsibility:** HTTP file download with progress tracking

Features:
- Streaming download with adaptive chunk size
- Progress bar via `rich`
- Resume support (HTTP Range header)
- Retry with exponential backoff
- Auto-detect filename from Content-Disposition

Key classes:
- `Downloader` — Main download engine
- `DownloadResult` — Download outcome
- `DownloadMetadata` — File metadata

### `scanner.py` — Checksum Scanner

**Responsibility:** Find and parse checksum files

Features:
- Scan directory URLs for checksum files
- Parse GNU coreutils format
- Support multiple formats (SHA256SUMS, checksums.txt, etc.)
- GitHub Releases asset scanning

Key classes:
- `Scanner` — URL scanning engine
- `ChecksumFile` — Parsed checksum file
- `ChecksumEntry` — Single checksum entry
- `ScanResult` — Scan outcome

### `verifier.py` — File Verifier

**Responsibility:** Hash and signature verification

Features:
- SHA256, SHA512, SHA1, MD5 verification
- GPG signature verification
- Batch verification
- Auto-detect checksum files

Key classes:
- `Verifier` — Verification engine
- `VerificationResult` — Verification outcome
- `VerificationStatus` — Status enum

### `github.py` — GitHub Integration

**Responsibility:** GitHub Releases API integration

Features:
- Fetch release metadata
- Get repository information
- Scan assets for checksum files
- Verify release authenticity

Key classes:
- `GitHubClient` — API client
- `GitHubRelease` — Release information
- `GitHubRepo` — Repository information

### `trust.py` — Trust Engine

**Responsibility:** Security scoring and risk analysis

Features:
- Transparent 0-100 scoring
- Domain reputation database
- GitHub Release analysis
- Configurable weights

Key classes:
- `TrustEngine` — Scoring engine
- `TrustReport` — Analysis report
- `TrustFactor` — Individual factor
- `RiskLevel` — Risk classification

### `reporter.py` — Output Formatter

**Responsibility:** Consistent output formatting

Features:
- JSON output for machine readability
- Rich text output for terminal
- Quiet mode support
- Consistent formatting

### `utils.py` — Utilities

**Responsibility:** Shared helper functions

Provides:
- URL parsing
- Hash computation
- File formatting utilities
- Path helpers

## Data Flow

### Download Flow

```
User Input (URL)
    │
    ▼
┌─────────────────┐
│   cli.py        │ ──▶ Parse arguments
│   (main)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   github.py     │ ──▶ Fetch release info (if GitHub URL)
│   (optional)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   trust.py      │ ──▶ Initial trust analysis
│   (pre-check)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   downloader.py │ ──▶ Download file
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   scanner.py    │ ──▶ Find checksum files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   verifier.py   │ ──▶ Verify checksum
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   trust.py      │ ──▶ Final trust analysis
│   (with result) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   reporter.py   │ ──▶ Output results
└─────────────────┘
```

## Error Handling

TrustGet uses a consistent error handling strategy:

1. **Custom Exceptions** — Each module defines specific exception types
2. **Graceful Degradation** — Non-critical failures don't abort the entire flow
3. **Clear Messages** — Error messages explain what went wrong and how to fix it
4. **Exit Codes** — Standard exit codes for scripting integration

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Verification failed |
| 130 | Interrupted (Ctrl+C) |

## Testing Strategy

### Unit Tests

- Test each function in isolation
- Mock external dependencies
- Cover edge cases and error conditions

### Integration Tests

- Test module interactions
- Use mock HTTP servers
- Test with real URLs (marked as integration)

### End-to-End Tests

- Full download flow
- Real GitHub Releases
- Manual testing for release candidates

## Security Considerations

1. **No Code Execution** — TrustGet never executes downloaded code
2. **Sandbox Option** — `sg run` uses isolation when available
3. **Transparent Scoring** — Trust factors are explainable
4. **No Telemetry** — No data is sent to external servers (except GitHub API)

## Performance Optimizations

1. **Streaming Download** — No memory buffering of large files
2. **Adaptive Chunk Size** — Larger chunks for large files
3. **Connection Reuse** — HTTP session reuse
4. **Parallel Scanning** — Multiple checksum sources checked in parallel

## Future Architecture

### Phase 5+ Considerations

- **Async Engine** — Consider `aiohttp` for async downloads
- **Plugin System** — Extensible verification backends
- **Policy Engine** — Organization-wide security policies
- **SBOM Support** — Software Bill of Materials verification
