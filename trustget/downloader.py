"""
Streaming downloader with progress bar and resume support.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from trustget.utils import (
    compute_hash,
    format_duration,
    format_size,
    format_speed,
    get_filename_from_content_disposition,
    get_filename_from_url,
    safe_filename,
)


class DownloadError(Exception):
    """Exception raised for download errors."""

    def __init__(self, message: str, url: str | None = None, status_code: int | None = None):
        self.message = message
        self.url = url
        self.status_code = status_code
        super().__init__(self.message)


@dataclass
class DownloadMetadata:
    """Metadata about a downloaded file."""

    url: str
    filename: str
    filepath: Path
    size: int
    checksum_sha256: str
    download_time: float
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "filename": self.filename,
            "filepath": str(self.filepath),
            "size": self.size,
            "checksum_sha256": self.checksum_sha256,
            "download_time": self.download_time,
            "timestamp": self.timestamp,
        }


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success: bool
    filepath: Path | None = None
    filename: str | None = None
    size: int = 0
    error: str | None = None
    metadata: DownloadMetadata | None = None


class Downloader:
    """
    Streaming file downloader with progress bar and resume support.

    Features:
    - Streaming download with adaptive chunk size
    - Real-time progress bar with speed and ETA
    - Auto-detect filename from Content-Disposition or URL
    - Resume support for partial downloads
    - Timeout handling + retry with exponential backoff
    """

    DEFAULT_CHUNK_SIZE = 8192
    MAX_CHUNK_SIZE = 1024 * 1024  # 1MB for large files
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3
    BACKOFF_FACTOR = 2

    def __init__(
        self,
        output_dir: Path | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        console: Console | None = None,
        progress_callback: Callable[[float], None] | None = None,
    ):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files
            timeout: HTTP request timeout in seconds
            retries: Number of retry attempts
            console: Rich console for output
            progress_callback: Optional callback for progress updates (0.0-1.0)
        """
        self.output_dir = output_dir or Path.cwd()
        self.timeout = timeout
        self.retries = retries
        self.console = console or Console()
        self.progress_callback = progress_callback
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "User-Agent": "TrustGet/0.1.0 (https://github.com/trustget/trustget)",
                }
            )
        return self._session

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> Downloader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _get_filename(
        self,
        url: str,
        response: requests.Response,
        preferred_name: str | None = None,
    ) -> str:
        """Determine filename from response or URL."""
        # Priority 1: User-specified name
        if preferred_name:
            return safe_filename(preferred_name)

        # Priority 2: Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        filename = get_filename_from_content_disposition(content_disposition)
        if filename:
            return safe_filename(filename)

        # Priority 3: URL path
        return safe_filename(get_filename_from_url(url))

    def _get_chunk_size(self, total_size: int | None) -> int:
        """Determine optimal chunk size based on file size."""
        if total_size is None:
            return self.DEFAULT_CHUNK_SIZE
        if total_size > 100 * 1024 * 1024:  # > 100MB
            return self.MAX_CHUNK_SIZE
        return self.DEFAULT_CHUNK_SIZE

    def _resume_info(self, filepath: Path, resume_byte_pos: int) -> None:
        """Show resume information."""
        self.console.print(f"[yellow]⚠ Resuming from {format_size(resume_byte_pos)}[/]")

    def download(
        self,
        url: str,
        filename: str | None = None,
        show_progress: bool = True,
    ) -> DownloadResult:
        """
        Download a file from URL.

        Args:
            url: URL to download from
            filename: Optional filename override
            show_progress: Whether to show progress bar

        Returns:
            DownloadResult with success status and file info
        """
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                return self._download_single(url, filename, show_progress, attempt)
            except requests.RequestException as e:
                last_error = e
                if attempt < self.retries:
                    wait_time = self.BACKOFF_FACTOR ** (attempt - 1)
                    self.console.print(f"[yellow]⚠ Download failed, retrying in {wait_time}s...[/]")
                    time.sleep(wait_time)

        error_msg = str(last_error) if last_error else "Unknown error"
        raise DownloadError(
            f"Download failed after {self.retries} attempts: {error_msg}",
            url=url,
        )

    def _download_single(
        self,
        url: str,
        filename: str | None,
        show_progress: bool,
        attempt: int = 1,
    ) -> DownloadResult:
        """Single download attempt."""
        start_time = time.time()

        # Stream request
        response = self.session.get(
            url,
            stream=True,
            timeout=self.timeout,
            allow_redirects=True,
        )

        if response.status_code not in (200, 206):
            raise DownloadError(
                f"HTTP {response.status_code}: {response.reason}",
                url=url,
                status_code=response.status_code,
            )

        # Determine filename
        final_filename = self._get_filename(url, response, filename)
        filepath = self.output_dir / final_filename

        # Check for partial file (resume support)
        resume_byte_pos = 0
        if filepath.exists():
            resume_byte_pos = filepath.stat().st_size
            if resume_byte_pos > 0:
                self._resume_info(filepath, resume_byte_pos)
                response = self.session.get(
                    url,
                    stream=True,
                    timeout=self.timeout,
                    headers={"Range": f"bytes={resume_byte_pos}-"},
                )

        # Get total size
        total_size = response.headers.get("Content-Length")
        total_size = int(total_size) if total_size else None
        initial_size = resume_byte_pos

        if total_size:
            total_size += initial_size

        # Setup progress bar
        progress: Progress | None = None
        task_id: TaskID | None = None

        if show_progress:
            progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
                console=self.console,
            )
            progress.start()
            task_id = progress.add_task(
                f"Downloading {final_filename}",
                total=total_size,
                initial=resume_byte_pos,
            )

        # Download with streaming
        chunk_size = self._get_chunk_size(total_size)
        downloaded = resume_byte_pos

        try:
            with open(filepath, "ab") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress and task_id is not None:
                        progress.update(task_id, completed=downloaded)

                    if self.progress_callback and total_size:
                        self.progress_callback(downloaded / total_size)

        finally:
            if progress:
                progress.stop()

        # Calculate download time and speed
        download_time = time.time() - start_time
        actual_size = downloaded - resume_byte_pos

        if show_progress:
            speed = format_speed(actual_size / download_time) if download_time > 0 else "N/A"
            self.console.print(
                f"[green]✓[/] Downloaded {format_size(actual_size)} in "
                f"{format_duration(download_time)} ({speed})"
            )

        # Compute checksum
        checksum = compute_hash(filepath, "sha256")

        # Create metadata
        metadata = DownloadMetadata(
            url=url,
            filename=final_filename,
            filepath=filepath,
            size=downloaded,
            checksum_sha256=checksum,
            download_time=download_time,
        )

        return DownloadResult(
            success=True,
            filepath=filepath,
            filename=final_filename,
            size=downloaded,
            metadata=metadata,
        )

    def download_with_resume(
        self,
        url: str,
        filename: str | None = None,
        show_progress: bool = True,
    ) -> DownloadResult:
        """
        Download with explicit resume support.

        This is an alias for download() which has built-in resume support.
        """
        return self.download(url, filename, show_progress)
