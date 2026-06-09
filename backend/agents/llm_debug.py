"""
LLM Debug Logger — Wrapper around ollama.Client.chat()

Shows in console and accumulates logs in a queue to stream to the frontend terminal.
"""

import os
import time
import textwrap
import json
import queue
from typing import Any

# ── Configuration ──────────────────────────────────────────────────────────
DEBUG_LLM    = os.getenv("DEBUG_LLM", "true").lower() in ("1", "true", "yes")
DEBUG_COLOUR = os.getenv("DEBUG_COLOUR", "true").lower() in ("1", "true", "yes")

# ── Global Thread-Safe Queue for Front-end ──────────────────────────────────
_log_queue = queue.Queue()

def get_new_logs() -> list[str]:
    """Retrieve all accumulated logs and empty the queue."""
    logs = []
    while not _log_queue.empty():
        logs.append(_log_queue.get())
    return logs

def add_to_log(text: str):
    """Add a raw log message to the queue."""
    _log_queue.put(text)

# ── ANSI Colors ───────────────────────────────────────────────────────────
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


# ── Formatting Helpers ────────────────────────────────────────────────────
def _box(title: str, content: str, colour: str = C.CYAN, width: int = 90) -> str:
    """Draws a box with a title and multiline content."""
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
    return text[:limit] + f"\n... [{len(text) - limit} characters truncated]"


# ── Main Wrapper Function ──────────────────────────────────────────────────
def llm_chat(
    client,
    model: str,
    messages: list,
    node_name: str = "unknown",
    **kwargs
) -> dict:
    """
    Wrapper for ollama.Client.chat() with console debug logging and queueing for the frontend.
    """
    # 1. Format and queue the request for the front-end
    req_log_parts = []
    req_log_parts.append(f">>> LLM CALL | Node: {node_name.upper()} | Model: {model}")
    
    for i, msg in enumerate(messages):
        role = msg.get("role", "?").upper()
        content = msg.get("content", "")
        req_log_parts.append(f"--- {role} MESSAGE ({i+1}/{len(messages)}) ---")
        req_log_parts.append(content)
    
    req_log_parts.append("=" * 60)
    add_to_log("\n".join(req_log_parts))

    # Also print to stdout if configured
    if DEBUG_LLM:
        _print_request(node_name, model, messages)

    t0 = time.perf_counter()
    try:
        response = client.chat(model=model, messages=messages, **kwargs)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        
        # 2. Format and queue the response
        res_content = ""
        try:
            res_content = response["message"]["content"]
            # Try to prettify if it's JSON
            try:
                parsed = json.loads(res_content)
                res_content = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                pass
        except Exception:
            res_content = str(response)

        res_log_parts = []
        res_log_parts.append(f"<<< LLM RESPONSE | Node: {node_name.upper()} | Time: {elapsed_ms:.0f} ms")
        res_log_parts.append(res_content)
        res_log_parts.append("=" * 60 + "\n")
        add_to_log("\n".join(res_log_parts))

        if DEBUG_LLM:
            _print_response(node_name, response, elapsed_ms)
            
        return response
    except Exception as e:
        err_log = f"!!! LLM ERROR | Node: {node_name.upper()}\nError: {str(e)}\n" + "=" * 60
        add_to_log(err_log)
        raise e


# ── Console Request Print ───────────────────────────────────────────────
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


# ── Console Response Print ──────────────────────────────────────────────
def _print_response(node_name: str, response: Any, elapsed_ms: float) -> None:
    raw_content = ""
    try:
        raw_content = response["message"]["content"]
    except (KeyError, TypeError):
        raw_content = str(response)

    # Pretty-print JSON
    display_content = raw_content
    try:
        parsed = json.loads(raw_content)
        display_content = json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Tokens info
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
