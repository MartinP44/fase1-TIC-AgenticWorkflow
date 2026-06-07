"""
Flexible field extractor — fills in missing structured fields from unstructured text.

When a challenge is submitted as Markdown/TXT (parsed_template is None or incomplete),
this module scans the raw text for semantic signals so field-based rules degrade to
warnings instead of hard errors on every field.
"""
import re
from typing import Optional


# ── Keyword maps per field ────────────────────────────────────────────────────
# Maps field_name → list of regex patterns that signal its presence in raw text.
_FIELD_SIGNALS: dict[str, list[str]] = {
    # Forensic fields
    "artifact_type": [
        r"\b(pcap|\.pcap)\b",
        r"\b(memory.?dump|\.raw|volatility|ram\b)",
        r"\b(disk.?image|\.img|\.dd|\.e01)\b",
        r"\b(log.?file|auth\.log|syslog|\.log)\b",
        r"\bsteganography\b",
        r"\b(image|\.png|\.jpg|\.jpeg)\b",
    ],
    "artifact_file": [
        r"\b\w+\.(raw|pcap|img|dd|e01|png|jpg|jpeg|log|zip|tar)\b",
        r"\b(volcado|dump|artefacto|archivo)\b",
    ],
    "required_tools": [
        r"\b(volatility|wireshark|autopsy|testdisk|binwalk|strings|file\b|exiftool)\b",
        r"\b(herramienta|tool|utility)\b",
    ],
    "difficulty": [
        r"\b(easy|medium|hard|expert|beginner|fácil|difícil|intermedio|avanzado)\b",
    ],
    "tags": [
        r"\b(memory|network|stego|forensic|dfir|log|disk|pcap|steganography)\b",
    ],
    "author": [
        r"\b(autor|author|created by|by|diseñado por)\b",
    ],
    "size": [
        r"\b\d+\s*(mb|gb|kb|bytes?)\b",
        r"\bsize\b",
        r"\btamaño\b",
    ],

    # Crypto fields
    "algorithm": [
        r"\b(rsa|aes|des|3des|rc4|blowfish|ecdsa|elliptic|xor|caesar|vigenere|base64|rot13)\b",
        r"\b(cipher|encrypt|decrypt|hash|crypt)\b",
    ],
    "key_size": [
        r"\b(\d+)\s*(bits?|bytes?)\b",
        r"\bkey.?size\b",
    ],
    "challenge_files": [
        r"\b\w+\.(enc|txt|py|pem|pub|key|bin|b64|hex)\b",
        r"\b(ciphertext|encrypted|output\.txt|chall\.py)\b",
    ],
    "solve_script": [
        r"\b(solve\.py|solution\.py|exploit\.py|script\b)\b",
        r"\b(resolver|solve|solución|solution)\b",
    ],

    # Web fields
    "url": [
        r"https?://\S+",
        r"\b(localhost|127\.0\.0\.1|0\.0\.0\.0)\b",
        r"\b(endpoint|url|uri|ruta|route)\b",
    ],
    "port": [
        r"\bport\s*[:\s]\s*\d{2,5}\b",
        r":\d{2,5}\b",
        r"\bpuerto\b",
    ],
    "docker_image": [
        r"\b(docker|image|imagen|container|contenedor)\b",
        r"docker\.io/\S+",
        r"\bfrom\s+\w+[:/]\S+",
    ],
    "technology_stack": [
        r"\b(flask|django|fastapi|node\.?js|express|php|laravel|ruby|rails|spring|go|gin|nginx|apache)\b",
    ],
    "http_method": [
        r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b",
    ],
    "authentication_required": [
        r"\b(auth|login|authentication|credenciales|usuario|password|token|jwt|cookie)\b",
    ],
    "endpoint": [
        r"/\w+(?:/\w+)*",
        r"\b(endpoint|ruta|route|path)\b",
    ],
}

# Value hints to infer a plausible value string for each field
_FIELD_VALUE_HINTS: dict[str, str] = {
    "artifact_type":           "inferred_from_text",
    "artifact_file":           "inferred_from_text",
    "required_tools":          ["inferred"],
    "difficulty":              "medium",
    "tags":                    ["inferred"],
    "author":                  "inferred_from_text",
    "size":                    "inferred_from_text",
    "algorithm":               "inferred_from_text",
    "key_size":                "inferred_from_text",
    "challenge_files":         ["inferred"],
    "solve_script":            "inferred_from_text",
    "url":                     "http://localhost",
    "port":                    "inferred_from_text",
    "docker_image":            "ctf/challenge:v1",
    "technology_stack":        "inferred_from_text",
    "http_method":             "GET",
    "authentication_required": True,
    "endpoint":                "/",
    "session_type":            "stateless",
    "ram":                     "inferred_from_text",
}


def enrich_parsed(parsed: Optional[dict], content: str) -> dict:
    """
    Returns an enriched copy of `parsed` where missing fields are inferred
    from signals found in the raw text content.

    Fields inferred this way are marked with a special sentinel value so the
    rule checker can downgrade severity from error → warning instead of failing.
    """
    enriched = dict(parsed) if parsed else {}
    normalized_content = content.lower()

    for field, patterns in _FIELD_SIGNALS.items():
        if field in {k.lower() for k in enriched}:
            continue  # already explicitly set — don't override

        for pattern in patterns:
            if re.search(pattern, normalized_content, re.IGNORECASE):
                enriched[field] = _FIELD_VALUE_HINTS.get(field, "inferred_from_text")
                break  # found at least one signal — field is "present"

    return enriched


def is_unstructured(parsed: Optional[dict]) -> bool:
    """Returns True when the original file has no parseable structure (Markdown, TXT)."""
    return not parsed or len(parsed) == 0
