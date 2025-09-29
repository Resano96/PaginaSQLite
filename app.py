import os
import sqlite3
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_session import Session
import uuid

app = Flask(__name__)

# === Configuración de sesiones ===
app.secret_key = os.environ.get("SECRET_KEY", "clave-secreta")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(tempfile.gettempdir(), "flask_sessions")
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
Session(app)

# === Función para obtener ruta de BD por usuario ===
def get_db_path():
    if "db_id" not in session:
        session["db_id"] = str(uuid.uuid4())[:8]  # identificador único
    return os.path.join(tempfile.gettempdir(), f"temp_data_{session['db_id']}.db")

def get_conn():
    return sqlite3.connect(get_db_path(), check_same_thread=False)


@app.route("/")
def index():
    # Si no existe la BD del usuario, crearla vacía
    db_path = get_db_path()
    if not os.path.exists(db_path):
        open(db_path, "a").close()
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
    db_path = get_db_path()
    if os.path.exists(db_path):
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        copia_path = os.path.join(tempfile.gettempdir(), f"ejercicio_{fecha}.db")
        with open(db_path, "rb") as original, open(copia_path, "wb") as copia:
            copia.write(original.read())
        return send_file(copia_path, as_attachment=True)
    else:
        return "Base de datos no encontrada", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)