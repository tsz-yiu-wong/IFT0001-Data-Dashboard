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

// Admin Related
let isAdminLoggedIn = false;

// Edit Modal
const modal = document.getElementById('login-modal');
const adminLoginBtn = document.getElementById('admin-login-btn');
const closeBtn = document.querySelector('.close');
const loginSubmitBtn = document.getElementById('login-submit');
const loginStatus = document.getElementById('login-status');
const scope1DirectHint = document.getElementById('scope1_direct_hint');
const scope2LocationHint = document.getElementById('scope2_location_hint');
const scope2MarketHint = document.getElementById('scope2_market_hint');

// Chart Related
let emissionsChart = null;



/****************************************************/
/*              Data Loading Functions              */
/****************************************************/

// Page Load
document.addEventListener('DOMContentLoaded', async () => {
    // Data Display Related Initialization
    resetSortConditions();
    await loadFilters();
    await loadRegionCountryMap();
    await loadPageData();
    
    // Visualization Related Initialization
    $('#chart-items').select2({
        placeholder: 'Select items to compare',
        allowClear: true,
        width: '100%'
    });
    initializeChart();
    setupChartControls();
});

// Filter Related
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

// Region-Country Mapping Related
async function loadRegionCountryMap() {
    try {
        const response = await fetch('/get_region_country_map');
        regionCountryMap = await response.json();
    } catch (error) {
        console.error('Error loading region-country map:', error);
    }
}

// Load Page Data with specific conditions
async function loadPageData() {
    try {
        // Build query conditions
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

        // Get data from server
        const response = await fetch(`/get_data?query=${encodeURIComponent(query)}&page=${currentPage}&items_per_page=${itemsPerPage}`);
        const data = await response.json();
        
        // Update table and pagination
        updateTable(data.data);
        initPagination(data.totalItems, itemsPerPage);
        
        // Update URL (not need to refresh page)
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

// Update Table Structure
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
/*            Filter Update Functions               */
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
        event.preventDefault();
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
        // Clear search input and search condition
        searchInput.value = '';
        searchCondition = '';
        
        // Reset all filter conditions
        filters = { sector: 'all', region: 'all', country: 'all' };
        
        // Reload filter options
        await loadFilters();
        
        // Reset dropdown values
        sectorSelect.value = 'all';
        regionSelect.value = 'all';
        countrySelect.value = 'all';
        
        // Reset sorting
        resetSortConditions();
        
        // Reset page number
        currentPage = 1;
        
        // Reset query
        query = basic_query;
        
        // Reload data
        await loadPageData();
    } catch (error) {
        // Even if error, reset basic query
        console.error('Error clearing filters:', error);
        query = basic_query;
        await loadPageData();
    }
});

// If sector is changed, reset page number and reload data
sectorSelect.addEventListener('change', async () => {
    filters.sector = sectorSelect.value;
    currentPage = 1;
    await loadPageData();
});

// If region is changed, reset country to 'all' and reload data
regionSelect.addEventListener('change', async () => {
    filters.region = regionSelect.value;
    filters.country = 'all';
    updateCountryOptions(filters.region);
    countrySelect.value = 'all';
    currentPage = 1;
    await loadPageData();
});

// If country is changed, reset page number and reload data
countrySelect.addEventListener('change', async () => {
    filters.country = countrySelect.value;
    currentPage = 1;
    await loadPageData();
});

// Scope1 Sort Events
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

// Scope2-Location Sort Events
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

// Scope2-Market Sort Events
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
        // Query without pagination and sorting
        let downloadQuery = basic_query;
        let conditions = [];
        
        // Add search condition
        if (searchCondition) {
            conditions.push(searchCondition);
        }
        
        // Add filter conditions
        if (filters.sector !== 'all') conditions.push(`sector = '${filters.sector}'`);
        if (filters.region !== 'all') conditions.push(`area = '${filters.region}'`);
        if (filters.country !== 'all') conditions.push(`country_region = '${filters.country}'`);
        
        if (conditions.length > 0) {
            downloadQuery += ` WHERE ${conditions.join(' AND ')}`;
        }
        
        // Create download link and trigger download
        const downloadUrl = `/download_data?query=${encodeURIComponent(downloadQuery)}`;
        window.location.href = downloadUrl;
        
    } catch (error) {
        console.error('Error downloading data:', error);
        alert('Error downloading data. Please try again.');
    }
});

// Dropdown Menu Event
dropdowns.forEach(dropdown => {
    // When dropdown menu is opened
    dropdown.addEventListener('mousedown', function() {
        const th = this.closest('th');
        if (this.getAttribute('data-open') !== 'true') {
            this.setAttribute('data-open', 'true');
            th.classList.add('dropdown-open');
        } else {
            this.setAttribute('data-open', 'false');
            th.classList.remove('dropdown-open');
        }
    });

    // When option is selected or loses focus
    dropdown.addEventListener('change', function() {
        this.setAttribute('data-open', 'false');
        this.closest('th').classList.remove('dropdown-open');
    });

    // When dropdown loses focus
    dropdown.addEventListener('blur', function() {
        this.setAttribute('data-open', 'false');
        this.closest('th').classList.remove('dropdown-open');
    });
});




