from flask import Flask, request, render_template, session, jsonify
import pandas as pd
import os

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

if __name__ == '__main__':
    app.run(debug=True)
