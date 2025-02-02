/****************************************************/
/*                Global Variables                   */
/****************************************************/

// Database and Query Related
const table_name = "emissions_data";
const basic_query = `SELECT * from ${table_name}`;
let query = basic_query;

// Search Related
let searchCondition = '';

// Filter Related
let regionCountryMap = {};
let filters = {
    sector: 'all',
    region: 'all',
    country: 'all'
};

// Sort Related
let sortBy = null;
let sortOrder = null;

// Pagination Related
const itemsPerPage = 10;
let currentPage = 1;

// DOM Elements
const searchBtn = document.querySelector('#search-btn');
const searchInput = document.querySelector('#search-input');
const sectorSelect = document.getElementById('sector-select');
const regionSelect = document.getElementById('region-select');
const countrySelect = document.getElementById('country-select');
const scope1 = document.getElementById('scope1');
const scope2_location = document.getElementById('scope2_location');
const scope2_market = document.getElementById('scope2_market');
const dataTableBody = document.getElementById('data-table-body');
const downloadBtn = document.querySelector('#download-btn');
const dropdowns = document.querySelectorAll('.dropdown');

// 添加管理员状态变量
let isAdminLoggedIn = false;

// 获取模态框元素
const modal = document.getElementById('login-modal');
const adminLoginBtn = document.getElementById('admin-login-btn');
const closeBtn = document.querySelector('.close');
const loginSubmitBtn = document.getElementById('login-submit');
const loginStatus = document.getElementById('login-status');

// 在文件开头的 DOM Elements 部分添加新的元素引用
const scope1DirectHint = document.getElementById('scope1_direct_hint');
const scope2LocationHint = document.getElementById('scope2_location_hint');
const scope2MarketHint = document.getElementById('scope2_market_hint');

// 在全局变量部分添加
let emissionsChart = null;


/****************************************************/
/*              Initialization Functions            */
/****************************************************/

// Page Load Event
document.addEventListener('DOMContentLoaded', async() => {
    resetSortConditions();
    await loadFilters();
    await loadRegionCountryMap();
    const data = await getDataFromServer(basic_query, 1, itemsPerPage);
    updateTable(data.items);
    initPagination(data.totalItems, itemsPerPage);
    
    // 初始化Select2
    $('#chart-items').select2({
        placeholder: 'Select items to compare',
        allowClear: true,
        width: '100%'
    });
    
    // 初始化图表
    initializeChart();
    
    // 添加图表控件事件监听
    setupChartControls();
});

