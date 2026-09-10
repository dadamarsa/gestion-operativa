#!/usr/bin/env python3
"""
Servidor simple para la app de recopilación de datos
Uso: python3 server.py
Accede a: http://localhost:8000
"""

import http.server
import socketserver
import os
import json
import sqlite3
import base64
import re
from pathlib import Path

PORT = int(os.environ.get('PORT', 8000))
DIRECTORY = Path(__file__).parent
DATA_DIRECTORY = DIRECTORY / 'datos'
DATABASE = DATA_DIRECTORY / 'gestion_operativa.db'
IMAGES_DIRECTORY = DATA_DIRECTORY / 'imagenes'
PDF_DIRECTORY = DATA_DIRECTORY / 'documentos-pdf'
BACKUP_DIRECTORY = DATA_DIRECTORY / 'copias-seguridad'
DATA_DIRECTORY.mkdir(exist_ok=True)
IMAGES_DIRECTORY.mkdir(exist_ok=True)
PDF_DIRECTORY.mkdir(exist_ok=True)
BACKUP_DIRECTORY.mkdir(exist_ok=True)


def migrar_archivos_a_carpetas():
    """Mueve imágenes y PDFs sueltos (versiones antiguas) a su carpeta por página."""
    for archivo in IMAGES_DIRECTORY.iterdir():
        if archivo.is_file() and not archivo.name.startswith('.') and '_' in archivo.stem:
            tipo = archivo.stem.split('_', 1)[0]
            carpeta = IMAGES_DIRECTORY / tipo
            carpeta.mkdir(exist_ok=True)
            archivo.rename(carpeta / archivo.name)
    for archivo in PDF_DIRECTORY.iterdir():
        if archivo.is_file() and not archivo.name.startswith('.'):
            carpeta = PDF_DIRECTORY / 'partes'
            carpeta.mkdir(exist_ok=True)
            archivo.rename(carpeta / archivo.name)


