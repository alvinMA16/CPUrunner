from flask import Flask, request, render_template, session, jsonify
from openai import OpenAI
import pandas as pd
import os
from dotenv import load_dotenv
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

load_dotenv()  # 加载 .env 文件

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 设置一个安全的密钥

UPLOAD_FOLDER = 'uploads'  # 创建上传文件夹
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # 保存文件到临时目录
        file_path = os.path.join(UPLOAD_FOLDER, f"{session.get('_id', os.urandom(16).hex())}.xlsx")
        file.save(file_path)
        
        # 只在 session 中存储文件路径
        session['file_path'] = file_path
        
        return jsonify({'message': 'File uploaded successfully'}), 200
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Error processing file'}), 500

@app.route('/process')
def process():
    file_path = session.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return "No file found", 404
        
    # 读取文件时再处理数据
    df = pd.read_excel(file_path)
    headers = df.columns.tolist()
    file_contents = df.values.tolist()
    
    return render_template('process.html', headers=headers, file_contents=file_contents)

# 添加清理函数
def cleanup_old_files():
    """清理超过24小时的临时文件"""
    current_time = time.time()
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # 如果文件超过24小时
        if os.path.getmtime(file_path) < current_time - 86400:  # 86400 秒 = 24 小时
            os.remove(file_path)

# 在应用启动时添加定时清理任务
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_files, trigger="interval", hours=24)
scheduler.start()

# 在应用退出时停止调度器
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_response():
    try:
        data = request.json
        model_name = data['model_name']

        if model_name == "openai/gpt-4o-2024-11-20":
            # Initialize OpenAI client
            openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv('OPENROUTER_API_KEY')
            )
            # OpenRouter API 调用方式
            messages = [
                {
                    "role": "system",
                    "content": f"Goal: {data['goal']}"
                }
            ]

            user_content = []
            user_content.append({
                "type": "text",
                "text": data['prompt']
            })
            
            if data.get('image'):
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data['image']
                    }
                })

            messages.append({
                "role": "user",
                "content": user_content
            })
            
            completion = openrouter_client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": request.headers.get('Referer', ''),
                    "X-Title": "AI Test Runner",
                },
                model=model_name,
                messages=messages
            )
            response_content = completion.choices[0].message.content
            
        elif model_name == "claude-3.5-sonnet":
            # 使用 Anthropic API 客户端
            anthropic_client = OpenAI(
                base_url="https://api.anthropic.com/v1",
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
            
            messages = [
                {
                    "role": "system",
                    "content": f"Goal: {data['goal']}"
                },
                {
                    "role": "user",
                    "content": data['prompt']
                }
            ]
            
            completion = anthropic_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=4096
            )
            response_content = completion.choices[0].message.content
            
        else:
            return jsonify({'error': 'Unsupported model'}), 400

        return jsonify({
            'response': response_content
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
