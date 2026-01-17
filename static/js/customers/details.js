/**
 * Customer Details Page JavaScript
 * Handles loading and displaying customer orders and statistics
 */

const customerId = window.location.pathname.split('/')[2];

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    loadCustomerOrders();
    loadCustomerStats();
});

async function loadCustomerOrders() {
    try {
        const response = await fetch(`/api/customers/${customerId}/orders`);
        if (!response.ok) throw new Error('Failed to load orders');

        const orders = await response.json();
        renderOrders(orders);
    } catch (error) {
        console.error('Error loading orders:', error);
        // Show empty state
        renderEmptyOrders();
    }
}

function renderOrders(orders) {
    const allOrdersTab = document.getElementById('all-orders');
    const newOrdersTab = document.getElementById('new-orders');
    const processingTab = document.getElementById('processing');
    const readyTab = document.getElementById('ready');

    if (orders.length === 0) {
        renderEmptyOrders();
        return;
    }

    // Render all orders
    allOrdersTab.innerHTML = renderOrdersTable(orders);

    // Render by status
    newOrdersTab.innerHTML = renderOrdersTable(orders.filter(o => o.status === 'new'));
    processingTab.innerHTML = renderOrdersTable(orders.filter(o => o.status === 'processing'));
    readyTab.innerHTML = renderOrdersTable(orders.filter(o => o.status === 'ready'));
}

function renderOrdersTable(orders) {
    if (orders.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-icon"><i class="fa-regular fa-comment-alt"></i></div>
                <h6>لا توجد طلبات</h6>
            </div>
        `;
    }

    return `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>رقم الطلب</th>
                        <th>التاريخ</th>
                        <th>الحالة</th>
                        <th>المبلغ</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${orders.map(order => `
                        <tr>
                            <td><a href="/orders/${order.id}">#${order.id}</a></td>
                            <td>${formatDate(order.created_at)}</td>
                            <td>${getStatusBadge(order.status)}</td>
                            <td>${order.total_amount} ر.س</td>
                            <td>
                                <a href="/orders/${order.id}" class="btn btn-sm btn-outline-primary">عرض</a>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderEmptyOrders() {
    const tabs = ['all-orders', 'new-orders', 'processing', 'ready'];
    tabs.forEach(tabId => {
        const tab = document.getElementById(tabId);
        if (tab) {
            tab.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon"><i class="fa-regular fa-comment-alt"></i></div>
                    <h6>لا توجد بيانات حالياً، ستظهر هنا عند توفرها</h6>
                </div>
            `;
        }
    });
}

async function loadCustomerStats() {
    try {
        const response = await fetch(`/api/customers/${customerId}/stats`);
        if (!response.ok) return; // Stats endpoint might not exist yet

        const stats = await response.json();
        updateStatsCards(stats);
    } catch (error) {
        // Stats not available, keep default values
        console.log('Stats not available');
    }
}

function updateStatsCards(stats) {
    // Update completed orders
    const completedEl = document.querySelector('.stats-value');
    if (completedEl && stats.completed_orders !== undefined) {
        completedEl.textContent = stats.completed_orders;
    }

    // Update all orders
    const allOrdersEls = document.querySelectorAll('.stats-value');
    if (allOrdersEls[1] && stats.total_orders !== undefined) {
        allOrdersEls[1].textContent = stats.total_orders;
    }

    // Update average order value
    if (allOrdersEls[2] && stats.average_order_value !== undefined) {
        allOrdersEls[2].textContent = stats.average_order_value.toFixed(2);
    }

    // Update total spent
    if (allOrdersEls[3] && stats.total_spent !== undefined) {
        allOrdersEls[3].textContent = stats.total_spent.toFixed(2);
    }
}

// Utilities
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getStatusBadge(status) {
    const statusMap = {
        'new': '<span class="badge bg-primary">جديد</span>',
        'processing': '<span class="badge bg-info">جاري التجهيز</span>',
        'ready': '<span class="badge bg-warning">جاهز</span>',
        'delivering': '<span class="badge bg-info">قيد التوصيل</span>',
        'completed': '<span class="badge bg-success">مكتمل</span>',
        'cancelled': '<span class="badge bg-danger">ملغي</span>'
    };
    return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
}
