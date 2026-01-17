/**
 * Customers List Page JavaScript
 * Handles filtering, searching, pagination, and actions
 */

// State
let currentPage = 1;
let totalPages = 1;
let currentFilters = {
    status: 'all',
    search: '',
    country: '',
    city: '',
    ordersCondition: '',
    ordersValue: '',
    accountStatus: '',
    gender: '',
    birthMonth: '',
    customerType: '',
    channel: ''
};

// DOM Elements
let customersTable, searchInput, filterSidebar, closeFilterBtn, applyFiltersBtn, resetFiltersBtn;

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    initializeElements();
    bindEvents();
    loadCustomers();
    loadCountriesForFilter();
});

function initializeElements() {
    customersTable = document.getElementById('customersTable');
    searchInput = document.getElementById('searchInput');
    filterSidebar = document.getElementById('filterSidebar');
    closeFilterBtn = document.getElementById('closeFilterBtn');
    applyFiltersBtn = document.getElementById('applyFiltersBtn');
    resetFiltersBtn = document.getElementById('resetFiltersBtn');
}

function bindEvents() {
    // Search with debounce
    let searchTimeout;
    searchInput?.addEventListener('input', function (e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.search = e.target.value;
            currentPage = 1;
            loadCustomers();
        }, 500);
    });

    // Status tabs
    document.querySelectorAll('.status-tab').forEach(tab => {
        tab.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelectorAll('.status-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentFilters.status = this.dataset.status;
            currentPage = 1;
            loadCustomers();
        });
    });

    // Filter sidebar
    document.getElementById('openFilterBtn')?.addEventListener('click', openFilterSidebar);
    closeFilterBtn?.addEventListener('click', closeFilterSidebar);
    applyFiltersBtn?.addEventListener('click', applyFilters);
    resetFiltersBtn?.addEventListener('click', resetFilters);

    // Country change in filter
    document.getElementById('filterCountry')?.addEventListener('change', function (e) {
        loadCitiesForFilter(e.target.value);
    });

    // Actions menu
    document.getElementById('exportBtn')?.addEventListener('click', exportCustomers);
    document.getElementById('importBtn')?.addEventListener('click', () => {
        document.getElementById('importFile').click();
    });
    document.getElementById('importFile')?.addEventListener('change', importCustomers);
}

async function loadCustomers() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: 20,
            ...currentFilters
        });

        // Remove empty values
        for (let [key, value] of params.entries()) {
            if (!value || value === 'all' || value === '') {
                params.delete(key);
            }
        }

        const response = await fetch(`/api/customers?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load customers');

        const data = await response.json();
        renderCustomers(data.customers || data);
        updatePagination(data.total || 0, data.page || currentPage);
    } catch (error) {
        console.error('Error loading customers:', error);
        if (window.notifier) notifier.showToast('فشل تحميل العملاء', 'error');
    }
}

function renderCustomers(customers) {
    if (!customersTable) return;

    if (customers.length === 0) {
        customersTable.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <div class="text-muted">
                        <i class="fa-regular fa-folder-open fa-3x mb-3"></i>
                        <p>لا توجد عملاء</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    customersTable.innerHTML = customers.map(customer => `
        <tr>
            <td><input type="checkbox" class="form-check-input" value="${customer.id}"></td>
            <td>
                <div class="fw-bold">${escapeHtml(customer.name)}</div>
                <div class="text-muted small">
                    ${customer.customer_type === 'individual' ? 'فرد' : 'شركة'}
                </div>
            </td>
            <td>
                <div dir="ltr" class="text-end">${customer.mobile || '-'}</div>
                <div class="text-muted small">${customer.email || '-'}</div>
            </td>
            <td>
                <div>${customer.city || '-'}</div>
                <div class="text-muted small">${customer.country}</div>
            </td>
            <td>${customer.channel}</td>
            <td>${customer.total_orders}</td>
            <td>${customer.points}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/customers/${customer.id}" class="btn btn-outline-primary" title="عرض">
                        <i class="fa-solid fa-eye"></i>
                    </a>
                    <a href="/customers/${customer.id}/edit" class="btn btn-outline-secondary" title="تعديل">
                        <i class="fa-solid fa-pen"></i>
                    </a>
                    <button class="btn btn-outline-danger" onclick="deleteCustomer(${customer.id})" title="حذف">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function updatePagination(total, page) {
    totalPages = Math.ceil(total / 20);
    currentPage = page;

    const paginationEl = document.getElementById('pagination');
    if (!paginationEl || totalPages <= 1) {
        if (paginationEl) paginationEl.innerHTML = '';
        return;
    }

    let html = `
        <button class="btn btn-sm btn-outline-secondary" ${currentPage === 1 ? 'disabled' : ''} 
                onclick="changePage(${currentPage - 1})">
            السابق
        </button>
        <span class="mx-2">صفحة ${currentPage} من ${totalPages}</span>
        <button class="btn btn-sm btn-outline-secondary" ${currentPage === totalPages ? 'disabled' : ''} 
                onclick="changePage(${currentPage + 1})">
            التالي
        </button>
    `;
    paginationEl.innerHTML = html;
}

function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadCustomers();
}

