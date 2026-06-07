"""
CTF Challenge: SQL Injection Básico
Nivel: Fácil
Categoría: Web

La aplicación simula un panel de login vulnerable a SQL Injection clásico.
El objetivo del participante es bypassear la autenticación y recuperar la
flag almacenada en la base de datos.

La flag se genera dinámicamente en init_db.py y NO se expone en este código.
"""

import sqlite3
import os
from flask import Flask, request, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(32)  # Generada aleatoriamente en cada arranque

DB_PATH = "/app/db/users.db"

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Panel de Administración — Secure Corp</title>
  <style>
    body { background: #1a1a2e; color: #eee; font-family: monospace;
           display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
    .box { background: #16213e; border: 1px solid #0f3460; padding: 2rem; border-radius: 8px; width: 360px; }
    h2 { color: #e94560; margin-bottom: 1.5rem; text-align: center; }
    input { width: 100%; padding: 0.6rem; margin: 0.5rem 0 1rem; background: #0f3460;
            border: 1px solid #e94560; color: #eee; border-radius: 4px; box-sizing: border-box; }
    button { width: 100%; padding: 0.7rem; background: #e94560; border: none;
             color: white; font-weight: bold; border-radius: 4px; cursor: pointer; }
    .error { color: #e94560; font-size: 0.85rem; margin-top: 0.5rem; }
    .info { color: #a8dadc; font-size: 0.8rem; margin-top: 1rem; text-align: center; }
  </style>
</head>
<body>
  <div class="box">
    <h2>🔒 Admin Login</h2>
    <form method="POST">
      <label>Usuario:</label>
      <input name="username" type="text" placeholder="admin" autocomplete="off">
      <label>Contraseña:</label>
      <input name="password" type="password" placeholder="••••••••">
      <button type="submit">Iniciar Sesión</button>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
    </form>
    <p class="info">Secure Corp — Sistema de Gestión Interno v2.1</p>
  </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Dashboard — Secure Corp</title>
  <style>
    body { background: #1a1a2e; color: #eee; font-family: monospace;
           display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
    .box { background: #16213e; border: 2px solid #22c55e; padding: 2rem;
           border-radius: 8px; text-align: center; max-width: 480px; }
    h2 { color: #22c55e; }
    .flag { background: #0f3460; padding: 1rem; border-radius: 6px;
            font-size: 1.1rem; color: #fbbf24; margin-top: 1rem; word-break: break-all; }
    a { color: #a8dadc; font-size: 0.85rem; }
  </style>
</head>
<body>
  <div class="box">
    <h2>✅ Acceso Concedido</h2>
    <p>Bienvenido, <strong>{{ username }}</strong></p>
    <p>Has encontrado la flag secreta:</p>
    <div class="flag">{{ flag }}</div>
    <br>
    <a href="/logout">Cerrar sesión</a>
  </div>
</body>
</html>
"""

def get_db():
    return sqlite3.connect(DB_PATH)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # =====================================================================
        # VULNERABILIDAD INTENCIONAL: SQL Injection sin sanitización
        # Esta query es deliberadamente vulnerable para el reto CTF.
        # En producción NUNCA se debe construir SQL de esta forma.
        # =====================================================================
        query = f"SELECT id, username, flag FROM users WHERE username='{username}' AND password='{password}'"

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            conn.close()

            if row:
                session["user_id"] = row[0]
                session["username"] = row[1]
                session["flag"] = row[2]
                return redirect(url_for("dashboard"))
            else:
                error = "Credenciales incorrectas."
        except Exception as e:
            error = "Error en la base de datos."

    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template_string(
        DASHBOARD_TEMPLATE,
        username=session.get("username"),
        flag=session.get("flag", "???")
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=False)
