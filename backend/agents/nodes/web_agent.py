"""
Web Agent Node — analyzes web CTF challenges against business rules.
Uses both structural (field checks) and Ollama SDK semantic analysis (no LangChain).
"""
import re
import json
import os
import ollama
from agents.state import CTFReviewState, AgentStep, Finding
from rules.web_rules import get_web_rules, get_insecure_patterns
from rules.field_extractor import enrich_parsed

OLLAMA_HOST  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """You are a CTF platform security reviewer specializing in Web challenges.
You will receive the content of a CTF challenge template and perform a deep analysis.

Your task:
1. Check if it follows good security design practices
2. Verify the challenge is solvable but not trivially so
3. Identify any unintended vulnerabilities or design flaws
4. Check that the docker setup is secure and reproducible

You MUST respond ONLY with valid JSON (no markdown fences):
{
  "llm_findings": [
    {
      "severity": "pass" | "warning" | "error",
      "rule": "<rule_id>",
      "message": "<message in Spanish>",
      "field": "<field_name or null>"
    }
  ],
  "overall_assessment": "<brief assessment in Spanish>",
  "is_well_designed": true | false
}"""


def web_agent_node(state: CTFReviewState) -> CTFReviewState:
    """Applies web-specific business rules and LLM analysis."""
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="web_agent",
        status="running",
        label="🌐 Analizando reto WEB con reglas de negocio...",
        result=None
    ))

    content          = state.get("file_content", "")
    parsed           = state.get("parsed_template") or {}
    findings         = list(state.get("findings", []))
    explorer_ctx     = state.get("explorer_context") or {}
    severity_mode    = explorer_ctx.get("severity_mode", "lenient")

    # Enrich parsed fields from raw text when file is unstructured (MD/TXT)
    enriched_parsed = enrich_parsed(parsed, content)

    # ── 1. Structural rule checks ─────────────────────────────────────────────
    findings.extend(_check_structural_rules(enriched_parsed, content, severity_mode))

    # ── 2. Security pattern checks ────────────────────────────────────────────
    findings.extend(_check_security_patterns(content))

    # ── 3. LLM deep analysis (Ollama SDK) ────────────────────────────────────
    findings.extend(_llm_analysis(content))

    pass_count = sum(1 for f in findings if f["severity"] == "pass")
    warn_count = sum(1 for f in findings if f["severity"] == "warning")
    err_count  = sum(1 for f in findings if f["severity"] == "error")

    steps[-1] = AgentStep(
        node="web_agent",
        status="completed",
        label=f"🌐 Análisis WEB completado — ✅{pass_count} ⚠️{warn_count} ❌{err_count}",
        result={"pass": pass_count, "warnings": warn_count, "errors": err_count}
    )

    return {**state, "findings": findings, "steps": steps}


def _check_structural_rules(parsed: dict, content: str, severity_mode: str = "strict") -> list:
    """Check required fields and structural rules."""
    findings = []
    rules    = get_web_rules()
    normalized = {k.lower(): v for k, v in parsed.items()}

    for rule in rules:
        if "field" not in rule:
            continue

        field = rule["field"].lower()
        check = rule.get("check")

        # ── Field presence check ──────────────────────────────────────────────
        # In lenient mode (unstructured files), downgrade errors → warnings
        effective_severity = rule["severity"]
        if severity_mode == "lenient" and effective_severity == "error":
            effective_severity = "warning"

        if field not in normalized:
            findings.append(Finding(
                severity=effective_severity,
                rule=rule["id"],
                message=rule["message"],
                field=rule["field"]
            ))
            continue

        value = normalized[field]

        # ── Empty value ───────────────────────────────────────────────────────
        if value is None or value == "" or value == []:
            findings.append(Finding(
                severity=effective_severity,
                rule=rule["id"],
                message=rule["message"],
                field=rule["field"]
            ))
            continue

        # ── Special check: docker no latest tag ──────────────────────────────
        if check == "no_latest":
            v = str(value)
            # Flag :latest explicitly OR no tag AND no registry path (bare image name)
            if v.endswith(":latest") or (":" not in v and "/" not in v):
                findings.append(Finding(
                    severity=rule["severity"],
                    rule=rule["id"],
                    message=rule["message"],
                    field=rule["field"]
                ))
                continue

        # ── Allowed values check ──────────────────────────────────────────────
        if "allowed_values" in rule and value:
            if str(value).upper() not in rule["allowed_values"]:
                findings.append(Finding(
                    severity=rule["severity"],
                    rule=rule["id"],
                    message=f"Valor inválido '{value}'. {rule['message']}",
                    field=rule["field"]
                ))
                continue

        # ── All checks passed ─────────────────────────────────────────────────
        findings.append(Finding(
            severity="pass",
            rule=rule["id"],
            message=f"✓ Campo '{rule['field']}' correctamente definido",
            field=rule["field"]
        ))

    return findings


def _check_security_patterns(content: str) -> list:
    """Check for insecure patterns in the raw text."""
    findings = []
    for p in get_insecure_patterns():
        flags = re.IGNORECASE if p.get("flags") == "IGNORECASE" else 0
        if re.search(p["pattern"], content, flags):
            findings.append(Finding(
                severity=p["severity"],
                rule=p["id"],
                message=p["message"],
                field=None
            ))
        else:
            findings.append(Finding(
                severity="pass",
                rule=p["id"],
                message=f"✓ Sin problemas de seguridad: {p['id'].replace('_', ' ')}",
                field=None
            ))
    return findings


def _llm_analysis(content: str) -> list:
    """Semantic analysis via Ollama SDK — no LangChain."""
    try:
        client  = ollama.Client(host=OLLAMA_HOST)
        preview = content[:3000] if len(content) > 3000 else content

        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Analyze this web CTF challenge template:\n\n{preview}"},
            ],
            format="json",
            options={"temperature": 0.1},
        )

        result = json.loads(response["message"]["content"])
        return [
            Finding(
                severity=f["severity"],
                rule=f.get("rule", "llm_analysis"),
                message=f["message"],
                field=f.get("field"),
            )
            for f in result.get("llm_findings", [])
        ]
    except Exception as e:
        return [Finding(
            severity="warning",
            rule="llm_analysis",
            message=f"Análisis semántico LLM no disponible: {e}",
            field=None,
        )]
