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
});

// Load Filter Options
async function loadFilters() {
    try {
        const response = await fetch('/get_filters');
        const filters = await response.json();
        updateSelectOptions(sectorSelect, filters.sectors, 'All Sectors');
        updateSelectOptions(regionSelect, filters.regions, 'All Regions');
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
            query += ` ORDER BY CAST(${sortBy} AS DECIMAL(10,2)) ${sortOrder}`;
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
            <tr>
                <td title="${item.company_name !== null ? item.company_name : 'None'}">${item.company_name !== null ? item.company_name : 'None'}</td>
                <td title="${item.sector !== null ? item.sector : 'None'}">${item.sector !== null ? item.sector : 'None'}</td>
                <td title="${item.area !== null ? item.area : 'None'}">${item.area !== null ? item.area : 'None'}</td>
                <td title="${item.country_region !== null ? item.country_region : 'None'}">${item.country_region !== null ? item.country_region : 'None'}</td>
                <td title="${item.scope1_direct !== null ? parseFloat(item.scope1_direct) : 'None'}">${item.scope1_direct !== null ? parseFloat(item.scope1_direct) : 'None'}</td>
                <td title="${item.scope2_location !== null ? parseFloat(item.scope2_location) : 'None'}">${item.scope2_location !== null ? parseFloat(item.scope2_location) : 'None'}</td>
                <td title="${item.scope2_market !== null ? parseFloat(item.scope2_market) : 'None'}">${item.scope2_market !== null ? parseFloat(item.scope2_market) : 'None'}</td>
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
        query += ` ORDER BY CAST(${sortBy} AS DECIMAL(10,2)) ${sortOrder}`;
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