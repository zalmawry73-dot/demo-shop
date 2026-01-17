
let currentChannel = 'sms';
let templatesData = [];

// Available variables for injection
const VARIABLES = [
    { label: 'اسم العميل', value: '{customer_name}' },
    { label: 'رقم الطلب', value: '{order_id}' },
    { label: 'حالة الطلب', value: '{order_status}' },
    { label: 'رابط الطلب', value: '{order_url}' },
    { label: 'اسم المتجر', value: '{store_name}' }
];

// Status Display Names mapping
const STATUS_NAMES = {
    'order_created': 'جديد',
    'order_processing': 'قيد التجهيز',
    'order_ready': 'جاهز',
    'order_shipped': 'جاري التوصيل',
    'order_delivered': 'تم التوصيل',
    'order_completed': 'مكتمل',
    'order_cancelled': 'ملغى' // Fixed typo from 'cancelled'
};

document.addEventListener('DOMContentLoaded', () => {
    loadTemplates(currentChannel);
});

function switchChannel(channel) {
    currentChannel = channel;
    loadTemplates(channel);
}

async function loadTemplates(channel) {
    const accordionContainer = document.getElementById('statusesAccordion');
    accordionContainer.innerHTML = '<div class="text-center py-5"><i class="fas fa-spinner fa-spin fa-2x text-muted"></i></div>';

    try {
        const token = localStorage.getItem('access_token');
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`/api/settings/notifications/templates?channel=${channel}`, {
            headers: headers
        });

        if (!response.ok) {
            if (response.status === 401) {
                if (typeof notifier !== 'undefined') notifier.showToast('جلسة العمل انتهت، يرجى تسجيل الدخول', 'error');
                return;
            }
            throw new Error('Failed to fetch templates');
        }

        templatesData = await response.json();
        console.log("Fetched templates:", templatesData); // Debugging

        if (templatesData.length === 0) {
            accordionContainer.innerHTML = '<div class="text-center py-5 text-muted">لا يوجد قوالب متاحة (No templates found)</div>';
            return;
        }

        renderAccordion(templatesData);
    } catch (error) {
        console.error('Error:', error);
        accordionContainer.innerHTML = '<div class="text-center py-5 text-danger">فشل تحميل القوالب</div>';
        if (typeof notifier !== 'undefined') notifier.showToast('فشل تحميل القوالب', 'error');
    }
}

function renderAccordion(templates) {
    const container = document.getElementById('statusesAccordion');
    container.innerHTML = '';

    templates.forEach((template, index) => {
        const statusName = STATUS_NAMES[template.event_type] || template.event_type || 'Unknown Status';
        console.log(`Mapping ${template.event_type} to ${statusName}`);

        const itemId = `collapse${template.id}`;
        const headerId = `heading${template.id}`;

        const isChecked = template.is_enabled ? 'checked' : '';

        const itemHtml = `
            <div class="accordion-item border-0 border-bottom">
                <h2 class="accordion-header" id="${headerId}">
                    <div class="d-flex align-items-center w-100 py-3 pe-4 ps-2">
                         <!-- Toggle Switch (Right) -->
                         <div class="form-check form-switch ms-3 mb-0">
                            <input class="form-check-input" type="checkbox" id="toggle_${template.id}" 
                                ${isChecked} onchange="toggleTemplate(${template.id}, this.checked)">
                        </div>
                        
                        <!-- Status Name -->
                        <span class="fw-bold fs-6 flex-grow-1 text-end">${statusName}</span>
                        
                        <!-- Edit Button (Left/Accordion Trigger) -->
                        <button class="btn btn-light rounded-pill px-3 ms-2 collapsed bg-white border text-muted" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#${itemId}" aria-expanded="false" aria-controls="${itemId}">
                            تخصيص
                        </button>
                    </div>
                </h2>
                <div id="${itemId}" class="accordion-collapse collapse" aria-labelledby="${headerId}" data-bs-parent="#statusesAccordion">
                    <div class="accordion-body bg-light p-4">
                        <div class="row g-4">
                            <!-- Helper Chips -->
                            <div class="col-12">
                                <label class="form-label text-muted small mb-2">القيم المقترحة: (اضغط لإدراجها في النص)</label>
                                <div class="d-flex flex-wrap gap-2">
                                    ${VARIABLES.map(v => `
                                        <span class="badge bg-white text-secondary border variable-chip py-2 px-3 fw-normal" 
                                            onclick="insertVariable('${v.value}', ${template.id})">
                                            ${v.value} (${v.label})
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <!-- Arabic Template -->
                            <div class="col-md-6">
                                <label class="form-label fw-bold small">نص الرسالة (العربية)</label>
                                <textarea class="form-control border-0 shadow-sm p-3" id="template_ar_${template.id}" rows="4" 
                                    placeholder="اكتب نص الرسالة هنا...">${template.message_template_ar || ''}</textarea>
                                <div class="text-end text-muted small mt-1">
                                    <span id="char_count_ar_${template.id}">0</span> حرف
                                </div>
                            </div>
                            
                            <!-- English Template -->
                            <div class="col-md-6">
                                <label class="form-label fw-bold small">نص الرسالة (الإنجليزية)</label>
                                <textarea class="form-control border-0 shadow-sm p-3 text-start" dir="ltr" id="template_en_${template.id}" rows="4" 
                                    placeholder="Enter message text here...">${template.message_template_en || ''}</textarea>
                                 <div class="text-start text-muted small mt-1">
                                    <span id="char_count_en_${template.id}">0</span> chars
                                </div>
                            </div>
                            
                            <!-- Actions -->
                            <div class="col-12 d-flex gap-2 justify-content-end mt-2">
                                <button class="btn btn-outline-secondary bg-white px-4 rounded-pill" onclick="previewTemplate(${template.id})">
                                    <i class="fa-regular fa-eye me-1"></i> معاينة
                                </button>
                                <button class="btn btn-purple px-5 rounded-pill" onclick="saveTemplate(${template.id})">
                                    حفظ
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', itemHtml);
    });
}

