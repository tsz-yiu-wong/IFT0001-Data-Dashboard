from flask import Flask, render_template, request, jsonify, make_response
import database as db
import atexit
import csv
from io import StringIO

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
    # 定义列的顺序
    columns = [
        'company_name', 'isin', 'sector', 'area', 'country_region',
        'is_fiscal_year', 'scope1_direct', 'scope2_location', 'scope2_market', 'scope1_and_2'
    ]
    
    # 使用指定的列顺序获取数据
    query = f"SELECT {', '.join(columns)} FROM web_test"
    results = db.get_data(query)
    
    return jsonify({
        "columns": columns,  # 返回列顺序
        "data": results
    })

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
    sectors_query = "SELECT DISTINCT sector FROM emissions_data ORDER BY sector"
    regions_query = "SELECT DISTINCT area FROM emissions_data ORDER BY area"
    countries_query = "SELECT DISTINCT country_region FROM emissions_data ORDER BY country_region"

    sectors = [row['sector'] for row in db.get_data(sectors_query)]
    regions = [row['area'] for row in db.get_data(regions_query)]
    countries = [row['country_region'] for row in db.get_data(countries_query)]

    return jsonify({
        "sectors": sectors,
        "regions": regions,
        "countries": countries
    })

@app.route('/get_region_country_map', methods=['GET'])
def get_region_country_map():
    query = "SELECT DISTINCT area, country_region FROM emissions_data ORDER BY area, country_region"
    data = db.get_data(query)

    region_country_map = {}
    for row in data:
        region = row['area']
        country = row['country_region']
        if region not in region_country_map:
            region_country_map[region] = []
        region_country_map[region].append(country)

    # 确保每个区域下的国家/地区也是排序的
    for region in region_country_map:
        region_country_map[region].sort()

    return jsonify(region_country_map)

@app.route('/download_data', methods=['GET'])
def download_data():
    query = request.args.get('query', '')
    
    # 移除 LIMIT 和 OFFSET 部分（如果有）
    base_query = query.split(' LIMIT')[0]
    
    # 移除 ORDER BY 部分（如果有）
    base_query = base_query.split(' ORDER BY')[0]
    
    results = db.get_data(base_query)
    
    if not results:
        return jsonify({"error": "No data to download"}), 404
    
    # 创建CSV字符串缓冲区
    si = StringIO()
    writer = csv.DictWriter(si, fieldnames=results[0].keys())
    
    # 写入表头
    writer.writeheader()
    
    # 写入数据行
    writer.writerows(results)
    
    # 创建响应
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
