from flask import Flask, render_template, jsonify
from database import get_data_from_db  # 引入数据库逻辑

app = Flask(__name__)

# 后端 API 路由
@app.route('/api/data')
def api_data():
    data = get_data_from_db()
    return jsonify(data)

# HTML 前端渲染
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
