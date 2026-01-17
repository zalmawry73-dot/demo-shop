// Permissions Structure Definition matchin Store structure
const PERMISSIONS_TREE = [
    {
        key: 'home',
        label: 'الرئيسية',
        children: [
            { key: 'view_home', label: 'عرض الرئيسية' }
        ]
    },
    {
        key: 'orders',
        label: 'الطلبات',
        children: [
            { key: 'view_orders', label: 'الطلبات' },
            { key: 'create_orders', label: 'إنشاء طلب' },
            { key: 'edit_orders', label: 'تعديل الطلبات' },
            { key: 'drafts', label: 'المسودات' },
            { key: 'abandoned', label: 'السلات المتروكة' }
        ]
    },
    {
        key: 'products',
        label: 'المنتجات',
        children: [
            { key: 'view_products', label: 'جميع المنتجات' },
            { key: 'create_product', label: 'إضافة منتج' },
            { key: 'edit_product', label: 'تعديل منتج' },
            { key: 'delete_product', label: 'حذف منتج' },
            { key: 'services', label: 'الخدمات' },
            { key: 'inventory', label: 'المخزون' }
        ]
    },
    {
        key: 'customers',
        label: 'العملاء',
        children: [
            { key: 'view_customers', label: 'قائمة العملاء' },
            { key: 'groups', label: 'مجموعات العملاء' }
        ]
    },
    {
        key: 'analytics',
        label: 'التحليلات',
        children: [
            { key: 'view_analytics', label: 'عرض التقارير' }
        ]
    },
    {
        key: 'marketing',
        label: 'التسويق',
        children: [
            { key: 'coupons', label: 'كوبونات التخفيض' },
            { key: 'offers', label: 'العروض الخاصة' },
            { key: 'campaigns', label: 'الحملات التسويقية' }
        ]
    },
    {
        key: 'settings',
        label: 'الإعدادات',
        children: [
            { key: 'general_settings', label: 'الإعدادات الأساسية' },
            { key: 'payment_methods', label: 'طرق الدفع' },
            { key: 'shipping_options', label: 'خيارات الشحن' },
            { key: 'team', label: 'فريق العمل' },
            { key: 'roles', label: 'الصلاحيات (هذه الصفحة)' }
        ]
    }
];

let selectedUsers = new Set();
let fetchedUsers = [];
let currentGroupId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Check if edit mode
    const path = window.location.pathname;
    const match = path.match(/\/settings\/team\/groups\/(\d+)\/edit/);
    if (match) {
        currentGroupId = match[1];
        document.querySelector('.page-title').innerText = 'تعديل مجموعة';
        document.getElementById('groupId').value = currentGroupId;
    }

    renderPermissionsTree();
    fetchUsers();

    if (currentGroupId) {
        loadGroupData(currentGroupId);
    }

    // Search filter for users
    document.getElementById('userSearchInput').addEventListener('input', (e) => {
        renderUsersList(e.target.value);
    });
});

function renderPermissionsTree() {
    const container = document.getElementById('permissionsAccordion');
    container.innerHTML = '';

    PERMISSIONS_TREE.forEach((module, index) => {
        const itemId = `collapse_${module.key}`;

        const html = `
            <div class="accordion-item border-0 border-bottom">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed bg-white shadow-none" type="button" data-bs-toggle="collapse" data-bs-target="#${itemId}">
                        <div class="form-check">
                            <input class="form-check-input module-checkbox" type="checkbox" data-module="${module.key}" 
                                onclick="event.stopPropagation(); toggleModule('${module.key}', this.checked)">
                            <label class="form-check-label fw-bold ms-2" onclick="event.stopPropagation()">
                                ${module.label}
                            </label>
                        </div>
                    </button>
                </h2>
                <div id="${itemId}" class="accordion-collapse collapse" data-bs-parent="#permissionsAccordion">
                    <div class="accordion-body ps-5">
                        <div class="row g-3">
                            ${module.children.map(child => `
                                <div class="col-md-4">
                                    <div class="form-check">
                                        <input class="form-check-input permission-checkbox" type="checkbox" 
                                            name="permissions" value="${child.key}" data-parent="${module.key}" 
                                            onchange="updateModuleCheckbox('${module.key}')">
                                        <label class="form-check-label text-muted">
                                            ${child.label}
                                        </label>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += html;
    });
}

function toggleModule(moduleKey, checked) {
    const checkboxes = document.querySelectorAll(`.permission-checkbox[data-parent="${moduleKey}"]`);
    checkboxes.forEach(cb => cb.checked = checked);
    checkSelectAllStatus();
}

function updateModuleCheckbox(moduleKey) {
    const checkboxes = document.querySelectorAll(`.permission-checkbox[data-parent="${moduleKey}"]`);
    const parentCb = document.querySelector(`.module-checkbox[data-module="${moduleKey}"]`);

    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const someChecked = Array.from(checkboxes).some(cb => cb.checked);

    parentCb.checked = allChecked;
    parentCb.indeterminate = someChecked && !allChecked;

    checkSelectAllStatus();
}