// Load Filter Options
async function loadFilters() {
    try {
        const response = await fetch('/get_filters');
        const filters = await response.json();
        updateSelectOptions(sectorSelect, filters.sectors, 'All Sectors');
        updateSelectOptions(regionSelect, filters.regions, 'All Areas');
        updateSelectOptions(countrySelect, filters.countries, 'All Countries/Regions');
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Load Region-Country Mapping
async function loadRegionCountryMap() {
    try {
        const response = await fetch('/get_region_country_map');
        regionCountryMap = await response.json();
    } catch (error) {
        console.error('Error loading region-country map:', error);
    }
}


/****************************************************/
/*                  Data Functions                  */
/****************************************************/

// Load Page Data with Loading State
async function loadPageData() {
    try {
        // 构建查询条件
        let conditions = [];
        if (searchCondition) {
            conditions.push(searchCondition);
        }
        
        if (filters.sector !== 'all') conditions.push(`sector = '${filters.sector}'`);
        if (filters.region !== 'all') conditions.push(`area = '${filters.region}'`);
        if (filters.country !== 'all') conditions.push(`country_region = '${filters.country}'`);
        
        query = basic_query;
        if (conditions.length > 0) {
            query += ` WHERE ${conditions.join(' AND ')}`;
        }

        if (sortBy && sortOrder) {
            query += ` ORDER BY CAST(${sortBy} AS DECIMAL(18,2)) ${sortOrder}`;
        }

        // 使用 fetch 获取数据
        const response = await fetch(`/get_data?query=${encodeURIComponent(query)}&page=${currentPage}&items_per_page=${itemsPerPage}`);
        const data = await response.json();
        
        // 更新表格和分页
        updateTable(data.data);
        initPagination(data.totalItems, itemsPerPage);
        
        // 更新 URL，但不刷新页面
        const searchParams = new URLSearchParams(window.location.search);
        searchParams.set('page', currentPage);
        searchParams.set('sector', filters.sector);
        searchParams.set('region', filters.region);
        searchParams.set('country', filters.country);
        window.history.pushState({}, '', `${window.location.pathname}?${searchParams.toString()}`);
        
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Fetch Data from Server
async function getDataFromServer(query, page = 1, itemsPerPage = 10) {
    const response = await fetch(`/get_data?query=${encodeURIComponent(query)}&page=${page}&items_per_page=${itemsPerPage}`);
    const data = await response.json();
    return {
        items: data.data,
        totalItems: data.totalItems
    };
}

// Update Table Display
function updateTable(items) {
    dataTableBody.innerHTML = '';
    items.forEach(item => {
        const row = `
            <tr data-isin="${item.isin}"
                data-ticker="${item.ticker || ''}"
                data-weight="${item.weight || ''}"
                data-fiscal-year="${item.is_fiscal_year || ''}"
                data-scope1-and-2="${item.scope1_and_2 || ''}">
                <td title="${item.company_name}">${item.company_name}</td>
                <td title="${item.sector}">${item.sector}</td>
                <td title="${item.area}">${item.area}</td>
                <td title="${item.country_region}">${item.country_region}</td>
                <td title="${item.scope1_direct || 'None'}">${item.scope1_direct || 'None'}</td>
                <td title="${item.scope2_location || 'None'}">${item.scope2_location || 'None'}</td>
                <td title="${item.scope2_market || 'None'}">${item.scope2_market || 'None'}</td>
                ${isAdminLoggedIn ? `<td><button class="edit-btn" onclick="editRow('${item.isin}')">Edit</button></td>` : ''}
            </tr>
        `;
        dataTableBody.insertAdjacentHTML('beforeend', row);
    });
}



/****************************************************/
/*                Filter Functions                   */
/****************************************************/

// Update Select Options
function updateSelectOptions(selectElement, options, defaultOption) {
    selectElement.innerHTML = '';
    const defaultOpt = document.createElement('option');
    defaultOpt.value = 'all';
    defaultOpt.textContent = defaultOption;
    selectElement.appendChild(defaultOpt);

    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option;
        selectElement.appendChild(opt);
    });
}

// Update Country Options Based on Region
function updateCountryOptions(region) {
    countrySelect.innerHTML = '';
    const allCountriesOption = document.createElement('option');
    allCountriesOption.value = 'all';
    allCountriesOption.textContent = 'All Countries/Regions';
    countrySelect.appendChild(allCountriesOption);

    if (region !== 'all') {
        const matchedRegion = Object.keys(regionCountryMap).find(
            key => key === region
        );
        const countries = matchedRegion ? regionCountryMap[matchedRegion] : [];
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        });
    } else {
        const allCountries = [...new Set(Object.values(regionCountryMap).flat())];
        allCountries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        });
    }
}

// Apply All Filters
async function applyFilters() {
    let conditions = [];
    
    if (searchCondition) {
        conditions.push(searchCondition);
    }

    if (filters.sector !== 'all') conditions.push(`sector = '${filters.sector}'`);
    if (filters.region !== 'all') conditions.push(`area = '${filters.region}'`);
    if (filters.country !== 'all') conditions.push(`country_region = '${filters.country}'`);
    
    query = basic_query;
    if (conditions.length > 0) {
        query += ` WHERE ${conditions.join(' AND ')}`;
    }

    if (sortBy && sortOrder) {
        query += ` ORDER BY CAST(${sortBy} AS DECIMAL(18,2)) ${sortOrder}`;
    }

    await loadPageData();
}


