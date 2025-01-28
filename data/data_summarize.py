import pandas as pd
import csv

def process_data():
    # 读取ishares数据
    ishares_df = pd.read_csv('data/data_from_ishares_20250124.csv')
    
    # 创建新的DataFrame，设置所需的列
    data_df = pd.DataFrame(columns=['name', 'ticker', 'isin', 'weight', 'sector', 'area', 'country/region', 'scope1_direct', 'scope2_location', 'scope2_market'])
    
    # 从ishares数据中提取需要的列
    data_df['name'] = ishares_df['Name']
    data_df['ticker'] = ishares_df['Ticker']
    data_df['isin'] = ishares_df['ISIN']
    data_df['weight'] = ishares_df['Weight (%)']
    data_df['sector'] = ishares_df['Sector']
    
    # 读取Bloomberg数据
    try:
        bloomberg_df = pd.read_excel('data/data_from_bloomberg.xlsx')
        
        # 创建以ISIN为键的映射字典
        company_info = {}
        for _, row in bloomberg_df.iterrows():
            company_info[row['ISIN']] = {
                'area': row['Region'],
                'country/region': row['Country/Region'],
                'scope1_direct': row['ghg_scope_1'],
                'scope2_location': row['ghg_scope_2_market'],
                'scope2_market': row['ghg_scope_2_location']
            }
        
        # 根据ISIN填充公司信息
        for index, row in data_df.iterrows():
            isin = row['isin']
            if isin in company_info:
                data_df.at[index, 'area'] = company_info[isin]['area']
                data_df.at[index, 'country/region'] = company_info[isin]['country/region']
                data_df.at[index, 'scope1_direct'] = company_info[isin]['scope1_direct']
                data_df.at[index, 'scope2_location'] = company_info[isin]['scope2_location']
                data_df.at[index, 'scope2_market'] = company_info[isin]['scope2_market']
    
    except Exception as e:
        print(f"处理Bloomberg数据时出错: {e}")
        # 如果无法读取Bloomberg数据，将region和country设为空值
        data_df['area'] = ''
        data_df['country/region'] = ''
        data_df['scope1_direct'] = ''
        data_df['scope2_location'] = ''
        data_df['scope2_market'] = ''
    
    # 删除sector为"Cash and/or Derivatives"的行
    data_df = data_df[data_df['sector'] != 'Cash and/or Derivatives']
    
    # 保存处理后的数据到data.csv
    data_df.to_csv('data/data.csv', index=False)
    print("数据处理完成，已保存到data.csv")

if __name__ == "__main__":
    process_data()