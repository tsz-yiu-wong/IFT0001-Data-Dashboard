/****************************************************/
/*                Global Variables                   */
/****************************************************/

// Database and Query Related
const table_name = "web_test";
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
const scope2 = document.getElementById('scope2');
const dataTableBody = document.getElementById('data-table-body');
const downloadBtn = document.querySelector('#download-btn');
const toggleFullDataBtn = document.querySelector('#toggle-full-data-btn');
const fullDataContainer = document.querySelector('#full-data-container');
const fullDataHeader = document.querySelector('#full-data-header');
const fullDataBody = document.querySelector('#full-data-body');


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
        updateSelectOptions(countrySelect, filters.countries, 'All Countries');
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
        dataTableBody.innerHTML = '<tr><td colspan="6">Loading...</td></tr>';
        const data = await getDataFromServer(query, currentPage, itemsPerPage);
        updateTable(data.items);
        initPagination(data.totalItems, itemsPerPage);
    } catch (error) {
        console.error('Error loading data:', error);
        dataTableBody.innerHTML = '<tr><td colspan="6">Error loading data</td></tr>';
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
                <td>${item.company_name !== null ? item.company_name : 'None'}</td>
                <td>${item.sector !== null ? item.sector : 'None'}</td>
                <td>${item.region !== null ? item.region : 'None'}</td>
                <td>${item.country !== null ? item.country : 'None'}</td>
                <td>${item.scope1_direct !== null ? parseFloat(item.scope1_direct) : 'None'}</td> 
                <td>${item.scope2_indirect !== null ? parseFloat(item.scope2_indirect) : 'None'}</td>   
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
    allCountriesOption.textContent = 'All Countries';
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
    if (filters.region !== 'all') conditions.push(`region = '${filters.region}'`);
    if (filters.country !== 'all') conditions.push(`country = '${filters.country}'`);
    
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
    const searchQuery = searchInput.value.trim();
    if (searchQuery) {
        const isinPattern = /^[A-Za-z]{2}\d{8}$/;
        searchCondition = isinPattern.test(searchQuery) 
            ? `isin='${searchQuery}'`
            : `company_name LIKE '%${searchQuery}%'`;
        
        // 重置筛选条件
        filters = { sector: 'all', region: 'all', country: 'all' };
        sectorSelect.value = 'all';
        regionSelect.value = 'all';
        countrySelect.value = 'all';
        
        resetSortConditions();
        currentPage = 1;
        await applyFilters();
    }
});

// Clear Event
const clearBtn = document.querySelector('#clear-btn');
clearBtn.addEventListener('click', async () => {
    // 清除搜索输入框和搜索条件
    searchInput.value = '';
    searchCondition = '';
    
    // 重置所有筛选条件
    filters = { sector: 'all', region: 'all', country: 'all' };
    sectorSelect.value = 'all';
    regionSelect.value = 'all';
    countrySelect.value = 'all';
    
    // 重置排序
    resetSortConditions();
    
    // 重置页码
    currentPage = 1;
    
    // 重新加载数据
    await applyFilters();
});

// Filter Events
sectorSelect.addEventListener('change', (event) => {
    filters.sector = event.target.value;
    currentPage = 1;
    resetSortConditions();
    applyFilters();
});

regionSelect.addEventListener('change', (event) => {
    filters.region = event.target.value;
    filters.country = 'all';
    updateCountryOptions(filters.region);
    countrySelect.value = 'all';
    currentPage = 1;
    resetSortConditions();
    applyFilters();
});

countrySelect.addEventListener('change', (event) => {
    filters.country = event.target.value;
    currentPage = 1;
    resetSortConditions();
    applyFilters();
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
        scope2.textContent = 'Scope2';
    }
    currentPage = 1;
    applyFilters();
});

scope2.addEventListener('click', () => {
    if (sortBy === 'scope2_indirect') {
        sortOrder = sortOrder === 'ASC' ? 'DESC' : 'ASC';
        scope2.textContent = `Scope2 ${sortOrder === 'ASC' ? '▲' : '▼'}`;
    } else {
        sortBy = 'scope2_indirect';
        sortOrder = 'DESC';
        scope2.textContent = 'Scope2 ▼';
        scope1.textContent = 'Scope1';
    }
    currentPage = 1;
    applyFilters();
});

// Reset Sort Conditions Functions
function resetSortConditions() {
    sortBy = null;
    sortOrder = null;
    scope1.textContent = 'Scope1';
    scope2.textContent = 'Scope2';
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
        if (filters.region !== 'all') conditions.push(`region = '${filters.region}'`);
        if (filters.country !== 'all') conditions.push(`country = '${filters.country}'`);
        
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

// Toggle Full Data Event
toggleFullDataBtn.addEventListener('click', async () => {
    const isHidden = fullDataContainer.style.display === 'none';
    
    if (isHidden) {
        fullDataContainer.style.display = 'block';
        toggleFullDataBtn.textContent = 'Hide All Data ▲';
        
        // 如果表格还没有数据，则加载数据
        if (!fullDataBody.children.length) {
            try {
                const response = await fetch('/get_all_data');
                const { columns, data } = await response.json();
                
                if (data && data.length > 0) {
                    // 使用后端定义的列顺序生成表头
                    fullDataHeader.innerHTML = `
                        <tr>
                            ${columns.map(header => `<th>${header}</th>`).join('')}
                        </tr>
                    `;
                    
                    // 使用相同的列顺序生成数据行
                    fullDataBody.innerHTML = data.map(row => `
                        <tr>
                            ${columns.map(column => 
                                `<td>${row[column] !== null ? row[column] : 'None'}</td>`
                            ).join('')}
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading full data:', error);
                fullDataBody.innerHTML = '<tr><td colspan="100%">Error loading data</td></tr>';
            }
        }
    } else {
        fullDataContainer.style.display = 'none';
        toggleFullDataBtn.textContent = 'Show All Data ▼';
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
            const page = parseInt(pageInput.value, 10);
            if (page >= 1 && page <= totalPages) {
                currentPage = page;
                await loadPageData();
            } else {
                alert(`请输入有效页码（1-${totalPages}）`);
            }
        }
    });
}