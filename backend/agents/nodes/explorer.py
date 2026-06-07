"""
Explorer Node — runs BEFORE the classifier to deeply analyze any CTF challenge file.

Responsibilities:
  1. Detect file format: "structured" (YAML/JSON) vs "unstructured" (MD/TXT/free text)
  2. Scan for semantic signals across all CTF categories (forensic, crypto, web)
  3. Detect common fields: difficulty, author, flag, tags, points, title
  4. Produce `explorer_context` consumed by all downstream agents
  5. Set `severity_mode`:
       - "strict"  → structured file, missing required fields are ERRORS
       - "lenient" → unstructured file, missing fields are WARNINGS only

This prevents false mass-errors when users submit narrative Markdown challenges.
"""
import re
from agents.state import CTFReviewState, AgentStep


# ── Signal definitions per category ──────────────────────────────────────────
# Each entry: (signal_name, regex_pattern)

FORENSIC_SIGNALS: list[tuple[str, str]] = [
    ("pcap",           r"\b(pcap|\.pcap|wireshark|tshark|tcpdump)\b"),
    ("memory_dump",    r"\b(memory.?dump|\.raw|volatility|vol\.py|pslist|netscan|memdump|ram\b)\b"),
    ("disk_image",     r"\b(disk.?image|\.img|\.dd|\.e01|autopsy|testdisk|foremost)\b"),
    ("log_file",       r"\b(auth\.log|syslog|\.log|journalctl|/var/log)\b"),
    ("steganography",  r"\b(steganography|stego|stegsolve|binwalk|strings\b|exiftool|zsteg)\b"),
    ("network_traffic",r"\b(tcp|udp|http|dns|arp|icmp|packet|frame|stream)\b"),
    ("anti_forensics", r"\b(shred|wipe|overwrite|secure.?delete|anti.?forensic|cover.?track)\b"),
    ("timeline",       r"\b(timeline|timestamp|utc|epoch|creation.?time|modified.?time)\b"),
]

CRYPTO_SIGNALS: list[tuple[str, str]] = [
    ("rsa",            r"\b(rsa|modulus|public.?key|private.?key|prime|p\s*[*x]\s*q|e\s*=\s*\d+|n\s*=\s*\d+)\b"),
    ("aes",            r"\b(aes|advanced.?encrypt|cbc|ecb|gcm|block.?cipher|iv\s*=|padding)\b"),
    ("xor",            r"\b(xor|x?or.?cipher|key.?stream|one.?time.?pad)\b"),
    ("classical",      r"\b(caesar|vigenere|rot13|substitution|transposition|playfair|affine)\b"),
    ("hash",           r"\b(md5|sha1|sha256|sha512|hash|digest|collision|rainbow)\b"),
    ("encoding",       r"\b(base64|hex.?encoded|b64|urlencod|ascii|utf.?8)\b"),
    ("ciphertext",     r"\b(ciphertext|encrypted|chall\.py|output\.txt|enc\b|\.enc)\b"),
    ("elliptic",       r"\b(ecc|ecdsa|ecdh|elliptic.?curve|secp256k1|curve25519)\b"),
]

WEB_SIGNALS: list[tuple[str, str]] = [
    ("endpoint",       r"(https?://\S+|/[\w/-]+|localhost:\d+|127\.0\.0\.1)"),
    ("docker",         r"\b(docker|container|dockerfile|image|docker-compose|docker\.io)\b"),
    ("framework",      r"\b(flask|django|fastapi|express|node\.?js|php|laravel|spring|rails|gin|nginx|apache)\b"),
    ("sqli",           r"\b(sql.?inject|sqli|sqlite|mysql|postgres|select.+from|union.+select|'.*or.*')\b"),
    ("xss",            r"\b(xss|cross.?site.?script|innerHTML|document\.cookie|alert\(|script.?inject)\b"),
    ("auth_bypass",    r"\b(jwt|json.?web.?token|bypass|session.?fixation|csrf|ssrf|idor|broken.?auth)\b"),
    ("file_upload",    r"\b(file.?upload|arbitrary.?upload|webshell|multipart|content.?type)\b"),
    ("lfi_rfi",        r"\b(lfi|rfi|path.?traversal|directory.?traversal|include|require|file_get_contents)\b"),
    ("port",           r":\d{2,5}\b|\bport\s*[:\s]\s*\d{2,5}\b|\bpuerto\b"),
    ("auth",           r"\b(login|authentication|credencial|password|token|cookie|bearer|oauth)\b"),
]

COMMON_SIGNALS: list[tuple[str, str]] = [
    ("has_flag_format",r"CTF\{[^}]*\}|FLAG\{[^}]*\}|\{[A-Z0-9_]{4,}\}"),
    ("has_difficulty", r"\b(easy|medium|hard|expert|beginner|fácil|difícil|intermedio|avanzado)\b"),
    ("has_author",     r"\b(author|autor|created.?by|by|diseñado.?por)\b"),
    ("has_tags",       r"\b(tags?|categoría|category)\s*[:\-]"),
    ("has_points",     r"\b(points?|puntos?|score|puntaje)\s*[:\-]?\s*\d+"),
    ("has_hints",      r"\b(hint|pista|tip|clue)\b"),
    ("has_objectives", r"\b(objective|objetivo|pregunta|question|goal|find|identifica)\b"),
    ("has_flag_hidden",r"\b(flag.{0,30}(embed|oculta|hidden|inside|dentro|artefact))\b"),
    ("has_docker_flag",r"\b(docker.?run|docker.?compose|docker-compose\.yml|Dockerfile)\b"),
    ("has_writeup",    r"\b(writeup|write.?up|solution|solución|solve)\b"),
]


