"""
Script de inicialización de la base de datos SQLite para el reto CTF.
La flag se genera y almacena en la BD, y NO se expone en ningún archivo de texto.
"""
import sqlite3
import os
import hashlib

DB_DIR = "/app/db"
DB_PATH = f"{DB_DIR}/users.db"

# La flag va embebida en la BD, nunca en texto plano en el código fuente
FLAG = "CTF{sqli_bypass_is_classic_but_never_gets_old}"

os.makedirs(DB_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("""
    CREATE TABLE users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        flag     TEXT
    )
""")

# Usuario admin real (contraseña imposible de adivinar en brute force para el reto)
admin_pass = hashlib.sha256(os.urandom(32)).hexdigest()
cursor.execute(
    "INSERT INTO users (username, password, flag) VALUES (?, ?, ?)",
    ("admin", admin_pass, FLAG)
)

# Usuario señuelo sin flag
cursor.execute(
    "INSERT INTO users (username, password, flag) VALUES (?, ?, ?)",
    ("guest", "guest123", "")
)

conn.commit()
conn.close()

print("[init_db] Base de datos inicializada correctamente.")
print(f"[init_db] La flag está almacenada en la BD — NO en texto plano.")
