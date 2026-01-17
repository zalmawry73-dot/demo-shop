const MovementsManager = {
    init() {
        this.loadData();
    },

    async loadData() {
        const tbody = document.getElementById('movementsTableBody');
        const loading = document.getElementById('loadingState');

        loading.style.display = 'block';
        tbody.innerHTML = '';

        try {
            const res = await axios.get('/api/movements', {
                params: {
                    limit: 100,
                    offset: 0
                }
            });
            const data = res.data;

            loading.style.display = 'none';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px">لا توجد حركات مسجلة</td></tr>';
                return;
            }

            data.forEach(item => {
                const tr = document.createElement('tr');

                // Format Date
                const date = moment(item.date).format('YYYY-MM-DD HH:mm');

                // Style Quantity
                let qtyClass = item.qty_change > 0 ? 'text-success' : 'text-danger';
                let qtySign = item.qty_change > 0 ? '+' : '';

                // Translate Reason
                const reasons = {
                    'new_order': 'طلب جديد',
                    'cancelled_order': 'طلب ملغى',
                    'manual_edit': 'تعديل يدوي',
                    'stock_take': 'جرد',
                    'transfer': 'نقل'
                };
                const reasonText = reasons[item.reason] || item.reason;

                tr.innerHTML = `
                    <td>${date}</td>
                    <td>
                        <div style="font-weight:bold">${item.product_name}</div>
                        <div style="font-size:0.85rem; color:#64748b">${item.sku}</div>
                    </td>
                    <td>${item.warehouse}</td>
                    <td><span class="badge bg-light text-dark border">${reasonText}</span></td>
                    <td class="${qtyClass}" style="font-weight:bold; direction:ltr">${qtySign}${item.qty_change}</td>
                    <td>${item.user}</td>
                `;
                tbody.appendChild(tr);
            });

        } catch (error) {
            console.error('Error loading movements:', error);
            loading.style.display = 'none';
            tbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center">حدث خطأ أثناء تحميل البيانات</td></tr>`;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    MovementsManager.init();
});
