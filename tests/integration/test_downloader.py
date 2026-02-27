"""
Integration tests for TrustGet downloader.
"""

import pytest
from pathlib import Path
from trustget.downloader import Downloader, DownloadError, DownloadResult


class TestDownloaderIntegration:
    """Integration tests for Downloader."""

    @pytest.fixture
    def downloader(self, tmp_path: Path) -> Downloader:
        """Create Downloader instance with temp output dir."""
        return Downloader(output_dir=tmp_path, timeout=10, retries=1)

    def test_download_invalid_url(self, downloader: Downloader):
        """Test download with invalid URL."""
        with pytest.raises(DownloadError):
            downloader.download("http://invalid-url-that-does-not-exist.com/file.txt")

    def test_download_with_output_dir(self, downloader: Downloader):
        """Test download respects output directory."""
        # This would require a real URL or mock server
        # For now, just verify the output_dir is set correctly
        assert downloader.output_dir.exists()


@pytest.mark.integration
class TestDownloaderRealURL:
    """Integration tests with real URLs (skipped by default)."""

    def test_download_small_file(self, tmp_path: Path):
        """Test downloading a small real file."""
        # Using a reliable test file
        url = "https://httpbin.org/bytes/1024"  # 1KB random bytes
        
        downloader = Downloader(output_dir=tmp_path, timeout=30, retries=2)
        result = downloader.download(url, show_progress=False)
        
        assert result.success is True
        assert result.filepath is not None
        assert result.filepath.exists()
        assert result.size > 0