/****************************************************/
/*              Event Listeners Setup                */
/****************************************************/

// Search Event
searchBtn.addEventListener('click', async () => {
    const searchValue = searchInput.value.trim();
    if (searchValue) {
        searchCondition = `(company_name LIKE '%${searchValue}%' OR isin LIKE '%${searchValue}%')`;
    } else {
        searchCondition = '';
    }
    currentPage = 1;
    await loadPageData();
});

// Add Enter key event for search input
searchInput.addEventListener('keypress', async (event) => {
    if (event.key === 'Enter') {
        event.preventDefault(); // 防止表单提交
        const searchValue = searchInput.value.trim();
        if (searchValue) {
            searchCondition = `(company_name LIKE '%${searchValue}%' OR isin LIKE '%${searchValue}%')`;
        } else {
            searchCondition = '';
        }
        currentPage = 1;
        await loadPageData();
    }
});

// Clear Event
const clearBtn = document.querySelector('#clear-btn');
clearBtn.addEventListener('click', async () => {
    try {
        // 清除搜索输入框和搜索条件
        searchInput.value = '';
        searchCondition = '';
        
        // 重置所有筛选条件
        filters = { sector: 'all', region: 'all', country: 'all' };
        
        // 重新加载筛选器选项
        await loadFilters();
        
        // 重置下拉菜单的选中值
        sectorSelect.value = 'all';
        regionSelect.value = 'all';
        countrySelect.value = 'all';
        
        // 重置排序
        resetSortConditions();
        
        // 重置页码
        currentPage = 1;
        
        // 重置查询
        query = basic_query;
        
        // 重新加载数据
        await loadPageData();
    } catch (error) {
        console.error('Error clearing filters:', error);
        // 即使出错也要重置基本查询
        query = basic_query;
        await loadPageData();
    }
});

// Filter Events
sectorSelect.addEventListener('change', async () => {
    filters.sector = sectorSelect.value;
    currentPage = 1;  // 重置页码
    await loadPageData();
});

regionSelect.addEventListener('change', async () => {
    filters.region = regionSelect.value;
    // 当选择新的region时，重置country为'all'
    filters.country = 'all';
    // 更新country下拉菜单选项
    updateCountryOptions(filters.region);
    // 确保country下拉菜单显示'all'
    countrySelect.value = 'all';
    currentPage = 1;
    await loadPageData();
});

countrySelect.addEventListener('change', async () => {
    filters.country = countrySelect.value;
    currentPage = 1;
    await loadPageData();
});

// Sort Events
scope1.addEventListener('click', () => {
    if (sortBy === 'scope1_direct') {
        sortOrder = sortOrder === 'ASC' ? 'DESC' : 'ASC';
        scope1.textContent = `Scope1 ${sortOrder === 'ASC' ? '▲' : '▼'}`;
    } else {
        sortBy = 'scope1_direct';
        sortOrder = 'DESC';
        scope1.textContent = 'Scope1 ▼';
        scope2_location.textContent = 'Scope2-Location';
        scope2_market.textContent = 'Scope2-Market';
    }
    currentPage = 1;
    applyFilters();
});

scope2_location.addEventListener('click', () => {
    if (sortBy === 'scope2_location') {
        sortOrder = sortOrder === 'ASC' ? 'DESC' : 'ASC';
        scope2_location.textContent = `Scope2-Location ${sortOrder === 'ASC' ? '▲' : '▼'}`;
    } else {
        sortBy = 'scope2_location';
        sortOrder = 'DESC';
        scope2_location.textContent = 'Scope2-Location ▼';
        scope1.textContent = 'Scope1';
        scope2_market.textContent = 'Scope2-Market';
    }
    currentPage = 1;
    applyFilters();
});

