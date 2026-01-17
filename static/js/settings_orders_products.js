document.addEventListener('DOMContentLoaded', async () => {
    // Orders Elements
    const orderElements = [
        'is_guest_checkout_enabled',
        'auto_complete_paid_orders',
        'auto_ready_paid_orders',
        'enable_reorder',
        'min_order_limit_enabled',
        'min_order_limit',
        'max_order_limit_enabled',
        'max_order_limit'
    ];

    // Products Elements
    const productElements = [
        'show_similar_products',
        'return_cancelled_quantity',
        'show_similar_on_product_page',
        'similar_products_limit',
        'show_low_stock_warning',
        'low_stock_threshold',
        'set_max_quantity_per_cart',
        'max_quantity_per_cart',
        'show_purchase_count',
        'min_purchase_count_to_show',
        'show_out_of_stock_at_end'
    ];

    // Helper to toggle visibility of dependent inputs
    function toggleDependentInput(checkboxId, inputId) {
        const checkbox = document.getElementById(checkboxId);
        const input = document.getElementById(inputId);
        if (checkbox && input) {
            const updateVisibility = () => {
                if (checkbox.checked) {
                    input.classList.remove('d-none');
                } else {
                    input.classList.add('d-none');
                }
            };
            checkbox.addEventListener('change', updateVisibility);
            updateVisibility(); // Initial state
        }
    }

    // Toggle container visibility helper (for products usually inside a div)
    function toggleDependentContainer(checkboxId, containerId) {
        const checkbox = document.getElementById(checkboxId);
        const container = document.getElementById(containerId);
        if (checkbox && container) {
            const updateVisibility = () => {
                if (checkbox.checked) {
                    container.classList.remove('d-none');
                } else {
                    container.classList.add('d-none');
                }
            };
            checkbox.addEventListener('change', updateVisibility);
            updateVisibility();
        }
    }


    // Load Order Settings
    async function loadOrderSettings() {
        try {
            const response = await fetch('/api/settings/orders');
            if (response.ok) {
                const data = await response.json();
                orderElements.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        if (el.type === 'checkbox') {
                            el.checked = data[id];
                        } else {
                            el.value = data[id];
                        }
                    }
                });

                // Trigger visibility updates
                toggleDependentInput('min_order_limit_enabled', 'min_order_limit');
                toggleDependentInput('max_order_limit_enabled', 'max_order_limit');
            }
        } catch (error) {
            console.error('Error loading order settings:', error);
            notifier.showToast('فشل تحميل إعدادات الطلبات', 'error');
        }
    }

    // Load Product Settings
    async function loadProductSettings() {
        try {
            const response = await fetch('/api/settings/products');
            if (response.ok) {
                const data = await response.json();
                productElements.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        if (el.type === 'checkbox') {
                            el.checked = data[id];
                        } else {
                            el.value = data[id];
                        }
                    }
                });

                toggleDependentContainer('show_similar_on_product_page', 'similar_products_limit_container');
                toggleDependentContainer('show_low_stock_warning', 'low_stock_threshold_container');
                toggleDependentContainer('show_purchase_count', 'min_purchase_count_to_show_container');
            }
        } catch (error) {
            console.error('Error loading product settings:', error);
            notifier.showToast('فشل تحميل إعدادات المنتجات', 'error');

        }
    }

    // Save Order Settings
    document.getElementById('saveOrdersBtn').addEventListener('click', async () => {
        const data = {};
        orderElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (el.type === 'checkbox') {
                    data[id] = el.checked;
                } else {
                    data[id] = el.value ? parseFloat(el.value) : 0;
                }
            }
        });

        try {
            const response = await fetch('/api/settings/orders', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                notifier.showToast('تم حفظ إعدادات الطلبات بنجاح', 'success');
            } else {
                throw new Error('Failed to save');
            }
        } catch (error) {
            console.error('Error saving order settings:', error);
            notifier.showToast('فشل حفظ إعدادات الطلبات', 'error');
        }
    });

    // Save Product Settings
    document.getElementById('saveProductsBtn').addEventListener('click', async () => {
        const data = {};
        productElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (el.type === 'checkbox') {
                    data[id] = el.checked;
                } else {
                    data[id] = el.value ? parseInt(el.value) : 0;
                }
            }
        });

        try {
            const response = await fetch('/api/settings/products', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                notifier.showToast('تم حفظ إعدادات المنتجات بنجاح', 'success');
            } else {
                throw new Error('Failed to save');
            }
        } catch (error) {
            console.error('Error saving product settings:', error);
            notifier.showToast('فشل حفظ إعدادات المنتجات', 'error');
        }
    });

    // Initial Load
    await loadOrderSettings();
    await loadProductSettings();
});
