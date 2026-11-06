import sqlite3
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Ruta de la base de datos
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "GestorDeVeterinariar.db"


def inicializar_bd():
    with sqlite3.connect(DB_PATH) as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS pruebas (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """)


def contar_registros():
    with sqlite3.connect(DB_PATH) as conexion:
        return conexion.execute(
            "SELECT COUNT(*) FROM pruebas"
        ).fetchone()[0]


def guardar_prueba():
    with sqlite3.connect(DB_PATH) as conexion:
        conexion.execute("INSERT INTO pruebas DEFAULT VALUES")

    estado.set(f"Registros guardados: {contar_registros()}")


inicializar_bd()

ventana = tk.Tk()
ventana.title("GestorDeVeterinariar")
ventana.geometry("450x250")

ttk.Label(
    ventana,
    text="Bienvenido a GestorDeVeterinariar",
    font=("Arial", 18, "bold")
).pack(pady=25)

ttk.Label(
    ventana,
    text="Sistema de gestión veterinaria"
).pack(pady=5)

estado = tk.StringVar(
    value=f"Registros guardados: {contar_registros()}"
)

ttk.Label(
    ventana,
    textvariable=estado
).pack(pady=10)

ttk.Button(
    ventana,
    text="Guardar dato de prueba",
    command=guardar_prueba
).pack(pady=10)

ventana.mainloop()