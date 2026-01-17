// Product Editor with Variant Generator
const API_BASE = '/catalog/api';

const ProductEditor = {
    mode: 'create', // 'create' or 'edit'
    productId: null,
    quill: null,
    uploadedImages: [],
    optionsMap: {},
    customFieldDefinitions: [],

    async init(mode, productId) {
        this.mode = mode;
        this.productId = productId;

        this.setupTabs();
        this.setupQuill();
        this.setupMediaUploader();
        this.setupPricingToggle();
        this.setupOptionsBuilder();
        this.setupSEOPreview();
        this.setupSlugGenerator();
        this.setupSaveButton();

        await this.fetchCategories();
        await this.fetchCustomFieldDefinitions();

        if (mode === 'edit' && productId) {
            await this.loadProduct(productId);
        } else {
            this.renderCustomFields({});
        }
    },

    // ============================================================
    // TAB NAVIGATION
    // ============================================================
    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        const panels = document.querySelectorAll('.panel');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.target;

                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));

                tab.classList.add('active');
                document.getElementById(target).classList.add('active');
            });
        });
    },

    // ============================================================
    // RICH TEXT EDITOR (Quill.js)
    // ============================================================
    setupQuill() {
        this.quill = new Quill('#productDesc', {
            theme: 'snow',
            placeholder: 'أدخل وصف المنتج بالتفصيل...',
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline'],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    ['link', 'image'],
                    ['clean']
                ]
            }
        });
    },

    // ============================================================
    // MEDIA UPLOADER
    // ============================================================
    setupMediaUploader() {
        const uploader = document.getElementById('mediaUploader');
        const fileInput = document.getElementById('mediaInput');
        const preview = document.getElementById('mediaPreview');

        uploader.addEventListener('click', () => fileInput.click());

        uploader.addEventListener('dragover', e => {
            e.preventDefault();
            uploader.style.borderColor = '#10b981';
            uploader.style.background = '#f0fdf4';
        });

        uploader.addEventListener('dragleave', () => {
            uploader.style.borderColor = '#9ca3af';
            uploader.style.background = 'transparent';
        });

        uploader.addEventListener('drop', e => {
            e.preventDefault();
            uploader.style.borderColor = '#9ca3af';
            uploader.style.background = 'transparent';
            this.handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', e => this.handleFiles(e.target.files));
    },

    async handleFiles(files) {
        const preview = document.getElementById('mediaPreview');

        for (const file of files) {
            if (!file.type.startsWith('image/')) continue;
            if (file.size > 5 * 1024 * 1024) {
                window.notifier.showToast('الصورة أكبر من 5 ميغابايت: ' + file.name, 'warning');
                continue;
            }

            // Create temporary preview (optional) or loading state

            // Upload
            const formData = new FormData();
            formData.append('file', file);

            try {
                // Show loading toast or spinner if needed

                const response = await axios.post('/catalog/api/upload/image', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                const imageData = {
                    url: response.data.url,
                    alt: file.name,
                    isMain: this.uploadedImages.length === 0,
                    order: this.uploadedImages.length
                };
                this.uploadedImages.push(imageData);

            } catch (error) {
                console.error('Upload failed', error);
                window.notifier.showToast('فشل رفع الصورة: ' + file.name, 'error');
            }
        }

        this.renderMediaPreview();
    },

    renderMediaPreview() {
        const preview = document.getElementById('mediaPreview');
        preview.innerHTML = this.uploadedImages.map((img, idx) => `
            <div class="media-item" data-index="${idx}">
                <img src="${img.url}" alt="${img.alt}">
                <div class="media-actions">
                    <button type="button" onclick="ProductEditor.setMainImage(${idx})" class="media-btn ${img.isMain ? 'active' : ''}">
                        <i class="fa-solid fa-star"></i>
                    </button>
                    <button type="button" onclick="ProductEditor.removeImage(${idx})" class="media-btn delete">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
                ${img.isMain ? '<span class="main-badge">رئيسية</span>' : ''}
            </div>
        `).join('');
    },

    setMainImage(index) {
        this.uploadedImages.forEach((img, idx) => {
            img.isMain = idx === index;
        });
        this.renderMediaPreview();
    },

    removeImage(index) {
        this.uploadedImages.splice(index, 1);
        // Re-index
        this.uploadedImages.forEach((img, idx) => {
            img.order = idx;
            if (idx === 0) img.isMain = true;
        });
        this.renderMediaPreview();
    },

    // ============================================================
    // PRICING & INVENTORY
    // ============================================================
    setupPricingToggle() {
        const trackQty = document.getElementById('trackQty');
        const qtyGroup = document.getElementById('qtyGroup');

        trackQty.addEventListener('change', () => {
            qtyGroup.style.display = trackQty.checked ? 'block' : 'none';
        });
    },

    // ============================================================
    // OPTIONS & VARIANT GENERATOR
    // ============================================================
    setupOptionsBuilder() {
        const addBtn = document.getElementById('addOptionBtn');
        addBtn.addEventListener('click', () => this.addOptionRow());
    },

    addOptionRow() {
        const container = document.getElementById('optionsContainer');
        const rowId = 'opt-' + Date.now();

        const row = document.createElement('div');
        row.className = 'option-row';
        row.id = rowId;
        row.innerHTML = `
            <input type="text" class="option-name" placeholder="اسم الخاصية (مثال: اللون)" data-row="${rowId}">
            <input type="text" class="option-values" placeholder="قيم مفصولة بفواصل (مثال: أحمر,أزرق,أخضر)" data-row="${rowId}">
            <button type="button" class="remove-option" onclick="ProductEditor.removeOptionRow('${rowId}')">
                <i class="fa-solid fa-times"></i>
            </button>
        `;

        container.appendChild(row);

        // Add event listeners
        row.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => this.regenerateVariants());
        });
    },

    removeOptionRow(rowId) {
        const row = document.getElementById(rowId);
        if (row) row.remove();
        this.regenerateVariants();
    },

    regenerateVariants() {
        // Collect options
        const optionRows = document.querySelectorAll('.option-row');
        this.optionsMap = {};

        optionRows.forEach(row => {
            const nameInput = row.querySelector('.option-name');
            const valuesInput = row.querySelector('.option-values');

            const name = nameInput.value.trim();
            const values = valuesInput.value
                .split(',')
                .map(v => v.trim())
                .filter(v => v);

            if (name && values.length > 0) {
                this.optionsMap[name] = values;
            }
        });

        // Generate Cartesian product
        const variants = this.cartesianProduct(this.optionsMap);

        // Update count
        document.getElementById('variantCount').textContent = variants.length;

        // Render table
        this.renderVariantsTable(variants);
    },

    cartesianProduct(optionsMap) {
        const names = Object.keys(optionsMap);
        if (names.length === 0) return [];

        const values = names.map(name => optionsMap[name]);

        const recurse = (idx, current, acc) => {
            if (idx === values.length) {
                const obj = {};
                names.forEach((n, i) => (obj[n] = current[i]));
                acc.push(obj);
                return;
            }
            values[idx].forEach(v => {
                recurse(idx + 1, [...current, v], acc);
            });
        };

        const result = [];
        recurse(0, [], result);
        return result;
    },

    renderVariantsTable(variants) {
        const headerRow = document.getElementById('variantHeaderRow');
        const tbody = document.getElementById('variantsGridBody');

        // Clear existing option columns
        while (headerRow.children.length > 3) {
            headerRow.removeChild(headerRow.lastChild);
        }

        // Add option columns to header
        Object.keys(this.optionsMap).forEach(optName => {
            const th = document.createElement('th');
            th.textContent = optName;
            headerRow.appendChild(th);
        });

        // Render variant rows
        if (variants.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="${3 + Object.keys(this.optionsMap).length}" style="text-align:center; padding:20px; color:#9ca3af;">
                        أضف خصائص المنتج لتوليد الأنواع تلقائياً
                    </td>
                </tr>
            `;
            return;
        }

        const productName = document.getElementById('productName').value || 'PRODUCT';
        const basePrice = parseFloat(document.getElementById('basePrice').value) || 0;
        const baseQty = parseInt(document.getElementById('stockQty').value) || 0;

        tbody.innerHTML = variants.map((variant, idx) => {
            const sku = this.generateSKU(productName, variant, idx);

            return `
                <tr data-variant-index="${idx}">
                    <td><input type="text" class="variant-sku" value="${sku}" style="width:100%; border:none; text-align:center;"></td>
                    <td><input type="number" class="variant-qty" value="${baseQty}" min="0" style="width:100%; border:none; text-align:center;"></td>
                    <td><input type="number" class="variant-price" value="${basePrice}" step="0.01" min="0" style="width:100%; border:none; text-align:center;"></td>
                    ${Object.values(variant).map(val => `<td style="background:#f9fafb;">${val}</td>`).join('')}
                </tr>
            `;
        }).join('');
    },

    generateSKU(productName, variantOptions, index) {
        const base = productName.toUpperCase().replace(/\s+/g, '').substring(0, 4);
        const optParts = Object.values(variantOptions).map(v => v.substring(0, 2).toUpperCase());
        const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
        return `${base}-${optParts.join('-')}-${String(index + 1).padStart(3, '0')}-${randomSuffix}`;
    },

    // ============================================================
    // SEO PREVIEW
    // ============================================================
    setupSEOPreview() {
        const pageTitle = document.getElementById('pageTitle');
        const metaDesc = document.getElementById('metaDesc');
        const slugInput = document.getElementById('slug');

        const updatePreview = () => {
            const productName = document.getElementById('productName').value || 'عنوان المنتج';
            const titleText = pageTitle.value || productName;
            const descText = metaDesc.value || 'وصف الميتا سيظهر هنا...';
            const slugText = slugInput.value || 'slug';

            document.querySelector('.preview-title').textContent = titleText;
            document.getElementById('previewSlug').textContent = slugText;
            document.querySelector('.preview-desc').textContent = descText;

            // Update char counts
            document.getElementById('titleCharCount').textContent = titleText.length;
            document.getElementById('descCharCount').textContent = descText.length;
        };

        [pageTitle, metaDesc, slugInput, document.getElementById('productName')].forEach(el => {
            el.addEventListener('input', updatePreview);
        });
    },

    setupSlugGenerator() {
        const productName = document.getElementById('productName');
        const slugInput = document.getElementById('slug');

        productName.addEventListener('blur', () => {
            if (!slugInput.value) {
                const slug = this.generateSlug(productName.value);
                slugInput.value = slug;
                slugInput.dispatchEvent(new Event('input'));
            }
        });
    },

    generateSlug(text) {
        return text
            .toLowerCase()
            .replace(/[^\w\u0600-\u06FF\s-]/g, '') // Allow Arabic & English
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-+|-+$/g, ''); // Trim dashes
    },

    // ============================================================
    // CUSTOM FIELDS
    // ============================================================
    async fetchCustomFieldDefinitions() {
        try {
            const response = await axios.get('/catalog/api/custom-fields');
            this.customFieldDefinitions = response.data;
        } catch (error) {
            console.error('Failed to load custom fields:', error);
            document.getElementById('customFieldsLoader').innerHTML = '<span class="text-danger">فشل تحميل الحقول المخصصة</span>';
        }
    },

    renderCustomFields(values = {}) {
        const container = document.getElementById('customFieldsContainer');

        if (this.customFieldDefinitions.length === 0) {
            container.innerHTML = '<p style="text-align:center; padding:20px; color:#6b7280">لا توجد حقول مخصصة معرفة.</p>';
            return;
        }

        container.innerHTML = '';

        this.customFieldDefinitions.forEach(field => {
            const value = values[field.id] || '';
            const isRequired = field.is_required ? 'required' : '';
            const labelStar = field.is_required ? '<span style="color:red">*</span>' : '';

            let inputHtml = '';

            if (field.type === 'boolean') {
                inputHtml = `
                    <div class="form-check form-switch">
                        <input class="form-check-input custom-field-input" type="checkbox" 
                            id="cf_${field.id}" 
                            data-field-id="${field.id}"
                            data-type="boolean"
                            ${value === 'true' || value === true ? 'checked' : ''}>
                        <label class="form-check-label" for="cf_${field.id}">${field.name}</label>
                    </div>
                `;
            } else if (field.type === 'date') {
                inputHtml = `
                     <div class="form-group">
                        <label>${field.name} ${labelStar}</label>
                        <input type="date" class="form-control input-style custom-field-input" 
                            id="cf_${field.id}" 
                            data-field-id="${field.id}"
                            data-type="date"
                            value="${value}" ${isRequired}>
                    </div>
                `;
            } else {
                inputHtml = `
                     <div class="form-group">
                        <label>${field.name} ${labelStar}</label>
                        <input type="${field.type === 'number' ? 'number' : 'text'}" 
                            class="form-control input-style custom-field-input" 
                            id="cf_${field.id}" 
                            data-field-id="${field.id}"
                            data-type="${field.type}"
                            value="${value}" ${isRequired}>
                    </div>
                `;
            }

            const wrapper = document.createElement('div');
            wrapper.className = 'mb-3';
            wrapper.innerHTML = inputHtml;
            container.appendChild(wrapper);
        });
    },

    collectCustomFields() {
        const fields = {};
        document.querySelectorAll('.custom-field-input').forEach(input => {
            const fieldId = input.dataset.fieldId;
            const type = input.dataset.type;
            let value = input.value;

            if (type === 'boolean') {
                value = input.checked;
            }

            if (value !== '') {
                fields[fieldId] = value;
            }
        });
        return fields;
    },

    // ============================================================
    // LOAD RESOURCES
    // ============================================================
    async fetchCategories() {
        try {
            const response = await axios.get(`${API_BASE}/categories/tree`);
            const categories = response.data;
            const select = document.getElementById('productCategory');

            // Helper to render options recursively
            const renderOptions = (items, level = 0) => {
                items.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = '—'.repeat(level) + ' ' + cat.name;
                    select.appendChild(option);

                    if (cat.children && cat.children.length > 0) {
                        renderOptions(cat.children, level + 1);
                    }
                });
            };

            renderOptions(categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
            window.notifier.showToast('فشل تحميل التصنيفات', 'error');
        }
    },

    // ============================================================
    // LOAD EXISTING PRODUCT (Edit Mode)
    // ============================================================
    async loadProduct(productId) {
        try {
            const response = await axios.get(`${API_BASE}/products/${productId}`);
            const product = response.data;

            // Populate fields
            document.getElementById('productName').value = product.name;
            this.quill.root.innerHTML = product.description || '';
            document.getElementById('productType').value = product.product_type;
            if (product.category_id) {
                document.getElementById('productCategory').value = product.category_id;
            }
            document.getElementById('productStatus').value = product.status;
            document.getElementById('taxable').checked = product.taxable;
            document.getElementById('pageTitle').value = product.page_title || '';
            document.getElementById('metaDesc').value = product.meta_description || '';
            document.getElementById('slug').value = product.slug;

            // Load images
            this.uploadedImages = product.images.map(img => ({
                url: img.image_url,
                alt: img.alt_text,
                isMain: img.is_main,
                order: img.display_order
            }));
            this.renderMediaPreview();

            // Load options and regenerate variants
            product.options.forEach(opt => {
                this.addOptionRow();
                const lastRow = document.querySelector('.option-row:last-child');
                lastRow.querySelector('.option-name').value = opt.name;
                const values = Array.isArray(opt.values) ? opt.values : JSON.parse(opt.values);
                lastRow.querySelector('.option-values').value = values.join(',');
            });
            this.regenerateVariants();

            // Populate variant data if exists
            // Populate variant data if exists
            if (product.variants.length > 0) {
                // Set base values from first variant for reference
                const firstVariant = product.variants[0];
                const basePriceEl = document.getElementById('basePrice');
                const costPriceEl = document.getElementById('costPrice');
                const comparePriceEl = document.getElementById('comparePrice');
                const stockQtyEl = document.getElementById('stockQty');
                const trackQtyEl = document.getElementById('trackQty');

                if (basePriceEl) basePriceEl.value = firstVariant.price;
                if (costPriceEl) costPriceEl.value = firstVariant.cost_price || '';
                if (comparePriceEl) comparePriceEl.value = firstVariant.compare_at_price || '';

                // Populate Global Stock Settings (heuristic from first variant)
                if (stockQtyEl) stockQtyEl.value = firstVariant.quantity;
                if (trackQtyEl) trackQtyEl.checked = firstVariant.quantity > 0;

                // Map saved variants to table rows
                const rows = document.querySelectorAll('#variantsGridBody tr');
                const optionsMap = this.optionsMap;
                const optionNames = Object.keys(optionsMap);

                rows.forEach(row => {
                    // Extract options from current row
                    const optionCells = Array.from(row.querySelectorAll('td')).slice(3); // options start at index 3
                    const rowOptions = {};
                    optionNames.forEach((name, i) => {
                        if (optionCells[i]) rowOptions[name] = optionCells[i].textContent.trim();
                    });

                    // Find matching saved variant
                    const match = product.variants.find(v => {
                        const vOptions = typeof v.options === 'string' ? JSON.parse(v.options) : v.options;
                        // Compare all option keys
                        return optionNames.every(name => vOptions[name] === rowOptions[name]);
                    });

                    if (match) {
                        const skuInput = row.querySelector('.variant-sku');
                        const qtyInput = row.querySelector('.variant-qty');
                        const priceInput = row.querySelector('.variant-price');

                        if (skuInput) skuInput.value = match.sku;
                        if (qtyInput) qtyInput.value = match.quantity;
                        if (priceInput) priceInput.value = match.price;
                    }
                });
            }

            // Load Custom Fields
            const customFieldValues = {};
            if (product.custom_field_values) {
                product.custom_field_values.forEach(cf => {
                    customFieldValues[cf.field_id] = cf.value;
                });
            }
            this.renderCustomFields(customFieldValues);

        } catch (error) {
            window.notifier.showToast('فشل تحميل المنتج: ' + (error.response?.data?.detail || error.message), 'error');
        }
    },

    // ============================================================
    // SAVE PRODUCT
    // ============================================================
    setupSaveButton() {
        document.getElementById('saveBtn').addEventListener('click', () => this.saveProduct());
    },

    async saveProduct() {
        // Validate required fields
        const name = document.getElementById('productName').value.trim();
        const slug = document.getElementById('slug').value.trim();
        const basePrice = parseFloat(document.getElementById('basePrice').value);

        if (!name) return window.notifier.showToast('يرجى إدخال اسم المنتج', 'warning');
        if (!name) return window.notifier.showToast('يرجى إدخال اسم المنتج', 'warning');

        // Auto-generate slug if empty
        if (!slug) {
            slug = this.generateSlug(name);
            document.getElementById('slug').value = slug;
        }

        if (!slug) return window.notifier.showToast('يرجى إدخال الرابط (Slug)', 'warning');
        if (isNaN(basePrice) || basePrice < 0) return window.notifier.showToast('يرجى إدخال سعر صحيح', 'warning');

        // If no variants generated (Simple Product), create default variant
        let variantsData = this.collectVariants();
        if (variantsData.length === 0) {
            variantsData.push({
                sku: document.getElementById('slug').value || this.generateSKU(name, {}, 0),
                price: basePrice,
                quantity: document.getElementById('trackQty').checked ? (parseInt(document.getElementById('stockQty').value) || 0) : 0,
                cost_price: parseFloat(document.getElementById('costPrice').value) || null,
                compare_at_price: parseFloat(document.getElementById('comparePrice').value) || null,
                options: {}
            });
        }

        // Build payload
        const payload = {
            name: name,
            description: this.quill.root.innerHTML,
            category_id: document.getElementById('productCategory').value || null,
            product_type: document.getElementById('productType').value,
            status: document.getElementById('productStatus').value,
            taxable: document.getElementById('taxable').checked,
            page_title: document.getElementById('pageTitle').value || name,
            meta_description: document.getElementById('metaDesc').value,
            slug: slug,
            images: this.uploadedImages.map((img, idx) => ({
                image_url: img.url,
                alt_text: img.alt || name,
                is_main: img.isMain,
                display_order: idx
            })),
            options: Object.entries(this.optionsMap).map(([name, values]) => ({
                name: name,
                values: values
            })),
            variants: variantsData,
            custom_fields: this.collectCustomFields()
        };

        try {
            let response;
            if (this.mode === 'edit') {
                response = await axios.put(`${API_BASE}/products/${this.productId}`, payload);
                window.notifier.showFlashToast('✅ تم تحديث المنتج بنجاح!', 'success');
            } else {
                response = await axios.post(`${API_BASE}/products`, payload);
                window.notifier.showFlashToast('✅ تم إضافة المنتج بنجاح!', 'success');
            }

            window.location.href = '/catalog/products';
        } catch (error) {
            window.notifier.showToast('❌ فشل الحفظ: ' + (error.response?.data?.detail || error.message), 'error');
            console.error('Save error:', error);
        }
    },

    collectVariants() {
        const variants = [];
        const rows = document.querySelectorAll('#variantsGridBody tr');

        rows.forEach((row, idx) => {
            const skuInput = row.querySelector('.variant-sku');
            const qtyInput = row.querySelector('.variant-qty');
            const priceInput = row.querySelector('.variant-price');

            if (!skuInput) return; // Skip empty state row

            // Get option values from this row
            const optionCells = Array.from(row.querySelectorAll('td')).slice(3);
            const optionNames = Object.keys(this.optionsMap);
            const options = {};
            optionNames.forEach((name, i) => {
                if (optionCells[i]) {
                    options[name] = optionCells[i].textContent.trim();
                }
            });

            variants.push({
                sku: skuInput.value,
                quantity: parseInt(qtyInput.value) || 0,
                price: parseFloat(priceInput.value) || 0,
                cost_price: parseFloat(document.getElementById('costPrice').value) || null,
                compare_at_price: parseFloat(document.getElementById('comparePrice').value) || null,
                options: options
            });
        });

        return variants;
    }
};
