import os
import sqlite3
from flask import Flask, render_template, request, jsonify
import cloudinary
import cloudinary.uploader

app = Flask(__name__, template_folder=".")

# إعداد Cloudinary باستعمال بياناتك
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL,
            title TEXT NOT NULL,
            file_url TEXT NOT NULL,
            file_type TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    module = request.form.get('module')
    title = request.form.get('title')
    file = request.files.get('file')

    if not file or not module or not title:
        return jsonify({'error': 'جميع الحقول مطلوبة'}), 400

    try:
        # رفع الملف مباشرة إلى Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            resource_type = "auto",
            folder = "sharia_files"
        )
        file_url = upload_result.get('secure_url')
        filename = file.filename.lower()
        file_type = 'PDF' if filename.endswith('.pdf') else 'صورة'

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO lessons (module, title, file_url, file_type) VALUES (?, ?, ?, ?)',
            (module, title, file_url, file_type)
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print("Upload Error:", e)
        return jsonify({'error': 'فشل رفع الملف إلى السحابة'}), 500

@app.route('/api/lessons/<path:module_name>', methods=['GET'])
def get_lessons(module_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, file_url, file_type FROM lessons WHERE module = ? ORDER BY id DESC', (module_name,))
    rows = cursor.fetchall()
    conn.close()

    lessons = []
    for row in rows:
        lessons.append({
            'id': row[0],
            'title': row[1],
            'url': row[2],
            'type': row[3]
        })

    return jsonify(lessons)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
