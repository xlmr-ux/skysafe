from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import os
import sqlite3

app = Flask(__name__)

# Generate encryption key
SECRET_KEY = Fernet.generate_key()
cipher = Fernet(SECRET_KEY)

# File upload directory
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database setup
DATABASE_FILE = 'file_data.db'

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    """Encrypt a file and save the encrypted file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        original_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(original_path)

        # Encrypt file
        with open(original_path, 'rb') as f:
            encrypted_data = cipher.encrypt(f.read())

        encrypted_path = f"{original_path}.enc"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)

        return jsonify({"message": "File encrypted successfully", "path": encrypted_path})
    except Exception as e:
        return jsonify({"error": "Encryption failed", "details": str(e)}), 500

@app.route('/decrypt', methods=['POST'])
def decrypt_file():
    """Decrypt an encrypted file and save the original file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        encrypted_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(encrypted_path)

        # Decrypt file
        try:
            with open(encrypted_path, 'rb') as f:
                decrypted_data = cipher.decrypt(f.read())
        except Exception as e:
            return jsonify({"error": "Decryption failed", "details": str(e)}), 400

        decrypted_path = encrypted_path.replace('.enc', '')
        with open(decrypted_path, 'wb') as f:
            f.write(decrypted_data)

        return jsonify({"message": "File decrypted successfully", "path": decrypted_path})
    except Exception as e:
        return jsonify({"error": "Decryption failed", "details": str(e)}), 500

@app.route('/upload/database', methods=['POST'])
def upload_to_database():
    """Upload a file to the database."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Insert file details into the database
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (filename, file_path) VALUES (?, ?)", (file.filename, file_path))
        conn.commit()
        conn.close()

        return jsonify({"message": f"File uploaded and saved in the database: {file.filename}"})
    except Exception as e:
        return jsonify({"error": "File upload failed", "details": str(e)}), 500

@app.route('/list/files', methods=['GET'])
def list_files():
    """List all files stored in the database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename FROM files")
        files = cursor.fetchall()
        conn.close()

        return jsonify({"files": [{"id": file[0], "filename": file[1]} for file in files]})
    except Exception as e:
        return jsonify({"error": "Failed to fetch file details", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