/****************************************************/
/*    Admin Login Related Functions and Events      */
/****************************************************/

// Login Submit Process Function
async function handleLoginSubmit() {
    try {
        // Get login name and password from user input
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // Send login request to server, verify username and password
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        
        // If verified, update login status and show edit button
        if (data.success) {
            isAdminLoggedIn = true;
            modal.style.display = 'none';
            adminLoginBtn.style.display = 'none';
            document.getElementById('admin-logout-btn').style.display = '';
            document.querySelector('.actions-column').style.display = '';
            await loadPageData();
        } else {
            alert('Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
}

// Logout Handler Function
function handleLogout() {
    isAdminLoggedIn = false;
    adminLoginBtn.style.display = '';
    document.getElementById('admin-logout-btn').style.display = 'none';
    document.querySelector('.actions-column').style.display = 'none';
    loadPageData();
}

// Login/Logout Button Events
loginSubmitBtn.addEventListener('click', handleLoginSubmit);
document.getElementById('admin-logout-btn').addEventListener('click', handleLogout);

// Open Login Modal Event
adminLoginBtn.addEventListener('click', () => {
    modal.style.display = 'block';
    document.getElementById('username').focus();
});

// Close Login Modal Event (if clicked "x" button)
closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

// Close Login Modal Event (if clicked outside)
window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// Enter Key Events for Login Form
['username', 'password'].forEach(id => {
    document.getElementById(id).addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            if (id === 'username') {
                document.getElementById('password').focus();
            } else {
                handleLoginSubmit();
            }
        }
    });
});




/****************************************************/
/*       Edit Data Related Functions and Events     */
/****************************************************/

// Get edit modal elements
const editModal = document.getElementById('edit-modal');
const editModalClose = editModal.querySelector('.close');
const saveBtn = editModal.querySelector('.save-btn');
let currentEditData = null;

// Edit Data Function
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

    // Set read-only information display
    document.getElementById('display_company_name').textContent = currentEditData.company_name;
    document.getElementById('display_ticker').textContent = currentEditData.ticker || 'N/A';
    document.getElementById('display_isin').textContent = currentEditData.isin || 'N/A';
    document.getElementById('display_weight').textContent = currentEditData.weight || 'N/A';

    // Set editable field values, modify ID
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

    // Get Bloomberg reference data
    try {
        const response = await fetch(`/get_bloomberg_data?isin=${isin}`);
        const bloombergData = await response.json();
        
        // Set reference data hint
        if (bloombergData) {
            document.getElementById('scope1_direct_hint').textContent = 
                `Bloomberg data ('000): ${bloombergData.scope1_direct || 'N/A'}`;
            document.getElementById('scope2_location_hint').textContent = 
                `Bloomberg data ('000): ${bloombergData.scope2_location || 'N/A'}`;
            document.getElementById('scope2_market_hint').textContent = 
                `Bloomberg data ('000): ${bloombergData.scope2_market || 'N/A'}`;
        } else {
            // If no reference data is found, clear hint
            ['scope1_direct_hint', 'scope2_location_hint', 'scope2_market_hint', 'scope1_and_2_hint']
                .forEach(id => document.getElementById(id).textContent = '');
        }
    } catch (error) {
        console.error('Error fetching Bloomberg data:', error);
        ['scope1_direct_hint', 'scope2_location_hint', 'scope2_market_hint', 'scope1_and_2_hint']
            .forEach(id => document.getElementById(id).textContent = 'Error fetching Bloomberg data');
    }

    // Show modal
    editModal.style.display = 'block';
}