// Filter Sidebar
function openFilterSidebar() {
    filterSidebar?.classList.add('open');
}

function closeFilterSidebar() {
    filterSidebar?.classList.remove('open');
}

function applyFilters() {
    currentFilters.country = document.getElementById('filterCountry')?.value || '';
    currentFilters.city = document.getElementById('filterCity')?.value || '';
    currentFilters.ordersCondition = document.getElementById('filterOrdersCondition')?.value || '';
    currentFilters.ordersValue = document.getElementById('filterOrdersValue')?.value || '';
    currentFilters.accountStatus = document.getElementById('filterAccountStatus')?.value || '';
    currentFilters.gender = document.getElementById('filterGender')?.value || '';
    currentFilters.birthMonth = document.getElementById('filterBirthMonth')?.value || '';
    currentFilters.customerType = document.getElementById('filterCustomerType')?.value || '';
    currentFilters.channel = document.getElementById('filterChannel')?.value || '';

    currentPage = 1;
    loadCustomers();
    closeFilterSidebar();
}

function resetFilters() {
    currentFilters = {
        status: currentFilters.status, // Keep status tab
        search: currentFilters.search, // Keep search
        country: '',
        city: '',
        ordersCondition: '',
        ordersValue: '',
        accountStatus: '',
        gender: '',
        birthMonth: '',
        customerType: '',
        channel: ''
    };

    // Reset form
    document.querySelectorAll('#filterSidebar select, #filterSidebar input').forEach(el => {
        el.value = '';
    });

    currentPage = 1;
    loadCustomers();
    closeFilterSidebar();
}

async function loadCountriesForFilter() {
    try {
        const response = await fetch('/static/data/countries_cities.json');
        const data = await response.json();

        const select = document.getElementById('filterCountry');
        if (!select) return;

        select.innerHTML = '<option value="">الكل</option>' +
            Object.keys(data).map(country =>
                `<option value="${country}">${country}</option>`
            ).join('');
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

async function loadCitiesForFilter(country) {
    const citySelect = document.getElementById('filterCity');
    if (!citySelect) return;

    if (!country) {
        citySelect.innerHTML = '<option value="">الكل</option>';
        return;
    }

    try {
        const response = await fetch('/static/data/countries_cities.json');
        const data = await response.json();
        const cities = data[country] || [];

        citySelect.innerHTML = '<option value="">الكل</option>' +
            cities.map(city => `<option value="${city}">${city}</option>`).join('');
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

// Export/Import
async function exportCustomers() {
    try {
        window.location.href = '/api/customers/export';
        if (window.notifier) notifier.showToast('جاري التصدير...', 'info');
    } catch (error) {
        console.error('Error exporting:', error);
        if (window.notifier) notifier.showToast('فشل التصدير', 'error');
    }
}

async function importCustomers(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/customers/import', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            if (window.notifier) notifier.showToast('تم الاستيراد بنجاح', 'success');
            loadCustomers();
        } else {
            throw new Error('Import failed');
        }
    } catch (error) {
        console.error('Error importing:', error);
        if (window.notifier) notifier.showToast('فشل الاستيراد', 'error');
    }
}

// Delete customer
async function deleteCustomer(id) {
    if (!confirm('هل أنت متأكد من حذف هذا العميل؟')) return;

    try {
        const response = await fetch(`/api/customers/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            if (window.notifier) notifier.showToast('تم الحذف بنجاح', 'success');
            loadCustomers();
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Error deleting:', error);
        if (window.notifier) notifier.showToast('فشل الحذف', 'error');
    }
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
