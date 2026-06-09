"""
Classifier Node — uses Ollama SDK (no LangChain) to classify the CTF challenge type.
Outputs: challenge_type (web | crypto | forensic | unknown)
"""
import json
import os
import ollama
from agents.state import CTFReviewState, AgentStep

OLLAMA_HOST  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """You are a cybersecurity expert specialized in CTF (Capture The Flag) challenges.
Your task is to classify a CTF challenge template/description into one of these categories:
- web: Web application vulnerabilities (SQL injection, XSS, SSRF, path traversal, etc.)
- crypto: Cryptographic challenges (cipher breaking, RSA, hash cracking, etc.)
- forensic: Digital forensics (file analysis, steganography, memory dumps, pcap analysis, etc.)
- unknown: Cannot determine the category

You MUST respond ONLY with a valid JSON object (no markdown, no explanation outside JSON):
{
  "type": "web" | "crypto" | "forensic" | "unknown",
  "confidence": <float 0.0-1.0>,
  "reason": "<brief explanation in Spanish>",
  "key_indicators": ["indicator1", "indicator2"]
}"""


def classifier_node(state: CTFReviewState) -> CTFReviewState:
    """Classifies the CTF challenge type using Ollama SDK directly."""
    steps = list(state.get("steps", []))
    steps.append(AgentStep(
        node="classifier",
        status="running",
        label="🏷️ Clasificando tipo de reto CTF...",
        result=None
    ))

    content = state.get("file_content", "")
    if not content or state.get("error"):
        steps[-1] = AgentStep(
            node="classifier",
            status="error",
            label="🏷️ No hay contenido para clasificar",
            result=None
        )
        return {**state, "steps": steps, "challenge_type": "unknown"}

    # Truncate to avoid context limits
    preview = content[:4000] if len(content) > 4000 else content

    try:
        from agents.llm_debug import llm_chat
        client = ollama.Client(host=OLLAMA_HOST)
        response = llm_chat(
            client,
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Classify this CTF challenge:\n\n{preview}"},
            ],
            node_name="classifier",
            format="json",
            options={"temperature": 0},
        )

        result = json.loads(response["message"]["content"])

        challenge_type = result.get("type", "unknown")
        confidence     = float(result.get("confidence", 0.0))
        reason         = result.get("reason", "")

        steps[-1] = AgentStep(
            node="classifier",
            status="completed",
            label=f"🏷️ Clasificado como: {challenge_type.upper()} (confianza: {int(confidence * 100)}%)",
            result=result
        )

        return {
            **state,
            "challenge_type":             challenge_type,
            "classification_confidence":  confidence,
            "classification_reason":      reason,
            "steps":                      steps,
        }

    except Exception as e:
        steps[-1] = AgentStep(
            node="classifier",
            status="error",
            label=f"🏷️ Error en clasificación: {str(e)}",
            result=None
        )
        return {
            **state,
            "steps":          steps,
            "challenge_type": "unknown",
            "error":          str(e),
        }


def route_by_type(state: CTFReviewState) -> str:
    """Router function — returns the next node name based on challenge type."""
    route_map = {
        "web":      "web_agent",
        "crypto":   "crypto_agent",
        "forensic": "forensic_agent",
    }
    return route_map.get(state.get("challenge_type", "unknown"), "verdict")
