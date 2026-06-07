# CTF Challenge: SQL Injection Básico

**Autor**: SecureLab CTF Team  
**Dificultad**: Fácil  
**Categoría**: Web — SQL Injection  
**Puntos**: 100

## Descripción

El equipo de seguridad de Secure Corp ha detectado que su panel de administración interno tiene una vulnerabilidad crítica. Tu misión es demostrar que el panel puede ser comprometido y recuperar la flag del sistema.

La aplicación usa una base de datos SQLite y un endpoint `/login` que procesa credenciales de forma insegura.

## Objetivo

Bypasear el sistema de autenticación del panel de administración y recuperar la flag almacenada en la base de datos.

## Entorno

- **URL**: `http://localhost:8090`  
- **Endpoint de ataque**: `POST /login`  
- **Stack**: Flask + SQLite  
- **Docker**: `docker compose up -d`  

## Archivos Entregados

- `Dockerfile` — imagen del entorno
- `docker-compose.yml` — orquestación del contenedor
- `requirements.txt` — dependencias Python

## Reglas

- La flag tiene el formato `CTF{...}`
- NO se permiten ataques al sistema anfitrión fuera del contenedor
- El reto es completamente autocontenido en Docker
