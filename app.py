from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import threading

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# සරලව දත්ත තබා ගැනීමට
status_msg = {"msg": "Ready", "link": None}

def start_dl(url):
    global status_msg
    ydl_opts = {
        # Render එකේ හිර නොවී ඉක්මනින් වැඩ කිරීමට හොඳම සරල format එක
        'format': 'best[ext=mp4]/best', 
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',
        'noplaylist': True,
        'restrictfilenames': True,
    }
    try:
        status_msg["msg"] = "Downloading... please wait."
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = os.path.basename(ydl.prepare_filename(info))
            status_msg["msg"] = "Finished!"
            status_msg["link"] = filename
    except Exception as e:
        status_msg["msg"] = f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    status_msg["msg"] = "Starting..."
    status_msg["link"] = None
    thread = threading.Thread(target=start_dl, args=(url,))
    thread.start()
    return jsonify({"status": "started"})

@app.route('/progress')
def progress():
    return jsonify(status_msg)

@app.route('/get-video/<path:filename>')
def save_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
