"""
Business rules for Crypto CTF challenges.
"""
from typing import List


CRYPTO_RULES = [
    {
        "id": "algorithm_specified",
        "field": "algorithm",
        "severity": "error",
        "message": "El algoritmo criptográfico debe estar especificado (RSA, AES, DES, etc.)",
    },
    {
        # MEJORADO: regex anterior disparaba falsos positivos en nombres de campo
        # como "des_key_size" o "sha1_length". Ahora requiere contexto de algoritmo.
        "id": "no_weak_hash",
        "check": "no_pattern",
        "pattern": r"\b(md5|sha1)\b|\bdes\s*[-_]?(encrypt|cipher|hash|algorithm|mode)\b",
        "severity": "error",
        "message": "Uso de algoritmo débil detectado (MD5/SHA1/DES) — son criptográficamente inseguros para firmas e integridad",
        "flags": "IGNORECASE",
    },
    {
        "id": "key_size_minimum",
        "field": "key_size",
        "severity": "warning",
        "message": "El tamaño de clave debe estar especificado (RSA ≥ 2048 bits, AES ≥ 128 bits)",
    },
    {
        "id": "challenge_files_present",
        "field": "challenge_files",
        "severity": "error",
        "message": "Deben listarse los archivos del reto (ciphertext, public key, etc.)",
    },
    {
        "id": "flag_format_correct",
        "check": "no_flag_direct",
        "severity": "error",
        "message": "La flag no debe estar expuesta en la plantilla — solo el formato esperado",
    },
    {
        "id": "docker_image_present",
        "field": "docker_image",
        "severity": "warning",
        "message": "Se recomienda una imagen Docker para retos con scripts de generación",
    },
    {
        "id": "no_private_key_exposed",
        "check": "no_pattern",
        "pattern": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "severity": "error",
        "message": "Clave privada expuesta — esto resuelve el reto automáticamente",
    },
    {
        "id": "solve_script_mentioned",
        "field": "solve_script",
        "severity": "warning",
        "message": "Se recomienda mencionar si existe un solve script de referencia",
    },
]


def get_crypto_rules() -> List[dict]:
    return CRYPTO_RULES
