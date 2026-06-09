"""
Forensic Agent Node — analyzes forensic CTF challenges.
Uses Ollama SDK directly (no LangChain).
"""
import re
import json
import os
import ollama
from agents.state import CTFReviewState, AgentStep, Finding
from rules.forensic_rules import get_forensic_rules
from rules.field_extractor import enrich_parsed, is_unstructured

OLLAMA_HOST  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """You are a CTF platform security reviewer specializing in Digital Forensics challenges.
Analyze the CTF challenge template and verify:
1. The forensic artifact is properly described and typed
2. Required tools for solving are documented
3. The challenge difficulty is appropriate and fair
4. The flag is embedded in the artifact, NOT exposed in the template

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


def forensic_agent_node(state: CTFReviewState) -> CTFReviewState:
    """Applies forensic-specific business rules and LLM analysis."""
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="forensic_agent",
        status="running",
        label="🔍 Analizando reto FORENSE con reglas de negocio...",
        result=None
    ))

    content       = state.get("file_content", "")
    parsed        = state.get("parsed_template") or {}
    findings      = list(state.get("findings", []))
    explorer_ctx  = state.get("explorer_context") or {}
    severity_mode = explorer_ctx.get("severity_mode", "lenient")

    # Enrich parsed fields from raw text when file is unstructured (MD/TXT)
    enriched_parsed = enrich_parsed(parsed, content)

    findings.extend(_check_structural_rules(enriched_parsed, content, severity_mode))
    findings.extend(_llm_analysis(content))

    pass_count = sum(1 for f in findings if f["severity"] == "pass")
    warn_count = sum(1 for f in findings if f["severity"] == "warning")
    err_count  = sum(1 for f in findings if f["severity"] == "error")

    steps[-1] = AgentStep(
        node="forensic_agent",
        status="completed",
        label=f"🔍 Análisis FORENSE completado — ✅{pass_count} ⚠️{warn_count} ❌{err_count}",
        result={"pass": pass_count, "warnings": warn_count, "errors": err_count}
    )

    return {**state, "findings": findings, "steps": steps}


def _check_structural_rules(parsed: dict, content: str, severity_mode: str = "strict") -> list:
    findings   = []
    rules      = get_forensic_rules()
    normalized = {k.lower(): v for k, v in parsed.items()}

    for rule in rules:
        check = rule.get("check")

        # ── Direct flag exposure ──────────────────────────────────────────────
        if check == "no_flag_direct":
            if re.search(r"CTF\{[^}]+\}", content):
                findings.append(Finding(severity=rule["severity"], rule=rule["id"],
                                        message=rule["message"], field=None))
            else:
                findings.append(Finding(severity="pass", rule=rule["id"],
                                        message="✓ Flag no expuesta directamente", field=None))
            continue

        # ── Field presence + optional allowed_values ──────────────────────────
        if "field" in rule:
            field = rule["field"].lower()
            # Downgrade errors → warnings for unstructured files
            effective_severity = rule["severity"]
            if severity_mode == "lenient" and effective_severity == "error":
                effective_severity = "warning"

            if field not in normalized or normalized[field] in (None, "", []):
                findings.append(Finding(severity=effective_severity, rule=rule["id"],
                                        message=rule["message"], field=rule["field"]))
            else:
                value = normalized[field]
                # Validate against allowed values if specified
                if "allowed_values" in rule and str(value).lower() not in [
                    v.lower() for v in rule["allowed_values"]
                ]:
                    findings.append(Finding(
                        severity="warning",
                        rule=rule["id"],
                        message=f"Tipo '{value}' no reconocido. {rule['message']}",
                        field=rule["field"],
                    ))
                else:
                    findings.append(Finding(severity="pass", rule=rule["id"],
                                            message=f"✓ Campo '{rule['field']}' presente",
                                            field=rule["field"]))

    return findings


def _llm_analysis(content: str) -> list:
    """Semantic analysis via Ollama SDK."""
    try:
        from agents.llm_debug import llm_chat
        client  = ollama.Client(host=OLLAMA_HOST)
        preview = content[:3000] if len(content) > 3000 else content

        response = llm_chat(
            client,
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Analyze this forensic CTF challenge template:\n\n{preview}"},
            ],
            node_name="forensic_agent",
            format="json",
            options={"temperature": 0.1},
        )

        result = json.loads(response["message"]["content"])
        return [
            Finding(severity=f["severity"], rule=f.get("rule", "llm_analysis"),
                    message=f["message"], field=f.get("field"))
            for f in result.get("llm_findings", [])
        ]
    except Exception as e:
        return [Finding(severity="warning", rule="llm_analysis",
                        message=f"Análisis LLM no disponible: {e}", field=None)]
