from typing import TypedDict, Optional, List, Any


class Finding(TypedDict):
    severity: str       # "pass" | "warning" | "error"
    rule: str           # rule id
    message: str        # human readable
    field: Optional[str]  # which field triggered this


class AgentStep(TypedDict):
    node: str           # node name
    status: str         # "running" | "completed" | "error"
    label: str          # human readable label shown in UI
    result: Optional[Any]  # node output


class CTFReviewState(TypedDict):
    # Input
    filename: str
    file_content: str       # raw extracted text
    _raw_bytes: Optional[bytes]  # injected by API, consumed by extractor_node

    # Explorer analysis (produced before classification)
    explorer_context: Optional[dict]  # signals, file_format, severity_mode, detected_fields

    # Classification
    challenge_type: Optional[str]    # "web" | "crypto" | "forensic" | "unknown"
    classification_confidence: Optional[float]
    classification_reason: Optional[str]
    parsed_template: Optional[dict]  # parsed JSON/YAML fields if applicable

    # Analysis
    findings: List[Finding]
    score: Optional[int]             # 0-100

    # Final verdict
    verdict: Optional[str]           # "valid" | "invalid" | "insecure"

    # Pipeline tracking (for SSE)
    steps: List[AgentStep]
    error: Optional[str]

    # Nuevos campos del rediseño agéntico declarativo
    format_detected: Optional[str]     # "structured" | "unstructured"
    domain_detected: Optional[str]     # "web" | "crypto" | "forensic" | "unknown"
    template_rules: Optional[dict]
    compiled_model: Optional[Any]
    structural_errors: List[dict]       # [{"field": str, "message": str}]
    security_violations: List[dict]     # [{"name": str, "message": str, "severity": str}]
    warnings: List[dict]                 # [{"field": str, "message": str}]
    semantic_report: Optional[dict]
    agent_logs: List[str]
    iteration: int                      # Para el loop de autocorrección semántica
    parsed_metadata: Optional[dict]     # Metadatos unificados leídos o inferidos
    magic_blocked: Optional[bool]       # True si el workflow fue bloqueado por mismatch de firma

