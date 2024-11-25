from flask import Flask, request, render_template, session, jsonify
from openai import OpenAI
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 设置一个安全的密钥

# Initialize OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY')
)

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
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 获取表头和数据内容
        headers = df.columns.tolist()
        file_contents = df.values.tolist()
        
        # 将表头和数据内容都存储在session中
        session['headers'] = headers
        session['file_contents'] = file_contents
        
        return jsonify({'message': 'File uploaded successfully'}), 200
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Error processing file'}), 500

@app.route('/process')
def process():
    headers = session.get('headers', [])
    file_contents = session.get('file_contents', [])
    return render_template('process.html', headers=headers, file_contents=file_contents)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_response():
    try:
        data = request.json
        messages = [
            {
                "role": "system",
                "content": f"Goal: {data['goal']}"
            }
        ]

        # 构建用户消息内容
        user_content = []
        
        # 添加文本提示
        user_content.append({
            "type": "text",
            "text": data['prompt']
        })
        
        # 如果存在图片数据，添加图片URL
        if data.get('image'):
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": data['image']
                }
            })
        
        # 添加用户消息
        messages.append({
            "role": "user",
            "content": user_content
        })

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": request.headers.get('Referer', ''),
                "X-Title": "AI Test Runner",
            },
            model=data['model_name'],
            messages=messages
        )
        return jsonify({
            'response': completion.choices[0].message.content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