def init_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS users (
                identifier TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        # Registro permanente: nunca se borra, ni cuando se elimina el registro operativo correspondiente.
        # Es la fuente de datos del libro de Excel para permitir el análisis histórico.
        connection.execute('''
            CREATE TABLE IF NOT EXISTS historial_registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL DEFAULT -1
            )
        ''')
        connection.execute('''
            INSERT OR IGNORE INTO users
            (identifier, name, position, password, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', ('admin', 'Administrador', 'Administración', 'admin123', 'Administrativo', 1))
        connection.execute('''
            INSERT OR IGNORE INTO users
            (identifier, name, position, password, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', ('conductor', 'Conductor', 'Conductor', 'cond123', 'Conductor', 1))


def json_response(handler, status, payload):
    content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(content)))
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(content)


def read_json_body(handler):
    content_length = int(handler.headers.get('Content-Length', '0'))
    if content_length > 25 * 1024 * 1024:
        raise ValueError('Payload demasiado grande')
    return json.loads(handler.rfile.read(content_length).decode('utf-8'))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def do_POST(self):
        if self.path == '/api/login':
            try:
                body = read_json_body(self)
                with sqlite3.connect(DATABASE) as connection:
                    user = connection.execute(
                        'SELECT identifier, name, position, role, active FROM users WHERE identifier = ? AND password = ?',
                        (body.get('identifier', '').strip().lower(), body.get('password', ''))
                    ).fetchone()
                if not user:
                    json_response(self, 401, {'error': 'Credenciales incorrectas'})
                elif not user[4]:
                    json_response(self, 403, {'error': 'Cuenta pendiente de autorización'})
                else:
                    json_response(self, 200, {'identifier': user[0], 'name': user[1], 'position': user[2], 'role': user[3]})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/register':
            try:
                body = read_json_body(self)
                identifier = body.get('identifier', '').strip().lower()
                name = body.get('name', '').strip()
                position = body.get('position', '').strip()
                password = body.get('password', '')
                if not identifier or not name or not position or len(password) < 6:
                    json_response(self, 400, {'error': 'Faltan datos obligatorios'})
                    return
                with sqlite3.connect(DATABASE) as connection:
                    connection.execute(
                        'INSERT INTO users (identifier, name, position, password, role, active, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime(\'now\'))',
                        (identifier, name, position, password, 'Conductor', 0)
                    )
                json_response(self, 201, {'message': 'Solicitud registrada'})
            except sqlite3.IntegrityError:
                json_response(self, 409, {'error': 'La cuenta ya existe'})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/records':
            try:
                body = read_json_body(self)
                record_type = body.get('record_type', '').strip()
                data = body.get('data')
                if not record_type or not isinstance(data, dict):
                    json_response(self, 400, {'error': 'Registro no válido'})
                    return
                with sqlite3.connect(DATABASE) as connection:
                    cursor = connection.execute(
                        'INSERT INTO records (record_type, data, created_at) VALUES (?, ?, datetime(\'now\'))',
                        (record_type, json.dumps(data, ensure_ascii=False))
                    )
                    connection.execute(
                        'INSERT INTO historial_registros (record_type, data, created_at) VALUES (?, ?, datetime(\'now\'))',
                        (record_type, json.dumps(data, ensure_ascii=False))
                    )
                    foto = data.get('foto', '')
                    if isinstance(foto, str) and foto.startswith('data:image/'):
                        cabecera, contenido = foto.split(',', 1)
                        extension = 'png' if 'png' in cabecera else 'jpg'
                        carpeta_tipo = IMAGES_DIRECTORY / record_type
                        carpeta_tipo.mkdir(exist_ok=True)
                        ruta_foto = carpeta_tipo / f'{record_type}_{cursor.lastrowid}.{extension}'
                        ruta_foto.write_bytes(base64.b64decode(contenido))
                json_response(self, 201, {'id': cursor.lastrowid})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/partes/numero':
            try:
                with sqlite3.connect(DATABASE) as connection:
                    connection.execute('BEGIN IMMEDIATE')
                    current = connection.execute(
                        'SELECT value FROM counters WHERE name = ?', ('partes',)
                    ).fetchone()
                    numero = (current[0] + 1) if current else 0
                    connection.execute(
                        'INSERT INTO counters (name, value) VALUES (?, ?) '
                        'ON CONFLICT(name) DO UPDATE SET value = excluded.value',
                        ('partes', numero)
                    )
                json_response(self, 200, {'numero': numero})
            except sqlite3.Error:
                json_response(self, 500, {'error': 'No se pudo reservar el número del parte'})
            return

        if self.path == '/api/partes/pdf':
            try:
                body = read_json_body(self)
                nombre = body.get('filename', '')
                contenido = body.get('pdf', '')
                if not isinstance(nombre, str) or not re.fullmatch(r'parte_\d{4,}\.pdf', nombre):
                    json_response(self, 400, {'error': 'Nombre de PDF no válido'})
                    return
                if not isinstance(contenido, str) or ',' not in contenido:
                    json_response(self, 400, {'error': 'PDF no válido'})
                    return
                _, base64_pdf = contenido.split(',', 1)
                datos_pdf = base64.b64decode(base64_pdf, validate=True)
                if len(datos_pdf) > 10 * 1024 * 1024:
                    json_response(self, 413, {'error': 'El PDF es demasiado grande'})
                    return
                carpeta_partes = PDF_DIRECTORY / 'partes'
                carpeta_partes.mkdir(exist_ok=True)
                ruta_pdf = carpeta_partes / nombre
                ruta_pdf.write_bytes(datos_pdf)
                json_response(self, 201, {'filename': nombre, 'path': str(ruta_pdf.relative_to(DIRECTORY))})
            except (ValueError, json.JSONDecodeError, OSError):
                json_response(self, 400, {'error': 'No se pudo guardar el PDF'})
            return

        if self.path == '/api/users/status':
            try:
                body = read_json_body(self)
                identifier = body.get('identifier', '').strip().lower()
                active = bool(body.get('active'))
                with sqlite3.connect(DATABASE) as connection:
                    cursor = connection.execute('UPDATE users SET active = ? WHERE identifier = ?', (int(active), identifier))
                    if cursor.rowcount == 0 and body.get('name') and body.get('password'):
                        connection.execute(
                            'INSERT INTO users (identifier, name, position, password, role, active, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime(\'now\'))',
                            (identifier, body['name'], body.get('position', 'Conductor'), body['password'], body.get('role', 'Conductor'), int(active))
                        )
                        cursor = type('Result', (), {'rowcount': 1})()
                if cursor.rowcount == 0:
                    json_response(self, 404, {'error': 'Usuario no encontrado'})
                else:
                    json_response(self, 200, {'message': 'Estado actualizado'})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/users/role':
            try:
                body = read_json_body(self)
                identifier = body.get('identifier', '').strip().lower()
                role = body.get('role', '').strip()
                if role not in ('Administrativo', 'Conductor') or identifier == 'admin':
                    json_response(self, 400, {'error': 'Rol no permitido para este usuario'})
                    return
                with sqlite3.connect(DATABASE) as connection:
                    cursor = connection.execute('UPDATE users SET role = ? WHERE identifier = ?', (role, identifier))
                if cursor.rowcount == 0:
                    json_response(self, 404, {'error': 'Usuario no encontrado'})
                else:
                    json_response(self, 200, {'message': 'Rol actualizado'})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/users/delete':
            try:
                body = read_json_body(self)
                identifier = body.get('identifier', '').strip().lower()
                if identifier == 'admin':
                    json_response(self, 400, {'error': 'La cuenta principal no se puede eliminar'})
                    return
                with sqlite3.connect(DATABASE) as connection:
                    cursor = connection.execute('DELETE FROM users WHERE identifier = ?', (identifier,))
                if cursor.rowcount == 0:
                    json_response(self, 404, {'error': 'Usuario no encontrado'})
                else:
                    json_response(self, 200, {'message': 'Usuario eliminado'})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/users/password':
            try:
                body = read_json_body(self)
                identifier = body.get('identifier', '').strip().lower()
                current_password = body.get('currentPassword', '')
                password = body.get('password', '')
                if len(password) < 6:
                    json_response(self, 400, {'error': 'La contraseña debe tener al menos 6 caracteres'})
                    return
                with sqlite3.connect(DATABASE) as connection:
                    user = connection.execute('SELECT password FROM users WHERE identifier = ?', (identifier,)).fetchone()
                    if not user or user[0] != current_password:
                        json_response(self, 403, {'error': 'La contraseña actual no es correcta'})
                        return
                    cursor = connection.execute('UPDATE users SET password = ? WHERE identifier = ?', (password, identifier))
                if cursor.rowcount == 0:
                    json_response(self, 404, {'error': 'Usuario no encontrado'})
                else:
                    json_response(self, 200, {'message': 'Contraseña actualizada'})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path == '/api/vehicles/delete':
            try:
                body = read_json_body(self)
                matricula = body.get('matricula', '').strip().upper()
                with sqlite3.connect(DATABASE) as connection:
                    cursor = connection.execute(
                        "DELETE FROM records WHERE record_type = 'vehiculos' AND json_extract(data, '$.matricula') = ?",
                        (matricula,)
                    )
                if cursor.rowcount == 0:
                    json_response(self, 404, {'error': 'Vehículo no encontrado'})
                else:
                    json_response(self, 200, {'message': 'Vehículo eliminado'})
            except (ValueError, json.JSONDecodeError):
                json_response(self, 400, {'error': 'Solicitud no válida'})
            return

        if self.path != "/api/gestion-operativa.xlsx":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            if content_length > 25 * 1024 * 1024:
                self.send_error(413, 'Archivo demasiado grande')
                return

            contenido = self.rfile.read(content_length)
            (DATA_DIRECTORY / 'data.xlsx').write_bytes(contenido)
            self.send_response(204)
            self.end_headers()
        except (ValueError, OSError):
            self.send_error(500, 'No se pudo guardar el Excel')

    def do_GET(self):
        if self.path == '/api/users':
            with sqlite3.connect(DATABASE) as connection:
                users = connection.execute(
                    'SELECT identifier, name, position, role, active, created_at FROM users ORDER BY name'
                ).fetchall()
            json_response(self, 200, [
                {'identifier': row[0], 'name': row[1], 'position': row[2], 'role': row[3], 'active': bool(row[4]), 'created_at': row[5]}
                for row in users
            ])
            return

        if self.path == '/api/records':
            with sqlite3.connect(DATABASE) as connection:
                records = connection.execute(
                    'SELECT id, record_type, data, created_at FROM records ORDER BY id'
                ).fetchall()
            json_response(self, 200, [
                {'id': row[0], 'record_type': row[1], 'data': json.loads(row[2]), 'created_at': row[3]}
                for row in records
            ])
            return

        if self.path == '/api/historial':
            # Historial permanente para el libro de Excel: no se ve afectado por borrados operativos.
            with sqlite3.connect(DATABASE) as connection:
                records = connection.execute(
                    'SELECT id, record_type, data, created_at FROM historial_registros ORDER BY id'
                ).fetchall()
            json_response(self, 200, [
                {'id': row[0], 'record_type': row[1], 'data': json.loads(row[2]), 'created_at': row[3]}
                for row in records
            ])
            return

        super().do_GET()
    
    def log_message(self, format, *args):
        """Log messages in a cleaner format"""
        print(f"[{self.log_date_time_string()}] {format % args}")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Atiende cada conexión en un hilo aparte para que un cliente lento (móvil, otra pestaña...)
    # no bloquee al resto de peticiones, como pasaba con TCPServer de un solo hilo.
    daemon_threads = True
    allow_reuse_address = True

def run_server():
    try:
        with ThreadingHTTPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"🚀 Servidor ejecutándose en: http://localhost:{PORT}")
            print(f"📁 Sirviendo archivos desde: {DIRECTORY}")
            print(f"🌐 Abre tu navegador y accede a http://localhost:{PORT}")
            print(f"\n⏹️  Presiona Ctrl+C para detener el servidor\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✋ Servidor detenido.")
    except OSError as e:
        print(f"❌ Error: {e}")
        print(f"Asegúrate de que el puerto {PORT} no esté en uso.")

if __name__ == "__main__":
    init_database()
    migrar_archivos_a_carpetas()
    run_server()
