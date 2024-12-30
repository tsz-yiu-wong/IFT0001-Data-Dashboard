from flask import Flask, render_template, request, jsonify
import database as db

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # 渲染 HTML 页面

@app.route('/get_all_data', methods=['GET'])
def get_all_data():
    # 查询数据库获取所有数据
    results = db.get_all_data()
    return jsonify(results)  # 返回 JSON 格式的数据

@app.route('/get_data', methods=['POST'])
def get_data():
    # 从请求中获取数据
    print(f"Request method: {request.method}")
    print(f"Request data: {request.json}")  # 打印接收到的 JSON 数据

    data = request.json
    '''
    company_name = data.get('company_name')
    sector = data.get('sector')
    region = data.get('region')
    scope1 = data.get('scope1')
    scope2_market_based = data.get('scope2_market_based')
    scope2_location_based = data.get('scope2_location_based')
    sort_order_scope1 = data.get('sort_order_scope1', 'ASC')
    sort_order_scope2_market_based = data.get('sort_order_scope2', 'ASC')
    sort_order_scope2_location_based = data.get('sort_order_scope2', 'ASC')
    '''

    page = data.get('page', 1)  # 默认第一页
    per_page = data.get('per_page', 10)  # 默认每页显示 10 条数据
    offset = (page - 1) * per_page

    # 根据这些数据构建查询条件
    query = "SELECT * FROM emissions_data WHERE 1=1"
    params = []
    '''
    # 添加筛选条件
    if sector != "All":
        query += " AND sector = %s"
        params.append(sector)
    if region != "All":
        query += " AND region = %s"
        params.append(region)

    # 添加排序条件
    if scope1:
        query += f" ORDER BY scope1 {sort_order_scope1}"
    if scope2_market_based:
        query += f", scope2 {sort_order_scope2_market_based}"
    '''
    # 添加分页信息
    query += f" LIMIT {per_page} OFFSET {offset}"

    # 执行查询
    results = db.get_data(query, params)

    # 返回查询结果
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
