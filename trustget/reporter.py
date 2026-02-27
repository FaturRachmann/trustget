"""
Output formatter for TrustGet.

Provides:
- JSON output for machine readability
- Rich text output for human readability
- Consistent formatting across all commands
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from rich.console import Console
from rich.table import Table

from trustget.downloader import DownloadResult
from trustget.github import GitHubRelease
from trustget.trust import TrustReport
from trustget.verifier import BatchVerificationResult, VerificationResult, VerificationStatus


class Reporter:
    """
    Output formatter for TrustGet.

    Features:
    - JSON output for CI/CD integration
    - Rich text output for terminal
    - Consistent formatting
    - Quiet mode support
    """

    def __init__(
        self,
        console: Console | None = None,
        json_output: bool = False,
        quiet: bool = False,
        no_color: bool = False,
    ):
        """
        Initialize reporter.

        Args:
            console: Rich console for output
            json_output: Output in JSON format
            quiet: Suppress non-essential output
            no_color: Disable colored output
        """
        self.json_output = json_output
        self.quiet = quiet

        if console is None:
            self.console = Console(color_system=None if no_color else "auto")
        else:
            self.console = console

    def _output_json(self, data: dict) -> None:
        """Output data as JSON."""
        self.console.print(json.dumps(data, indent=2, default=str))

    def output_download_start(self, url: str, filename: str) -> None:
        """Output download start message."""
        if self.json_output or self.quiet:
            return

        self.console.print(f"\n[bold blue]Downloading[/] {filename}")
        self.console.print(f"[dim]From: {url}[/]")

    def output_download_complete(self, result: DownloadResult) -> None:
        """Output download completion message."""
        if self.json_output:
            self._output_json(
                {"download": result.to_dict() if hasattr(result, "to_dict") else asdict(result)}
            )
            return

        if self.quiet:
            return

        if result.success and result.filepath:
            self.console.print(f"\n[green]✓ File saved →[/] {result.filepath}")

    def output_verification(self, result: VerificationResult) -> None:
        """Output verification result."""
        if self.json_output:
            self._output_json({"verification": result.to_dict()})
            return

        if self.quiet:
            return

        if result.status == VerificationStatus.VERIFIED:
            source = f" (from {result.source})" if result.source else ""
            self.console.print(f"\n[green]✓ {result.algorithm.upper()} matched[/]{source}")

            if result.expected_hash and result.actual_hash:
                self.console.print(f"  [dim]Expected : {result.expected_hash}[/]")
                self.console.print(f"  [dim]Got      : {result.actual_hash}[/]")

        elif result.status == VerificationStatus.MISMATCH:
            self.console.print(f"\n[red]✗ {result.algorithm.upper()} MISMATCH[/]")
            self.console.print(f"  [red]Expected : {result.expected_hash}[/]")
            self.console.print(f"  [red]Got      : {result.actual_hash}[/]")

        elif result.status == VerificationStatus.NOT_FOUND:
            self.console.print("\n[yellow]⚠ No checksum found[/]")

        elif result.status == VerificationStatus.ERROR:
            self.console.print(f"\n[red]✗ Verification error: {result.error}[/]")

    def output_trust_report(self, report: TrustReport) -> None:
        """Output trust analysis report."""
        if self.json_output:
            self._output_json({"trust": report.to_dict()})
            return

        if self.quiet:
            return

        # Build the trust score panel
        score_text = f"{report.score} / 100"
        risk_text = f"{report.risk_level.emoji} {report.risk_level.value}"

        # Build factors table
        factors_table = Table(show_header=False, box=None, padding=(0, 1))
        factors_table.add_column("Factor", style="white")
        factors_table.add_column("Points", justify="right")

        for factor in report.factors:
            if factor.applied:
                points_style = "green" if factor.weight > 0 else "red"
                factors_table.add_row(
                    f"{'✓' if factor.weight > 0 else '⚠'} {factor.name}",
                    f"[{points_style}]{factor.display_weight}[/]",
                )

        self.console.print("\n[bold]Security Analysis[/]")
        self.console.print(f"┌{'─' * 50}┐")
        self.console.print(f"│  [bold]Trust Score[/]    {score_text}    {risk_text}  │")
        self.console.print(f"├{'─' * 50}┤")

        for factor in report.factors:
            if factor.applied:
                points_style = "green" if factor.weight > 0 else "red"
                symbol = "✓" if factor.weight > 0 else "⚠"
                line = f"  {symbol} {factor.name:<35} {factor.display_weight}"
                self.console.print(f"│  {line}    │")

        self.console.print(f"└{'─' * 50}┘")

    def output_github_info(self, release: GitHubRelease) -> None:
        """Output GitHub Release information."""
        if self.json_output:
            self._output_json({"github": release.to_dict()})
            return

        if self.quiet:
            return

        self.console.print(
            f"\n[bold]GitHub Release detected:[/] {release.owner}/{release.repo} @ {release.tag_name}"
        )

        # Publisher info
        publisher_text = f"Published: {release.published_at[:10]}"
        if release.author_login:
            publisher_text += f" by @{release.author_login}"

        status_flags = []
        if release.is_prerelease:
            status_flags.append("[yellow]pre-release[/]")
        if release.is_draft:
            status_flags.append("[red]draft[/]")

        if status_flags:
            publisher_text += f" ({', '.join(status_flags)})"

        self.console.print(f"[dim]{publisher_text}[/]")

        # Release notes preview
        if release.short_body:
            self.console.print(f"\n[dim]{release.short_body}[/]")

    def output_batch_verification(self, result: BatchVerificationResult) -> None:
        """Output batch verification results."""
        if self.json_output:
            self._output_json({"batch_verification": result.to_dict()})
            return

        if self.quiet:
            return

        self.console.print("\n[bold]Batch Verification Results[/]")
        self.console.print(
            f"Total: {result.total} | "
            f"[green]Verified: {result.verified}[/] | "
            f"[red]Failed: {result.failed}[/] | "
            f"[dim]Skipped: {result.skipped}[/]"
        )
        self.console.print(f"Success Rate: {result.success_rate:.1f}%")

    def output_error(self, message: str, title: str = "Error") -> None:
        """Output error message."""
        if self.json_output:
            self._output_json({"error": message})
            return

        self.console.print(f"\n[red bold]{title}:[/] {message}")

    def output_warning(self, message: str) -> None:
        """Output warning message."""
        if self.json_output or self.quiet:
            return

        self.console.print(f"\n[yellow]⚠ Warning:[/] {message}")

    def output_info(self, message: str) -> None:
        """Output info message."""
        if self.json_output or self.quiet:
            return

        self.console.print(f"\n[dim]{message}[/]")

    def output_success(self, message: str) -> None:
        """Output success message."""
        if self.json_output:
            self._output_json({"success": True, "message": message})
            return

        if self.quiet:
            return

        self.console.print(f"\n[green]✓[/] {message}")

    def output_full_result(
        self,
        download_result: DownloadResult | None = None,
        verification_result: VerificationResult | None = None,
        trust_report: TrustReport | None = None,
        github_release: GitHubRelease | None = None,
    ) -> None:
        """
        Output complete TrustGet result.

        Args:
            download_result: Download result
            verification_result: Verification result
            trust_report: Trust analysis report
            github_release: GitHub Release info
        """
        if self.json_output:
            data: dict[str, Any] = {}
            if download_result:
                data["download"] = (
                    download_result.to_dict()
                    if hasattr(download_result, "to_dict")
                    else asdict(download_result)
                )
            if verification_result:
                data["verification"] = verification_result.to_dict()
            if trust_report:
                data["trust"] = trust_report.to_dict()
            if github_release:
                data["github"] = github_release.to_dict()
            self._output_json(data)
            return

        # Human-readable output is handled by individual methods
        # This is for coordinated output
        pass

    def output_help(self, text: str) -> None:
        """Output help text."""
        if self.quiet:
            return

        self.console.print(text)
