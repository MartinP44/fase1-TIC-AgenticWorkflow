"""
Business rules for Web CTF challenges.
"""
from typing import List
from agents.state import Finding


WEB_RULES = [
    {
        "id": "url_present",
        "field": "url",
        "severity": "error",
        "message": "Debe incluir una URL o endpoint base del reto",
    },
    {
        "id": "port_defined",
        "field": "port",
        "severity": "warning",
        "message": "El puerto del servicio debe estar definido",
    },
    {
        "id": "http_method_valid",
        "field": "http_method",
        "severity": "warning",
        "message": "El método HTTP debe ser uno de: GET, POST, PUT, DELETE, PATCH",
        "allowed_values": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    },
    {
        # Presente en el diagrama del usuario
        "id": "endpoint_documented",
        "field": "endpoint",
        "severity": "warning",
        "message": "El endpoint del reto debe documentarse (ej: /login, /upload, /api/v1/flag)",
    },
    {
        "id": "docker_image_present",
        "field": "docker_image",
        "severity": "error",
        "message": "Se requiere una imagen Docker para reproducir el entorno",
    },
    {
        "id": "docker_no_latest_tag",
        "field": "docker_image",
        "severity": "warning",
        "message": "La imagen Docker no debe usar el tag ':latest', usa un tag específico (ej: myimage:v1.2)",
        "check": "no_latest",
    },
    {
        "id": "technology_stack_present",
        "field": "technology_stack",
        "severity": "warning",
        "message": "El stack tecnológico debe estar especificado (Flask, Django, Node.js, etc.)",
    },
    {
        "id": "authentication_required_defined",
        "field": "authentication_required",
        "severity": "warning",
        "message": "Debe indicarse si el reto requiere autenticación (true/false)",
    },
    {
        # Presente en el diagrama del usuario
        "id": "session_type_defined",
        "field": "session_type",
        "severity": "warning",
        "message": "El tipo de sesión debe definirse (cookie, jwt, stateless, none)",
        "allowed_values": ["COOKIE", "JWT", "STATELESS", "NONE", "SESSION", "TOKEN", "OAUTH"],
    },
    {
        "id": "size_defined",
        "field": "size",
        "severity": "warning",
        "message": "El tamaño del contenedor debe estar definido",
    },
    {
        "id": "ram_defined",
        "field": "ram",
        "severity": "warning",
        "message": "La RAM asignada al contenedor debe estar definida",
    },
]

INSECURE_PATTERNS = [
    {
        # Mejorado: detecta password, passwd, secret, api_key, apikey, token hardcodeados
        "id": "no_hardcoded_passwords",
        "check": "no_pattern",
        "pattern": r"(password|passwd|secret|api_key|apikey|token|auth_token)\s*[:=]\s*['\"][^'\"]{3,}['\"]" ,
        "severity": "error",
        "message": "Se detectaron credenciales hardcodeadas en la plantilla (password/secret/api_key/token)",
    },
    {
        "id": "no_private_keys",
        "check": "no_pattern",
        "pattern": r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        "severity": "error",
        "message": "Se detectó una clave privada expuesta en la plantilla",
    },
    {
        "id": "no_flag_exposure",
        "check": "no_pattern",
        "pattern": r"CTF\{[^}]+\}",
        "severity": "error",
        "message": "La flag NO debe estar expuesta directamente en la plantilla",
    },
    {
        # Detecta credenciales en formato URL (http://user:pass@host)
        "id": "no_credentials_in_url",
        "check": "no_pattern",
        "pattern": r"https?://[\w.%+-]+:[^@/\s]+@",
        "severity": "error",
        "message": "Se detectaron credenciales embebidas en una URL (http://user:pass@host)",
    },
]


def get_web_rules() -> List[dict]:
    return WEB_RULES


def get_insecure_patterns() -> List[dict]:
    return INSECURE_PATTERNS
