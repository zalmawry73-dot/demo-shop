document.addEventListener('DOMContentLoaded', () => {
    loadGroups();
});

let groupsData = [];
let groupToDeleteId = null;

async function loadGroups() {
    try {
        const response = await fetch('/api/settings/team/groups');
        if (!response.ok) throw new Error('Failed to load groups');

        groupsData = await response.json();
        renderTable(groupsData);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('groupsTableBody').innerHTML = `
            <tr>
                <td colspan="3" class="text-center p-4 text-danger">
                    <i class="fa-solid fa-circle-exclamation me-1"></i> فشل تحميل البيانات
                </td>
            </tr>
        `;
    }
}

function renderTable(groups) {
    const tbody = document.getElementById('groupsTableBody');
    tbody.innerHTML = '';

    if (groups.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center p-5">
                    <div class="text-muted mb-3 opacity-50">
                        <i class="fa-solid fa-users-gear fa-3x"></i>
                    </div>
                    <h6 class="fw-bold">لا توجد مجموعات عمل</h6>
                    <p class="text-muted small">قم بإنشاء مجموعة جديدة لتنظيم صلاحيات فريقك.</p>
                    <a href="/settings/team/groups/create" class="btn btn-sm btn-primary">
                        <i class="fa-solid fa-plus me-1"></i> إنشاء مجموعة نوية
                    </a>
                </td>
            </tr>
        `;
        return;
    }

    groups.forEach(group => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="p-3 ps-4">
                <div class="fw-bold text-dark">${group.name}</div>
                <small class="text-muted">${getPermissionsCount(group.permissions)} صلاحيات</small>
            </td>
            <td class="p-3">
                <div class="d-flex align-items-center">
                    <span class="badge bg-light text-dark border rounded-pill px-3 py-2">
                        <i class="fa-regular fa-user me-1"></i> ${group.users_count} مستخدم
                    </span>
                </div>
            </td>
            <td class="p-3 text-end pe-4">
                <div class="dropdown">
                    <button class="btn btn-light btn-sm rounded-circle" type="button" data-bs-toggle="dropdown">
                        <i class="fa-solid fa-ellipsis-vertical"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end border-0 shadow">
                        <li><a class="dropdown-item" href="/settings/team/groups/${group.id}/edit"><i class="fa-regular fa-pen-to-square me-2 text-primary"></i> تعديل</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" onclick="promptDelete(${group.id})"><i class="fa-regular fa-trash-can me-2"></i> حذف</a></li>
                    </ul>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function getPermissionsCount(permissions) {
    // Determine count roughly based on keys in the permissions dict
    if (!permissions) return 0;
    // This is a naive count, if permissions is deep structure we might need traversal
    // Assuming simple structure for now or keys of modules
    return Object.keys(permissions).length;
}

function promptDelete(id) {
    groupToDeleteId = id;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
    if (!groupToDeleteId) return;

    // Disable button
    const btn = document.getElementById('confirmDeleteBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحذف...';

    try {
        const response = await fetch(`/api/settings/team/groups/${groupToDeleteId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete');

        // Hide Modal
        const modalEl = document.getElementById('deleteModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();

        // Reload
        if (window.notifier) window.notifier.showToast('تم حذف المجموعة بنجاح', 'success');
        loadGroups();

    } catch (error) {
        console.error('Error:', error);
        if (window.notifier) window.notifier.showToast('فشل حذف المجموعة', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
        groupToDeleteId = null;
    }
});
