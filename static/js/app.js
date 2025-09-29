let tablaSeleccionada = "alumnos"; // por defecto

// ==== Solo poner SQL en el editor ====
function ponerSQL(btn) {
  document.getElementById("editor").value = btn.getAttribute("data-sql");
}

// ==== Selección de tabla activa ====
function seleccionarTabla(nombre) {
  tablaSeleccionada = nombre;
  document.getElementById("tabla-activa").textContent = nombre;
  document.querySelectorAll(".tabla-lista button").forEach(btn => {
    btn.classList.remove("tabla-activa");
    if (btn.textContent === nombre) btn.classList.add("tabla-activa");
  });
}

// ==== Acciones dinámicas sobre la tabla seleccionada ====
function insertarEjemplo() {
  let sql = "";
  switch (tablaSeleccionada) {
    case "alumnos":
      sql = "INSERT INTO alumnos (nombre, edad) VALUES ('Carlos', 25);";
      break;
    case "usuarios":
      sql = "INSERT INTO usuarios (nombre) VALUES ('UsuarioDemo');";
      break;
    case "cursos":
      sql = "INSERT INTO cursos (titulo) VALUES ('Curso Demo');";
      break;
    default:
      sql = `INSERT INTO ${tablaSeleccionada} DEFAULT VALUES;`;
  }
  document.getElementById("editor").value = sql;
}

function modificarEjemplo() {
  let sql = "";
  switch (tablaSeleccionada) {
    case "alumnos":
      sql = "UPDATE alumnos SET edad = 30 WHERE nombre = 'Carlos';";
      break;
    case "usuarios":
      sql = "UPDATE usuarios SET nombre = 'UsuarioEditado' WHERE id = 1;";
      break;
    case "cursos":
      sql = "UPDATE cursos SET titulo = 'Curso Editado' WHERE id = 1;";
      break;
    default:
      sql = `-- No hay ejemplo definido para ${tablaSeleccionada}`;
  }
  document.getElementById("editor").value = sql;
}

function borrarEjemplo() {
  let sql = `DELETE FROM ${tablaSeleccionada} WHERE id = 1;`;
  document.getElementById("editor").value = sql;
}

function consultarEjemplo() {
  let sql = `SELECT * FROM ${tablaSeleccionada};`;
  document.getElementById("editor").value = sql;
}
// ==== Añadir columna a la tabla seleccionada ====
function anadirColumna() {
  const nombreColumna = prompt("Nombre de la nueva columna:", "nueva_columna");
  const tipoColumna = prompt("Tipo de la columna:", "TEXT");

  if (!nombreColumna || !tipoColumna) return;

  const sql = `ALTER TABLE ${tablaSeleccionada} ADD COLUMN ${nombreColumna} ${tipoColumna};`;
  document.getElementById("editor").value = sql;
}

// ==== Modificar columna (simulado) ====
function modificarColumna() {
  alert("⚠️ Atención: SQLite no soporta modificar columnas directamente.\nSe debe recrear la tabla.\nTe generaremos un ejemplo.");

  const sql = `-- Ejemplo para modificar columna en SQLite
-- 1. Renombrar tabla original
ALTER TABLE ${tablaSeleccionada} RENAME TO ${tablaSeleccionada}_old;

-- 2. Crear nueva tabla con la definición deseada
CREATE TABLE ${tablaSeleccionada} (
  id INTEGER PRIMARY KEY,
  -- aquí defines la columna modificada como quieras
);

-- 3. Copiar datos de la tabla antigua a la nueva
INSERT INTO ${tablaSeleccionada} (id)
SELECT id FROM ${tablaSeleccionada}_old;

-- 4. Borrar tabla antigua
DROP TABLE ${tablaSeleccionada}_old;`;

  document.getElementById("editor").value = sql;
}
// ==== Ver tablas y seleccionar ====
function verTablas() {
  fetch("/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql: "SELECT name FROM sqlite_master WHERE type='table';" }),
  })
  .then(res => res.json())
  .then(data => {
    const salida = document.getElementById("output");
    salida.innerHTML = "<h3>Tablas:</h3><div class='tabla-lista'></div>";
    const lista = salida.querySelector(".tabla-lista");

    if (data.result && data.result.rows.length > 0) {
      data.result.rows.forEach(row => {
        const nombre = row[0];
        const btn = document.createElement("button");
        btn.textContent = nombre;
        btn.onclick = () => seleccionarTabla(nombre);
        if (nombre === tablaSeleccionada) btn.classList.add("tabla-activa");
        lista.appendChild(btn);
      });
    } else {
      salida.innerHTML += "<p>No hay tablas creadas.</p>";
    }
  });
}

