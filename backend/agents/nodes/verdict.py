"""
Verdict Node — computes the final mathematical weighted score and determines
the business verdict (valid, invalid, insecure) based on deterministic thresholds.
Consolidates findings to match the format expected by the frontend.
"""
from typing import List, Dict, Any, Optional
from agents.state import CTFReviewState, AgentStep, Finding


def verdict_node(state: CTFReviewState) -> dict:
    """
    Consolida todos los hallazgos en la lista compatible con el frontend,
    calcula la puntuación normalizada ponderada y determina el veredicto.
    """
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="verdict",
        status="running",
        label="⚖️ Calculando veredicto final...",
        result=None
    ))

    error = state.get("error")
    if error:
        steps[-1] = AgentStep(
            node="verdict",
            status="error",
            label="⚖️ Error en el pipeline — no se puede emitir veredicto",
            result=None
        )
        return {
            "verdict": "invalid",
            "score": 0,
            "findings": [],
            "steps": steps
        }

    template = state.get("template_rules") or {}
    errors = state.get("structural_errors") or []
    warnings = state.get("warnings") or []
    violations = state.get("security_violations") or []
    
    # ── 1. CÁLCULO DEL SCORE PONDERADO NORMALIZADO ──────────────────────────
    total_weight = 0.0
    approved_weight = 0.0
    error_weight = 0.0
    warning_weight = 0.0
    
    # Rastrear qué reglas específicas fallaron
    failed_fields = {err.get("field") for err in errors if err.get("field")}
    warned_fields = {warn.get("field") for warn in warnings if warn.get("field")}
    
    # A. Pesos de campos definidos
    fields_spec = template.get("validation_rules", {}).get("fields", {})
    for field, specs in fields_spec.items():
        # Peso por defecto: 1.0 si es requerido, 0.5 si es opcional
        weight = specs.get("weight", 1.0 if specs.get("required") else 0.5)
        total_weight += weight
        
        if field in failed_fields:
            error_weight += weight
        elif field in warned_fields:
            warning_weight += weight
        else:
            approved_weight += weight
            
    # B. Pesos de firmas de seguridad
    security_sigs = template.get("validation_rules", {}).get("security_signatures", [])
    violated_sigs = {v.get("name") for v in violations if v.get("name")}
    for sig in security_sigs:
        weight = sig.get("weight", 1.0)
        total_weight += weight
        
        sig_name = sig.get("name")
        if sig_name in violated_sigs:
            error_weight += weight
        else:
            approved_weight += weight
            
    # C. Pesos de advertencias dinámicas
    warnings_rules = template.get("validation_rules", {}).get("warnings_rules", [])
    triggered_warn_rules = {w.get("name") for w in warnings if w.get("name")}
    for rule in warnings_rules:
        weight = rule.get("weight", 0.5)
        total_weight += weight
        
        rule_name = rule.get("name")
        if rule_name in triggered_warn_rules:
            warning_weight += weight
        else:
            approved_weight += weight
            
    # D. Pesos de comprobaciones semánticas
    semantic_checks = template.get("validation_rules", {}).get("semantic_checks", [])
    semantic_findings = state.get("semantic_report", {}).get("semantic_findings", [])
    
    for check in semantic_checks:
        weight = check.get("weight", 1.0)
        total_weight += weight
        
        check_id = check.get("id")
        finding = next((f for f in semantic_findings if f.get("rule") == check_id), None)
        
        if finding:
            severity = finding.get("severity")
            if severity == "error":
                error_weight += weight
            elif severity == "warning":
                warning_weight += weight
            else:
                approved_weight += weight
        else:
            approved_weight += weight

    if total_weight == 0.0:
        total_weight = 1.0

    # Fórmula lineal normalizada
    base_ratio = approved_weight / total_weight
    warning_penalty = (warning_weight / total_weight) * 0.30
    error_penalty = (error_weight / total_weight) * 0.70
    
    calculated_score = 100.0 * (base_ratio - warning_penalty - error_penalty)
    final_score = int(max(0.0, min(100.0, calculated_score)))

    # ── 2. DETERMINACIÓN LÓGICA DEL VEREDICTO ────────────────────────────────
    has_critical_security = len(violations) > 0
    num_structural_errors = len(errors)
    num_warnings = len(warnings)
    
    # Los valores de verdict deben guardarse en minúsculas ('valid', 'invalid', 'insecure')
    # para ser compatibles con las clases css y el mapeo del frontend.
    if has_critical_security or num_structural_errors >= 3:
        verdict_status = "insecure"
        verdict_label = "⚖️ Veredicto: 🔴 INSEGURO — problemas de seguridad críticos"
    elif num_structural_errors > 0 or num_warnings > 5:
        verdict_status = "invalid"
        verdict_label = "⚖️ Veredicto: ❌ INVÁLIDO — no cumple requisitos mínimos"
    elif num_warnings > 2:
        verdict_status = "valid"
        verdict_label = "⚖️ Veredicto: ✅ VÁLIDO (con advertencias menores)"
    else:
        verdict_status = "valid"
        verdict_label = "⚖️ Veredicto: ✅ VÁLIDO"

    # ── 3. CONSOLIDACIÓN DE FINDINGS COMPATIBLES CON FRONTEND ──────────────────
    findings: List[Finding] = []
    
    # A. Agregar errores estructurales
    for err in errors:
        findings.append(Finding(
            severity="error",
            rule=err.get("rule") or f"missing_field_{err.get('field')}",
            message=err.get("message"),
            field=err.get("field")
        ))
        
    # B. Agregar violaciones de seguridad
    for viol in violations:
        findings.append(Finding(
            severity="error",
            rule=viol.get("name") or "security_violation",
            message=viol.get("message"),
            field=None
        ))
        
    # C. Agregar advertencias
    for warn in warnings:
        findings.append(Finding(
            severity="warning",
            rule=warn.get("name") or f"warning_{warn.get('field')}",
            message=warn.get("message"),
            field=warn.get("field")
        ))
        
    # D. Agregar comprobaciones que pasaron con éxito (para llenar el contador verde)
    # Campos que pasaron
    for field in fields_spec:
        if field not in failed_fields and field not in warned_fields:
            findings.append(Finding(
                severity="pass",
                rule=f"field_{field}",
                message=f"✓ Campo '{field}' correctamente definido",
                field=field
            ))
            
    # Firmas de seguridad que pasaron
    for sig in security_sigs:
        sig_name = sig.get("name")
        if sig_name not in violated_sigs:
            findings.append(Finding(
                severity="pass",
                rule=sig_name,
                message=f"✓ Sin problemas de seguridad: {sig.get('message') or sig_name}",
                field=None
            ))
            
    # Advertencias que pasaron
    for rule in warnings_rules:
        rule_name = rule.get("name")
        if rule_name not in triggered_warn_rules:
            findings.append(Finding(
                severity="pass",
                rule=rule_name,
                message=f"✓ Verificación de advertencia superada: {rule.get('message') or rule_name}",
                field=None
            ))
            
    # Comprobaciones semánticas que pasaron
    for check in semantic_checks:
        check_id = check.get("id")
        finding = next((f for f in semantic_findings if f.get("rule") == check_id), None)
        if not finding or finding.get("severity") == "pass":
            findings.append(Finding(
                severity="pass",
                rule=check_id,
                message=f"✓ Análisis semántico superado: {check.get('criterion') or check_id}",
                field=None
            ))

    # Actualizar paso
    steps[-1] = AgentStep(
        node="verdict",
        status="completed",
        label=f"{verdict_label} — Score: {final_score}/100",
        result={
            "verdict": verdict_status,
            "score": final_score,
            "errors": len(errors) + len(violations),
            "warnings": len(warnings),
            "passes": sum(1 for f in findings if f["severity"] == "pass")
        }
    )

    # Actualizar estado final
    return {
        "verdict": verdict_status,
        "score": final_score,
        "findings": findings,
        "steps": steps,
        "classification_reason": f"Análisis dinámico completado para el dominio {state.get('domain_detected', 'unknown').upper()}.",
        "challenge_type": state.get("domain_detected", "unknown")
    }
