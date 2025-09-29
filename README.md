# 🗄️ Practicando SQLite con Flask

Aplicación web interactiva para **aprender y practicar SQL** usando **Flask** y **SQLite**.  
Incluye un editor de código, botones de ejemplo para crear tablas y relaciones, y opciones para descargar tus ejercicios como bases de datos `.db`.

---

## ✨ Características
- Ejecuta cualquier comando SQL (`CREATE`, `INSERT`, `SELECT`, etc.).
- Genera ejemplos automáticos según la tabla seleccionada.
- Permite **añadir columnas** o **modificar la estructura** de tablas.
- Comparación **antes/después** al insertar, actualizar o borrar datos.
- Botones para crear relaciones **1:1, 1:N y N:M**.
- Descarga tus ejercicios en formato `.db` para guardarlos en tu PC.
- Tema claro/oscuro con recordatorio en localStorage.
- Base de datos **desechable**: se reinicia en cada despliegue y no guarda datos permanentes.

---

## 📂 Estructura del proyecto
    mi_proyecto_sqlite/
    │
    ├── app.py # Backend Flask
    ├── requirements.txt # Dependencias
    ├── Procfile # Instrucción para Render/Heroku
    ├── database/ # Carpeta donde se guardan copias descargadas
    │ ├── auto_backups/
    │ └── manual_backups/
    ├── templates/
    │ └── index.html # Interfaz principal
    └── static/
    ├── css/style.css # Estilos
    └── js/app.js # Lógica de frontend


---

## 🔧 Uso
- Abre la app en tu navegador.
- Usa los botones de la izquierda para generar SQL o selecciona una tabla.
- El SQL se muestra en el editor: pulsa **Ejecutar SQL** para correrlo.
- Cambia entre **Resultado**, **Antes/Después** o **Nada** con el desplegable.
- Descarga tu ejercicio como `.db` para guardarlo o compartirlo.

---

## ⚠️ Nota
Este proyecto está diseñado como **herramienta de aprendizaje**.  
La base de datos es **temporal/desechable** y no debe usarse para datos sensibles ni en producción real.

---

## 📜 Licencia
MIT License – Puedes usar, modificar y compartir este proyecto libremente.