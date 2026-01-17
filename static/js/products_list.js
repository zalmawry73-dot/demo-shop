// Product List Manager
const API_BASE = '/catalog/api';

const ProductsManager = {
    state: {
        products: [],
        currentPage: 1,
        totalPages: 1,
        selectedIds: [],
        currentCategoryId: null
    },

    init() {
        this.loadCategoriesFilter();
        this.setupEventListeners();
        this.loadProducts();
    },

    setupEventListeners() {
        // Filters - Auto reload on change
        // Category Filter special handling
        const catFilter = document.getElementById('categoryFilter');
        if (catFilter) {
            catFilter.addEventListener('change', (e) => {
                this.filterByCategory(e.target.value);
            });
        }

        // Other Filters - Auto reload on change
        ['typeFilter', 'statusFilter', 'stockFilter'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => {
                this.state.currentPage = 1;
                this.loadProducts();
            });
        });

        // Search - Debounce
        const searchInput = document.getElementById('searchInput');
        let timeout = null;
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.state.currentPage = 1;
                    this.loadProducts();
                }, 500);
            });
        }
    },

    async loadCategoriesFilter() {
        try {
            const response = await axios.get('/catalog/api/categories/tree');
            const tree = response.data;
            const select = document.getElementById('categoryFilter');

            // Helper to render indented options
            const addOptions = (items, level = 0) => {
                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.innerHTML = '&nbsp;'.repeat(level * 4) + item.name;
                    select.appendChild(option);
                    if (item.children) addOptions(item.children, level + 1);
                });
            };
            addOptions(tree);
        } catch (e) {
            console.error('Failed to load categories filter', e);
        }
    },

    filterByCategory(categoryId) {
        this.state.currentCategoryId = categoryId || null;
        this.state.currentPage = 1;
        this.updateBreadcrumbs(categoryId);
        this.loadProducts();
    },

    async updateBreadcrumbs(categoryId) {
        const container = document.getElementById('breadcrumbsContainer');
        const list = container.querySelector('ol');

        if (!categoryId) {
            container.style.display = 'none';
            list.innerHTML = '';
            return;
        }

        try {
            const response = await axios.get(`/catalog/api/categories/${categoryId}/breadcrumbs`);
            const crumbs = response.data;

            let html = `<li class="breadcrumb-item"><a href="#" onclick="ProductsManager.filterByCategory('')">المنتجات</a></li>`;

            crumbs.forEach((crumb, index) => {
                const isActive = index === crumbs.length - 1;
                if (isActive) {
                    html += `<li class="breadcrumb-item active" aria-current="page">${crumb.name}</li>`;
                } else {
                    html += `<li class="breadcrumb-item"><a href="#" onclick="ProductsManager.filterByCategory('${crumb.id}')">${crumb.name}</a></li>`;
                }
            });

            list.innerHTML = html;
            container.style.display = 'block';
        } catch (e) {
            console.error('Failed to update breadcrumbs', e);
        }
    },

    async loadProducts() {
        try {
            const searchInput = document.getElementById('searchInput');
            const typeFilter = document.getElementById('typeFilter');
            const statusFilter = document.getElementById('statusFilter');
            const stockFilter = document.getElementById('stockFilter');

            const params = new URLSearchParams({
                page: this.state.currentPage,
                page_size: 20
            });

            if (this.state.currentCategoryId) params.append('category_id', this.state.currentCategoryId);
            if (searchInput.value) params.append('search', searchInput.value);
            if (typeFilter.value) params.append('product_type', typeFilter.value);
            if (statusFilter.value) params.append('status', statusFilter.value);
            if (stockFilter.value && stockFilter.value !== 'all') params.append('stock_status', stockFilter.value);

            const response = await axios.get(`${API_BASE}/products?${params}`);
            const data = response.data;

            this.state.products = data.items;
            this.state.totalPages = data.total_pages;
            this.renderTable();
            this.renderPagination();
        } catch (error) {
            console.error('Error loading products:', error);
            window.notifier.showToast('فشل تحميل المنتجات: ' + (error.response?.data?.detail || error.message), 'error');
        }
    },

    renderTable() {
        const tbody = document.getElementById('productsTableBody');
        if (!this.state.products.length) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px">لا توجد منتجات</td></tr>';
            return;
        }

        tbody.innerHTML = this.state.products.map(product => {
            const checked = this.state.selectedIds.includes(product.id) ? 'checked' : '';

            // Stock level color coding
            let stockClass = 'stock-high';
            let stockColor = '#10b981';
            if (product.total_stock === 0) {
                stockClass = 'stock-out';
                stockColor = '#ef4444';
            } else if (product.total_stock < 5) {
                stockClass = 'stock-low';
                stockColor = '#f59e0b';
            }

            // Price display
            const priceDisplay = product.min_price === product.max_price
                ? `${product.min_price?.toFixed(2) || '0.00'} ر.س`
                : `${product.min_price?.toFixed(2) || '0.00'} - ${product.max_price?.toFixed(2) || '0.00'} ر.س`;

            // Product image
            const imageSrc = product.main_image_url || '/static/images/placeholder-product.png';

            return `
                <tr>
                    <td>
                        <input type="checkbox" class="product-checkbox" value="${product.id}" 
                            ${checked} onchange="ProductsManager.toggleSelectRow('${product.id}')">
                    </td>
                    <td>
                        <img src="${imageSrc}" alt="${product.name}" 
                             style="width:50px; height:50px; object-fit:cover; border-radius:4px; border:1px solid #e5e7eb;"
                             onerror="this.src='/static/images/placeholder-product.png'">
                    </td>
                    <td>
                        <div style="font-weight:bold; font-size:0.95rem;">${product.name}</div>
                        <div style="font-size:0.8rem; color:#94a3b8">${product.total_variants} متغير | <span style="font-family:monospace">${product.slug}</span></div>
                    </td>
                    <td>${this.getTypeLabel(product.product_type)}</td>
                    <td style="font-weight:600">${priceDisplay}</td>
                    <td>
                        <span class="${stockClass}" style="color:${stockColor}; font-weight:bold;">
                            ${product.total_stock}
                        </span>
                    </td>
                    <td>
                        <span style="font-size:0.9rem; color:#475569;">${product.category_name || '-'}</span>
                    </td>
                    <td>
                        <span class="status-badge ${this.getStatusClass(product.status)}">
                            ${this.getStatusLabel(product.status)}
                        </span>
                    </td>
                    <td>
                        <button class="action-btn secondary" style="padding:5px 10px; font-size:0.8rem;" 
                                onclick="window.location.href='/catalog/products/${product.id}/edit'">
                            <i class="fa-solid fa-edit"></i> تعديل
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        this.updateBulkToolbar();
    },

    getTypeLabel(type) {
        const labels = {
            'Physical': 'مادي',
            'Digital': 'رقمي',
            'Service': 'خدمة',
            'Food': 'طعام'
        };
        return labels[type] || type;
    },

    getStatusLabel(status) {
        const labels = {
            'Active': 'نشط',
            'Draft': 'مسودة',
            'Archived': 'مؤرشف'
        };
        return labels[status] || status;
    },

    getStatusClass(status) {
        const classes = {
            'Active': 'success',
            'Draft': 'warning',
            'Archived': 'default'
        };
        return classes[status] || 'default';
    },

    renderPagination() {
        const container = document.getElementById('pagination');
        if (this.state.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '';
        for (let i = 1; i <= this.state.totalPages; i++) {
            const activeClass = i === this.state.currentPage ? 'active' : '';
            html += `<button class="page-btn ${activeClass}" onclick="ProductsManager.goToPage(${i})">${i}</button>`;
        }
        container.innerHTML = html;
    },

    goToPage(page) {
        this.state.currentPage = page;
        this.loadProducts();
    },

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.product-checkbox');
        const mainCb = document.getElementById('selectAll');
        const ids = [];

        checkboxes.forEach(cb => {
            cb.checked = mainCb.checked;
            if (cb.checked) ids.push(cb.value);
        });

        this.state.selectedIds = mainCb.checked ? ids : [];
        this.updateBulkToolbar();
    },

    toggleSelectRow(id) {
        const index = this.state.selectedIds.indexOf(id);
        if (index > -1) {
            this.state.selectedIds.splice(index, 1);
        } else {
            this.state.selectedIds.push(id);
        }
        this.updateBulkToolbar();

        const allChecked = document.querySelectorAll('.product-checkbox:not(:checked)').length === 0;
        document.getElementById('selectAll').checked = allChecked && this.state.selectedIds.length > 0;
    },

    updateBulkToolbar() {
        const count = this.state.selectedIds.length;
        document.getElementById('selectedCount').innerText = count;

        const toolbar = document.getElementById('bulkActions');
        if (count > 0) toolbar.classList.add('show');
        else toolbar.classList.remove('show');
    },

    async bulkUpdateStatus(status) {
        if (this.state.selectedIds.length === 0) return;

        try {
            await axios.post(`${API_BASE}/products/bulk`, {
                product_ids: this.state.selectedIds,
                action: 'update_status',
                value: status
            });
            window.notifier.showToast('تم تحديث الحالة بنجاح', 'success');
            this.state.selectedIds = [];
            this.loadProducts();
            this.updateBulkToolbar();
        } catch (error) {
            window.notifier.showToast('فشل التحديث: ' + (error.response?.data?.detail || error.message), 'error');
        }
    },

    async bulkExport() {
        if (this.state.selectedIds.length > 0) {
            const ids = this.state.selectedIds.join(',');
            window.location.href = `/catalog/api/products/export?ids=${ids}`;
        } else {
            // Full export
            window.location.href = '/catalog/api/products/export';
        }
    },

    async bulkDelete() {
        if (this.state.selectedIds.length === 0) return;
        if (!await window.notifier.showConfirm(`هل أنت متأكد من حذف ${this.state.selectedIds.length} منتج؟`)) return;

        try {
            await axios.post(`${API_BASE}/products/bulk`, {
                product_ids: this.state.selectedIds,
                action: 'delete'
            });
            window.notifier.showToast('تم الحذف بنجاح', 'success');
            this.state.selectedIds = [];
            this.loadProducts();
            this.updateBulkToolbar();
        } catch (error) {
            window.notifier.showToast('فشل الحذف: ' + (error.response?.data?.detail || error.message), 'error');
        }
    },

    async executeBulkAction(action) {
        if (this.state.selectedIds.length === 0) return;

        if (action === 'delete') {
            if (!await window.notifier.showConfirm(`هل أنت متأكد من حذف ${this.state.selectedIds.length} منتج؟`)) return;

            try {
                await axios.post(`${API_BASE}/products/bulk`, {
                    product_ids: this.state.selectedIds,
                    action: 'delete'
                });
                window.notifier.showToast('تم الحذف بنجاح', 'success');
                this.state.selectedIds = [];
                this.loadProducts();
            } catch (error) {
                window.notifier.showToast('فشل الحذف: ' + (error.response?.data?.detail || error.message), 'error');
            }
        } else if (action === 'status') {
            const status = document.getElementById('bulkStatusSelect').value;
            if (!status) {
                window.notifier.showToast('يرجى اختيار حالة', 'warning');
                return;
            }

            try {
                await axios.post(`${API_BASE}/products/bulk`, {
                    product_ids: this.state.selectedIds,
                    action: 'update_status',
                    value: status
                });
                window.notifier.showToast('تم تحديث الحالة بنجاح', 'success');
                this.state.selectedIds = [];
                document.getElementById('bulkStatusSelect').value = '';
                // Optional: keep current filters or reset? keeping for now
                this.loadProducts();
            } catch (error) {
                window.notifier.showToast('فشل التحديث: ' + (error.response?.data?.detail || error.message), 'error');
            }
        }
    },

    async handleImport(event) {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${API_BASE}/products/import`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            window.notifier.showToast(response.data.message || 'تم الاستيراد بنجاح', 'success');
            this.loadProducts();
        } catch (error) {
            window.notifier.showToast('فشل الاستيراد: ' + (error.response?.data?.detail || error.message), 'error');
        }

        event.target.value = ''; // Reset input
    }
};
