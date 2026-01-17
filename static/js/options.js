const OptionsManager = {
    init() {
        this.loadOptions();
    },

    async loadOptions() {
        const tbody = document.getElementById('optionsTableBody');
        const loading = document.getElementById('loadingState');
        const empty = document.getElementById('emptyState');
        const table = document.getElementById('optionsTable');

        try {
            tbody.innerHTML = '';
            loading.style.display = 'block';
            table.style.display = 'none';
            empty.style.display = 'none';

            const response = await axios.get('/catalog/api/attributes');
            const options = response.data;

            loading.style.display = 'none';

            if (options.length === 0) {
                empty.style.display = 'block';
                return;
            }

            table.style.display = 'table';
            options.forEach(opt => {
                const tr = document.createElement('tr');

                // Format values badge
                const valuesHtml = opt.values.map(v =>
                    `<span class="badge" style="background:#f1f5f9; color:#334155; margin-right:4px; font-weight:normal">${v.value}</span>`
                ).slice(0, 5).join('');

                const extraCount = opt.values.length > 5 ? ` <span style="font-size:0.8rem; color:#94a3b8">+${opt.values.length - 5}</span>` : '';

                tr.innerHTML = `
                    <td><strong>${opt.name}</strong></td>
                    <td>${this.getTypeLabel(opt.type)}</td>
                    <td>${valuesHtml}${extraCount}</td>
                    <td>${new Date(opt.created_at).toLocaleDateString('ar-SA')}</td>
                    <td>
                        <button class="btn-icon" onclick="window.location.href='/catalog/options/${opt.id}/form'" title="تعديل">
                            <i class="fa-solid fa-edit"></i>
                        </button>
                        <button class="btn-icon delete" onclick="OptionsManager.deleteOption('${opt.id}')" title="حذف">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

        } catch (error) {
            console.error('Error loading options:', error);
            loading.style.display = 'none';
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:red">حدث خطأ أثناء تحميل البيانات</td></tr>';
            table.style.display = 'table';
        }
    },

    getTypeLabel(type) {
        const map = {
            'text': 'نص (زر)',
            'color': 'لون',
            'image': 'صورة'
        };
        return map[type] || type;
    },

    async deleteOption(id) {
        if (!await window.notifier.showConfirm('هل أنت متأكد من حذف هذا الخيار؟ سيتم إزالته من جميع المنتجات المرتبطة.')) return;

        try {
            await axios.delete(`/catalog/api/attributes/${id}`);
            window.notifier.showToast('تم الحذف بنجاح', 'success');
            this.loadOptions(); // Reload
        } catch (error) {
            console.error("Error deleting option:", error);
            window.notifier.showToast('حدث خطأ أثناء الحذف', 'error');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    OptionsManager.init();
});
