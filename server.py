from flask import Flask, render_template, request, jsonify, make_response
import database as db
import atexit
import csv
from io import StringIO
import json

app = Flask(__name__)

# Initialize database connection
@app.before_request
def before_request():
    if db.connection_pool is None:
        db.init_connection_pool()

# Close database connection when application shuts down
atexit.register(db.close_connection_pool)

# Load admin configuration
with open('admin.json', 'r') as f:
    admin_config = json.load(f)


############################################
#            Basic routes                  #
############################################

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Data display
@app.route('/get_data', methods=['GET'])
def get_data():
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    items_per_page = int(request.args.get('items_per_page', 10))
    offset = (page - 1) * items_per_page

    # Get data and total count in one query
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
    
    # Remove total_count field from results
    for row in results:
        if 'total_count' in row:
            del row['total_count']

    return jsonify({
        "data": results,
        "totalItems": total
    })

# Get filters
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

# Get region and country map
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

    # Ensure each region's countries are sorted
    for region in region_country_map:
        region_country_map[region].sort()

    return jsonify(region_country_map)

# Download data
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


############################################
#        Admin related routes               #
############################################

# Admin login
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if (data.get('username') == admin_config['username'] and 
        data.get('password') == admin_config['password']):
        return jsonify({'success': True})
    return jsonify({'success': False})

# Edit and update data
@app.route('/update_data', methods=['POST'])
def update_data():
    try:
        data = request.get_json()
        
        select_query = f"""
        SELECT * FROM emissions_data 
        WHERE company_name = '{data['company_name']}' 
        AND isin = '{data['isin']}'
        LIMIT 1
        """
        
        result = db.get_data(select_query)
        
        if not result:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
            
        row = result[0]
        
        # Handle is_fiscal_year, set to NULL if empty string
        is_fiscal_year = data['is_fiscal_year']
        if is_fiscal_year == '':
            is_fiscal_year = None
        
        # Prepare data to be inserted/updated
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
            'is_fiscal_year': is_fiscal_year,
            'scope1_and_2': data['scope1_and_2']
        }
        
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

# Get Bloomberg data
@app.route('/get_bloomberg_data')
def get_bloomberg_data():
    isin = request.args.get('isin')
    if not isin:
        return jsonify(None)
    
    try:
        query = f"""
            SELECT 
                scope1_direct,
                scope2_location,
                scope2_market
            FROM bloomberg_emissions_data 
            WHERE isin = '{isin}'
            LIMIT 1
        """
        
        result = db.get_data(query)

        if result and len(result) > 0:
            data = result[0]
            formatted_data = {
                'scope1_direct': f"{float(data['scope1_direct']):.2f}" if data.get('scope1_direct') else None,
                'scope2_location': f"{float(data['scope2_location']):.2f}" if data.get('scope2_location') else None,
                'scope2_market': f"{float(data['scope2_market']):.2f}" if data.get('scope2_market') else None
            }
            return jsonify(formatted_data)
            
        return jsonify(None)
        
    except Exception as e:
        print(f"Error fetching Bloomberg data: {str(e)}")
        return jsonify(None)


############################################
#        Visualization related routes       #
############################################

# Get chart items
@app.route('/get_chart_items', methods=['GET'])
def get_chart_items():
    query = request.args.get('query', '')
    results = db.get_data(query)
    items = [row[list(row.keys())[0]] for row in results]
    return jsonify(items)

# Get chart data
@app.route('/get_chart_data', methods=['GET'])
def get_chart_data():
    query = request.args.get('query', '')
    results = db.get_data(query)
    return jsonify(results)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)