scope2_market.addEventListener('click', () => {
    if (sortBy === 'scope2_market') {
        sortOrder = sortOrder === 'ASC' ? 'DESC' : 'ASC';
        scope2_market.textContent = `Scope2-Market ${sortOrder === 'ASC' ? '▲' : '▼'}`;
    } else {
        sortBy = 'scope2_market';
        sortOrder = 'DESC';
        scope2_market.textContent = 'Scope2-Market ▼';
        scope1.textContent = 'Scope1';
        scope2_location.textContent = 'Scope2-Location';
    }
    currentPage = 1;
    applyFilters();
});

// Reset Sort Conditions Functions
function resetSortConditions() {
    sortBy = null;
    sortOrder = null;
    scope1.textContent = 'Scope1';
    scope2_location.textContent = 'Scope2-Location';
    scope2_market.textContent = 'Scope2-Market';
}


// Download Event
downloadBtn.addEventListener('click', async () => {
    try {
        // 构建不包含分页和排序的查询
        let downloadQuery = basic_query;
        let conditions = [];
        
        // 添加搜索条件
        if (searchCondition) {
            conditions.push(searchCondition);
        }
        
        // 添加筛选条件
        if (filters.sector !== 'all') conditions.push(`sector = '${filters.sector}'`);
        if (filters.region !== 'all') conditions.push(`area = '${filters.region}'`);
        if (filters.country !== 'all') conditions.push(`country_region = '${filters.country}'`);
        
        if (conditions.length > 0) {
            downloadQuery += ` WHERE ${conditions.join(' AND ')}`;
        }
        
        // 创建下载链接并触发下载
        const downloadUrl = `/download_data?query=${encodeURIComponent(downloadQuery)}`;
        window.location.href = downloadUrl;
        
    } catch (error) {
        console.error('Error downloading data:', error);
        alert('Error downloading data. Please try again.');
    }
});


/****************************************************/
/*              Pagination Functions                 */
/****************************************************/

// Initialize Pagination
function initPagination(totalItems, itemsPerPage) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pageInput = document.getElementById('page-input');
    const totalPagesDisplay = document.getElementById('total-pages');

    pageInput.value = currentPage;
    totalPagesDisplay.textContent = totalPages;
    pageInput.setAttribute('min', 1);
    pageInput.setAttribute('max', totalPages);

    document.querySelector('#prev-btn').disabled = currentPage === 1;
    document.querySelector('#next-btn').disabled = currentPage === totalPages;

    if (!window.paginationInitialized) {
        setPageButtonsListener(totalPages);
        setPaginationListener(totalPages);
        window.paginationInitialized = true;
    }
}

// Set Page Navigation Listeners
function setPageButtonsListener(totalPages) {
    const prevBtn = document.querySelector('#prev-btn');
    const nextBtn = document.querySelector('#next-btn');

    prevBtn.addEventListener('click', async () => {
        if (currentPage > 1) {
            currentPage--;
            await loadPageData();
        }
    });

    nextBtn.addEventListener('click', async () => {
        if (currentPage < totalPages) {
            currentPage++;
            await loadPageData();
        }
    });
}

// Set Page Input Listener
function setPaginationListener(totalPages) {
    const pageInput = document.getElementById('page-input');
    pageInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter') {
            let page = parseInt(pageInput.value, 10);
            if (page < 1) {
                page = 1;
            } else if (page > totalPages) {
                page = totalPages;
            }
            currentPage = page;
            pageInput.value = page;
            await loadPageData();
        }
    });
}

