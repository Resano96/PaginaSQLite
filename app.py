import os
import io
import uuid
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from flask import (
    Flask, render_template, request,
    jsonify, send_file, session
)
from flask_session import Session

# ============================================================
# Configuración de Flask y sesiones
# ============================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-secreta")

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(tempfile.gettempdir(), "flask_sessions")
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
Session(app)

# Historial de comandos por sesión
comandos_por_sesion = {}

# ============================================================
# Helpers: obtener ruta de BD y conexión
# ============================================================
def get_db_path():
    """Devuelve la ruta a la base de datos temporal del usuario."""
    if "db_id" not in session:
        session["db_id"] = str(uuid.uuid4())[:8]  # ID único por usuario
    return os.path.join(tempfile.gettempdir(), f"temp_data_{session['db_id']}.db")

def get_conn():
    """Devuelve la conexión SQLite para la base del usuario."""
    return sqlite3.connect(get_db_path(), check_same_thread=False)

# ============================================================
# Rutas principales
# ============================================================
@app.route("/")
def index():
    """Carga la página principal y asegura que el usuario tenga su BD."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        open(db_path, "a").close()
    if session["db_id"] not in comandos_por_sesion:
        comandos_por_sesion[session["db_id"]] = []
    return render_template("index.html")


@app.route("/execute", methods=["POST"])
def execute():
    """Ejecuta un comando SQL y lo guarda en el historial del usuario."""
    data = request.json
    sql = data.get("sql", "").strip()

    # Guardar el comando en el historial
    db_id = session["db_id"]
    comandos_por_sesion.setdefault(db_id, []).append(sql)

    conn = get_conn()
    cursor = conn.cursor()

    try:
        before = after = None

        # INSERT / UPDATE / DELETE → capturar antes y después
        if sql.upper().startswith(("INSERT", "UPDATE", "DELETE")):
            tabla = None
            palabras = sql.split()
            for i, p in enumerate(palabras):
                if p.upper() in ("INTO", "UPDATE", "FROM"):
                    if i + 1 < len(palabras):
                        tabla = palabras[i + 1].replace(";", "")
                        break

            if tabla:
                try:
                    cursor.execute(f"SELECT * FROM {tabla}")
                    before = {"columns": [d[0] for d in cursor.description], "rows": cursor.fetchall()}
                except Exception:
                    before = None

            cursor.execute(sql)
            conn.commit()

            if tabla:
                try:
                    cursor.execute(f"SELECT * FROM {tabla}")
                    after = {"columns": [d[0] for d in cursor.description], "rows": cursor.fetchall()}
                except Exception:
                    after = None

            return jsonify({"success": True, "before": before, "after": after})

        # SELECT → devolver resultados
        elif sql.upper().startswith("SELECT"):
            cursor.execute(sql)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            return jsonify({"success": True, "result": {"columns": cols, "rows": rows}})

        # Otros comandos
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
    """Descarga solo la base de datos del usuario."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return "Base de datos no encontrada", 404

    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return send_file(
        db_path,
        as_attachment=True,
        download_name=f"ejercicio_{fecha}_{session['db_id']}.db"
    )


@app.route("/manual-backup", methods=["POST"])
def manual_backup():
    """Descarga un ZIP con la base de datos y el historial de comandos."""
    db_path = get_db_path()
    db_id = session["db_id"]
    comandos = comandos_por_sesion.get(db_id, [])

    if not os.path.exists(db_path):
        return "Base de datos no encontrada", 404

    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Crear ZIP en memoria
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Incluir base de datos
        zipf.write(db_path, "base_de_datos.db")

        # Incluir comandos
        contenido_sql = "-- Historial de comandos ejecutados\n\n"
        for cmd in comandos:
            contenido_sql += cmd.rstrip(";") + ";\n"
        zipf.writestr("comandos.sql", contenido_sql)

    mem_zip.seek(0)

    return send_file(
        mem_zip,
        as_attachment=True,
        download_name=f"ejercicio_{fecha}_{db_id}.zip",
        mimetype="application/zip"
    )

# ============================================================
# Arranque de la aplicación
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
