import os
import re
import asyncio
import threading
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import edge_tts

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = os.path.abspath("outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

file_counter = 0
counter_lock = threading.Lock()

HTML_CODE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Edge-TTS Nam Minh Web App</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 30px; }
    .main-container { display: flex; gap: 25px; max-width: 1100px; margin: 0 auto; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); flex: 1; }
    h2 { margin-top: 0; font-size: 20px; color: #2d3748; }
    label { font-weight: 600; color: #4a5568; display: block; margin-bottom: 8px; font-size: 14px; }
    textarea { width: 100%; height: 280px; padding: 12px; border: 1px solid #cbd5e0; border-radius: 8px; box-sizing: border-box; font-size: 14px; resize: vertical; outline: none; }
    select { width: 100%; padding: 10px; margin-bottom: 20px; border-radius: 8px; border: 1px solid #cbd5e0; outline: none; background: white; }
    .btn { background: #2b6cb0; color: white; border: none; padding: 12px 20px; font-weight: 600; border-radius: 8px; cursor: pointer; width: 100%; }
    .btn:hover { background: #2c5282; }
    audio { width: 100%; margin-top: 15px; }
    .result-box { margin-top: 15px; color: #718096; font-size: 14px; }
  </style>
</head>
<body>
  <div class="main-container">
    <div class="card">
      <h2>Tạo Audio Truyện (Edge-TTS)</h2>
      <label>Nội dung văn bản:</label>
      <textarea id="text" placeholder="Dán nội dung chương truyện vào đây..."></textarea>
      
      <label>Chọn giọng đọc:</label>
      <select id="voice">
        <option value="vi-VN-NamMinhNeural" selected>Nam Minh (Nam - Trầm ấm)</option>
        <option value="vi-VN-HoaiMyNeural">Hoài My (Nữ - Tự nhiên)</option>
      </select>

      <button class="btn" onclick="generateAudio()">Tạo Audio Ngay</button>
    </div>
    
    <div class="card">
      <h2>Kết quả</h2>
      <div id="result" class="result-box">Chưa có file nào được tạo.</div>
    </div>
  </div>

  <script>
    async function generateAudio() {
      const text = document.getElementById('text').value.trim();
      const voice = document.getElementById('voice').value;
      const resBox = document.getElementById('result');
      
      if (!text) { alert('Vui lòng nhập văn bản!'); return; }

      resBox.innerHTML = "⏳ Đang kết nối tạo audio, vui lòng chờ...";
      try {
        const response = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice })
        });
        const data = await response.json();
        if(!response.ok) throw new Error(data.error);

        resBox.innerHTML = `<b>✅ Thành công!</b><audio controls src="${data.url}"></audio>`;
      } catch(e) {
        resBox.innerHTML = `<span style="color: #e53e3e;">❌ Lỗi: ${e.message}</span>`;
      }
    }
  </script>
</body>
</html>
"""

async def amain(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/api/tts', methods=['POST'])
def api_tts():
    global file_counter
    data = request.json or {}
    text = data.get('text', '').strip()
    voice = data.get('voice', 'vi-VN-NamMinhNeural')
    
    if not text:
        return jsonify({'error': 'Thiếu văn bản'}), 400

    with counter_lock:
        file_counter += 1
        filename = f"audio_{file_counter}.mp3"
    
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    try:
        asyncio.run(amain(text, voice, output_path))
        return jsonify({'success': True, 'url': f"/outputs/{filename}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/outputs/<path:filename>')
def outputs(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