// 添加下拉菜单事件监听
dropdowns.forEach(dropdown => {
    // 打开下拉菜单时
    dropdown.addEventListener('mousedown', function() {
        // 获取箭头元素（th的伪元素）
        const th = this.closest('th');
        if (this.getAttribute('data-open') !== 'true') {
            this.setAttribute('data-open', 'true');
            th.classList.add('dropdown-open');
        } else {
            this.setAttribute('data-open', 'false');
            th.classList.remove('dropdown-open');
        }
    });

    // 选择选项或失去焦点时
    dropdown.addEventListener('change', function() {
        this.setAttribute('data-open', 'false');
        this.closest('th').classList.remove('dropdown-open');
    });

    dropdown.addEventListener('blur', function() {
        this.setAttribute('data-open', 'false');
        this.closest('th').classList.remove('dropdown-open');
    });
});

// 登录相关事件监听
adminLoginBtn.addEventListener('click', () => {
    modal.style.display = 'block';
    // 聚焦到用户名输入框
    document.getElementById('username').focus();
});

closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// 添加回车键登录功能
function handleLoginSubmit() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    loginSubmit(username, password);
}

// 登录提交处理
async function loginSubmit(username, password) {
    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        
        if (data.success) {
            isAdminLoggedIn = true;
            modal.style.display = 'none';
            
            // 切换按钮显示
            adminLoginBtn.style.display = 'none';
            document.getElementById('admin-logout-btn').style.display = '';
            
            // 显示 Actions 列
            document.querySelector('.actions-column').style.display = '';
            
            // 重新加载数据以显示编辑按钮
            await loadPageData();
        } else {
            alert('Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

// 添加回车键监听
document.getElementById('username').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('password').focus();
    }
});

document.getElementById('password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleLoginSubmit();
    }
});

// 登录按钮点击事件
loginSubmitBtn.addEventListener('click', handleLoginSubmit);

// 添加登出按钮事件监听
document.getElementById('admin-logout-btn').addEventListener('click', () => {
    isAdminLoggedIn = false;
    adminLoginBtn.style.display = '';
    document.getElementById('admin-logout-btn').style.display = 'none';
    document.querySelector('.actions-column').style.display = 'none';
    loadPageData(); // 重新加载数据以移除编辑按钮
});

// 获取编辑模态框元素
const editModal = document.getElementById('edit-modal');
const editModalClose = editModal.querySelector('.close');
const saveBtn = editModal.querySelector('.save-btn');
let currentEditData = null;

// 修改 editRow 函数
async function editRow(isin) {
    const row = event.target.closest('tr');
    const cells = row.cells;
    
    currentEditData = {
        company_name: cells[0].textContent,
        ticker: row.getAttribute('data-ticker'),
        isin: row.getAttribute('data-isin'),
        weight: row.getAttribute('data-weight'),
        sector: cells[1].textContent,
        area: cells[2].textContent,
        country_region: cells[3].textContent,
        is_fiscal_year: row.getAttribute('data-fiscal-year'),
        scope1_direct: cells[4].textContent === 'None' ? '' : cells[4].textContent,
        scope2_location: cells[5].textContent === 'None' ? '' : cells[5].textContent,
        scope2_market: cells[6].textContent === 'None' ? '' : cells[6].textContent,
        scope1_and_2: row.getAttribute('data-scope1-and-2')
    };

    // 设置只读信息显示
    document.getElementById('display_company_name').textContent = currentEditData.company_name;
    document.getElementById('display_ticker').textContent = currentEditData.ticker || 'N/A';
    document.getElementById('display_isin').textContent = currentEditData.isin || 'N/A';
    document.getElementById('display_weight').textContent = currentEditData.weight || 'N/A';

    // 设置可编辑字段的值，修改 ID
    const idMap = {
        'sector': 'sector_input',
        'area': 'area_input',
        'country_region': 'country_region_input',
        'is_fiscal_year': 'is_fiscal_year_input',
        'scope1_direct': 'scope1_direct_input',
        'scope2_location': 'scope2_location_input',
        'scope2_market': 'scope2_market_input',
        'scope1_and_2': 'scope1_and_2_input'
    };

    Object.entries(idMap).forEach(([key, inputId]) => {
        const element = document.getElementById(inputId);
        if (element) {
            element.value = currentEditData[key] || '';
        }
    });

    // 获取 Bloomberg 参考数据
    try {
        const response = await fetch(`/get_bloomberg_data?isin=${isin}`);
        const bloombergData = await response.json();
        
        // 设置参考数据提示
        if (bloombergData) {
            document.getElementById('scope1_direct_hint').textContent = 
                `Bloomberg data ('000): ${bloombergData.scope1_direct || 'N/A'}`;
            document.getElementById('scope2_location_hint').textContent = 
                `Bloomberg data ('000): ${bloombergData.scope2_location || 'N/A'}`;
            document.getElementById('scope2_market_hint').textContent = 
                `Bloomberg data ('000): ${bloombergData.scope2_market || 'N/A'}`;
        } else {
            // 如果没有找到参考数据，清空提示
            ['scope1_direct_hint', 'scope2_location_hint', 'scope2_market_hint', 'scope1_and_2_hint']
                .forEach(id => document.getElementById(id).textContent = '');
        }
    } catch (error) {
        console.error('Error fetching Bloomberg data:', error);
        ['scope1_direct_hint', 'scope2_location_hint', 'scope2_market_hint', 'scope1_and_2_hint']
            .forEach(id => document.getElementById(id).textContent = 'Error fetching Bloomberg data');
    }

    // 显示模态框
    editModal.style.display = 'block';
}

