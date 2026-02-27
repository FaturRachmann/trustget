"""
TrustGet — Secure file downloader with automatic verification.

wget yang punya otak keamanan.
TrustGet = download + verify + trust analysis — satu perintah, nol drama.
"""

__version__ = "0.1.0"
__author__ = "TrustGet Team"

from trustget.downloader import Downloader, DownloadError
from trustget.github import GitHubClient
from trustget.trust import TrustEngine, TrustReport
from trustget.verifier import VerificationError, Verifier

__all__ = [
    "__version__",
    "Downloader",
    "DownloadError",
    "Verifier",
    "VerificationError",
    "TrustEngine",
    "TrustReport",
    "GitHubClient",
]