// ==== Ejecutar SQL ====
function ejecutarSQL() {
  const sql = document.getElementById("editor").value;
  fetch("/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql })
  })
  .then(res => res.json())
  .then(data => mostrarResultado(data));
}

// ==== Mostrar resultados ====
function mostrarResultado(data) {
  const salida = document.getElementById("output");
  const modo = document.getElementById("modo-resultado").value;
  salida.innerHTML = "";

  if (modo === "ninguno") return;

  if (data.success) {
    if (modo === "comparacion" && data.before && data.after) {
      salida.innerHTML += "<h3>Antes:</h3>" + tablaHTML(data.before.columns, data.before.rows);
      salida.innerHTML += "<h3>Después:</h3>" + tablaHTML(data.after.columns, data.after.rows);
    } else if (modo === "resultado") {
      if (data.result?.columns) {
        salida.innerHTML = tablaHTML(data.result.columns, data.result.rows);
      } else if (data.result?.message) {
        salida.innerHTML = "<p>" + data.result.message + "</p>";
      }
    }
  } else {
    salida.innerHTML = "<p style='color:red'>Error: " + data.error + "</p>";
  }
}

function tablaHTML(columns, rows) {
  let html = "<table><tr>";
  columns.forEach(c => html += `<th>${c}</th>`);
  html += "</tr>";
  rows.forEach(r => {
    html += "<tr>";
    r.forEach(v => html += `<td>${v}</td>`);
    html += "</tr>";
  });
  html += "</table>";
  return html;
}

// ==== Borrar todas las tablas ====
function borrarTodas() {
  const sql = `
    SELECT 'DROP TABLE ' || name || ';'
    FROM sqlite_master
    WHERE type='table' AND name NOT LIKE 'sqlite_%';
  `;
  fetch("/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql })
  })
  .then(res => res.json())
  .then(data => {
    if (data.result && data.result.rows) {
      data.result.rows.forEach(r => {
        fetch("/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sql: r[0] })
        });
      });
    }
    alert("Todas las tablas han sido eliminadas.");
  });
}

// ==== Backups ====
function crearBackupManual() {
  const marca = prompt("Introduce una marca para el backup:", "manual");
  if (!marca) return;
  fetch("/manual-backup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ marca })
  })
  .then(res => res.json())
  .then(data => alert("Backup creado: " + data.file));
}
// ==== Descargar ZIP con BD + comandos ====
function descargarZIP() {
  fetch("/manual-backup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  })
  .then(response => {
    if (!response.ok) throw new Error("Error al crear el ZIP");
    return response.blob();
  })
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ejercicio.zip";
    document.body.appendChild(a);
    a.click();
    a.remove();
  })
  .catch(err => alert("Error: " + err));
}
function insertCode(sql) {
  navigator.clipboard.writeText(sql).then(() => {
    alert("Comando copiado al portapapeles. Vuelve al editor y pégalo.");
  });
}


// ==== Tema oscuro ====
function toggleDarkMode() {
  document.body.classList.toggle("dark");
  if (document.body.classList.contains("dark")) {
    localStorage.setItem("tema", "oscuro");
  } else {
    localStorage.setItem("tema", "claro");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const temaGuardado = localStorage.getItem("tema");
  if (temaGuardado === "oscuro") {
    document.body.classList.add("dark");
  }
});