// 关闭模态框
editModalClose.addEventListener('click', () => {
    editModal.style.display = 'none';
});

// 点击模态框外部关闭
window.addEventListener('click', (event) => {
    if (event.target === editModal) {
        editModal.style.display = 'none';
    }
});

// 保存更改
saveBtn.addEventListener('click', async () => {
    if (!currentEditData) return;

    const updatedData = {
        // 保留原有的不可编辑字段
        company_name: currentEditData.company_name,
        ticker: currentEditData.ticker,
        isin: currentEditData.isin,
        weight: currentEditData.weight,
        // 获取可编辑字段的新值，并确保正确处理空值
        sector: document.getElementById('sector_input').value.trim(),
        area: document.getElementById('area_input').value.trim(),
        country_region: document.getElementById('country_region_input').value.trim(),
        is_fiscal_year: document.getElementById('is_fiscal_year_input').value,
        scope1_direct: document.getElementById('scope1_direct_input').value.trim() || null,
        scope2_location: document.getElementById('scope2_location_input').value.trim() || null,
        scope2_market: document.getElementById('scope2_market_input').value.trim() || null,
        scope1_and_2: document.getElementById('scope1_and_2_input').value.trim() || null
    };

    try {
        const response = await fetch('/update_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedData)
        });

        const result = await response.json();
        
        if (result.success) {
            editModal.style.display = 'none';
            await loadPageData();
            alert('Data updated successfully');
        } else {
            alert('Failed to update data: ' + result.message);
        }
    } catch (error) {
        console.error('Error updating data:', error);
        alert('Error updating data');
    }
});


// 添加图表相关函数
function initializeChart() {
    console.log('开始初始化图表');
    const ctx = document.getElementById('emissions-chart').getContext('2d');
    if (!ctx) {
        console.error('未找到图表canvas元素');
        return;
    }
    
    emissionsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Emissions Data'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });
    console.log('图表初始化完成');
}

