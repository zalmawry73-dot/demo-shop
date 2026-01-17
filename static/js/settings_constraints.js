
document.addEventListener('DOMContentLoaded', async function () {
    // Determine which page we are on based on elements presence
    const constraintsTableBody = document.getElementById('shippingConstraintsTable');
    const constraintForm = document.getElementById('constraintForm');

    if (constraintsTableBody) {
        // Load Shipping by default
        fetchConstraints('shipping');

        // Handle Tab Switches
        const paymentTab = document.getElementById('payment-tab');
        if (paymentTab) {
            paymentTab.addEventListener('shown.bs.tab', () => fetchConstraints('payment'));
        }
    }

    if (constraintForm) {
        initConstraintForm();
    }
});

// --- LIST PAGE LOGIC ---

async function fetchConstraints(type = 'shipping') {
    const tableId = type === 'shipping' ? 'shippingConstraintsTable' : 'paymentConstraintsTable';
    const tableBody = document.getElementById(tableId);
    if (!tableBody) return;

    tableBody.innerHTML = '<tr><td colspan="5" class="text-center">جاري التحميل...</td></tr>';

    try {
        const response = await fetch(`/api/settings/constraints/${type}`);
        if (!response.ok) throw new Error('Failed to fetch constraints');
        const constraints = await response.json();

        tableBody.innerHTML = '';
        if (constraints.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">لا توجد قيود مضافة حالياً</td></tr>';
            return;
        }

        constraints.forEach(c => {
            const count = type === 'shipping' ? (c.shipping_company_ids ? c.shipping_company_ids.length : 0) : (c.payment_method_ids ? Object.keys(c.payment_method_ids).length : 0);

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="fw-bold">${c.name}</div>
                    <div class="small text-muted text-truncate" style="max-width: 200px;">
                        ${c.custom_error_message || 'لا توجد رسالة مخصصة'}
                    </div>
                </td>
                <td>
                    <span class="badge bg-light text-dark border">
                        ${count} ${type === 'shipping' ? 'شركات' : 'خيارات'}
                    </span>
                </td>
                <td>
                    <span class="badge bg-light text-dark border">${c.conditions.length} شروط</span>
                </td>
                <td>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" ${c.is_active ? 'checked' : ''} disabled>
                    </div>
                </td>
                <td class="text-end">
                    <a href="/settings/constraints/${type}/${c.id}/edit" class="btn btn-sm btn-outline-primary me-1">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteConstraint(${c.id}, '${type}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error(error);
        notifier.showToast('فشل في تحميل البيانات', 'error');
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">حدث خطأ أثناء التحميل</td></tr>';
    }
}

async function deleteConstraint(id, type) {
    if (!confirm('هل أنت متأكد من حذف هذا القيد؟')) return;
    try {
        const response = await fetch(`/api/settings/constraints/${type}/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete');
        notifier.showToast('تم الحذف بنجاح', 'success');
        fetchConstraints(type);
    } catch (error) {
        console.error(error);
        notifier.showToast('فشل الحذف', 'error');
    }
}


// --- FORM PAGE LOGIC ---

let currentConditions = []; // Stores the current state of conditions
let isEditMode = false;
let currentConstraintId = null;

// Cache for Products and Categories
let cachedCategories = null; // Flat list
let cachedProducts = null; // List

// Temporary Selection State for Modals
let tempSelectedCategoryIds = new Set();
let tempSelectedProductIds = new Set();
let selectedCategoriesForInput = []; // Validated selection for current condition being added
let selectedProductsForInput = [];   // Validated selection for current condition being added

async function initConstraintForm() {
    const idInput = document.getElementById('constraintId');
    if (idInput) {
        isEditMode = true;
        currentConstraintId = idInput.value;
        await loadConstraintDetails(currentConstraintId);
    }

    // Toggle Custom Error Visibility
    document.getElementById('isCustomErrorEnabled').addEventListener('change', function () {
        const container = document.getElementById('customErrorContainer');
        if (this.checked) container.classList.remove('d-none');
        else container.classList.add('d-none');
    });

    // Modal Condition Type Change - Delegated listener for Radio Grid
    document.getElementById('conditionTypeGrid').addEventListener('change', (e) => {
        if (e.target.name === 'conditionType') {
            document.getElementById('conditionTypeSelect').value = e.target.value; // Sync to hidden input if needed
            renderConditionInputs();
        }
    });

    // Save Button
    document.getElementById('saveConstraintBtn').addEventListener('click', saveConstraint);

    // Add Condition Confirm
    document.getElementById('confirmAddCondition').addEventListener('click', addConditionFromModal);

    // Categories Modal Confirm
    const confirmCatBtn = document.getElementById('confirmCategorySelectionBtn');
    if (confirmCatBtn) confirmCatBtn.addEventListener('click', saveCategorySelection);

    // Products Modal Confirm
    const confirmProdBtn = document.getElementById('confirmProductSelectionBtn');
    if (confirmProdBtn) confirmProdBtn.addEventListener('click', saveProductSelection);
}

async function loadConstraintDetails(id) {
    try {
        const type = document.getElementById('constraintType').value;
        const response = await fetch(`/api/settings/constraints/${type}/${id}`);
        if (!response.ok) throw new Error('Failed to load detail');
        const data = await response.json();

        // Populate Shipping Companies or Payment Methods
        const methodSelectId = type === 'shipping' ? 'shippingCompanies' : 'paymentMethods';
        const methodIds = type === 'shipping' ? data.shipping_company_ids : data.payment_method_ids;

        const select = document.getElementById(methodSelectId);
        if (select && methodIds) {
            Array.from(select.options).forEach(opt => {
                if (methodIds.includes(opt.value)) {
                    opt.selected = true;
                }
            });
        }

        // Populate Conditions
        currentConditions = data.conditions;
        renderConditionsList();

    } catch (error) {
        console.error(error);
        notifier.showToast('فشل تحميل بيانات القيد', 'error');
    }
}

// Render the list of added conditions (The main cards)
function renderConditionsList() {
    const container = document.getElementById('conditionsList');
    container.innerHTML = '';

    if (currentConditions.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-3" id="noConditionsMsg">لا توجد شروط مضافة</div>';
        return;
    }

    currentConditions.forEach((cond, index) => {
        const div = document.createElement('div');
        div.className = 'border rounded p-3 bg-light position-relative';

        let displayValue = '';
        let displayType = '';

        switch (cond.type) {
            case 'CART_TOTAL':
                displayType = 'قيمة سلة المشتريات';
                displayValue = `من ${cond.value.min || 0} إلى ${cond.value.max || 'لا يوجد حد'}`;
                break;
            case 'CART_QUANTITY':
                displayType = 'عدد المنتجات في السلة';
                displayValue = `من ${cond.value.min || 0} إلى ${cond.value.max || 'لا يوجد حد'}`;
                break;
            case 'PRODUCTS':
                displayType = 'منتجات محددة';
                displayValue = `عدد المنتجات: ${cond.value.product_ids ? cond.value.product_ids.length : 0}`;
                break;
            default:
                displayType = cond.type;
                displayValue = JSON.stringify(cond.value);
        }

        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong class="text-primary">${displayType}</strong>
                    <div class="text-muted small mt-1">${displayValue}</div>
                </div>
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeCondition(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        container.appendChild(div);
    });
}

function removeCondition(index) {
    currentConditions.splice(index, 1);
    renderConditionsList();
}

// Mock Data for Locations
const MOCK_LOCATIONS = {
    "SA": { name: "المملكة العربية السعودية", cities: ["الرياض", "جدة", "الدمام", "مكة المكرمة", "المدينة المنورة"] },
    "AE": { name: "الإمارات العربية المتحدة", cities: ["دبي", "أبو ظبي", "الشارقة"] },
    "EG": { name: "جمهورية مصر العربية", cities: ["القاهرة", "الإسكندرية", "الجيزة"] },
    "KW": { name: "الكويت", cities: ["مدينة الكويت", "حولي"] }
};

// Helper: Populate Cities based on Country
function updateCityOptions(countrySelectId, citySelectId) {
    const countryCode = document.getElementById(countrySelectId).value;
    const citySelect = document.getElementById(citySelectId);
    citySelect.innerHTML = '<option value="" selected disabled>اختر المدينة...</option>';

    if (countryCode && MOCK_LOCATIONS[countryCode]) {
        MOCK_LOCATIONS[countryCode].cities.forEach(city => {
            const opt = document.createElement('option');
            opt.value = city;
            opt.textContent = city;
            citySelect.appendChild(opt);
        });
        citySelect.disabled = false;
    } else {
        citySelect.disabled = true;
    }
}

// Render Inputs inside Modal based on selected Type
async function renderConditionInputs() {
    const checkedRadio = document.querySelector('input[name="conditionType"]:checked');
    const type = checkedRadio ? checkedRadio.value : null;
    if (!type) {
        document.getElementById('conditionInputsContainer').innerHTML = ''; // Clear if nothing selected
        return;
    }
    const container = document.getElementById('conditionInputsContainer');
    container.innerHTML = '';

    if (type === 'CART_TOTAL' || type === 'CART_QUANTITY') {
        container.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <label class="form-label">الحد الأدنى</label>
                    <input type="number" class="form-control" id="condMin" value="0">
                </div>
                <div class="col-6">
                    <label class="form-label">الحد الأعلى</label>
                    <input type="number" class="form-control" id="condMax" placeholder="اتركه فارغاً للا محدود">
                </div>
            </div>
        `;
    } else if (type === 'PRODUCTS') {
        container.innerHTML = `
            <div class="alert alert-info small">
                سيتم تطبيق القيد إذا كانت السلة تحتوي على أي من المنتجات المختارة.
            </div>
            <button type="button" class="btn btn-outline-secondary w-100 mb-2" onclick="openProductModal()">
                <i class="fas fa-plus"></i> إضافة منتج
            </button>
            <div class="card p-2 bg-light ${selectedProductsForInput.length ? '' : 'd-none'}" id="selectedProdsList">
                 ${selectedProductsForInput.length ? renderSelectedProductsPreview() : '<small class="text-muted">لم يتم اختيار منتجات</small>'}
            </div>
        `;
    } else if (type === 'ORDER_TIME') {
        container.innerHTML = `
            <div class="mb-3">
                <label class="form-label">الأيام المحددة</label>
                <div class="d-flex flex-wrap gap-2 text-end" dir="rtl">
                    ${['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'].map((day, i) => `
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${i}" id="day_${i}" checked>
                            <label class="form-check-label" for="day_${i}">${day}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="row">
                <div class="col-6">
                    <label class="form-label">وقت البدء</label>
                    <input type="time" class="form-control" id="startTime">
                </div>
                <div class="col-6">
                    <label class="form-label">وقت الانتهاء</label>
                    <input type="time" class="form-control" id="endTime">
                </div>
            </div>
        `;
    } else if (type === 'SALES_CHANNEL') {
        container.innerHTML = `
            <label class="form-label">قنوات البيع</label>
            <select class="form-select" id="salesChannels" multiple size="3">
                <option value="store">المتجر الإلكتروني</option>
                <option value="app">تطبيق الجوال</option>
                <option value="pos">نقاط البيع (POS)</option>
            </select>
            <div class="form-text">اضغط Ctrl لتحديد أكثر من قناة</div>
        `;
    } else if (type === 'CART_WEIGHT') {
        container.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <label class="form-label">الحد الأدنى للوزن (كجم)</label>
                    <input type="number" class="form-control" id="weightMin" step="0.1" value="0">
                </div>
                <div class="col-6">
                    <label class="form-label">الحد الأعلى للوزن (كجم)</label>
                    <input type="number" class="form-control" id="weightMax" step="0.1" placeholder="لا محدود">
                </div>
            </div>
        `;
    } else if (type === 'CUSTOMER_GROUPS') {
        // Fetch groups dynamically
        container.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> جاري تحميل المجموعات...</div>';
        try {
            const res = await fetch('/api/customers/groups');
            const groups = await res.json();

            container.innerHTML = `
                <div class="mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="groupMode" id="groupInclude" value="include" checked>
                        <label class="form-check-label" for="groupInclude">مجموعات العملاء المختارة فقط</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="groupMode" id="groupExclude" value="exclude">
                        <label class="form-check-label" for="groupExclude">جميع المجموعات باستثناء المختارة</label>
                    </div>
                </div>
                <select class="form-select" id="customerGroups" multiple size="4">
                    ${groups.map(g => `<option value="${g.id}">${g.name}</option>`).join('')}
                </select>
                <div class="form-text">اضغط Ctrl لتحديد أكثر من مجموعة</div>
            `;
        } catch (e) {
            container.innerHTML = '<div class="text-danger">فشل تحميل المجموعات</div>';
        }
    } else if (type === 'PRODUCT_CATEGORY') {
        container.innerHTML = `
            <div class="mb-3">
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="catMode" id="catInclude" value="include" checked>
                    <label class="form-check-label" for="catInclude">تضمين التصنيفات المختارة</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="catMode" id="catExclude" value="exclude">
                    <label class="form-check-label" for="catExclude">استثناء التصنيفات المختارة</label>
                </div>
            </div>
            <button type="button" class="btn btn-outline-secondary w-100 mb-2" onclick="openCategoryModal()">
                <i class="fas fa-plus"></i> إضافة تصنيف
            </button>
            <div class="card p-2 bg-light ${selectedCategoriesForInput.length ? '' : 'd-none'}" id="selectedCatsList">
                ${selectedCategoriesForInput.length ? renderSelectedCategoriesPreview() : '<small class="text-muted">لم يتم اختيار تصنيفات</small>'}
            </div>
        `;
    } else if (type === 'PRODUCT_TYPE') {
        container.innerHTML = `
            <div class="mb-3">
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="ptMode" id="ptInclude" value="include" checked>
                    <label class="form-check-label" for="ptInclude">نوع المنتج المختار فقط</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="ptMode" id="ptExclude" value="exclude">
                    <label class="form-check-label" for="ptExclude">جميع أنواع المنتجات، باستثناء المختارة</label>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">اختر نوع المنتج</label>
                <select class="form-select" id="productTypeSelect">
                    <option value="" selected disabled>اختر النوع...</option>
                    <option value="Physical">منتج فعلي (Physical)</option>
                    <option value="Digital">منتج رقمي (Digital)</option>
                    <option value="Service">خدمة (Service)</option>
                    <option value="Food">طعام (Food)</option>
                </select>
            </div>
        `;
    } else if (type === 'COUPONS') {
        // Fetch coupons dynamically
        let optionsHtml = '<option disabled>جاري التحميل...</option>';
        try {
            const resp = await fetch('/api/marketing/coupons');
            if (resp.ok) {
                const coupons = await resp.json();
                optionsHtml = coupons.length ? coupons.map(c => `<option value="${c.code}">${c.code} (${c.discount_type})</option>`).join('') : '<option disabled>لا توجد قسائم متاحة</option>';
            } else {
                optionsHtml = '<option disabled class="text-danger">فشل تحميل القسائم</option>';
            }
        } catch (e) {
            console.error(e);
            optionsHtml = '<option disabled>خطأ في الاتصال</option>';
        }

        container.innerHTML = `
             <div class="mb-3">
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="cpnMode" id="cpnInclude" value="include" checked>
                    <label class="form-check-label" for="cpnInclude">أكواد الخصم المختارة فقط</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="cpnMode" id="cpnExclude" value="exclude">
                    <label class="form-check-label" for="cpnExclude">جميع أكواد الخصم، باستثناء المختارة</label>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">اختر أكواد الخصم</label>
                <select class="form-select" id="couponSelect" multiple size="4">
                    ${optionsHtml}
                </select>
                <div class="form-text">اضغط Ctrl لتحديد متعدد</div>
            </div>
        `;
    } else if (type === 'CUSTOMER_LOCATION') {
        const countryOptions = Object.keys(MOCK_LOCATIONS).map(code => `<option value="${code}">${MOCK_LOCATIONS[code].name}</option>`).join('');
        container.innerHTML = `
             <div class="mb-3">
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="locMode" id="locInclude" value="include" checked>
                    <label class="form-check-label" for="locInclude">الدولة والمدينة المختارة فقط</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="locMode" id="locExclude" value="exclude">
                    <label class="form-check-label" for="locExclude">جميع الدول والمدن، باستثناء المختارة</label>
                </div>
            </div>
            <div class="row">
                <div class="col-6">
                    <label class="form-label">الدولة</label>
                    <select class="form-select" id="locCountry" onchange="updateCityOptions('locCountry', 'locCity')">
                        <option value="" selected disabled>اختر الدولة...</option>
                        ${countryOptions}
                    </select>
                </div>
                <div class="col-6">
                    <label class="form-label">المدينة</label>
                    <select class="form-select" id="locCity" disabled>
                        <option value="" selected disabled>اختر الدولة أولاً...</option>
                    </select>
                </div>
            </div>
        `;
    } else if (type === 'CUSTOMER_ORDER_COUNT') {
        container.innerHTML = `
            <div class="mb-3">
                <label class="form-label">عدد طلبات العميل</label>
                <input type="number" class="form-control" id="orderCountMax" placeholder="أقل من أو يساوي">
                <div class="form-text">سيتم تطبيق القيد إذا كان عدد طلبات العميل أقل من أو يساوي هذا الرقم.</div>
            </div>
        `;
    } else if (type === 'CUSTOMER_CANCELLED_ORDER_COUNT') {
        container.innerHTML = `
            <div class="mb-3">
                <label class="form-label">عدد الطلبات الملغاة</label>
                <input type="number" class="form-control" id="cancelledOrderCountMin" placeholder="أكبر من أو يساوي">
                <div class="form-text">سيتم تطبيق القيد إذا كان عدد طلبات العميل الملغاة أكبر من أو يساوي هذا الرقم.</div>
            </div>
        `;
    }
}

async function addConditionFromModal() {
    const checkedRadio = document.querySelector('input[name="conditionType"]:checked');
    const type = checkedRadio ? checkedRadio.value : null;
    if (!type) return;

    let value = {};

    if (type === 'CART_TOTAL' || type === 'CART_QUANTITY') {
        const min = document.getElementById('condMin').value;
        const max = document.getElementById('condMax').value;
        value = { min: parseFloat(min), max: max ? parseFloat(max) : null };
    } else if (type === 'PRODUCTS') {
        if (!selectedProductsForInput.length) { notifier.showToast('يرجى اختيار منتج واحد على الأقل', 'warning'); return; }
        value = { product_ids: selectedProductsForInput.map(p => p.id) };
    } else if (type === 'ORDER_TIME') {
        const days = Array.from(document.querySelectorAll('input[id^="day_"]:checked')).map(cb => parseInt(cb.value));
        const start = document.getElementById('startTime').value;
        const end = document.getElementById('endTime').value;
        value = { days: days, start_time: start, end_time: end };
    } else if (type === 'SALES_CHANNEL') {
        const channels = Array.from(document.getElementById('salesChannels').selectedOptions).map(o => o.value);
        value = { channels: channels };
    } else if (type === 'CART_WEIGHT') {
        const min = document.getElementById('weightMin').value;
        const max = document.getElementById('weightMax').value;
        value = { min: parseFloat(min), max: max ? parseFloat(max) : null };
    } else if (type === 'CUSTOMER_GROUPS') {
        const mode = document.querySelector('input[name="groupMode"]:checked').value;
        const groups = Array.from(document.getElementById('customerGroups').selectedOptions).map(o => parseInt(o.value));
        value = { mode: mode, group_ids: groups };
    } else if (type === 'PRODUCT_CATEGORY') {
        const mode = document.querySelector('input[name="catMode"]:checked').value;
        if (!selectedCategoriesForInput.length) { notifier.showToast('يرجى اختيار تصنيف واحد على الأقل', 'warning'); return; }
        value = { mode: mode, category_ids: selectedCategoriesForInput.map(c => c.id) };
    } else if (type === 'PRODUCT_TYPE') {
        const mode = document.querySelector('input[name="ptMode"]:checked').value;
        const pType = document.getElementById('productTypeSelect').value;
        if (!pType) { notifier.showToast('يرجى اختيار نوع المنتج', 'warning'); return; }
        value = { mode: mode, product_type: pType };
    } else if (type === 'COUPONS') {
        const mode = document.querySelector('input[name="cpnMode"]:checked').value;
        const selectedOpts = Array.from(document.getElementById('couponSelect').selectedOptions).map(o => o.value);
        if (!selectedOpts.length) { notifier.showToast('يرجى اختيار كود خصم واحد على الأقل', 'warning'); return; }
        value = { mode: mode, coupons: selectedOpts };
    } else if (type === 'CUSTOMER_LOCATION') {
        const mode = document.querySelector('input[name="locMode"]:checked').value;
        const country = document.getElementById('locCountry').value;
        const city = document.getElementById('locCity').value;
        if (!country) { notifier.showToast('يرجى اختيار الدولة', 'warning'); return; }
        value = { mode: mode, country: country, city: city || null };
    } else if (type === 'CUSTOMER_ORDER_COUNT') {
        const max = document.getElementById('orderCountMax').value;
        if (!max) { notifier.showToast('يرجى إدخال العدد', 'warning'); return; }
        value = { max: parseInt(max) };
    } else if (type === 'CUSTOMER_CANCELLED_ORDER_COUNT') {
        const min = document.getElementById('cancelledOrderCountMin').value;
        if (!min) { notifier.showToast('يرجى إدخال العدد', 'warning'); return; }
        value = { min: parseInt(min) };
    }


    currentConditions.push({
        type: type,
        operator: 'EQ', // Default
        value: value
    });

    renderConditionsList();

    // Close Modal
    const modalEl = document.getElementById('addConditionModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();

    // Reset inputs
    document.getElementById('conditionInputsContainer').innerHTML = '';
    document.querySelectorAll('input[name="conditionType"]').forEach(el => el.checked = false);

    // Reset inputs state
    selectedCategoriesForInput = [];
    selectedProductsForInput = [];
}

// ----------------------------------------------------------------------
// CATEGORY LOGIC
// ----------------------------------------------------------------------

let catPage = 1;
let catSearch = '';
let catIsLoading = false;
let catHasMore = true;

async function fetchCategoryPage(page = 1, search = '') {
    try {
        const query = new URLSearchParams({ page: page, page_size: 20 });
        if (search) query.append('search', search);

        const response = await fetch(`/catalog/api/categories/list?${query.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch categories');
        return await response.json();
    } catch (e) {
        console.error(e);
        notifier.showToast('فشل تحميل التصنيفات', 'error');
        return { items: [], total: 0 };
    }
}

async function openCategoryModal() {
    tempSelectedCategoryIds = new Set(selectedCategoriesForInput.map(c => c.id));

    const modalEl = document.getElementById('categorySelectorModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    // Reset State
    catPage = 1;
    catSearch = '';
    catHasMore = true;
    cachedCategories = []; // We maintain a flat list of loaded cats for selection logic

    // Setup Search Logic
    const searchInput = document.getElementById('categorySearchInput');
    searchInput.value = '';
    searchInput.onkeyup = debounce(async (e) => {
        catSearch = e.target.value;
        catPage = 1;
        catHasMore = true;
        document.getElementById('categorySelectorList').innerHTML = ''; // Clear current list
        await loadMoreCategories();
    }, 500);

    // Initial Load
    document.getElementById('categorySelectorList').innerHTML = '';
    await loadMoreCategories();

    // Scroll Listener for "Load More" - simplified to a button for now or auto-detect end
    // For now, let's append a load more button at the bottom if hasMore
}

async function loadMoreCategories() {
    if (catIsLoading || !catHasMore) return;

    const listContainer = document.getElementById('categorySelectorList');

    // Remove "Load More" button if exists
    const loadMoreBtn = document.getElementById('catLoadMoreBtn');
    if (loadMoreBtn) loadMoreBtn.remove();

    // Add Loader
    const loader = document.createElement('div');
    loader.id = 'catLoader';
    loader.className = 'text-center py-3';
    loader.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div>';
    listContainer.appendChild(loader);

    catIsLoading = true;
    const data = await fetchCategoryPage(catPage, catSearch);
    catIsLoading = false;
    loader.remove();

    if (!data.items.length && catPage === 1) {
        listContainer.innerHTML = '<div class="p-3 text-center text-muted">لا توجد تصنيفات</div>';
        catHasMore = false;
        return;
    }

    if (data.items.length < 20) catHasMore = false;
    else catPage++;

    data.items.forEach(cat => {
        // Add to cache to support saving selection
        if (!cachedCategories.find(c => c.id === cat.id)) cachedCategories.push(cat);

        const isChecked = tempSelectedCategoryIds.has(cat.id);
        const label = document.createElement('label');
        label.className = 'list-group-item d-flex gap-3 align-items-center';
        label.style.cursor = 'pointer';
        label.innerHTML = `
            <input class="form-check-input flex-shrink-0 category-check" type="checkbox" value="${cat.id}" 
                ${isChecked ? 'checked' : ''} style="font-size: 1.3em;">
            <span class="pt-1 form-checked-content w-100">
                <div class="d-flex justify-content-between">
                    <strong>${cat.name}</strong>
                    <!-- <span class="badge bg-light text-dark border">? منتج</span> -->
                </div>
            </span>
        `;

        label.querySelector('input').addEventListener('change', (e) => {
            if (e.target.checked) tempSelectedCategoryIds.add(cat.id);
            else tempSelectedCategoryIds.delete(cat.id);
        });

        listContainer.appendChild(label);
    });

    if (catHasMore) {
        const btn = document.createElement('button');
        btn.id = 'catLoadMoreBtn';
        btn.className = 'btn btn-link w-100 text-center text-decoration-none';
        btn.innerText = 'عرض المزيد...';
        btn.onclick = loadMoreCategories;
        listContainer.appendChild(btn);
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function saveCategorySelection() {
    // Map IDs back to objects (for display)
    selectedCategoriesForInput = [];
    if (cachedCategories) {
        cachedCategories.forEach(c => {
            if (tempSelectedCategoryIds.has(c.id)) {
                selectedCategoriesForInput.push(c);
            }
        });
    }

    // Update Preview in Main Form
    const container = document.getElementById('selectedCatsList');
    if (selectedCategoriesForInput.length > 0) {
        container.classList.remove('d-none');
        container.innerHTML = renderSelectedCategoriesPreview();
    } else {
        container.classList.add('d-none');
    }

    // Close Modal
    const modalEl = document.getElementById('categorySelectorModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();
}

function renderSelectedCategoriesPreview() {
    // Simple table or list
    let html = `
        <table class="table table-sm table-borderless mb-0">
            <thead>
                <tr class="text-muted" style="font-size:0.85em;">
                    <th>الاسم</th>
                    <th>عدد المنتجات</th>
                    <th style="width:30px;"></th>
                </tr>
            </thead>
            <tbody>
    `;
    selectedCategoriesForInput.forEach((cat, idx) => {
        html += `
            <tr>
                <td>${cat.name}</td>
                <td>${cat.product_count || 0}</td>
                <td>
                    <button type="button" class="btn btn-link text-danger p-0 btn-sm" onclick="removeCategoryFromInput(${idx})">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    html += '</tbody></table>';
    return html;
}

function removeCategoryFromInput(idx) {
    selectedCategoriesForInput.splice(idx, 1);
    const container = document.getElementById('selectedCatsList');
    if (selectedCategoriesForInput.length > 0) {
        container.innerHTML = renderSelectedCategoriesPreview();
    } else {
        container.classList.add('d-none');
    }
}


// ----------------------------------------------------------------------
// PRODUCT LOGIC
// ----------------------------------------------------------------------

async function fetchProducts() {
    if (cachedProducts) return cachedProducts;
    try {
        const response = await fetch('/catalog/api/products?page=1&page_size=100'); // Limit to 100 for MVP selector
        if (!response.ok) throw new Error('Failed to fetch products');
        const data = await response.json();
        cachedProducts = data.items; // List of products
        return cachedProducts;
    } catch (e) {
        console.error(e);
        notifier.showToast('فشل تحميل المنتجات', 'error');
        return [];
    }
}

async function openProductModal() {
    tempSelectedProductIds = new Set(selectedProductsForInput.map(p => p.id));

    const modalEl = document.getElementById('productSelectorModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    const tbody = document.getElementById('productSelectorTableBody');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4"><div class="spinner-border text-primary"></div></td></tr>';

    const products = await fetchProducts();
    tbody.innerHTML = '';

    if (!products.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">لا توجد منتجات</td></tr>';
        return;
    }

    products.forEach(prod => {
        const isChecked = tempSelectedProductIds.has(prod.id);
        const tr = document.createElement('tr');

        const imgUrl = prod.main_image_url || '/static/images/placeholder.png'; // Fallback
        const price = prod.min_price ? `${prod.min_price} ر.س` : '-';

        tr.innerHTML = `
            <td>
                <input class="form-check-input product-check" type="checkbox" value="${prod.id}" ${isChecked ? 'checked' : ''}>
            </td>
            <td>
                <img src="${imgUrl}" class="rounded" style="width: 32px; height: 32px; object-fit: cover;">
            </td>
            <td>
                <div class="fw-bold">${prod.name}</div>
                <small class="text-muted">${prod.slug}</small>
            </td>
            <td>${price}</td>
        `;

        tr.querySelector('input').addEventListener('change', (e) => {
            if (e.target.checked) tempSelectedProductIds.add(prod.id);
            else tempSelectedProductIds.delete(prod.id);
        });

        tbody.appendChild(tr);
    });

    // Search Logic
    const searchInput = document.getElementById('productSearchInput');
    searchInput.onkeyup = () => {
        const term = searchInput.value.toLowerCase();
        Array.from(tbody.rows).forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }
}

function saveProductSelection() {
    selectedProductsForInput = [];
    if (cachedProducts) {
        cachedProducts.forEach(p => {
            if (tempSelectedProductIds.has(p.id)) {
                selectedProductsForInput.push(p);
            }
        });
    }

    const container = document.getElementById('selectedProdsList');
    if (selectedProductsForInput.length > 0) {
        container.classList.remove('d-none');
        container.innerHTML = renderSelectedProductsPreview();
    } else {
        container.classList.add('d-none');
    }

    const modalEl = document.getElementById('productSelectorModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();
}

function renderSelectedProductsPreview() {
    let html = `
        <table class="table table-sm table-borderless mb-0">
            <thead>
                <tr class="text-muted" style="font-size:0.85em;">
                    <th></th>
                    <th>الاسم</th>
                    <th>السعر</th>
                    <th style="width:30px;"></th>
                </tr>
            </thead>
            <tbody>
    `;
    selectedProductsForInput.forEach((prod, idx) => {
        const imgUrl = prod.main_image_url || '/static/images/placeholder.png';
        const price = prod.min_price ? `${prod.min_price} ر.س` : '-';
        html += `
            <tr>
                <td style="width:40px;"><img src="${imgUrl}" class="rounded" style="width:24px;height:24px;"></td>
                <td>${prod.name}</td>
                <td>${price}</td>
                <td>
                    <button type="button" class="btn btn-link text-danger p-0 btn-sm" onclick="removeProductFromInput(${idx})">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    html += '</tbody></table>';
    return html;
}

function removeProductFromInput(idx) {
    selectedProductsForInput.splice(idx, 1);
    const container = document.getElementById('selectedProdsList');
    if (selectedProductsForInput.length > 0) {
        container.innerHTML = renderSelectedProductsPreview();
    } else {
        container.classList.add('d-none');
    }
}

window.openCategoryModal = openCategoryModal;
window.openProductModal = openProductModal;
window.removeCategoryFromInput = removeCategoryFromInput;
window.removeProductFromInput = removeProductFromInput;

async function saveConstraint() {
    const name = document.getElementById('constraintName').value;
    if (!name) {
        notifier.showToast('يرجى إدخال اسم القيد', 'warning');
        return;
    }

    const type = document.getElementById('constraintType').value; // 'shipping' or 'payment'
    const isActive = document.getElementById('isActive').checked;

    let methodIds = [];
    if (type === 'shipping') {
        const select = document.getElementById('shippingCompanies');
        methodIds = Array.from(select.selectedOptions).map(opt => opt.value);
        if (methodIds.length === 0) {
            notifier.showToast('يرجى اختيار شركة شحن واحدة على الأقل', 'warning');
            return;
        }
    } else {
        const select = document.getElementById('paymentMethods');
        methodIds = Array.from(select.selectedOptions).map(opt => opt.value);
        if (methodIds.length === 0) {
            notifier.showToast('يرجى اختيار وسيلة دفع واحدة على الأقل', 'warning');
            return;
        }
    }

    if (currentConditions.length === 0) {
        notifier.showToast('يرجى إضافة شرط واحد على الأقل', 'warning');
        return;
    }

    const isCustomError = document.getElementById('isCustomErrorEnabled').checked;
    const customMsg = document.getElementById('customErrorMessage').value;

    const payload = {
        name: name,
        is_active: isActive,
        [type === 'shipping' ? 'shipping_company_ids' : 'payment_method_ids']: methodIds,
        is_custom_error_enabled: isCustomError,
        custom_error_message: isCustomError ? customMsg : null,
        conditions: currentConditions
    };

    const method = isEditMode ? 'PUT' : 'POST';
    const url = isEditMode ? `/api/settings/constraints/${type}/${currentConstraintId}` : `/api/settings/constraints/${type}`;

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to save');

        notifier.showToast('تم حفظ القيد بنجاح', 'success');

        setTimeout(() => {
            window.location.href = '/settings/constraints';
        }, 1000);

    } catch (error) {
        console.error(error);
        notifier.showToast('حدث خطأ أثناء الحفظ', 'error');
    }
}

// Global expose for HTML onclicks
window.removeCondition = removeCondition;
window.deleteConstraint = deleteConstraint;
