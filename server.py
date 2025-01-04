from flask import Flask, render_template, request, jsonify
import database as db
import atexit

app = Flask(__name__)

# 在每个请求之前检查并初始化数据库连接池
@app.before_request
def before_request():
    if db.connection_pool is None:
        db.init_connection_pool()

# 应用关闭时断开连接
atexit.register(db.close_connection_pool)

@app.route('/')
def home():
    return render_template('index.html')  # 渲染 HTML 页面

@app.route('/get_all_data', methods=['GET'])
def get_all_data():
    results = db.get_all_data("web_test")
    return jsonify(results)  # 返回 JSON 格式的数据

@app.route('/get_data', methods=['GET'])
def get_data():
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    items_per_page = int(request.args.get('items_per_page', 10))
    offset = (page - 1) * items_per_page

    # 使用子查询一次性获取数据和总数
    modified_query = f"""
    SELECT *, (
        SELECT COUNT(*) 
        FROM ({query}) as count_query
    ) as total_count 
    FROM ({query}) as data_query 
    LIMIT {items_per_page} OFFSET {offset}
    """
    
    results = db.get_data(modified_query)
    total = results[0]['total_count'] if results else 0
    
    # 移除结果中的total_count字段
    for row in results:
        if 'total_count' in row:
            del row['total_count']

    return jsonify({
        "data": results,
        "totalItems": total
    })

@app.route('/get_filters', methods=['GET'])
def get_filters():
    sectors_query = "SELECT DISTINCT sector FROM web_test"
    regions_query = "SELECT DISTINCT region FROM web_test"
    countries_query = "SELECT DISTINCT country FROM web_test"

    sectors = [row['sector'] for row in db.get_data(sectors_query)]
    regions = [row['region'] for row in db.get_data(regions_query)]
    countries = [row['country'] for row in db.get_data(countries_query)]

    return jsonify({
        "sectors": sectors,
        "regions": regions,
        "countries": countries
    })

@app.route('/get_region_country_map', methods=['GET'])
def get_region_country_map():
    query = "SELECT DISTINCT region, country FROM web_test"
    data = db.get_data(query)

    region_country_map = {}
    for row in data:
        region = row['region']
        country = row['country']
        if region not in region_country_map:
            region_country_map[region] = []
        region_country_map[region].append(country)

    return jsonify(region_country_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
