
async function loadTeamMembers() {
    const tbody = document.getElementById('teamList');
    const emptyTemplate = document.getElementById('emptyStateTemplate');

    try {
        const response = await fetch('/api/settings/team/members');
        if (!response.ok) throw new Error('Failed to load members');

        const members = await response.json();
        tbody.innerHTML = '';

        if (members.length === 0) {
            tbody.innerHTML = emptyTemplate.innerHTML;
            return;
        }

        members.forEach(member => {
            const tr = document.createElement('tr');

            const groupName = member.group ? member.group.name : '<span class="text-danger">بدون صلاحيات</span>';
            const statusBadge = member.is_active
                ? '<span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-2 rounded-pill">نشط</span>'
                : '<span class="badge bg-danger-subtle text-danger border border-danger-subtle px-3 py-2 rounded-pill">غير نشط</span>';

            tr.innerHTML = `
                <td class="ps-4 py-3">
                    <div class="d-flex align-items-center">
                        <div class="bg-primary-subtle rounded-circle p-2 text-primary me-3 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px">
                             <span class="fw-bold">${getInitials(member.full_name || member.username)}</span>
                        </div>
                        <div>
                            <div class="fw-bold text-dark">${member.full_name || member.username}</div>
                            <div class="small text-muted">${groupName}</div>
                        </div>
                    </div>
                </td>
                <td class="py-3">
                    <div class="text-dark">${member.email}</div>
                    <div class="small text-muted" dir="ltr">${member.phone_number || '-'}</div>
                </td>
                <td class="py-3">
                    ${statusBadge}
                </td>
                <td class="pe-4 py-3 text-end">
                    <div class="dropdown">
                        <button class="btn btn-light btn-sm border" type="button" data-bs-toggle="dropdown">
                            <i class="fa-solid fa-ellipsis"></i>
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/settings/team/${member.id}/edit"><i class="fa-regular fa-pen-to-square me-2"></i>تعديل</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-danger" href="#" onclick="deleteMember(${member.id})"><i class="fa-regular fa-trash-can me-2"></i>حذف</a></li>
                        </ul>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('Error loading members:', error);
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-5">فشل تحميل البيانات</td></tr>`;
    }
}

async function loadGroups(selectedGroupId = null) {
    const select = document.getElementById('groupId');
    try {
        const response = await fetch('/api/settings/team/groups');
        const groups = await response.json();

        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.innerText = group.name;
            if (selectedGroupId && group.id == selectedGroupId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Failed to load groups", error);
    }
}

async function saveMember(mode, id = null) {
    const btn = document.getElementById('saveBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحفظ...';

    const payload = {
        full_name: document.getElementById('fullName').value,
        phone_number: document.getElementById('phoneNumber').value,
        email: document.getElementById('email').value,
        username: document.getElementById('username').value,
        group_id: document.getElementById('groupId').value ? parseInt(document.getElementById('groupId').value) : null,
        // pos_access: document.getElementById('posAccess').checked, // Not in schema yet, but logic placeholder
        role: "staff"
    };

    const password = document.getElementById('password').value;
    if (mode === 'create') {
        if (!password) {
            window.notifier.showToast("كلمة المرور مطلوبة", 'error');
            btn.disabled = false;
            btn.innerText = originalText;
            return;
        }
        payload.password = password;
    } else {
        if (password) payload.password = password;
        delete payload.username; // Usually verify identity before changing username, so better keep it immutable for now or handled separately
    }

    try {
        const url = mode === 'create' ? '/api/settings/team/members' : `/api/settings/team/members/${id}`;
        const method = mode === 'create' ? 'POST' : 'PUT';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to save');
        }

        window.notifier.showToast('تم الحفظ بنجاح', 'success');

        setTimeout(() => {
            window.location.href = '/settings/team';
        }, 1000);

    } catch (error) {
        console.error('Error saving:', error);
        window.notifier.showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

async function deleteMember(id) {
    if (!await window.notifier.showConfirm('هل أنت متأكد من حذف هذا العضو؟')) return;

    try {
        const response = await fetch(`/api/settings/team/members/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete');

        loadTeamMembers();
        window.notifier.showToast('تم الحذف بنجاح', 'success');

    } catch (error) {
        console.error('Error deleting:', error);
        window.notifier.showToast('فشل الحذف', 'error');
    }
}

function getInitials(name) {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
}