function insertVariable(variable, templateId) {
    // Determine active textarea (hacky: default to Arabic, or last focused?)
    // Better: insert into both? Or specific one?
    // User usually edits one at a time. Let's insert into the focused one if possible, 
    // or fallback to Arabic if none focused.
    // For simplicity, we can just append, but that's annoying.
    // A better UX: when clicking a chip, assume it goes to the currently editing textarea.

    // Let's check which element was last focused
    const arField = document.getElementById(`template_ar_${templateId}`);
    // const enField = document.getElementById(`template_en_${templateId}`);

    // Simple implementation: Default to Arabic field for now as it's primary in RTL stores
    // Or we could pass the target field ID.

    activeInsert(arField, variable);
}

function activeInsert(field, value) {
    if (!field) return;
    const start = field.selectionStart;
    const end = field.selectionEnd;
    const text = field.value;
    const before = text.substring(0, start);
    const after = text.substring(end, text.length);
    field.value = before + value + after;
    field.selectionStart = field.selectionEnd = start + value.length;
    field.focus();
}

async function saveTemplate(id) {
    const arText = document.getElementById(`template_ar_${id}`).value;
    const enText = document.getElementById(`template_en_${id}`).value;
    const isEnabled = document.getElementById(`toggle_${id}`).checked;

    const payload = {
        is_enabled: isEnabled,
        message_template_ar: arText,
        message_template_en: enText
    };

    try {
        const token = localStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`/api/settings/notifications/templates/${id}`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            if (typeof notifier !== 'undefined') notifier.showToast('تم حفظ القالب بنجاح', 'success');
            // Update local data
            const idx = templatesData.findIndex(t => t.id === id);
            if (idx !== -1) {
                templatesData[idx].message_template_ar = arText;
                templatesData[idx].message_template_en = enText;
                templatesData[idx].is_enabled = isEnabled;
            }
        } else {
            throw new Error('Save failed');
        }
    } catch (error) {
        console.error('Error saving:', error);
        if (typeof notifier !== 'undefined') notifier.showToast('فشل حفظ القالب', 'error');
    }
}

async function toggleTemplate(id, isEnabled) {
    // Auto-save when toggled
    const arText = document.getElementById(`template_ar_${id}`).value;
    const enText = document.getElementById(`template_en_${id}`).value;

    const payload = {
        is_enabled: isEnabled,
        message_template_ar: arText,
        message_template_en: enText
    };

    try {
        const token = localStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`/api/settings/notifications/templates/${id}`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(payload)
        });
        if (response.ok) {
            if (typeof notifier !== 'undefined') notifier.showToast('تم تحديث الحالة', 'success');
        }
    } catch (e) {
        console.error(e);
        if (typeof notifier !== 'undefined') notifier.showToast('فشل تحديث الحالة', 'error');
    }
}

function previewTemplate(id) {
    const template = templatesData.find(t => t.id === id);
    if (!template) return;

    // Get current value from textarea (unsaved changes)
    let arText = document.getElementById(`template_ar_${id}`).value;

    // Dummy Data Substitution
    let previewText = arText || "لا يوجد نص للرسالة";

    const dummyData = {
        '{customer_name}': 'عبدالله محمد',
        '{order_id}': '#1024',
        '{order_status}': STATUS_NAMES[template.event_type] || 'جديد',
        '{order_url}': 'https://z.id/xyz123',
        '{store_name}': 'متجر زد التجريبي'
    };

    for (const [key, value] of Object.entries(dummyData)) {
        previewText = previewText.replaceAll(key, value);
    }

    document.getElementById('previewMessageBody').textContent = previewText;
    document.getElementById('previewStatusTitle').textContent = STATUS_NAMES[template.event_type];

    // Show Modal
    if (typeof bootstrap !== 'undefined') {
        const modalEl = document.getElementById('previewModal');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}
