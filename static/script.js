// 页面加载时自动获取数据
window.onload = function() {
    // 向后端请求全部数据
    fetch('/get_all_data')
        .then(response => response.json())  // 解析 JSON 响应
        .then(data => {
            // 填充表格
            const tableBody = document.querySelector('#data-table tbody');
            tableBody.innerHTML = '';  // 清空现有的表格内容

            // 遍历数据并生成表格行
            data.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.company_name !== 'null' ? item.company_name : 'N/A'}</td> 
                    <td>${item.sector !== 'null' ? item.sector : 'N/A'}</td>
                    <td>${item.region !== 'null' ? item.region : 'N/A'}</td>
                    <td>${item.scope1_total !== 'null' ? parseFloat(item.scope1_total) : 'N/A'}</td>  
                    <td>${item.scope2_market_based !== 'null' ? parseFloat(item.scope2_market_based) : 'N/A'}</td> 
                    <td>${item.scope2_location_based !== 'null' ? parseFloat(item.scope2_location_based) : 'N/A'}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
};

/*
// 获取 DOM 元素
const sectorElement = document.getElementById('sector');
const scope1Element = document.getElementById('scope1');
const scope2Element = document.getElementById('scope2');
const resultsElement = document.getElementById('results');

// fetchData 函数：从后端获取数据并更新页面
function fetchData() {
    const sector = sectorElement.value;
    const scope1 = scope1Element.value;
    const scope2 = scope2Element.value;
    const page = 1; // 固定为第一页
    const perPage = 10; // 每页显示 10 条数据

    const requestData = {
        sector: sector,
        scope1: scope1,
        scope2: scope2,
        page: page,
        per_page: perPage,
        sort_order_scope1: scope1,
        sort_order_scope2: scope2
    };

    fetch('http://localhost:5000/get_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
        .then(response => response.json())
        .then(data => {
            // 更新页面内容
            let resultHtml = "<ul>";
            data.forEach(item => {
                resultHtml += `<li>${JSON.stringify(item)}</li>`;
            });
            resultHtml += "</ul>";
            resultsElement.innerHTML = resultHtml;
        })
        .catch(error => console.error('Error fetching data:', error));
}

// 添加事件监听器：监听用户的选择更改
sectorElement.addEventListener('change', fetchData);
scope1Element.addEventListener('change', fetchData);
scope2Element.addEventListener('change', fetchData);
*/