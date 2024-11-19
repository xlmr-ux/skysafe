from flask import Flask, request, jsonify, send_file
from cryptography.fernet import Fernet
import sqlite3
import os
import io

app = Flask(__name__)

# Encryption/Decryption setup
SECRET_KEY = Fernet.generate_key()
cipher = Fernet(SECRET_KEY)

# Database setup
DB_FILE = 'file_storage.db'

def init_db():
    """Initialize the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

init_db()

# Routes

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    """Encrypt a file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_data = file.read()
    encrypted_data = cipher.encrypt(file_data)

    encrypted_filename = f"{file.filename}.enc"
    return send_file(io.BytesIO(encrypted_data),
                     as_attachment=True,
                     download_name=encrypted_filename,
                     mimetype="application/octet-stream")

@app.route('/decrypt', methods=['POST'])
def decrypt_file():
    """Decrypt a file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_data = file.read()
    decrypted_data = cipher.decrypt(file_data)

    original_filename = file.filename.replace('.enc', '')
    return send_file(io.BytesIO(decrypted_data),
                     as_attachment=True,
                     download_name=original_filename,
                     mimetype="application/octet-stream")

@app.route('/upload/database', methods=['POST'])
def upload_to_database():
    """Upload a file to the database."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_data = file.read()

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO files (file_name, file_data) VALUES (?, ?)', 
                       (file.filename, file_data))
        conn.commit()

    return jsonify({"message": f"File '{file.filename}' uploaded to the database successfully."})

@app.route('/download/database/<int:file_id>', methods=['GET'])
def download_from_database(file_id):
    """Download a file from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_name, file_data FROM files WHERE id = ?', (file_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "File not found"}), 404

        file_name, file_data = result
        return send_file(io.BytesIO(file_data),
                         as_attachment=True,
                         download_name=file_name,
                         mimetype="application/octet-stream")

@app.route('/list/files', methods=['GET'])
def list_files():
    """List all files in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, file_name, upload_date FROM files')
        files = cursor.fetchall()

    return jsonify({"files": [{"id": f[0], "file_name": f[1], "upload_date": f[2]} for f in files]})

if __name__ == '__main__':
    app.run(debug=True)