function setupChartControls() {
    const groupBySelect = document.getElementById('chart-group-by');
    const itemsSelect = document.getElementById('chart-items');
    const metricCheckboxes = document.querySelectorAll('.chart-metrics input[type="checkbox"]');
    
    // 初始化 Select2，添加搜索和最大选择限制
    $('#chart-items').select2({
        placeholder: 'Select items to compare (max 11)',
        allowClear: true,
        width: '100%',
        maximumSelectionLength: 11,
        language: {
            maximumSelected: function (e) {
                return 'You can only select up to 11 items';
            }
        }
    });
    
    // 添加复选框互斥逻辑
    const scope1Checkbox = document.getElementById('chart-scope1');
    const scope2LocationCheckbox = document.getElementById('chart-scope2-location');
    const scope2MarketCheckbox = document.getElementById('chart-scope2-market');
    const scope1And2Checkbox = document.getElementById('chart-scope1-and-2');
    
    // 分组复选框
    const individualScopes = [scope1Checkbox, scope2LocationCheckbox, scope2MarketCheckbox];
    
    // 处理单项scope的变化
    individualScopes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                // 如果选中任一单项，禁用 scope1_and_2
                scope1And2Checkbox.checked = false;
                scope1And2Checkbox.disabled = true;
            } else {
                // 如果所有单项都未选中，启用 scope1_and_2
                if (!individualScopes.some(cb => cb.checked)) {
                    scope1And2Checkbox.disabled = false;
                }
            }
            updateChart();
        });
    });
    
    // 处理 scope1_and_2 的变化
    scope1And2Checkbox.addEventListener('change', () => {
        if (scope1And2Checkbox.checked) {
            // 如果选中 scope1_and_2，禁用并取消选中所有单项
            individualScopes.forEach(checkbox => {
                checkbox.checked = false;
                checkbox.disabled = true;
            });
        } else {
            // 如果取消选中 scope1_and_2，启用所有单项
            individualScopes.forEach(checkbox => {
                checkbox.disabled = false;
            });
        }
        updateChart();
    });
    
    // 初始化时执行一次复选框状态检查
    if (individualScopes.some(cb => cb.checked)) {
        // 如果有任何单项被选中，禁用 scope1_and_2
        scope1And2Checkbox.checked = false;
        scope1And2Checkbox.disabled = true;
    } else if (scope1And2Checkbox.checked) {
        // 如果 scope1_and_2 被选中，禁用所有单项
        individualScopes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.disabled = true;
        });
    }
    
    // 组别变化时更新多选框选项
    groupBySelect.addEventListener('change', async () => {
        console.log('分组选项改变');
        await updateChartItems();
    });
    
    // 修改选项变化的监听方式
    $('#chart-items').on('change', function(e) {
        console.log('选项变化事件触发');
        console.log('当前选中值:', $(this).val());
        updateChart();
    });
    
    // 初始加载选项
    updateChartItems();
}

async function updateChartItems() {
    console.log('开始更新选项列表');
    const groupBy = document.getElementById('chart-group-by').value;
    const itemsSelect = document.getElementById('chart-items');
    
    // 获取分组选项
    const query = `SELECT DISTINCT ${groupBy} FROM emissions_data WHERE ${groupBy} IS NOT NULL ORDER BY ${groupBy}`;
    console.log('获取选项的查询:', query);
    
    try {
        const response = await fetch(`/get_chart_items?query=${encodeURIComponent(query)}`);
        const items = await response.json();
        console.log('获取到的选项:', items);
        
        // 清空并更新多选框选项
        const itemsSelect = $('#chart-items');
        itemsSelect.empty();
        
        items.forEach(item => {
            if (item) { // 确保不添加空值
                itemsSelect.append(new Option(item, item, false, false));
            }
        });
        
        // 触发 select2 更新
        itemsSelect.trigger('change');
        console.log('选项更新完成');
        
    } catch (error) {
        console.error('更新选项时出错:', error);
    }
}

