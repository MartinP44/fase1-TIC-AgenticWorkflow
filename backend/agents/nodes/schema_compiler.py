"""
Schema Compiler Node — compiles dynamic Pydantic validator models on the fly
based on the YAML template corresponding to the detected challenge domain.
"""
import os
import yaml
from typing import Any, Dict, List, Optional, Tuple, Type, Union, Literal
from pydantic import BaseModel, Field, create_model, StringConstraints, ValidationError
from typing_extensions import Annotated
from agents.state import CTFReviewState, AgentStep


def compile_pydantic_model(yaml_config: Dict[str, Any], force_strict: bool = False) -> Type[BaseModel]:
    """
    Compila dinámicamente una clase Pydantic BaseModel basada en las especificaciones 
    declaradas dentro de la plantilla ontológica YAML del dominio.
    """
    domain = yaml_config.get("domain", "unknown")
    fields_spec = yaml_config.get("validation_rules", {}).get("fields", {})
    
    # Si se fuerza modo estricto (para la primera iteración de autocorrección), ignoramos 'lenient'
    severity_mode = "strict" if force_strict else yaml_config.get("configuration", {}).get("severity_mode", "strict")
    
    dynamic_fields: Dict[str, Tuple[Any, Any]] = {}
    
    for field_name, rules in fields_spec.items():
        yaml_type = rules.get("type", "string")
        is_required = rules.get("required", False)
        
        # Mapeo de tipos declarativos de YAML a primitivas de Python
        python_type: Type = str
        if yaml_type == "integer":
            python_type = int
        elif yaml_type == "float":
            python_type = float
        elif yaml_type == "boolean":
            python_type = bool
        elif yaml_type == "array":
            python_type = List[Any]
            
        # Inyección dinámica de restricciones de validación nativas de Pydantic
        field_kwargs: Dict[str, Any] = {}
        
        # Validación de allowed_values
        allowed_values = rules.get("allowed_values")
        if allowed_values and isinstance(allowed_values, list):
            try:
                python_type = Literal[tuple(allowed_values)]
            except Exception:
                pass
        
        # String constraints (pattern matching)
        if python_type is str:
            pattern = rules.get("pattern")
            if pattern:
                python_type = Annotated[str, StringConstraints(pattern=pattern)]
                
        elif python_type in [int, float]:
            minimum = rules.get("minimum")
            maximum = rules.get("maximum")
            if minimum is not None:
                field_kwargs["ge"] = minimum
            if maximum is not None:
                field_kwargs["le"] = maximum
                
        # Evaluación del Modo de Severidad Dinámica
        if severity_mode == "lenient":
            python_type = Optional[python_type]
            default_value = None
        else:
            if is_required:
                default_value = ...
            else:
                python_type = Optional[python_type]
                default_value = None
                
        if allowed_values:
            field_kwargs["description"] = f"Allowed values: {allowed_values}"
            
        dynamic_fields[field_name] = (python_type, Field(default_value, **field_kwargs))
        
    model_name = f"Dynamic{domain.capitalize()}ChallengeModel"
    compiled_model = create_model(
        model_name,
        __module__=__name__,
        **dynamic_fields
    )
    
    return compiled_model


def schema_compiler_node(state: CTFReviewState) -> dict:
    """
    Localiza la plantilla ontológica correspondiente al dominio detectado,
    compila el modelo dinámico de Pydantic e inicializa la validación estructural.
    """
    steps = list(state.get("steps", []))
    domain = state.get("domain_detected", "unknown")
    iteration = state.get("iteration", 0)

    # 1. Cargar plantilla física basada en el dominio
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_path = os.path.join(base_dir, "templates", f"{domain}_template.yaml")
    
    if not os.path.exists(template_path):
        template_rules = {"domain": "unknown", "validation_rules": {"fields": {}}}
    else:
        with open(template_path, "r", encoding="utf-8") as f:
            template_rules = yaml.safe_load(f)

    # Si estamos en la iteración > 0, preservamos los errores y warnings que el semantic_refiner ya procesó.
    if iteration > 0:
        return {
            "template_rules": template_rules,
            "agent_logs": state.get("agent_logs", []) + ["Esquema dinámico preservado de la iteración anterior."]
        }

    steps.append(AgentStep(
        node="schema_compiler",
        status="running",
        label=f"📋 Compilando esquema y validando estructura ({domain.upper()})...",
        result=None
    ))

    # Para archivos desestructurados en la iteración 0, forzamos validación estricta
    # para poder identificar qué campos obligatorios hacen falta y pasarlos al refiner.
    force_strict = (state.get("format_detected") == "unstructured" and iteration == 0)
    
    # Compilar el modelo en caliente
    compiled_model = compile_pydantic_model(template_rules, force_strict=force_strict)
    parsed_metadata = state.get("parsed_metadata") or {}

    structural_errors = []
    try:
        # Validar de forma nativa contra la clase compilada de Pydantic
        compiled_model.model_validate(parsed_metadata)
    except ValidationError as e:
        # Extraer la localización exacta del campo fallido y el mensaje de error
        structural_errors = [
            {
                "field": str(err["loc"][0]) if err["loc"] else "unknown",
                "message": err["msg"]
            }
            for err in e.errors()
        ]

    steps[-1] = AgentStep(
        node="schema_compiler",
        status="completed",
        label=f"📋 Validación estructural completa | Errores: {len(structural_errors)}",
        result={
            "rules_defined": len(template_rules.get("validation_rules", {}).get("fields", {})),
            "errors_found": len(structural_errors)
        }
    )

    return {
        "template_rules": template_rules,
        "compiled_model": compiled_model,
        "structural_errors": structural_errors,
        "steps": steps,
        "agent_logs": state.get("agent_logs", []) + ["Esquema dinámico compilado y validación de Pydantic ejecutada."]
    }
