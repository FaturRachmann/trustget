"""
TrustGet CLI - Command-line interface.

Commands:
- sg <url>        : Download + verify + trust analysis
- sg verify <file>: Verify file against checksum
- sg trust <url>  : Analyze trust without download
- sg run <file>   : Execute file in sandbox
- sg info <url>   : Show file/release metadata
- sg config       : Manage configuration
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import click
import tomli_w
from rich.console import Console

from trustget import __version__
from trustget.downloader import Downloader, DownloadError
from trustget.github import GitHubClient
from trustget.reporter import Reporter
from trustget.trust import TrustEngine
from trustget.utils import (
    ensure_dirs,
    get_filename_from_url,
    is_github_releases_url,
    parse_github_url,
)
from trustget.verifier import VerificationStatus, Verifier

# Global console
console = Console()


def create_reporter(
    json_output: bool = False,
    quiet: bool = False,
    no_color: bool = False,
) -> Reporter:
    """Create reporter with given options."""
    return Reporter(
        console=console,
        json_output=json_output,
        quiet=quiet,
        no_color=no_color,
    )


@click.group()
@click.version_option(version=__version__, prog_name="TrustGet")
def cli():
    """
    TrustGet - Secure file downloader with automatic verification.

    wget yang punya otak keamanan.
    """
    ensure_dirs()


@cli.command()
@click.argument("url")
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for downloaded file",
)
@click.option(
    "--filename",
    "-n",
    help="Custom filename for downloaded file",
)
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
@click.option(
    "--no-verify",
    is_flag=True,
    help="Skip checksum verification",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=30,
    help="HTTP request timeout in seconds",
)
@click.option(
    "--retry",
    "-r",
    type=int,
    default=3,
    help="Number of retry attempts",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force download even if trust score is low",
)
def download(
    url: str,
    output: str | None,
    filename: str | None,
    json_output: bool,
    quiet: bool,
    verbose: bool,
    no_color: bool,
    no_verify: bool,
    timeout: int,
    retry: int,
    force: bool,
) -> None:
    """
    Download file with automatic verification and trust analysis.

    URL can be a direct download link or GitHub Releases URL.
    TrustGet will automatically find and verify checksums.
    """
    reporter = create_reporter(json_output, quiet, no_color)
    output_dir = Path(output) if output else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    download_result = None
    verification_result = None
    trust_report = None
    github_release = None

    try:
        # Step 1: Analyze URL and get GitHub info if applicable
        if is_github_releases_url(url):
            with GitHubClient() as gh_client:
                parsed = parse_github_url(url)
                if parsed:
                    try:
                        github_release = gh_client.get_release(
                            parsed["owner"],
                            parsed["repo"],
                            parsed["tag"],
                        )
                        reporter.output_github_info(github_release)
                    except Exception as e:
                        if verbose:
                            reporter.output_warning(f"Failed to get GitHub release info: {e}")

        # Step 2: Initial trust analysis
        with TrustEngine() as trust_engine:
            trust_report = trust_engine.analyze_minimal(url)

            # Check trust score before download
            if trust_report.risk_level.value == "CRITICAL" and not force:
                reporter.output_trust_report(trust_report)
                reporter.output_error(
                    "Trust score is CRITICAL. Use --force to download anyway.",
                    "Security Warning",
                )
                sys.exit(1)

            elif trust_report.risk_level.value == "HIGH" and not force:
                reporter.output_trust_report(trust_report)
                if not click.confirm("\n⚠ Trust score is HIGH. Continue anyway?", default=False):
                    sys.exit(0)

        # Step 3: Download
        reporter.output_download_start(url, filename or get_filename_from_url(url))

        with Downloader(
            output_dir=output_dir,
            timeout=timeout,
            retries=retry,
            console=console,
        ) as downloader:
            download_result = downloader.download(url, filename, show_progress=not quiet)

        reporter.output_download_complete(download_result)

        # Step 4: Verify checksum
        if not no_verify and download_result.success and download_result.filepath:
            with Verifier(timeout=timeout) as verifier:
                verification_result = verifier.verify_auto(
                    download_result.filepath,
                    source_url=url,
                )
                reporter.output_verification(verification_result)

                # Update trust report with verification result
                if trust_report and verification_result.status == VerificationStatus.VERIFIED:
                    with TrustEngine() as trust_engine:
                        trust_report = trust_engine.analyze(
                            url,
                            checksum_verified=True,
                        )

        # Step 5: Final trust report
        if trust_report:
            reporter.output_trust_report(trust_report)

        # Exit with appropriate code
        if download_result.success:
            if no_verify:
                sys.exit(0)
            elif verification_result and verification_result.status == VerificationStatus.MISMATCH:
                sys.exit(2)
            sys.exit(0)
        else:
            sys.exit(1)

    except DownloadError as e:
        reporter.output_error(str(e), "Download Failed")
        sys.exit(1)
    except KeyboardInterrupt:
        reporter.output_info("\nDownload cancelled.")
        if download_result and download_result.filepath and download_result.filepath.exists():
            download_result.filepath.unlink()
        sys.exit(130)
    except Exception as e:
        if verbose:
            import traceback

            traceback.print_exc()
        reporter.output_error(str(e), "Error")
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--checksum",
    "-c",
    help="Expected checksum value",
)
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(["sha256", "sha512", "sha1", "md5"]),
    help="Hash algorithm",
)
@click.option(
    "--checksum-file",
    type=click.Path(exists=True),
    help="Path to checksum file",
)
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
def verify(
    filepath: str,
    checksum: str | None,
    algorithm: str | None,
    checksum_file: str | None,
    json_output: bool,
    quiet: bool,
    no_color: bool,
) -> None:
    """
    Verify file against checksum.

    FILEPATH is the file to verify.

    Provide checksum via --checksum flag or --checksum-file option.
    If neither is provided, TrustGet will look for checksum files in the same directory.
    """
    reporter = create_reporter(json_output, quiet, no_color)
    file_path = Path(filepath)

    try:
        with Verifier() as verifier:
            result: VerificationStatus

            if checksum:
                result = verifier.verify_hash(file_path, checksum, algorithm)
            elif checksum_file:
                result = verifier.verify_with_checksum_file(
                    file_path,
                    Path(checksum_file),
                    algorithm,
                )
            else:
                result = verifier.verify_auto(file_path)

            reporter.output_verification(result)

            if result.status == VerificationStatus.VERIFIED:
                sys.exit(0)
            elif result.status == VerificationStatus.MISMATCH:
                reporter.output_error("Checksum verification failed", "Verification Failed")
                sys.exit(2)
            else:
                reporter.output_error("Could not verify file", "Verification Error")
                sys.exit(1)

    except Exception as e:
        reporter.output_error(str(e), "Error")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
@click.option(
    "--min-score",
    type=int,
    help="Minimum acceptable trust score",
)
def trust(
    url: str,
    json_output: bool,
    quiet: bool,
    no_color: bool,
    min_score: int | None,
) -> None:
    """
    Analyze trust score of URL without downloading.

    Quick security analysis to check if a URL is safe to download from.
    """
    reporter = create_reporter(json_output, quiet, no_color)

    try:
        with TrustEngine() as trust_engine:
            report = trust_engine.analyze_minimal(url)
            reporter.output_trust_report(report)

            if min_score is not None and report.score < min_score:
                reporter.output_error(
                    f"Trust score {report.score} is below minimum {min_score}",
                    "Trust Check Failed",
                )
                sys.exit(1)

            if report.risk_level.value == "CRITICAL":
                sys.exit(2)
            elif report.risk_level.value == "HIGH":
                sys.exit(1)

            sys.exit(0)

    except Exception as e:
        reporter.output_error(str(e), "Error")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
def info(url: str, json_output: bool, quiet: bool, no_color: bool) -> None:
    """
    Show metadata about file/release without downloading.

    For GitHub Releases, shows release info, assets, and publisher details.
    """
    reporter = create_reporter(json_output, quiet, no_color)

    try:
        info_data = {"url": url}

        if is_github_releases_url(url):
            with GitHubClient() as gh_client:
                parsed = parse_github_url(url)
                if parsed:
                    release = gh_client.get_release(
                        parsed["owner"],
                        parsed["repo"],
                        parsed["tag"],
                    )
                    info_data["github"] = release.to_dict()
                    reporter.output_github_info(release)

        with TrustEngine() as trust_engine:
            report = trust_engine.analyze_minimal(url)
            info_data["trust"] = report.to_dict()

        if json_output:
            reporter._output_json(info_data)
        elif not quiet:
            reporter.output_trust_report(report)

        sys.exit(0)

    except Exception as e:
        reporter.output_error(str(e), "Error")
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--no-sandbox",
    is_flag=True,
    help="Run without sandbox isolation",
)
@click.option(
    "--audit-log",
    type=click.Path(),
    help="Path to audit log file",
)
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
def run(
    filepath: str,
    no_sandbox: bool,
    audit_log: str | None,
    json_output: bool,
    quiet: bool,
    no_color: bool,
) -> None:
    """
    Execute file with sandbox isolation.

    FILEPATH is the file to execute (AppImage, script, binary).

    ⚠ WARNING: This is an experimental feature. Always verify files first.
    """
    reporter = create_reporter(json_output, quiet, no_color)
    file_path = Path(filepath)

    if not os.access(file_path, os.X_OK):
        reporter.output_warning("File is not executable. Attempting to make it executable...")
        try:
            file_path.chmod(0o755)
        except Exception as e:
            reporter.output_error(f"Cannot make file executable: {e}", "Permission Error")
            sys.exit(1)

    if not no_sandbox:
        reporter.output_warning(
            "Sandbox mode is experimental. Always verify files before running."
        )

    try:
        cmd = [str(file_path)]
        if audit_log:
            cmd = ["strace", "-o", audit_log] + cmd

        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    except subprocess.CalledProcessError as e:
        reporter.output_error(f"Execution failed: {e}", "Execution Error")
        sys.exit(e.returncode)
    except Exception as e:
        reporter.output_error(str(e), "Error")
        sys.exit(1)


@cli.command()
@click.option(
    "--set",
    "set_value",
    nargs=2,
    metavar="KEY VALUE",
    help="Set a config value",
)
@click.option(
    "--get",
    "get_key",
    metavar="KEY",
    help="Get a config value",
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset configuration to defaults",
)
@click.option(
    "--json",
    "-j",
    "json_output",
    is_flag=True,
    help="Output in JSON format",
)
def config(
    set_value: tuple[str, str] | None,
    get_key: str | None,
    reset: bool,
    json_output: bool,
) -> None:
    """
    Manage TrustGet configuration.

    Configuration is stored in ~/.config/trustget/config.toml
    """
    config_dir = Path.home() / ".config" / "trustget"
    config_file = config_dir / "config.toml"

    config_dir.mkdir(parents=True, exist_ok=True)

    default_config = {
        "timeout": 30,
        "retries": 3,
        "verify": True,
        "json_output": False,
        "quiet": False,
        "min_trust_score": 0,
    }

    if config_file.exists():
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
    else:
        config = default_config

    if get_key:
        value = config.get(get_key)
        if json_output:
            click.echo(json.dumps({get_key: value}))
        else:
            if value is not None:
                click.echo(f"{get_key} = {value}")
            else:
                click.echo(f"Key '{get_key}' not found")
                sys.exit(1)

    elif set_value:
        key, value = set_value
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        config[key] = value

        with open(config_file, "wb") as f:
            tomli_w.dump(config, f)

        if not json_output:
            click.echo(f"Set {key} = {value}")

    elif reset:
        with open(config_file, "wb") as f:
            tomli_w.dump(default_config, f)

        if not json_output:
            click.echo("Configuration reset to defaults")

    else:
        if json_output:
            click.echo(json.dumps(config, indent=2))
        else:
            click.echo("Current configuration:")
            for key, value in config.items():
                click.echo(f"  {key} = {value}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
