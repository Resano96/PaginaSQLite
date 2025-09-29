import os
import sqlite3
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

# === Configuración de la base de datos desechable ===
temp_dir = tempfile.gettempdir()
DB_PATH = os.path.join(temp_dir, "temp_data.db")

# Carpetas para descargas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, "database", "auto_backups")
MANUAL_BACKUP_DIR = os.path.join(BASE_DIR, "database", "manual_backups")
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(MANUAL_BACKUP_DIR, exist_ok=True)

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Al iniciar: crear archivo temporal vacío
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
open(DB_PATH, "a").close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    sql = data.get("sql", "")

    conn = get_conn()
    cursor = conn.cursor()
    try:
        before = None
        after = None

        if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            # Detectar tabla
            palabras = sql.strip().split()
            tabla = None
            for i, p in enumerate(palabras):
                if p.upper() in ("INTO", "UPDATE", "FROM"):
                    if i + 1 < len(palabras):
                        tabla = palabras[i + 1].replace(";", "")
                        break

            if tabla:
                try:
                    cursor.execute(f"SELECT * FROM {tabla}")
                    before = {"columns": [d[0] for d in cursor.description], "rows": cursor.fetchall()}
                except:
                    before = None

            cursor.execute(sql)
            conn.commit()

            if tabla:
                try:
                    cursor.execute(f"SELECT * FROM {tabla}")
                    after = {"columns": [d[0] for d in cursor.description], "rows": cursor.fetchall()}
                except:
                    after = None

            return jsonify({"success": True, "before": before, "after": after})

        elif sql.strip().upper().startswith("SELECT"):
            cursor.execute(sql)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            return jsonify({"success": True, "result": {"columns": cols, "rows": rows}})

        else:
            cursor.execute(sql)
            conn.commit()
            return jsonify({"success": True, "result": {"message": "Comando ejecutado"}})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()


@app.route("/download-db")
def download_db():
    if os.path.exists(DB_PATH):
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        copia_path = os.path.join(BACKUP_DIR, f"ejercicio_{fecha}.db")
        with open(DB_PATH, "rb") as original, open(copia_path, "wb") as copia:
            copia.write(original.read())
        return send_file(copia_path, as_attachment=True)
    else:
        return "Base de datos no encontrada", 404


@app.route("/manual-backup", methods=["POST"])
def manual_backup():
    data = request.json
    marca = data.get("marca", "manual")
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre = f"ejercicio_{fecha}_{marca}.db"
    copia_path = os.path.join(MANUAL_BACKUP_DIR, nombre)
    with open(DB_PATH, "rb") as original, open(copia_path, "wb") as copia:
        copia.write(original.read())
    return jsonify({"success": True, "file": os.path.basename(copia_path)})


if __name__ == "__main__":
    # Para Render, el puerto se define con PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)