"""
Semantic Refiner Node — runs when structural validation errors occur on an unstructured file.
Invokes Ollama to extract/infer missing required fields from the unstructured text.
"""
import os
import json
import ollama
from typing import Dict, Any, List
from agents.state import CTFReviewState, AgentStep


OLLAMA_HOST  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def semantic_refiner_node(state: CTFReviewState) -> dict:
    """
    Nodo de reflexión y autocorrección. Si se detectan errores estructurales
    en retos no estructurados, este nodo intenta deducir los datos faltantes
    utilizando el modelo de lenguaje a partir de la documentación del reto.
    """
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="semantic_refiner",
        status="running",
        label="🧠 Ejecutando bucle de autocorrección semántica...",
        result=None
    ))

    raw_content = state.get("file_content", "")
    errors = state.get("structural_errors") or []
    template = state.get("template_rules") or {}
    parsed_metadata = dict(state.get("parsed_metadata") or {})
    
    # Identificar qué campos obligatorios causaron el fallo
    missing_fields = [err["field"] for err in errors if "field" in err]
    fields_spec = template.get("validation_rules", {}).get("fields", {})
    
    target_extraction = {field: fields_spec[field] for field in missing_fields if field in fields_spec}
    
    if not target_extraction:
        steps[-1] = AgentStep(
            node="semantic_refiner",
            status="completed",
            label="🧠 Bucle de autocorrección: Nada que extraer",
            result={"status": "skipped"}
        )
        return {
            "iteration": state.get("iteration", 0) + 1,
            "steps": steps
        }

    # Construir un prompt adaptativo para la corrección semántica 
    prompt = f"""
    Usted es un analizador de configuraciones de CTF. El reto proporcionado falló la validación estricta de campos.
    Se requiere extraer o deducir los siguientes campos faltantes a partir del texto del reto:
    {json.dumps(target_extraction, indent=2)}
    
    Contenido del reto:
    \"\"\"{raw_content}\"\"\"
    
    Instrucciones: Devuelva un objeto JSON válido con los valores deducidos. Si un campo no puede ser inferido, escriba null.
    Devuelva ÚNICAMENTE el JSON sin formato Markdown:
    {{
      "campo1": "valor deducido",
      "campo2": null
    }}
    """
    
    inferred_data = {}
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise data extractor. Respond only in JSON."},
                {"role": "user",   "content": prompt},
            ],
            format="json",
            options={"temperature": 0.0}
        )
        
        inferred_data = json.loads(response["message"]["content"])
    except Exception as e:
        steps[-1] = AgentStep(
            node="semantic_refiner",
            status="error",
            label=f"🧠 Bucle de autocorrección fallido: {str(e)}",
            result=None
        )
        return {
            "iteration": state.get("iteration", 0) + 1,
            "steps": steps,
            "agent_logs": state.get("agent_logs", []) + [f"Error en el bucle de reflexión semántica: {str(e)}"]
        }

    resolved_errors = []
    warnings = list(state.get("warnings", []))
    
    for field, value in inferred_data.items():
        if value is not None:
            # El campo fue recuperado semánticamente. Guardar el metadato
            parsed_metadata[field] = value
            # Reducimos el error a una advertencia
            warnings.append({
                "field": field,
                "message": f"Campo inferido semánticamente a partir del texto libre: '{value}'."
            })
        else:
            # El campo realmente no existe. Se mantiene el error estructural
            resolved_errors.append({
                "field": field,
                "message": f"El campo obligatorio '{field}' no pudo ser inferido a partir de la documentación del reto."
            })

    # Si había errores que no se corresponden con campos en target_extraction (por ejemplo, errores de tipo/patrón),
    # los mantenemos intactos.
    for err in errors:
        field = err.get("field")
        if field not in target_extraction:
            resolved_errors.append(err)

    steps[-1] = AgentStep(
        node="semantic_refiner",
        status="completed",
        label=f"🧠 Autocorrección semántica finalizada | Recuperados: {len(inferred_data) - len(resolved_errors)}",
        result={
            "inferred_fields": inferred_data,
            "remaining_errors": len(resolved_errors)
        }
    )

    return {
        "parsed_metadata": parsed_metadata,
        "structural_errors": resolved_errors,
        "warnings": warnings,
        "iteration": state.get("iteration", 0) + 1,
        "steps": steps,
        "agent_logs": state.get("agent_logs", []) + [f"Deducción semántica ejecutada. Errores restantes: {len(resolved_errors)}"]
    }
