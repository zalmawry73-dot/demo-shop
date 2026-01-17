/**
 * Categories Management Module
 * Handles tree rendering, drag & drop reordering, and delete operations.
 */

document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
});

// State
let categoriesData = [];

// ----------------------------------------------------------------------
// Core Functions
// ----------------------------------------------------------------------

/**
 * Fetch categories tree from API and render
 */
async function loadCategories() {
    const container = document.getElementById('categories-tree');

    try {
        const response = await fetch('/catalog/api/categories/tree');
        if (!response.ok) throw new Error('فشل تحميل البيانات');

        categoriesData = await response.json();
        renderTree(categoriesData, container);

    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="alert alert-danger m-3">
                <i class="fas fa-exclamation-circle me-2"></i>
                فشل تحميل التصنيفات. <a href="#" onclick="loadCategories()" class="alert-link">إعادة المحاولة</a>
            </div>
        `;
    }
}

/**
 * Render the nested tree structure
 */
function renderTree(items, container) {
    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h5>لا توجد تصنيفات</h5>
                <p>قم بإضافة تصنيفك الأول للبدء.</p>
            </div>
        `;
        return;
    }

    const ul = document.createElement('ul');
    ul.className = 'tree-children';
    ul.setAttribute('data-parent-id', 'root');

    items.forEach(item => {
        const li = createTreeItem(item);
        ul.appendChild(li);
    });

    container.innerHTML = '';
    container.appendChild(ul);

    // Initialize Sortable on Root
    initSortable(ul);
}

/**
 * Create a single tree item (recursive)
 */
function createTreeItem(item) {
    const li = document.createElement('li');
    li.className = 'tree-item';
    li.setAttribute('data-id', item.id);

    // Toggle Icon logic
    const hasChildren = item.children && item.children.length > 0;
    const toggleHtml = hasChildren
        ? `<div class="collapse-icon" onclick="toggleChildren(this)"><i class="fas fa-chevron-down"></i></div>`
        : `<div class="collapse-icon" style="visibility: hidden"></div>`;

    // Status Badge
    const statusBadge = item.is_active
        ? `<span class="badge-status active">نشط</span>`
        : `<span class="badge-status inactive">مخفي</span>`;

    // Image
    const imageHtml = item.image_url
        ? `<div class="category-thumb"><img src="${item.image_url}" alt="${item.name}"></div>`
        : `<div class="category-thumb"><i class="fas fa-box"></i></div>`;

    li.innerHTML = `
        <div class="tree-content">
            <i class="fas fa-grip-vertical drag-handle"></i>
            ${toggleHtml}
            ${imageHtml}
            
            <div class="category-info">
                <div class="category-name">${item.name}</div>
                <div class="category-meta">
                    ${item.products_count} منتج • /${item.slug}
                </div>
            </div>

            ${statusBadge}

            <div class="category-actions">
                <button class="btn-action" onclick="window.location.href='/catalog/categories/${item.id}/edit'" title="تعديل">
                    <i class="fas fa-pencil-alt"></i>
                </button>
                <button class="btn-action text-danger" onclick="deleteCategory('${item.id}', '${item.name}')" title="حذف">
                    <i class="far fa-trash-alt"></i>
                </button>
            </div>
        </div>
    `;

    // Render Children recursively
    if (hasChildren) {
        const childUl = document.createElement('ul');
        childUl.className = 'tree-children';
        childUl.setAttribute('data-parent-id', item.id);

        item.children.forEach(child => {
            childUl.appendChild(createTreeItem(child));
        });

        li.appendChild(childUl);
        initSortable(childUl);
    } else {
        const emptyUl = document.createElement('ul');
        emptyUl.className = 'tree-children';
        emptyUl.setAttribute('data-parent-id', item.id);
        emptyUl.style.minHeight = '10px';
        li.appendChild(emptyUl);
        initSortable(emptyUl);
    }

    return li;
}

/**
 * Initialize SortableJS on a list
 */
function initSortable(el) {
    new Sortable(el, {
        group: 'categories',
        handle: '.drag-handle',
        animation: 150,
        ghostClass: 'sortable-ghost',
        fallbackOnBody: true,
        swapThreshold: 0.65,
        onEnd: function (evt) {
            if (evt.newIndex !== evt.oldIndex || evt.from !== evt.to) {
                handleReorder(evt);
            }
        }
    });
}

/**
 * Handle reordering logic (API update)
 */
function handleReorder(evt) {
    const itemEl = evt.item;
    const newParentUl = evt.to;
    const newParentId = newParentUl.getAttribute('data-parent-id') === 'root' ? null : newParentUl.getAttribute('data-parent-id');

    // Check if new parent is child of item (avoid circular) - handled by UI drag constraints mostly, but good to check API response
    // SortableJS allows dropping anywhere unless constrained. 
    // Backend API should ideally reject circular.

    const siblings = Array.from(newParentUl.children).filter(child => child.classList.contains('tree-item'));

    const updates = siblings.map((el, index) => ({
        id: el.getAttribute('data-id'),
        parent_id: newParentId,
        sort_order: index
    }));

    fetch('/catalog/api/categories/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    })
        .catch(err => {
            console.error(err);
            window.notifier.showToast('فشل حفظ الترتيب. جاري التحديث...', 'error');
            loadCategories();
        });
}

/**
 * Toggle children visibility
 */
window.toggleChildren = function (icon) {
    const treeRow = icon.closest('.tree-content');
    const childrenUl = treeRow.nextElementSibling;

    if (childrenUl && childrenUl.classList.contains('tree-children')) {
        if (childrenUl.style.display === 'none') {
            childrenUl.style.display = 'block';
            icon.classList.remove('collapsed');
        } else {
            childrenUl.style.display = 'none';
            icon.classList.add('collapsed');
        }
    }
}

/**
 * Delete Category
 */
window.deleteCategory = async function (id, name) {
    if (!await window.notifier.showConfirm(`هل أنت متأكد من حذف التصنيف "${name}"؟\n\nسيتم إلغاء ربط المنتجات بهذا التصنيف، ولكن لن يتم حذفها.`)) {
        return;
    }

    try {
        const response = await fetch(`/catalog/api/categories/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('فشل الحذف');

        window.notifier.showToast('تم الحذف بنجاح', 'success');
        loadCategories();

    } catch (error) {
        window.notifier.showToast(error.message, 'error');
    }
}
