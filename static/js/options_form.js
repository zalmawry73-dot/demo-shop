const OptionForm = {
    init() {
        this.valuesList = document.getElementById('valuesList');
        this.renderExistingValues();

        document.getElementById('optionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.save();
        });
    },

    renderExistingValues() {
        if (typeof EXISTING_VALUES !== 'undefined' && EXISTING_VALUES.length > 0) {
            EXISTING_VALUES.forEach(val => this.addValueRow(val));
        } else {
            // Add one empty row by default
            this.addValueRow();
        }
    },

    handleTypeChange() {
        const type = document.getElementById('optionType').value;
        document.querySelectorAll('.meta-input').forEach(el => {
            if (type === 'color') {
                el.type = 'color';
                el.style.padding = '0';
                el.style.width = '50px';
                el.style.cursor = 'pointer';
            } else {
                el.type = 'text';
                el.style.padding = '10px';
                el.style.width = '100px';
                el.style.removeProperty('cursor');
                if (!el.value.startsWith('#')) el.value = ''; // clear if switching back
                el.placeholder = 'Meta';
            }
        });
    },

    addValueRow(data = null) {
        const type = document.getElementById('optionType').value;
        const div = document.createElement('div');
        div.className = 'value-row';

        const value = data ? data.value : '';
        const meta = data ? data.meta : '';

        // Determine input type based on current selection
        // Use a generic logic: if type is color, input 2 is color picker
        const metaInputType = (type === 'color' || (data && data.meta && data.meta.startsWith('#'))) ? 'color' : 'text';

        div.innerHTML = `
            <input type="text" class="form-control value-input" placeholder="القيمة (مثال: أحمر)" value="${value}" required>
            <input type="${metaInputType}" class="form-control meta-input" placeholder="Meta" value="${meta || '#000000'}" 
                   style="${metaInputType === 'color' ? 'width:50px; padding:0; cursor:pointer' : 'width:100px'}">
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()"><i class="fa-solid fa-trash"></i></button>
        `;

        this.valuesList.appendChild(div);

        // Ensure future type changes affect this new row (this is simple via css/class but explicit handler is better)
        this.handleTypeChange();
    },

    async save() {
        const id = document.getElementById('optionId').value;
        const name = document.getElementById('optionName').value;
        const type = document.getElementById('optionType').value;

        const values = [];
        document.querySelectorAll('.value-row').forEach(row => {
            const val = row.querySelector('.value-input').value;
            const meta = row.querySelector('.meta-input').value;
            if (val) {
                values.push({ value: val, meta: meta });
            }
        });

        if (values.length === 0) {
            window.notifier.showToast('يجب إضافة قيمة واحدة على الأقل', 'warning');
            return;
        }

        const payload = {
            name: name,
            type: type,
            values: values
        };

        try {
            if (id) {
                await axios.put(`/catalog/api/attributes/${id}`, payload);
            } else {
                await axios.post('/catalog/api/attributes', payload);
            }
            window.notifier.showFlashToast('تم حفظ الخيارات بنجاح', 'success');
            window.location.href = '/catalog/options';
        } catch (error) {
            console.error('Error saving option:', error);
            window.notifier.showToast('حدث خطأ أثناء الحفظ. ربما الاسم مستخدم بالفعل؟', 'error');
        }
    }
};
