"""
LangGraph pipeline definition for CTF challenge review.
Unified single-agent declarative ReAct loop with Pydantic compilation.
"""
from langgraph.graph import StateGraph, END
from agents.state import CTFReviewState
from agents.nodes.extractor import extractor_node
from agents.nodes.schema_compiler import schema_compiler_node
from agents.nodes.generalized_agent import generalized_agent_node
from agents.nodes.semantic_refiner import semantic_refiner_node
from agents.nodes.verdict import verdict_node


def route_after_extractor(state: CTFReviewState) -> str:
    """
    Ruteo condicional inmediatamente después del extractor.

    Si se detectó un mismatch CRÍTICO de firma (magic numbers), el workflow
    se termina aquí — no se ejecuta ningún agente posterior.
    De lo contrario, el flujo continúa normalmente a schema_compiler.
    """
    if state.get("magic_blocked"):
        return END  # 🚨 Firma inválida — pipeline bloqueado
    return "schema_compiler"


def route_after_agent(state: CTFReviewState) -> str:
    """
    Ruteo condicional después de la ejecución del agente generalizado.
    Si se detectan errores estructurales en archivos no estructurados y es la primera iteración (0),
    se desvía el flujo al nodo de autocorrección semántica.
    De lo contrario, avanza al cálculo de veredicto.
    """
    format_detected = state.get("format_detected", "unstructured")
    structural_errors = state.get("structural_errors", [])
    iteration = state.get("iteration", 0)
    
    if format_detected == "unstructured" and len(structural_errors) > 0 and iteration == 0:
        return "semantic_refiner"
        
    return "verdict"


def build_graph() -> StateGraph:
    """Build and compile the CTF review LangGraph."""
    graph = StateGraph(CTFReviewState)

    # ── Nodes ─────────────────────────────────────────────────────────────────
    graph.add_node("extractor", extractor_node)
    graph.add_node("schema_compiler", schema_compiler_node)
    graph.add_node("generalized_agent", generalized_agent_node)
    graph.add_node("semantic_refiner", semantic_refiner_node)
    graph.add_node("verdict_node", verdict_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("extractor")

    # ── Edges ─────────────────────────────────────────────────────────────────
    # Ingesta → ruteo condicional: si magic_blocked → END, si no → schema_compiler
    graph.add_conditional_edges(
        "extractor",
        route_after_extractor,
        {
            "schema_compiler": "schema_compiler",
            END: END,
        }
    )

    # Compilador -> Agente Generalizado (Regex, Warnings, LLM Semántico)
    graph.add_edge("schema_compiler", "generalized_agent")

    # Ruteo condicional post-agente: Autocorrección Semántica o Veredicto
    graph.add_conditional_edges(
        "generalized_agent",
        route_after_agent,
        {
            "semantic_refiner": "semantic_refiner",
            "verdict": "verdict_node",
        }
    )

    # Bucle de autocorrección semántica: Refinamiento -> Re-validación del esquema
    graph.add_edge("semantic_refiner", "schema_compiler")

    # Cierre del flujo
    graph.add_edge("verdict_node", END)

    return graph.compile()


# Singleton — compiled once at startup
ctf_graph = build_graph()
