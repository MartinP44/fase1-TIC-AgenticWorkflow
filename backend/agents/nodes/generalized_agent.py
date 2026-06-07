"""
Generalized Domain Agent Node — performs unified validation using deterministic tools
(RegexScanner, Warning Evaluator) and conceptual checks (SemanticReviewer LLM).
"""
import os
import re
import json
import ollama
from typing import Dict, Any, List
from agents.state import CTFReviewState, AgentStep


OLLAMA_HOST  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def generalized_agent_node(state: CTFReviewState) -> dict:
    """
    Agente generalizado que orquesta herramientas deterministas de validación
    y delega en un LLM el análisis cualitativo.
    """
    domain = state.get("domain_detected", "unknown")
    steps = list(state.get("steps", []))

    # Mapear el nombre del nodo al dominio detectado para compatibilidad con la interfaz
    node_name = f"{domain}_agent" if domain in ("web", "crypto", "forensic") else "classifier"
    
    emojis = {"web": "🌐", "crypto": "🔐", "forensic": "🔍"}
    emoji = emojis.get(domain, "🏷️")
    
    steps.append(AgentStep(
        node=node_name,
        status="running",
        label=f"{emoji} Analizando reto {domain.upper()} con reglas declarativas...",
        result=None
    ))

    raw_content = state.get("file_content", "")
    template_rules = state.get("template_rules") or {}
    parsed_metadata = state.get("parsed_metadata") or {}

    # 1. RegexScanner: Firmas de Seguridad Críticas
    security_violations = _check_security_signatures(raw_content, template_rules)

    # 2. Warning Evaluator: Advertencias dinámicas basadas en condicionales
    # Preservamos advertencias previas (ej. de la autocorrección semántica)
    warnings = list(state.get("warnings", []))
    new_warnings = _evaluate_warning_rules(parsed_metadata, template_rules)
    
    # Evitar duplicados por nombre de regla
    existing_warn_names = {w.get("name") for w in warnings if w.get("name")}
    for nw in new_warnings:
        if nw.get("name") not in existing_warn_names:
            warnings.append(nw)

    # 3. SemanticReviewer: Análisis semántico mediante LLM local
    semantic_findings = _check_semantic_llm(raw_content, template_rules)
    
    # Incorporar los hallazgos semánticos cualitativos en las listas correspondientes
    structural_errors = list(state.get("structural_errors", []))
    
    for sf in semantic_findings:
        sev = sf.get("severity")
        if sev == "error":
            structural_errors.append({
                "field": sf.get("field"),
                "message": f"[Semántico] {sf.get('message')}",
                "rule": sf.get("rule")
            })
        elif sev == "warning":
            warnings.append({
                "field": sf.get("field"),
                "message": f"[Semántico] {sf.get('message')}",
                "name": sf.get("rule")
            })

    # Consolidar el resultado del agente para el paso de la interfaz
    pass_count = len(template_rules.get("validation_rules", {}).get("fields", {})) - len(structural_errors)
    pass_count = max(0, pass_count)

    steps[-1] = AgentStep(
        node=node_name,
        status="completed",
        label=f"{emoji} Análisis {domain.upper()} completado — ✅{pass_count} ⚠️{len(warnings)} ❌{len(structural_errors) + len(security_violations)}",
        result={
            "security_violations_count": len(security_violations),
            "warnings_count": len(warnings),
            "structural_errors_count": len(structural_errors),
            "semantic_findings_evaluated": len(semantic_findings)
        }
    )

    return {
        "security_violations": security_violations,
        "warnings": warnings,
        "structural_errors": structural_errors,
        "semantic_report": {
            "semantic_findings": semantic_findings
        },
        "steps": steps,
        "agent_logs": state.get("agent_logs", []) + [f"Análisis del agente generalizado {domain.upper()} ejecutado."]
    }


def _check_security_signatures(raw_content: str, template_rules: dict) -> list:
    """Escanea el contenido del reto usando expresiones regulares fijas."""
    violations = []
    signatures = template_rules.get("validation_rules", {}).get("security_signatures", [])
    
    for sig in signatures:
        name = sig.get("name")
        pattern = sig.get("pattern")
        severity = sig.get("severity", "insecure")
        message = sig.get("message")
        
        if pattern:
            try:
                if re.search(pattern, raw_content):
                    violations.append({
                        "name": name,
                        "severity": severity,
                        "message": message
                    })
            except Exception:
                pass
                
    return violations


def _evaluate_warning_rules(parsed_metadata: dict, template_rules: dict) -> list:
    """Evalúa dinámicamente las condiciones de advertencias declaradas en el YAML."""
    warnings = []
    warnings_rules = template_rules.get("validation_rules", {}).get("warnings_rules", [])
    
    eval_env = {
        "__builtins__": None,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }
    
    # Normalizar llaves para la evaluación
    normalized_metadata = {k.lower(): v for k, v in parsed_metadata.items()}
    fields_spec = template_rules.get("validation_rules", {}).get("fields", {})
    
    for field_name in fields_spec:
        val = normalized_metadata.get(field_name.lower(), None)
        eval_env[field_name] = val
        
    for rule in warnings_rules:
        name = rule.get("name")
        condition = rule.get("condition")
        message = rule.get("message")
        
        if condition:
            try:
                # Evaluar la condición en un entorno sandbox
                if eval(condition, eval_env):
                    warnings.append({
                        "name": name,
                        "field": None,
                        "message": message
                    })
            except Exception:
                pass
                
    return warnings


def _check_semantic_llm(raw_content: str, template_rules: dict) -> list:
    """Realiza la revisión conceptual delegando al LLM local (Ollama)."""
    semantic_checks = template_rules.get("validation_rules", {}).get("semantic_checks", [])
    if not semantic_checks:
        return []
        
    criteria_str = ""
    for check in semantic_checks:
        criteria_str += f"- ID: {check.get('id')}\n  Criterio: {check.get('criterion')}\n  Instrucción: {check.get('prompt')}\n\n"
        
    system_prompt = f"""You are a cybersecurity expert and CTF platform security reviewer.
Analyze the CTF challenge template and check it against these semantic criteria:
{criteria_str}

For each criterion, determine if the challenge design satisfies it (severity: pass) or violates it (severity: warning or error).
You MUST respond ONLY with a valid JSON object in this format:
{{
  "semantic_findings": [
    {{
      "rule": "<criterion_id>",
      "severity": "pass" | "warning" | "error",
      "message": "<explicación breve en español sobre por qué pasa o falla>"
    }}
  ]
}}"""

    preview = raw_content[:4000] if len(raw_content) > 4000 else raw_content
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"Analyze this CTF challenge description/template:\n\n{preview}"},
            ],
            format="json",
            options={"temperature": 0.1},
        )
        result = json.loads(response["message"]["content"])
        return result.get("semantic_findings", [])
    except Exception as e:
        return [{
            "rule": "semantic_llm_error",
            "severity": "warning",
            "message": f"No se pudo completar el análisis semántico: {str(e)}"
        }]
