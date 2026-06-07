"""
Unified Ingestor/Extractor Node — extracts readable text from uploaded files
and deterministically infers input format and domain category.
Supports: JSON, YAML, ZIP, TXT, Markdown, PDF (basic).
"""
import json
import zipfile
import io
import os
import yaml
from typing import Dict, Any, Tuple
from agents.state import CTFReviewState, AgentStep


def extractor_node(state: CTFReviewState) -> dict:
    """
    Ingesta el archivo del reto, descomprime de manera recursiva si es un ZIP,
    detecta si el formato es estructurado (YAML/JSON) o desestructurado,
    e identifica el dominio de seguridad sin usar LLMs.
    """
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="extractor",
        status="running",
        label="📄 Extrayendo contenido del archivo...",
        result=None
    ))

    filename = state["filename"]
    raw_bytes = state.get("_raw_bytes")  # injected by the API before graph run
    ext = filename.lower().split(".")[-1] if "." in filename else "txt"

    try:
        # 1. Extracción de contenido físico
        text = _extract(filename, ext, raw_bytes)
        parsed_metadata = _try_parse_structured(text, ext) or {}
        
        format_detected = "unstructured"
        if parsed_metadata and len(parsed_metadata) >= 2:
            format_detected = "structured"

        # 2. Escaneo determinista de señales de dominio
        domain_detected = "unknown"
        if format_detected == "unstructured":
            content_lower = text.lower()
            forensic_signals = ["wireshark", "pcap", "volatility", "memory_dump", "autopsy", "forense", "forensic"]
            crypto_signals = ["rsa", "aes", "cipher", "private key", "elliptic", "md5", "sha1", "des", "cripto", "crypto"]
            web_signals = ["docker", "http_method", "endpoint", "sqli", "xss", "session", "url", "puerto", "port"]
            
            if any(sig in content_lower for sig in forensic_signals):
                domain_detected = "forensic"
            elif any(sig in content_lower for sig in crypto_signals):
                domain_detected = "crypto"
            elif any(sig in content_lower for sig in web_signals):
                domain_detected = "web"
        else:
            # Si es estructurado, se lee directamente del campo clave de la ontología
            # Acepta claves como 'domain' o 'categoria'
            domain_detected = parsed_metadata.get("domain") or parsed_metadata.get("category") or "unknown"
            domain_detected = str(domain_detected).lower()

        # Completar paso
        steps[-1] = AgentStep(
            node="extractor",
            status="completed",
            label=f"📄 Ingesta completa ({format_detected.upper()}) | Dominio: {domain_detected.upper()}",
            result={
                "chars": len(text),
                "format_detected": format_detected,
                "domain_detected": domain_detected,
                "fields_found": list(parsed_metadata.keys())
            }
        )

        return {
            "file_content": text,
            "format_detected": format_detected,
            "domain_detected": domain_detected,
            "parsed_template": parsed_metadata,  # Keep for compatibility
            "parsed_metadata": parsed_metadata,
            "steps": steps,
            "iteration": 0,
            "warnings": [],
            "structural_errors": [],
            "security_violations": [],
            "agent_logs": ["Archivo ingerido y mapeado a dominio."],
            "findings": [] # Initialize empty list of findings
        }

    except Exception as e:
        steps[-1] = AgentStep(
            node="extractor",
            status="error",
            label=f"📄 Error en ingesta: {str(e)}",
            result=None
        )
        return {
            "steps": steps,
            "error": str(e),
            "file_content": "",
            "format_detected": "unstructured",
            "domain_detected": "unknown",
            "parsed_metadata": {},
            "iteration": 0,
            "warnings": [],
            "structural_errors": [],
            "security_violations": [],
            "agent_logs": [f"Error en extractor: {str(e)}"]
        }


def _extract(filename: str, ext: str, raw_bytes: bytes) -> str:
    if ext == "zip":
        return _extract_zip(raw_bytes)
    elif ext == "pdf":
        return _extract_pdf(raw_bytes)
    else:
        # JSON, YAML, TXT, MD — just decode
        return raw_bytes.decode("utf-8", errors="replace")


def _extract_zip(raw_bytes: bytes) -> str:
    """Extract all text files from ZIP."""
    parts = []
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
        for name in zf.namelist():
            ext = name.lower().split(".")[-1] if "." in name else ""
            if ext in ("txt", "md", "json", "yaml", "yml", "py", "sh", "c", "js", "ts", "html", "cfg", "ini", "conf"):
                try:
                    content = zf.read(name).decode("utf-8", errors="replace")
                    parts.append(f"=== FILE: {name} ===\n{content}")
                except Exception:
                    pass
    return "\n\n".join(parts) if parts else "Empty or binary ZIP"


def _extract_pdf(raw_bytes: bytes) -> str:
    """Basic PDF text extraction."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception:
        return "[PDF extraction failed]"


def _try_parse_structured(text: str, ext: str) -> dict | None:
    """Try to parse JSON or YAML into a dict."""
    try:
        if ext == "json":
            return json.loads(text)
        elif ext in ("yaml", "yml"):
            return yaml.safe_load(text)
        else:
            # Try JSON first, then YAML
            try:
                return json.loads(text)
            except Exception:
                try:
                    result = yaml.safe_load(text)
                    if isinstance(result, dict):
                        return result
                except Exception:
                    pass
    except Exception:
        pass
    return None
