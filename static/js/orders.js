/**
 * Order Management Logic
 */

const API_BASE = '/api';



// --- ORDERS MANAGER (List & Table) ---
const OrdersManager = {
    state: {
        page: 1,
        limit: 10,
        filters: {}
    },

    init() {
        this.loadOrders();
        // Debounce search
        const searchInput = document.getElementById('searchInput');
        let timeout = null;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                this.loadOrders({ search: e.target.value, page: 1 });
            }, 500);
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.action-dropdown')) {
                document.querySelectorAll('.dropdown-menu').forEach(el => el.classList.remove('show'));
            }
        });
    },

    async loadOrders(overrides = {}) {
        const status = document.getElementById('statusFilter').value;
        const dateFrom = document.getElementById('dateFrom').value;
        const dateTo = document.getElementById('dateTo').value;
        const search = document.getElementById('searchInput').value;

        this.state = { ...this.state, ...overrides };
        if (overrides.page) this.state.page = overrides.page;

        const tbody = document.getElementById('ordersTableBody');
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:20px">جاري التحميل...</td></tr>';

        try {
            const params = new URLSearchParams({
                page: this.state.page,
                limit: this.state.limit,
                status: status !== 'all' ? status : '',
                search: search,
                date_from: dateFrom,
                date_to: dateTo
            });

            // Clean empty params
            for (const [key, value] of [...params.entries()]) {
                if (!value) params.delete(key);
            }

            const res = await axios.get(`${API_BASE}/orders_list?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });

            this.renderTable(res.data.data);
            this.renderPagination(res.data.meta);

        } catch (e) {
            console.error(e);
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:red">حدث خطأ في جلب البيانات</td></tr>';
        }
    },

    renderTable(orders) {
        const tbody = document.getElementById('ordersTableBody');
        if (!orders.length) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px">لا توجد طلبات مطابقة</td></tr>';
            return;
        }

        const statusMap = {
            'new': { text: 'جديد', class: 'info' },
            'processing': { text: 'جاري التجهيز', class: 'warning' },
            'ready': { text: 'جاهز', class: 'primary' },
            'shipping': { text: 'جاري التوصيل', class: 'warning' },
            'completed': { text: 'مكتمل', class: 'success' },
            'cancelled': { text: 'ملغي', class: 'danger' }
        };

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td>
                    <input type="checkbox" class="order-checkbox" value="${o.id}" 
                        onchange="OrdersManager.toggleSelectRow(${o.id})"
                        ${this.state.selectedIds?.includes(o.id) ? 'checked' : ''}>
                </td>
                <td>#${o.id}</td>
                <td>
                    <div style="font-weight:bold">${o.customer}</div>
                    <div style="font-size:0.8rem; color:#94a3b8">${o.customer_phone || ''}</div>
                </td>
                <td>${o.date}</td>
                <td><span class="status-badge ${statusMap[o.status]?.class || 'default'}">${statusMap[o.status]?.text || o.status}</span></td>
                <td>${o.payment_method}</td>
                <td>${o.items_count}</td>
                <td style="font-weight:bold">${o.total.toFixed(2)}</td>
                <td>
                    <div class="action-dropdown">
                        <button class="action-dropdown-btn" onclick="OrdersManager.toggleDropdown(event, ${o.id})">
                            <i class="fa-solid fa-ellipsis-vertical"></i>
                        </button>
                        <div id="dropdown-${o.id}" class="dropdown-menu">
                            <a href="/orders/${o.id}" class="dropdown-item">
                                <i class="fa-solid fa-eye"></i> عرض التفاصيل
                            </a>
                            <a href="javascript:void(0)" onclick="OrdersManager.printInvoice(${o.id})" class="dropdown-item">
                                <i class="fa-solid fa-print"></i> طباعة الفاتورة
                            </a>
                            <a href="javascript:void(0)" onclick="OrdersManager.whatsappCustomer('${o.customer_phone}')" class="dropdown-item">
                                <i class="fa-brands fa-whatsapp"></i> مراسلة العميل
                            </a>
                        </div>
                    </div>
                </td>
            </tr>
        `).join('');

        this.updateBulkToolbar();
    },

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.order-checkbox');
        const mainCb = document.getElementById('selectAll');
        const ids = [];

        checkboxes.forEach(cb => {
            cb.checked = mainCb.checked;
            if (cb.checked) ids.push(parseInt(cb.value));
        });

        this.state.selectedIds = mainCb.checked ? ids : [];
        this.updateBulkToolbar();
    },

    toggleSelectRow(id) {
        if (!this.state.selectedIds) this.state.selectedIds = [];
        const index = this.state.selectedIds.indexOf(id);
        if (index > -1) {
            this.state.selectedIds.splice(index, 1);
        } else {
            this.state.selectedIds.push(id);
        }
        this.updateBulkToolbar();

        // Update Select All Checkbox State
        const allChecked = document.querySelectorAll('.order-checkbox:not(:checked)').length === 0;
        document.getElementById('selectAll').checked = allChecked && this.state.selectedIds.length > 0;
    },

    updateBulkToolbar() {
        if (!this.state.selectedIds) this.state.selectedIds = [];
        const count = this.state.selectedIds.length;

        const countElement = document.getElementById('selectedCount');
        if (countElement) {
            countElement.innerText = count;
        }

        const toolbar = document.getElementById('bulkToolbar');
        if (toolbar) {
            if (count > 0) toolbar.classList.add('show');
            else toolbar.classList.remove('show');
        }
    },

    async executeBulkAction(action) {
        if (!this.state.selectedIds || this.state.selectedIds.length === 0) return;

        if (action === 'delete') {
            if (!confirm(`هل أنت متأكد من حذف ${this.state.selectedIds.length} طلب؟ هذا الإجراء لا يمكن التراجع عنه.`)) return;

            try {
                await axios.post(`${API_BASE}/orders/bulk/delete`, { ids: this.state.selectedIds }, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
                });
                Toast.show('نجاح', 'تم الحذف بنجاح', 'success');
                this.state.selectedIds = [];
                this.loadOrders();
            } catch (e) {
                Toast.show('خطأ', 'فشل الحذف: ' + (e.response?.data?.detail || e.message), 'error');
            }
        } else if (action === 'status') {
            const status = document.getElementById('bulkStatusSelect').value;
            if (!status) {
                Toast.show('تنبيه', 'يرجى اختيار حالة', 'warning');
                return;
            }

            try {
                await axios.post(`${API_BASE}/orders/bulk/status`,
                    { ids: this.state.selectedIds, value: status },
                    { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` } }
                );
                Toast.show('نجاح', 'تم تحديث الحالة بنجاح', 'success');
                this.state.selectedIds = [];
                document.getElementById('bulkStatusSelect').value = ''; // Reset select
                this.loadOrders();
            } catch (e) {
                Toast.show('خطأ', 'فشل التحديث: ' + (e.response?.data?.detail || e.message), 'error');
            }
        }
    },

    toggleDropdown(event, id) {
        event.stopPropagation();
        // Close others
        document.querySelectorAll('.dropdown-menu').forEach(el => {
            if (el.id !== `dropdown-${id}`) el.classList.remove('show');
        });
        const menu = document.getElementById(`dropdown-${id}`);
        if (menu) menu.classList.toggle('show');
    },

    printInvoice(id) {
        // In real app, open specific invoice URL
        window.open(`/orders/${id}?print=true`, '_blank');
    },

    whatsappCustomer(phone) {
        if (!phone) {
            Toast.show('تنبيه', 'لا يوجد رقم هاتف للعميل', 'warning');
            return;
        }
        // Basic cleaning
        let p = phone.replace(/[^\d]/g, '');
        if (p.startsWith('05')) p = '966' + p.substring(1); // SA logic example
        window.open(`https://wa.me/${p}`, '_blank');
    },

    renderPagination(meta) {
        const container = document.getElementById('pagination');
        let html = '';

        // Prev
        if (meta.page > 1) {
            html += `<button class="page-btn" onclick="OrdersManager.loadOrders({page:${meta.page - 1}})"><i class="fa fa-chevron-right"></i></button>`;
        }

        // Numbers (Simplified)
        for (let i = 1; i <= meta.pages; i++) {
            // Show first, last, and around current
            if (i === 1 || i === meta.pages || (i >= meta.page - 1 && i <= meta.page + 1)) {
                html += `<button class="page-btn ${i === meta.page ? 'active' : ''}" onclick="OrdersManager.loadOrders({page:${i}})">${i}</button>`;
            } else if (i === meta.page - 2 || i === meta.page + 2) {
                html += `<span>...</span>`;
            }
        }

        // Next
        if (meta.page < meta.pages) {
            html += `<button class="page-btn" onclick="OrdersManager.loadOrders({page:${meta.page + 1}})"><i class="fa fa-chevron-left"></i></button>`;
        }

        container.innerHTML = html;
    }
};

// --- WIZARD LOGIC (Create Order) ---
const Wizard = {
    cart: [],
    customerId: null,
    step: 1,

    reset() {
        this.cart = [];
        this.customerId = null;
        this.step = 1;
        this.updateUI();
        this.renderCart();

        // Product Search Listener
        const searchInput = document.getElementById('productSearch');
        searchInput.value = '';
        searchInput.oninput = (e) => this.searchProducts(e.target.value);
    },

    updateUI() {
        // Steps
        document.querySelectorAll('.wizard-step-panel').forEach((el, idx) => {
            el.classList.remove('active');
            if (idx + 1 === this.step) el.classList.add('active');
        });

        // Dots
        document.querySelectorAll('.step-dot').forEach((el, idx) => {
            el.classList.remove('active');
            if (idx + 1 <= this.step) el.classList.add('active');
        });

        // Buttons
        document.getElementById('prevBtn').style.display = this.step > 1 ? 'block' : 'none';
        const nextBtn = document.getElementById('nextBtn');
        if (this.step === 3) {
            nextBtn.innerText = 'تأكيد وإنشاء الطلب';
            nextBtn.onclick = () => this.submitOrder();
        } else {
            nextBtn.innerText = this.step === 1 ? 'التالي: العميل' : 'التالي: الدفع';
            nextBtn.onclick = () => this.nextStep();
        }
    },

    nextStep() {
        if (this.step === 1 && this.cart.length === 0) {
            window.notifier.showToast("يرجى إضافة منتجات أولاً", 'warning');
            return;
        }
        if (this.step === 2) {
            // Validate Customer
            // If manual guest entry
            const guestName = document.getElementById('guestName').value;
            if (!this.customerId && !guestName) {
                window.notifier.showToast("يرجى اختيار عميل أو إدخال اسم العميل", 'warning');
                return;
            }
        }

        if (this.step === 3) return; // Handled by submit

        this.step++;
        this.updateUI();
        if (this.step === 3) this.calculateTotals();
    },

    prevStep() {
        if (this.step > 1) {
            this.step--;
            this.updateUI();
        }
    },

    // --- Step 1: Products ---
    async searchProducts(query) {
        if (query.length < 2) {
            document.getElementById('searchResults').style.display = 'none';
            return;
        }

        const token = localStorage.getItem('access_token');
        const results = document.getElementById('searchResults');

        if (!token) {
            results.innerHTML = `
                <div style="padding:15px; text-align:center; color:#e74c3c; background:#fee;">
                    <i class="fa fa-lock"></i><br>
                    <strong>يرجى تسجيل الدخول أولاً لرؤية المنتجات</strong>
                </div>
            `;
            results.style.display = 'block';
            return;
        }

        try {
            // Show loading
            results.innerHTML = '<div style="padding:15px; text-align:center"><i class="fa fa-spinner fa-spin"></i> جاري البحث...</div>';
            results.style.display = 'block';

            const res = await axios.get(`${API_BASE}/pos/products?search=${query}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.data.length === 0) {
                results.innerHTML = '<div style="padding:15px; text-align:center; color:#94a3b8">لا توجد منتجات مطابقة</div>';
                return;
            }

            results.innerHTML = res.data.map(p => `
                <div class="search-item" onclick="Wizard.addToCart('${p.id}', '${p.name.replace(/'/g, "\\'")}', ${p.price})">
                    <img src="${p.image}" style="width:30px;height:30px;border-radius:4px;object-fit:cover" onerror="this.src='/static/placeholder.png'">
                    <div>
                        <div style="font-weight:bold;font-size:0.9rem">${p.name}</div>
                        <div style="color:#10b981;font-size:0.8rem">${p.price.toFixed(2)} SAR</div>
                    </div>
                </div>
            `).join('');
            results.style.display = 'block';
        } catch (e) {
            console.error('Search error:', e);

            if (e.response?.status === 401) {
                results.innerHTML = `
                    <div style="padding:15px; text-align:center; color:#e74c3c; background:#fee;">
                        <i class="fa fa-exclamation-triangle"></i><br>
                        <strong>انتهت صلاحية الجلسة</strong><br>
                        <small>جاري إعادة التوجيه لتسجيل الدخول...</small>
                    </div>
                `;
                setTimeout(() => window.location.href = '/login', 2000);
            } else if (e.response?.status === 404) {
                results.innerHTML = '<div style="padding:15px; text-align:center; color:#94a3b8">لا توجد منتجات مطابقة</div>';
            } else {
                results.innerHTML = `
                    <div style="padding:15px; text-align:center; color:#e74c3c">
                        <i class="fa fa-times-circle"></i> فشل تحميل المنتجات<br>
                        <small>${e.response?.data?.detail || 'حاول مرة أخرى'}</small>
                    </div>
                `;
            }
            results.style.display = 'block';
        }
    },

    addToCart(id, name, price) {
        // id is now a string (UUID)
        const existing = this.cart.find(i => i.variant_id === id);
        if (existing) {
            existing.quantity++;
        } else {
            this.cart.push({ variant_id: id, name, price, quantity: 1 });
        }
        document.getElementById('productSearch').value = '';
        document.getElementById('searchResults').style.display = 'none';
        this.renderCart();
    },

    updateQty(id, delta) {
        const item = this.cart.find(i => i.variant_id === id);
        if (!item) return;
        item.quantity += delta;
        if (item.quantity <= 0) {
            this.cart = this.cart.filter(i => i.variant_id !== id);
        }
        this.renderCart();
    },

    renderCart() {
        const tbody = document.getElementById('cartItemsBody');
        const emptyMsg = document.getElementById('emptyCartMsg');

        if (this.cart.length === 0) {
            tbody.innerHTML = '';
            emptyMsg.style.display = 'block';
            return;
        }

        emptyMsg.style.display = 'none';
        tbody.innerHTML = this.cart.map(item => `
            <tr>
                <td>${item.name}</td>
                <td>${item.price.toFixed(2)}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:5px;justify-content:flex-end">
                        <button onclick="Wizard.updateQty('${item.variant_id}', -1)" style="padding:2px 6px">-</button>
                        <span>${item.quantity}</span>
                        <button onclick="Wizard.updateQty('${item.variant_id}', 1)" style="padding:2px 6px">+</button>
                    </div>
                </td>
                <td>${(item.price * item.quantity).toFixed(2)}</td>
                <td><i class="fa fa-trash" style="color:red;cursor:pointer" onclick="Wizard.updateQty('${item.variant_id}', -999)"></i></td>
            </tr>
        `).join('');
    },

    // --- Step 3: Check & Submit ---
    async calculateTotals() {
        try {
            const payload = { items: this.cart.map(i => ({ variant_id: i.variant_id, quantity: i.quantity })) };
            const res = await axios.post(`${API_BASE}/orders/calculate`, payload, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });

            const data = res.data;
            document.getElementById('summSubtotal').innerText = data.subtotal.toFixed(2);
            document.getElementById('summShipping').innerText = data.shipping.toFixed(2);
            document.getElementById('summTax').innerText = data.tax.toFixed(2);
            document.getElementById('summTotal').innerText = data.total.toFixed(2) + ' SAR';

            this.calculatedTotal = data.total; // Store for verification
        } catch (e) {
            console.error("Calculation Error", e);
        }
    },

    async submitOrder() {
        if (!await window.notifier.showConfirm("تأكيد إنشاء الطلب؟")) return;

        const guestName = document.getElementById('guestName').value;
        // Mock payload structure matching OrderCreate schema
        // Note: For real guest, backend handles it if customer_id is null/0?
        // Our backend implementation expects customer_id or auto-creates guest if ID provided but not found?
        // Actually the backend code: `if order.customer_id: ... if not customer: create guest`. 
        // We will pass customer_id=0 for guest or real ID.

        const payload = {
            customer_id: this.customerId || 0, // 0 triggers guest logic in some flows, or we can handle it
            items: this.cart.map(i => ({ variant_id: i.variant_id, quantity: i.quantity })),
            shipping_method: "standard"
            // Backend will likely create a guest named "Guest" if ID=0. 
            // Better to update backend to accept "guest_info". 
            // For now, let's assume standard flow.
        };

        try {
            const res = await axios.post(`${API_BASE}/orders`, payload, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
            window.notifier.showFlashToast("تم إنشاء الطلب بنجاح!", 'success');
            window.location.href = `/orders/${res.data.id}`;
        } catch (e) {
            window.notifier.showToast("فشل إنشاء الطلب: " + (e.response?.data?.detail || e.message), 'error');
        }
    }
};