async function updateChart() {
    console.log('开始更新图表');
    const groupBy = document.getElementById('chart-group-by').value;
    
    // 修改获取选中项目的方式
    const selectedItems = $('#chart-items').val() || [];
    console.log('Select2原始值:', $('#chart-items').val());
    console.log('选中的项目:', selectedItems);
    
    const metrics = {
        scope1: document.getElementById('chart-scope1').checked,
        scope2_location: document.getElementById('chart-scope2-location').checked,
        scope2_market: document.getElementById('chart-scope2-market').checked,
        scope1_and_2: document.getElementById('chart-scope1-and-2').checked
    };
    console.log('选中的指标:', metrics);
    
    if (selectedItems.length === 0) {
        console.log('没有选中任何项目，清空图表');
        emissionsChart.data.labels = [];
        emissionsChart.data.datasets = [];
        emissionsChart.update();
        return;
    }

    // 构建要查询的指标列表
    const selectedMetrics = Object.entries(metrics)
        .filter(([_, isChecked]) => isChecked)
        .map(([metric, _]) => {
            switch(metric) {
                case 'scope1': return 'scope1_direct';
                case 'scope2_location': return 'scope2_location';
                case 'scope2_market': return 'scope2_market';
                case 'scope1_and_2': return 'scope1_and_2';
            }
        });

    if (selectedMetrics.length === 0) {
        console.log('没有选中任何指标，清空图表');
        emissionsChart.data.labels = [];
        emissionsChart.data.datasets = [];
        emissionsChart.update();
        return;
    }

    // 构建查询条件时处理特殊字符
    const conditions = selectedItems.map(item => 
        `${groupBy} = '${item.replace(/'/g, "''")}'`
    ).join(' OR ');

    // 根据不同的分组类型构建不同的查询
    let query;
    if (groupBy === 'company_name') {
        // 公司级别的查询，直接获取数据
        const metricsQuery = selectedMetrics
            .map(metric => `CAST(NULLIF(${metric}, '') AS DECIMAL(18,2)) as ${metric}`)
            .join(', ');
        
        query = `
            SELECT ${groupBy}, ${metricsQuery}
            FROM emissions_data
            WHERE ${conditions}
            ORDER BY ${groupBy}
        `;
    } else {
        // 分组级别的查询，需要汇总数据
        const metricsQuery = selectedMetrics
            .map(metric => `SUM(CAST(NULLIF(${metric}, '') AS DECIMAL(18,2))) as ${metric}`)
            .join(', ');
        
        query = `
            SELECT ${groupBy}, ${metricsQuery}
            FROM emissions_data
            WHERE ${conditions}
            GROUP BY ${groupBy}
            ORDER BY ${groupBy}
        `;
    }
    
    console.log('构建的SQL查询:', query);
    
    try {
        // 获取数据
        const response = await fetch(`/get_chart_data?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        console.log('获取到的数据:', data);
        
        // 更新图表数据
        const labels = data.map(item => item[groupBy]);
        console.log('图表标签:', labels);
        
        emissionsChart.data.labels = labels;
        emissionsChart.data.datasets = [];
        
        const colors = {
            scope1_direct: 'rgba(255, 99, 132, 0.8)',
            scope2_location: 'rgba(54, 162, 235, 0.8)',
            scope2_market: 'rgba(75, 192, 192, 0.8)',
            scope1_and_2: 'rgba(153, 102, 255, 0.8)'
        };
        
        const metricLabels = {
            scope1_direct: 'Scope1 Direct',
            scope2_location: 'Scope2 Location',
            scope2_market: 'Scope2 Market',
            scope1_and_2: 'Scope1 and 2'
        };
        
        // 为每个选中的指标创建数据集
        selectedMetrics.forEach(metric => {
            const dataset = {
                label: metricLabels[metric],
                data: data.map(item => item[metric]),
                backgroundColor: colors[metric],
                borderColor: colors[metric],
                borderWidth: 1
            };
            console.log(`${metric} 数据集:`, dataset);
            emissionsChart.data.datasets.push(dataset);
        });
        
        console.log('更新前的图表数据:', emissionsChart.data);
        emissionsChart.update();
        console.log('图表更新完成');
    } catch (error) {
        console.error('更新图表时出错:', error);
    }
}