def explorer_node(state: CTFReviewState) -> CTFReviewState:
    """
    Explores the challenge content and produces a rich context object
    before classification and domain-specific analysis.
    """
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="explorer",
        status="running",
        label="🔭 Explorando contenido del reto...",
        result=None
    ))

    content  = state.get("file_content", "")
    parsed   = state.get("parsed_template")
    filename = state.get("filename", "")

    if not content or state.get("error"):
        steps[-1] = AgentStep(
            node="explorer",
            status="error",
            label="🔭 Sin contenido para explorar",
            result=None
        )
        return {**state, "steps": steps, "explorer_context": _empty_context()}

    content_lower = content.lower()

    # ── 1. File format detection ──────────────────────────────────────────────
    file_format = _detect_format(filename, parsed, content)

    # Structured = YAML/JSON with real fields → strict mode
    # Unstructured = MD/TXT narrative → lenient mode
    severity_mode = "strict" if file_format == "structured" else "lenient"

    # ── 2. Signal scanning ────────────────────────────────────────────────────
    forensic_hits = _scan_signals(content_lower, FORENSIC_SIGNALS)
    crypto_hits   = _scan_signals(content_lower, CRYPTO_SIGNALS)
    web_hits      = _scan_signals(content_lower, WEB_SIGNALS)
    common_hits   = _scan_signals(content_lower, COMMON_SIGNALS)

    # ── 3. Score each category (sum of unique signals found) ─────────────────
    forensic_score = len(forensic_hits)
    crypto_score   = len(crypto_hits)
    web_score      = len(web_hits)

    # ── 4. Detected fields from parsed template ───────────────────────────────
    structured_fields = set(k.lower() for k in (parsed or {}).keys())

    # ── 5. Build context ──────────────────────────────────────────────────────
    context = {
        "file_format":       file_format,
        "severity_mode":     severity_mode,
        "structured_fields": list(structured_fields),
        "signals": {
            "forensic": forensic_hits,
            "crypto":   crypto_hits,
            "web":      web_hits,
            "common":   common_hits,
        },
        "category_scores": {
            "forensic": forensic_score,
            "crypto":   crypto_score,
            "web":      web_score,
        },
        "flags": {
            "has_flag_exposed":  bool(re.search(r"CTF\{[^}]+\}", content)),
            "has_private_key":   bool(re.search(r"-----BEGIN.{0,20}PRIVATE KEY-----", content)),
            "has_difficulty":    "has_difficulty" in common_hits,
            "has_author":        "has_author"     in common_hits,
            "has_hints":         "has_hints"      in common_hits,
            "has_objectives":    "has_objectives" in common_hits,
            "has_flag_hidden":   "has_flag_hidden" in common_hits,
            "has_docker":        "has_docker_flag" in common_hits,
        },
        "char_count": len(content),
    }

    # ── 6. Build human-readable summary for the step ─────────────────────────
    top_category = max(
        [("forensic", forensic_score), ("crypto", crypto_score), ("web", web_score)],
        key=lambda x: x[1]
    )
    signal_summary = (
        f"forense={forensic_score} crypto={crypto_score} web={web_score}"
    )

    steps[-1] = AgentStep(
        node="explorer",
        status="completed",
        label=(
            f"🔭 Exploración completa — formato={file_format} modo={severity_mode} "
            f"| señales: {signal_summary} "
            f"| candidato: {top_category[0].upper()}"
        ),
        result={
            "file_format":    file_format,
            "severity_mode":  severity_mode,
            "category_scores": context["category_scores"],
            "signal_count": forensic_score + crypto_score + web_score,
        }
    )

    return {**state, "steps": steps, "explorer_context": context}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_format(filename: str, parsed: dict | None, content: str) -> str:
    """
    Returns 'structured' if the file is a parseable YAML/JSON with real fields,
    'unstructured' for Markdown, plain text, or empty parsed dicts.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
    if ext in ("json", "yaml", "yml"):
        return "structured" if parsed and len(parsed) >= 2 else "unstructured"
    if ext in ("md", "txt", "rst"):
        return "unstructured"
    # For unknown extensions: check if parsed has meaningful content
    return "structured" if parsed and len(parsed) >= 2 else "unstructured"


def _scan_signals(content_lower: str, signals: list[tuple[str, str]]) -> list[str]:
    """Returns list of signal names found in content."""
    found = []
    for name, pattern in signals:
        if re.search(pattern, content_lower, re.IGNORECASE):
            found.append(name)
    return found


def _empty_context() -> dict:
    return {
        "file_format":       "unknown",
        "severity_mode":     "lenient",
        "structured_fields": [],
        "signals":           {"forensic": [], "crypto": [], "web": [], "common": []},
        "category_scores":   {"forensic": 0, "crypto": 0, "web": 0},
        "flags": {
            "has_flag_exposed": False, "has_private_key": False,
            "has_difficulty": False,   "has_author": False,
            "has_hints": False,        "has_objectives": False,
            "has_flag_hidden": False,  "has_docker": False,
        },
        "char_count": 0,
    }
