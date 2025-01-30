from flask import Flask, render_template, request, jsonify, make_response
import database as db
import atexit
import csv
from io import StringIO
import json

app = Flask(__name__)

# 在每个请求之前检查并初始化数据库连接池
@app.before_request
def before_request():
    if db.connection_pool is None:
        db.init_connection_pool()

# 应用关闭时断开连接
atexit.register(db.close_connection_pool)

# 加载管理员配置
with open('admin.json', 'r') as f:
    admin_config = json.load(f)

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

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    print("Received login attempt:", data)  # 调试日志
    print("Stored credentials:", admin_config)  # 调试日志
    if (data.get('username') == admin_config['username'] and 
        data.get('password') == admin_config['password']):
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/update_data', methods=['POST'])
def update_data():
    try:
        data = request.get_json()
        print("Received data from frontend:", data)
        
        select_query = f"""
        SELECT * FROM emissions_data 
        WHERE company_name = '{data['company_name']}' 
        AND isin = '{data['isin']}'
        LIMIT 1
        """
        
        result = db.get_data(select_query)
        print("Found existing record:", result)
        
        if not result:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
            
        row = result[0]
        
        # 处理 is_fiscal_year，如果为空字符串则设为 NULL
        is_fiscal_year = data['is_fiscal_year']
        if is_fiscal_year == '':
            is_fiscal_year = None
        
        # 准备插入/更新的数据
        insert_data = {
            'company_name': row['company_name'],
            'isin': row['isin'],
            'ticker': row['ticker'],
            'weight': row['weight'],
            'sector': data['sector'],
            'area': data['area'],
            'country_region': data['country_region'],
            'scope1_direct': data['scope1_direct'],
            'scope2_location': data['scope2_location'],
            'scope2_market': data['scope2_market'],
            'is_fiscal_year': is_fiscal_year,  # 使用处理后的值
            'scope1_and_2': data['scope1_and_2']
        }
        
        print("Data to be inserted/updated:", insert_data)
        
        insert_query = """
        INSERT INTO emissions_data (
            company_name, isin, ticker, weight, sector, area, country_region,
            scope1_direct, scope2_location, scope2_market,
            is_fiscal_year, scope1_and_2
        ) VALUES (
            %(company_name)s, %(isin)s, %(ticker)s, %(weight)s, %(sector)s, 
            %(area)s, %(country_region)s, %(scope1_direct)s, %(scope2_location)s, 
            %(scope2_market)s, %(is_fiscal_year)s, %(scope1_and_2)s
        ) ON DUPLICATE KEY UPDATE
            sector = VALUES(sector),
            area = VALUES(area),
            country_region = VALUES(country_region),
            scope1_direct = VALUES(scope1_direct),
            scope2_location = VALUES(scope2_location),
            scope2_market = VALUES(scope2_market),
            is_fiscal_year = VALUES(is_fiscal_year),
            scope1_and_2 = VALUES(scope1_and_2)
        """
        
        db.insert_data(insert_query, insert_data)
        return jsonify({'success': True, 'message': 'Data updated successfully'})
        
    except Exception as e:
        print(f"Error updating data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
