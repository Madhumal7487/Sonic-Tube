from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import threading
import re

app = Flask(__name__)

# ඩවුන්ලෝඩ් දත්ත තාවකාලිකව ගබඩා කිරීමට
download_data = {
    "percent": "0%",
    "speed": "0 KB/s",
    "size": "0 MB",
    "status": "idle",
    "title": "",
    "thumb": "",
    "filename": ""
}

# වීඩියෝ තාවකාලිකව ගබඩා වන ෆෝල්ඩරය
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        size_mb = f"{total / (1024 * 1024):.2f} MB" if total > 0 else "Calculating..."
        
        # අකුරු වල පාට කේත (ANSI) ඉවත් කර පිරිසිදු දත්ත ලබාගැනීම
        speed = d.get('_speed_str', '0 KB/s').strip()
        speed = re.sub(r'\x1b\[[0-9;]*m', '', speed)
        
        p_raw = d.get('_percent_str', '0%').strip()
        percent = re.sub(r'\x1b\[[0-9;]*m', '', p_raw)
        
        download_data["percent"] = percent
        download_data["speed"] = speed
        download_data["size"] = size_mb
        download_data["status"] = "downloading"

def start_dl(url):
    global download_data
    ydl_opts = {
        'format': 'best',
        'progress_hooks': [progress_hook],
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # GitHub එකට දමන cookies.txt මෙහිදී සම්බන්ධ වේ
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            download_data["title"] = info.get('title', 'Video')
            download_data["thumb"] = info.get('thumbnail', '')
            download_data["filename"] = f"{info.get('title')}.{info.get('ext')}"
        download_data["status"] = "finished"
        download_data["percent"] = "100%"
    except Exception as e:
        print(f"Error logic: {str(e)}")
        download_data["status"] = "error"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    # කලින් තිබූ දත්ත ඉවත් කිරීම
    download_data.update({
        "percent": "0%", 
        "status": "starting", 
        "title": "Fetching...", 
        "thumb": "",
        "filename": ""
    })
    thread = threading.Thread(target=start_dl, args=(url,))
    thread.start()
    return jsonify({"status": "started"})

@app.route('/progress')
def progress():
    return jsonify(download_data)

# සර්වර් එකේ සිට ඔබේ ඩිවයිස් එකට වීඩියෝ එක ලබාදීම
@app.route('/get-video/<path:filename>')
def save_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    # Render හි Port එක හඳුනාගැනීම
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
