"""
magic_number.py — File signature (magic number) detection and validation.

Reads the actual bytes of a file to determine its real MIME type using
libmagic, then compares it against the MIME type implied by the file
extension to detect spoofed / mislabelled files.

Usage:
    from agents.nodes.magic_number import verify_signature

    result = verify_signature("challenge.pdf", raw_bytes)
    if not result["convergent"]:
        print(f"⚠️  Mismatch: declared {result['expected_mime']}, actual {result['real_mime']}")
"""

from typing import TypedDict
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TypedDict result
# ---------------------------------------------------------------------------

class MagicCheckResult(TypedDict):
    real_mime: str          # MIME detected from bytes
    expected_mime: str      # MIME expected for the declared extension
    convergent: bool        # True if they match (or close enough)
    mismatch_severity: str  # "none" | "warning" | "critical"
    detail: str             # Human-readable description


# ---------------------------------------------------------------------------
# Extension → expected MIME mapping
# ---------------------------------------------------------------------------

_EXT_TO_MIME: dict[str, str] = {
    # Documents
    "pdf":  "application/pdf",
    "txt":  "text/plain",
    "md":   "text/plain",
    "html": "text/html",
    "htm":  "text/html",
    # Data
    "json": "application/json",
    "yaml": "text/plain",
    "yml":  "text/plain",
    "xml":  "application/xml",
    "csv":  "text/plain",
    # Archives
    "zip":  "application/zip",
    "tar":  "application/x-tar",
    "gz":   "application/gzip",
    "bz2":  "application/x-bzip2",
    "xz":   "application/x-xz",
    "7z":   "application/x-7z-compressed",
    "rar":  "application/x-rar-compressed",
    # Images
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "gif":  "image/gif",
    "bmp":  "image/bmp",
    "svg":  "image/svg+xml",
    # Code / scripts
    "py":   "text/plain",
    "js":   "text/plain",
    "ts":   "text/plain",
    "sh":   "text/plain",
    "c":    "text/plain",
    "cpp":  "text/plain",
    # Executables / binary
    "exe":  "application/x-dosexec",
    "elf":  "application/x-executable",
    "bin":  "application/octet-stream",
    # Pcap
    "pcap": "application/vnd.tcpdump.pcap",
    "pcapng": "application/vnd.tcpdump.pcap",
}

# Groups of MIME types that are functionally equivalent (won't flag as mismatch)
_EQUIVALENT_GROUPS: list[set[str]] = [
    # text/* variants that libmagic sometimes returns for YAML/JSON/plain text
    {"text/plain", "application/json", "application/x-yaml", "text/x-yaml"},
    # gzip can wrap a tar → libmagic may report application/gzip for .tar.gz
    {"application/gzip", "application/x-gzip"},
    # JPEG variations
    {"image/jpeg", "image/jpg"},
    # RAR variations
    {"application/x-rar-compressed", "application/vnd.rar", "application/x-rar"},
]


def _are_equivalent(mime_a: str, mime_b: str) -> bool:
    """Return True if both MIMEs belong to the same equivalence group."""
    if mime_a == mime_b:
        return True
    for group in _EQUIVALENT_GROUPS:
        if mime_a in group and mime_b in group:
            return True
    return False


def _severity(real: str, expected: str) -> str:
    """
    Determine how serious a mismatch is.

    - "critical": completely different type families (e.g. archive vs document)
    - "warning":  related but not identical (e.g. text/x-script vs text/plain)
    - "none":     no mismatch
    """
    if _are_equivalent(real, expected):
        return "none"
    real_family = real.split("/")[0]
    exp_family = expected.split("/")[0]
    if real_family != exp_family:
        return "critical"
    return "warning"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_mime(raw_bytes: bytes) -> str:
    """
    Return the MIME type detected from the raw bytes of a file.
    Falls back to 'application/octet-stream' if libmagic is unavailable.
    """
    try:
        import magic  # python-magic
        return magic.from_buffer(raw_bytes, mime=True)
    except ImportError:
        logger.warning("python-magic not installed — MIME detection unavailable")
        return "application/octet-stream"
    except Exception as exc:
        logger.warning("magic.from_buffer failed: %s", exc)
        return "application/octet-stream"


def verify_signature(filename: str, raw_bytes: bytes) -> MagicCheckResult:
    """
    Verify that the file's actual bytes match the MIME type implied
    by its declared extension.

    Args:
        filename:   Original filename (e.g. "challenge.pdf")
        raw_bytes:  Raw file bytes

    Returns:
        MagicCheckResult with detection details and convergence status.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    expected_mime = _EXT_TO_MIME.get(ext, "application/octet-stream")
    real_mime = detect_mime(raw_bytes)

    sev = _severity(real_mime, expected_mime)
    convergent = sev == "none"

    if convergent:
        detail = (
            f"Firma verificada: '{filename}' es {real_mime} "
            f"(coincide con extensión .{ext})"
        )
    else:
        detail = (
            f"¡Discrepancia detectada! El archivo '{filename}' tiene extensión "
            f"'.{ext}' (esperado: {expected_mime}) pero su firma real es "
            f"{real_mime}. Severidad: {sev.upper()}."
        )

    logger.info("MagicCheck [%s] → real=%s expected=%s convergent=%s sev=%s",
                filename, real_mime, expected_mime, convergent, sev)

    return MagicCheckResult(
        real_mime=real_mime,
        expected_mime=expected_mime,
        convergent=convergent,
        mismatch_severity=sev,
        detail=detail,
    )
