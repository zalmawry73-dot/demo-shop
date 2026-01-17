
async function loadPagesList() {
    try {
        const response = await fetch('/api/settings/legal-pages');
        if (!response.ok) throw new Error('Failed to load pages');

        const pages = await response.json();
        const tbody = document.getElementById('pagesList');

        tbody.innerHTML = '';

        if (pages.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center py-5">لا توجد صفحات قانونية</td>
                </tr>
            `;
            return;
        }

        pages.forEach(page => {
            const tr = document.createElement('tr');

            // Status Badge
            const statusBadge = page.is_visible
                ? '<span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-2 rounded-pill">نشط</span>'
                : '<span class="badge bg-danger-subtle text-danger border border-danger-subtle px-3 py-2 rounded-pill">غير نشط</span>';

            tr.innerHTML = `
                <td class="ps-4 py-3">
                    <div class="d-flex align-items-center">
                        <div class="bg-light rounded p-2 text-primary me-3">
                            <i class="fa-regular fa-file-lines fa-lg"></i>
                        </div>
                        <div>
                            <div class="fw-bold text-dark">${page.title_ar}</div>
                            <div class="small text-muted">${page.title_en}</div>
                        </div>
                    </div>
                </td>
                <td class="py-3">
                    ${statusBadge}
                </td>
                <td class="pe-4 py-3 text-end">
                    <a href="/settings/legal-pages/${page.id}" class="btn btn-outline-primary btn-sm px-3">
                        <i class="fa-regular fa-pen-to-square me-1"></i> تعديل
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('Error loading pages:', error);
        if (window.notifier) window.notifier.showToast('فشل تحميل الصفحات', 'error');
    }
}

async function savePage(id) {
    const btn = document.getElementById('saveBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحفظ...';

    const payload = {
        title_ar: document.getElementById('titleAr').value,
        title_en: document.getElementById('titleEn').value,
        content_ar: document.getElementById('contentAr').value,
        content_en: document.getElementById('contentEn').value,
        is_visible: document.getElementById('isVisible').checked,
        is_customer_visible: document.getElementById('isCustomerVisible').checked
    };

    try {
        const response = await fetch(`/api/settings/legal-pages/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to save');

        if (window.notifier) window.notifier.showToast('تم حفظ التغييرات بنجاح', 'success');

    } catch (error) {
        console.error('Error saving page:', error);
        if (window.notifier) window.notifier.showToast('فشل حفظ التغييرات', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}
