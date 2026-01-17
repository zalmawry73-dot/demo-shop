const CustomFieldsManager = {
    modal: null,

    init() {
        this.modal = new bootstrap.Modal(document.getElementById('fieldModal'));
        this.loadData();
    },

    async loadData() {
        const tbody = document.getElementById('fieldsTableBody');
        const loading = document.getElementById('loadingState');

        tbody.innerHTML = '';
        loading.style.display = 'block';

        try {
            const response = await axios.get('/catalog/api/custom-fields');
            const data = response.data;

            loading.style.display = 'none';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px">لا توجد حقول مخصصة</td></tr>';
                return;
            }

            data.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:bold">${item.name}</td>
                    <td style="font-family:monospace; direction:ltr; text-align:right">${item.key}</td>
                    <td><span class="badge bg-light text-dark border">${item.type}</span></td>
                    <td>${item.is_required ? '<i class="fa-solid fa-check text-success"></i>' : '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="CustomFieldsManager.edit('${item.id}')"><i class="fa-solid fa-edit"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="CustomFieldsManager.delete('${item.id}')"><i class="fa-solid fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

        } catch (error) {
            console.error('Error loading fields:', error);
            loading.style.display = 'none';
            tbody.innerHTML = `<tr><td colspan="5" class="text-danger text-center">حدث خطأ أثناء تحميل البيانات</td></tr>`;
        }
    },

    openModal() {
        document.getElementById('fieldForm').reset();
        document.getElementById('fieldId').value = '';
        document.getElementById('modalTitle').textContent = 'حقل جديد';
        document.getElementById('fieldKey').disabled = false;
        this.modal.show();
    },

    async edit(id) {
        try {
            // Find item from UI or fetch? Fetching for safety
            // Since we don't have get-by-id easily exposed in JS list (optimization), we can reload or find in DOM if we stored data. 
            // For simplicity, let's reuse the list data if we had it, but here I'll just rely on the fact that I should probably have stored them.
            // Let's quick fetch list again or filter. 
            // Better: fetch list again or just implement get-by-id in backend (which we have).
            // Actually, we do not have a JS local store. I will refactor later if needed.
            // Let's iterate the list from API call again or reload. 
            // Re-fetching full list for 1 item is ok for small admin panels.
            const response = await axios.get('/catalog/api/custom-fields');
            const item = response.data.find(x => x.id === id);

            if (!item) return;

            document.getElementById('fieldId').value = item.id;
            document.getElementById('fieldName').value = item.name;
            document.getElementById('fieldKey').value = item.key;
            document.getElementById('fieldKey').disabled = true; // Key cannot be changed
            document.getElementById('fieldType').value = item.type;
            document.getElementById('fieldRequired').checked = item.is_required;

            document.getElementById('modalTitle').textContent = 'تعديل حقل';
            this.modal.show();
        } catch (e) {
            console.error(e);
        }
    },

    async save() {
        const id = document.getElementById('fieldId').value;
        const data = {
            name: document.getElementById('fieldName').value,
            key: document.getElementById('fieldKey').value,
            type: document.getElementById('fieldType').value,
            is_required: document.getElementById('fieldRequired').checked
        };

        if (!data.name || !data.key) {
            Swal.fire('خطأ', 'يرجى تعبئة الحقول المطلوبة', 'error');
            return;
        }

        try {
            if (id) {
                await axios.put(`/catalog/api/custom-fields/${id}`, data);
            } else {
                await axios.post('/catalog/api/custom-fields', data);
            }
            this.modal.hide();
            this.loadData();
            Swal.fire('تم', 'تم الحفظ بنجاح', 'success');
        } catch (error) {
            Swal.fire('خطأ', error.response?.data?.detail || 'حدث خطأ', 'error');
        }
    },

    async delete(id) {
        const result = await Swal.fire({
            title: 'هل أنت متأكد؟',
            text: "سيت يتم حذف هذا الحقل وجميع القيم المرتبطة به من المنتجات!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'نعم، احذف',
            cancelButtonText: 'إلغاء'
        });

        if (result.isConfirmed) {
            try {
                await axios.delete(`/catalog/api/custom-fields/${id}`);
                this.loadData();
                Swal.fire('تم الحلذف', '', 'success');
            } catch (error) {
                Swal.fire('خطأ', 'لم يتم الحذف', 'error');
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    CustomFieldsManager.init();
});
