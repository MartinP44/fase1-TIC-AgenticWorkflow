"""
LLM Debug Logger — Wrapper alrededor de ollama.Client.chat()

Actívalo con: DEBUG_LLM=true en el .env

Muestra en consola:
  - El prompt de sistema y de usuario completo enviado al modelo
  - La respuesta raw del LLM
  - El tiempo de respuesta en ms
  - Token count (si disponible)

Uso:
    from agents.llm_debug import llm_chat
    response = llm_chat(client, model, messages, **kwargs)
"""

import os
import time
import textwrap
import json
from typing import Any

# ── Configuración ──────────────────────────────────────────────────────────
DEBUG_LLM    = os.getenv("DEBUG_LLM", "false").lower() in ("1", "true", "yes")
DEBUG_COLOUR = os.getenv("DEBUG_COLOUR", "true").lower() in ("1", "true", "yes")

# ── Colores ANSI ───────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"   if DEBUG_COLOUR else ""
    BOLD   = "\033[1m"   if DEBUG_COLOUR else ""
    DIM    = "\033[2m"   if DEBUG_COLOUR else ""
    CYAN   = "\033[96m"  if DEBUG_COLOUR else ""
    YELLOW = "\033[93m"  if DEBUG_COLOUR else ""
    GREEN  = "\033[92m"  if DEBUG_COLOUR else ""
    PURPLE = "\033[95m"  if DEBUG_COLOUR else ""
    RED    = "\033[91m"  if DEBUG_COLOUR else ""
    BLUE   = "\033[94m"  if DEBUG_COLOUR else ""
    GREY   = "\033[90m"  if DEBUG_COLOUR else ""


# ── Helpers de formateo ────────────────────────────────────────────────────
def _box(title: str, content: str, colour: str = C.CYAN, width: int = 90) -> str:
    """Dibuja un cuadro con título y contenido multilínea."""
    bar    = "─" * width
    header = f"{colour}{C.BOLD}┌─ {title} {'─' * max(0, width - len(title) - 4)}┐{C.RESET}"
    body_lines = []
    for raw_line in content.splitlines():
        wrapped = textwrap.wrap(raw_line, width=width - 4) or [""]
        for wl in wrapped:
            body_lines.append(f"{colour}│{C.RESET}  {wl}")
    footer = f"{colour}{C.BOLD}└{bar}┘{C.RESET}"
    return "\n".join([header, *body_lines, footer])


def _truncate(text: str, limit: int = 3000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n{C.GREY}... [{len(text) - limit} caracteres truncados]{C.RESET}"


# ── Función principal ──────────────────────────────────────────────────────
def llm_chat(
    client,
    model: str,
    messages: list,
    node_name: str = "unknown",
    **kwargs
) -> dict:
    """
    Wrapper de ollama.Client.chat() con debug logging.

    Args:
        client    : instancia de ollama.Client
        model     : nombre del modelo (ej. 'llama3.1')
        messages  : lista de mensajes [{role, content}]
        node_name : nombre del nodo LangGraph (para el log)
        **kwargs  : resto de parámetros para client.chat()

    Returns:
        La misma respuesta que retorna ollama.Client.chat()
    """
    if DEBUG_LLM:
        _print_request(node_name, model, messages)

    t0 = time.perf_counter()
    response = client.chat(model=model, messages=messages, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if DEBUG_LLM:
        _print_response(node_name, response, elapsed_ms)

    return response


# ── Impresión de la petición ───────────────────────────────────────────────
def _print_request(node_name: str, model: str, messages: list) -> None:
    sep = f"\n{C.GREY}{'━' * 90}{C.RESET}\n"
    print(sep)
    print(f"{C.PURPLE}{C.BOLD}🤖 LLM CALL  ▸  nodo={node_name}  modelo={model}{C.RESET}")
    print()

    for i, msg in enumerate(messages):
        role    = msg.get("role", "?").upper()
        content = msg.get("content", "")

        if role == "SYSTEM":
            colour  = C.BLUE
            emoji   = "⚙️ "
        elif role == "USER":
            colour  = C.CYAN
            emoji   = "👤"
        else:
            colour  = C.GREY
            emoji   = "💬"

        title = f"{emoji} [{role}]  (mensaje {i+1}/{len(messages)})"
        print(_box(title, _truncate(content), colour=colour))
        print()


# ── Impresión de la respuesta ──────────────────────────────────────────────
def _print_response(node_name: str, response: Any, elapsed_ms: float) -> None:
    raw_content = ""
    try:
        raw_content = response["message"]["content"]
    except (KeyError, TypeError):
        raw_content = str(response)

    # Intentar pretty-print si es JSON
    display_content = raw_content
    try:
        parsed = json.loads(raw_content)
        display_content = json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Tokens (si el modelo los reporta)
    token_info = ""
    try:
        usage = response.get("usage") or {}
        pt = usage.get("prompt_tokens", "?")
        ct = usage.get("completion_tokens", "?")
        token_info = f"  {C.GREY}│  tokens → prompt={pt}  completion={ct}{C.RESET}"
    except Exception:
        pass

    timing_line = (
        f"  {C.GREEN}{C.BOLD}✓ Respuesta recibida{C.RESET}"
        f"  {C.GREY}│  nodo={node_name}  tiempo={elapsed_ms:.0f} ms{C.RESET}"
    )

    print(_box("🟢 RESPUESTA DEL MODELO", _truncate(display_content, 4000), colour=C.GREEN))
    print()
    print(timing_line)
    if token_info:
        print(token_info)
    print(f"\n{C.GREY}{'━' * 90}{C.RESET}\n")