// Save Changes Event
saveBtn.addEventListener('click', async () => {
    if (!currentEditData) return;

    const updatedData = {
        // Keep original non-editable fields
        company_name: currentEditData.company_name,
        ticker: currentEditData.ticker,
        isin: currentEditData.isin,
        weight: currentEditData.weight,
        // Get new values for editable fields, ensure proper handling of empty values
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

// Close Modal Event (if clicked "x" button)
editModalClose.addEventListener('click', () => {
    editModal.style.display = 'none';
});

// Close Modal Event (if clicked outside)
window.addEventListener('click', (event) => {
    if (event.target === editModal) {
        editModal.style.display = 'none';
    }
});


/****************************************************/
/*    Visualization Related Functions and Events    */
/****************************************************/

// Initialize Chart Function
function initializeChart() {
    const ctx = document.getElementById('emissions-chart').getContext('2d');
    if (!ctx) {
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
}

// Setup Chart Controls Function
function setupChartControls() {
    const groupBySelect = document.getElementById('chart-group-by');
    const itemsSelect = document.getElementById('chart-items');
    const metricCheckboxes = document.querySelectorAll('.chart-metrics input[type="checkbox"]');
    
    // Initialize Select2, add search and maximum selection limit
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
    
    // Add checkbox mutual exclusion logic
    const scope1Checkbox = document.getElementById('chart-scope1');
    const scope2LocationCheckbox = document.getElementById('chart-scope2-location');
    const scope2MarketCheckbox = document.getElementById('chart-scope2-market');
    const scope1And2Checkbox = document.getElementById('chart-scope1-and-2');
    
    // Group checkbox
    const individualScopes = [scope1Checkbox, scope2LocationCheckbox, scope2MarketCheckbox];
    
    // Handle single scope change
    individualScopes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                // If any single item is selected, disable scope1_and_2
                scope1And2Checkbox.checked = false;
                scope1And2Checkbox.disabled = true;
            } else {
                // If all single items are not selected, enable scope1_and_2
                if (!individualScopes.some(cb => cb.checked)) {
                    scope1And2Checkbox.disabled = false;
                }
            }
            updateChart();
        });
    });
    
    // Handle scope1_and_2 change
    scope1And2Checkbox.addEventListener('change', () => {
        if (scope1And2Checkbox.checked) {
            // If selected scope1_and_2, disable and uncheck all single items
            individualScopes.forEach(checkbox => {
                checkbox.checked = false;
                checkbox.disabled = true;
            });
        } else {
            // If unselected scope1_and_2, enable all single items
            individualScopes.forEach(checkbox => {
                checkbox.disabled = false;
            });
        }
        updateChart();
    });
    
    // Execute once checkbox status check on initialization
    if (individualScopes.some(cb => cb.checked)) {
        // If any single item is selected, disable scope1_and_2
        scope1And2Checkbox.checked = false;
        scope1And2Checkbox.disabled = true;
    } else if (scope1And2Checkbox.checked) {
        // If scope1_and_2 is selected, disable all single items
        individualScopes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.disabled = true;
        });
    }
    
    // Update multi-select options when group changes
    groupBySelect.addEventListener('change', async () => {
        await updateChartItems();
    });
    
    // Modify option change listening method
    $('#chart-items').on('change', function(e) {
        updateChart();
    });
    
    // Initial load options
    updateChartItems();
}

// Update Chart Items Function
async function updateChartItems() {
    const groupBy = document.getElementById('chart-group-by').value;
    const itemsSelect = document.getElementById('chart-items');
    
    // Get group options
    const query = `SELECT DISTINCT ${groupBy} FROM emissions_data WHERE ${groupBy} IS NOT NULL ORDER BY ${groupBy}`;
    
    try {
        const response = await fetch(`/get_chart_items?query=${encodeURIComponent(query)}`);
        const items = await response.json();
        
        // Clear and update multi-select options
        const itemsSelect = $('#chart-items');
        itemsSelect.empty();
        
        items.forEach(item => {
            if (item) {
                itemsSelect.append(new Option(item, item, false, false));
            }
        });
        
        // Trigger select2 update
        itemsSelect.trigger('change');
        
    } catch (error) {
        console.error('Error updating options:', error);
    }
}

// Update Chart Function
async function updateChart() {
    const groupBy = document.getElementById('chart-group-by').value;
    
    // Modify selected items retrieval method
    const selectedItems = $('#chart-items').val() || [];
    
    // Get metrics
    const metrics = {
        scope1: document.getElementById('chart-scope1').checked,
        scope2_location: document.getElementById('chart-scope2-location').checked,
        scope2_market: document.getElementById('chart-scope2-market').checked,
        scope1_and_2: document.getElementById('chart-scope1-and-2').checked
    };
    
    if (selectedItems.length === 0) {
        emissionsChart.data.labels = [];
        emissionsChart.data.datasets = [];
        emissionsChart.update();
        return;
    }

    // Build metrics list to query
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
        emissionsChart.data.labels = [];
        emissionsChart.data.datasets = [];
        emissionsChart.update();
        return;
    }

    // Build query conditions, handle special characters
    const conditions = selectedItems.map(item => 
        `${groupBy} = '${item.replace(/'/g, "''")}'`
    ).join(' OR ');

    // Build different queries based on different group types
    let query;
    if (groupBy === 'company_name') {
        // Company-level query, directly get data
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
        // Group-level query, need to aggregate data
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
    
    
    try {
        // Get data
        const response = await fetch(`/get_chart_data?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        // Update chart data
        const labels = data.map(item => item[groupBy]);
        
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
        
        // Create dataset for each selected metric
        selectedMetrics.forEach(metric => {
            const dataset = {
                label: metricLabels[metric],
                data: data.map(item => item[metric]),
                backgroundColor: colors[metric],
                borderColor: colors[metric],
                borderWidth: 1
            };
            emissionsChart.data.datasets.push(dataset);
        });
        
        emissionsChart.update();
    } catch (error) {
        console.error('Error updating chart:', error);
    }
}