"""
Business rules for Forensic CTF challenges.
"""
from typing import List


FORENSIC_RULES = [
    {
        "id": "artifact_type_defined",
        "field": "artifact_type",
        "severity": "error",
        "message": "El tipo de artefacto debe estar definido (pcap, image, memory_dump, log, disk)",
    },
    {
        "id": "artifact_file_present",
        "field": "artifact_file",
        "severity": "error",
        "message": "Debe especificarse el archivo artefacto del reto",
    },
    {
        "id": "tools_documented",
        "field": "required_tools",
        "severity": "warning",
        "message": "Se recomienda documentar las herramientas necesarias (Wireshark, Volatility, etc.)",
    },
    {
        "id": "no_flag_in_template",
        "check": "no_flag_direct",
        "severity": "error",
        "message": "La flag no debe estar expuesta en la plantilla — debe estar embebida en el artefacto",
    },
    {
        "id": "artifact_size_reasonable",
        "field": "size",
        "severity": "warning",
        "message": "El tamaño del artefacto debe estar especificado",
    },
    {
        "id": "difficulty_defined",
        "field": "difficulty",
        "severity": "warning",
        "message": "La dificultad del reto debe estar definida",
    },
    {
        "id": "category_tags_present",
        "field": "tags",
        "severity": "warning",
        "message": "Se recomiendan tags para categorizar el reto (steganography, network, memory, etc.)",
    },
    {
        "id": "author_defined",
        "field": "author",
        "severity": "warning",
        "message": "El autor del reto debe estar definido",
    },
]


def get_forensic_rules() -> List[dict]:
    return FORENSIC_RULES
