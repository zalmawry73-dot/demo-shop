const ReviewsManager = {
    init() {
        this.loadReviews();
    },

    async loadReviews() {
        const tbody = document.getElementById('reviewsTableBody');
        const loading = document.getElementById('loadingState');
        const empty = document.getElementById('emptyState');
        const table = document.getElementById('reviewsTable');
        const statusFilter = document.getElementById('statusFilter').value;

        try {
            tbody.innerHTML = '';
            loading.style.display = 'block';
            table.style.display = 'none';
            empty.style.display = 'none';

            let url = '/catalog/api/reviews';
            if (statusFilter) {
                url += `?status=${statusFilter}`;
            }

            const response = await axios.get(url);
            const reviews = response.data;

            loading.style.display = 'none';

            if (reviews.length === 0) {
                empty.style.display = 'block';
                return;
            }

            table.style.display = 'table';
            reviews.forEach(review => {
                const tr = document.createElement('tr');

                // Stars HTML
                let stars = '';
                for (let i = 1; i <= 5; i++) {
                    stars += `<i class="fa-solid fa-star" style="color:${i <= review.rating ? '#fbbf24' : '#cbd5e1'}; font-size:0.8rem"></i>`;
                }

                // Status Badge
                let statusBadge = '';
                if (review.status === 'Approved') statusBadge = '<span class="badge success">مقبول</span>';
                else if (review.status === 'Rejected') statusBadge = '<span class="badge danger">مرفوض</span>';
                else statusBadge = '<span class="badge warning">معلق</span>';

                tr.innerHTML = `
                    <td><strong>${review.product_name || 'منتج محذوف'}</strong></td>
                    <td>${review.customer_name}</td>
                    <td><div style="display:flex; gap:2px">${stars}</div></td>
                    <td><div style="max-width:300px; white-space:wrap">${review.comment || '-'}</div></td>
                    <td>${statusBadge}</td>
                    <td>${new Date(review.created_at).toLocaleDateString('ar-SA')}</td>
                    <td>
                        ${review.status === 'Pending' ? `
                        <button class="btn-icon" style="color:#10b981" onclick="ReviewsManager.updateStatus('${review.id}', 'Approved')" title="قبول">
                            <i class="fa-solid fa-check"></i>
                        </button>
                        <button class="btn-icon" style="color:#ef4444" onclick="ReviewsManager.updateStatus('${review.id}', 'Rejected')" title="رفض">
                            <i class="fa-solid fa-times"></i>
                        </button>
                        ` : ''}
                        <button class="btn-icon delete" onclick="ReviewsManager.deleteReview('${review.id}')" title="حذف">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

        } catch (error) {
            console.error('Error loading reviews:', error);
            loading.style.display = 'none';
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:red">حدث خطأ أثناء تحميل البيانات</td></tr>';
            table.style.display = 'table';
        }
    },

    async updateStatus(id, status) {
        if (!await window.notifier.showConfirm(`هل أنت متأكد من ${status === 'Approved' ? 'قبول' : 'رفض'} هذا التقييم؟`)) return;

        try {
            await axios.put(`/catalog/api/reviews/${id}/status`, { status: status });
            window.notifier.showToast('تم تحديث الحالة بنجاح', 'success');
            this.loadReviews();
        } catch (error) {
            console.error("Error updating review:", error);
            window.notifier.showToast('حدث خطأ', 'error');
        }
    },

    async deleteReview(id) {
        if (!await window.notifier.showConfirm('هل أنت متأكد من حذف التقييم نهائياً؟')) return;

        try {
            await axios.delete(`/catalog/api/reviews/${id}`);
            window.notifier.showToast('تم الحذف بنجاح', 'success');
            this.loadReviews();
        } catch (error) {
            console.error("Error deleting review:", error);
            window.notifier.showToast('حدث خطأ أثناء الحذف', 'error');
        }
    }
};