function toggleAllPermissions(checked) {
    document.querySelectorAll('.module-checkbox').forEach(cb => {
        cb.checked = checked;
        cb.indeterminate = false;
    });
    document.querySelectorAll('.permission-checkbox').forEach(cb => cb.checked = checked);
}

function checkSelectAllStatus() {
    const allModuleCbs = document.querySelectorAll('.module-checkbox');
    const selectAllCb = document.getElementById('selectAllPermissions');

    const allChecked = Array.from(allModuleCbs).every(cb => cb.checked);
    const someChecked = Array.from(allModuleCbs).some(cb => cb.checked || cb.indeterminate);

    selectAllCb.checked = allChecked;
    selectAllCb.indeterminate = someChecked && !allChecked;
}

async function fetchUsers() {
    try {
        const response = await fetch('/api/settings/team/users');
        if (response.ok) {
            fetchedUsers = await response.json();
            renderUsersList();
        }
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

function renderUsersList(filterText = '') {
    const container = document.getElementById('usersListContainer');
    container.innerHTML = '';

    const filtered = fetchedUsers.filter(u =>
        u.name.toLowerCase().includes(filterText.toLowerCase())
    );

    if (filtered.length === 0) {
        container.innerHTML = '<div class="text-center text-muted small p-2">لا يوجد مستخدمين</div>';
        return;
    }

    filtered.forEach(user => {
        // Skip if already selected
        if (selectedUsers.has(user.id)) return;

        const item = document.createElement('div');
        item.className = 'dropdown-item d-flex align-items-center gap-2 p-2 rounded cursor-pointer';
        item.onclick = (e) => {
            e.stopPropagation();
            addUser(user);
        };
        item.innerHTML = `
            <div class="bg-light rounded-circle d-flex align-items-center justify-content-center text-primary fw-bold" style="width: 32px; height: 32px">
                ${user.name.charAt(0)}
            </div>
            <span>${user.name}</span>
        `;
        container.appendChild(item);
    });
}

function addUser(user) {
    selectedUsers.add(user.id);
    renderSelectedUsers();
    renderUsersList(document.getElementById('userSearchInput').value);
}

function removeUser(userId) {
    selectedUsers.delete(userId);
    renderSelectedUsers();
    renderUsersList(document.getElementById('userSearchInput').value);
}

function renderSelectedUsers() {
    const container = document.getElementById('selectedUsersContainer');
    container.innerHTML = '';

    selectedUsers.forEach(userId => {
        const user = fetchedUsers.find(u => u.id === userId);
        if (!user) return;

        const tag = document.createElement('div');
        tag.className = 'badge bg-primary-subtle text-primary border border-primary-subtle d-flex align-items-center gap-2 px-3 py-2 rounded-pill';
        tag.innerHTML = `
            <span>${user.name}</span>
            <i class="fa-solid fa-xmark cursor-pointer hover-danger" onclick="removeUser(${user.id})"></i>
        `;
        container.appendChild(tag);
    });
}

async function loadGroupData(id) {
    try {
        const response = await fetch(`/api/settings/team/groups/${id}`);
        if (!response.ok) throw new Error('Failed to load group');

        const group = await response.json();

        document.getElementById('groupName').value = group.name;

        // Load Permissions
        if (group.permissions) {
            Object.keys(group.permissions).forEach(key => {
                const cb = document.querySelector(`.permission-checkbox[value="${key}"]`);
                if (cb && group.permissions[key]) {
                    cb.checked = true;
                    // Trigger update logic
                    const parent = cb.dataset.parent;
                    if (parent) updateModuleCheckbox(parent);
                }
            });
        }

        // Ideally we should also load assigned users
        if (group.users) {
            group.users.forEach(u => selectedUsers.add(u.id));
            renderSelectedUsers();
            renderUsersList();
        } else if (group.user_ids) {
            group.user_ids.forEach(uid => selectedUsers.add(uid));
            renderSelectedUsers();
            renderUsersList();
        }

    } catch (error) {
        console.error('Error loading group:', error);
        if (window.notifier) window.notifier.showToast('فشل تحميل بيانات المجموعة', 'error');
    }
}

async function saveGroup() {
    const name = document.getElementById('groupName').value.trim();
    if (!name) {
        if (window.notifier) window.notifier.showToast('يرجى إدخال اسم المجموعة', 'warning');
        return;
    }

    // Collect permissions
    const permissions = {};
    document.querySelectorAll('.permission-checkbox:checked').forEach(cb => {
        permissions[cb.value] = true;
    });

    const payload = {
        name: name,
        permissions: permissions,
        user_ids: Array.from(selectedUsers)
    };

    const btn = document.getElementById('saveBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحفظ...';

    try {
        const url = currentGroupId
            ? `/api/settings/team/groups/${currentGroupId}`
            : '/api/settings/team/groups';

        const method = currentGroupId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to save');
        }

        if (window.notifier) window.notifier.showToast('تم حفظ المجموعة بنجاح', 'success');

        // Redirect
        setTimeout(() => {
            window.location.href = '/settings/team/groups';
        }, 1000);

    } catch (error) {
        console.error('Error saving:', error);
        if (window.notifier) window.notifier.showToast(error.message, 'error');
        btn.disabled = false;
        btn.innerText = originalText;
    }
}
