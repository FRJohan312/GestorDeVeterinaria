"""Generación y verificación de hashes PBKDF2-HMAC-SHA256."""

import hashlib
import hmac
import secrets


ITERACIONES_PBKDF2 = 600_000


def generar_hash_contrasena(contrasena: str) -> str:
    """Devuelve algoritmo, costo, sal aleatoria y hash, sin guardar texto plano."""
    if not isinstance(contrasena, str) or not contrasena.strip():
        raise ValueError("La contraseña debe ser un texto no vacío")
    sal = secrets.token_bytes(16)
    resumen = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode("utf-8"), sal, ITERACIONES_PBKDF2
    )
    return f"pbkdf2_sha256${ITERACIONES_PBKDF2}${sal.hex()}${resumen.hex()}"


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    """Rechaza formatos dañados y compara el resumen en tiempo constante."""
    if not isinstance(contrasena, str) or not isinstance(hash_guardado, str):
        return False
    try:
        algoritmo, costo, sal_hex, resumen_hex = hash_guardado.split("$")
        if algoritmo != "pbkdf2_sha256" or not costo.isascii() or not costo.isdecimal():
            return False
        # Acota el trabajo frente a un costo corrupto o desmesurado en SQLite.
        if len(costo) > 7 or not 1 <= int(costo) <= 2_000_000:
            return False
        if len(sal_hex) != 32 or len(resumen_hex) != 64:
            return False
        sal = bytes.fromhex(sal_hex)
        esperado = bytes.fromhex(resumen_hex)
        if len(sal) != 16 or len(esperado) != 32:
            return False
        calculado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, int(costo))
        return hmac.compare_digest(calculado, esperado)
    except (ValueError, UnicodeError):
        return False
