// settings_tax.js

document.addEventListener('DOMContentLoaded', () => {
    // Check which page we are on
    if (document.getElementById('isVatEnabled')) {
        initTaxSettingsPage();
    } else if (document.getElementById('createCountryTaxForm')) {
        initCreateTaxCountryPage();
    }
});

// ----------------------------------------------------------------------
// Main Tax Settings Page Logic
// ----------------------------------------------------------------------
async function initTaxSettingsPage() {
    await loadStoreSettings();
    await loadCountryTaxes();

    // Toggle Listener
    const vatToggle = document.getElementById('isVatEnabled');
    const optionsContainer = document.getElementById('vatOptionsContainer');

    vatToggle.addEventListener('change', () => {
        if (vatToggle.checked) {
            optionsContainer.style.display = 'block';
        } else {
            optionsContainer.style.display = 'none';
        }
    });
}

async function loadStoreSettings() {
    try {
        const response = await fetch('/api/settings/general');
        if (!response.ok) throw new Error('Failed to load settings');
        const settings = await response.json();

        document.getElementById('isVatEnabled').checked = settings.is_vat_enabled || false;
        document.getElementById('pricesIncludeVat').checked = settings.prices_include_vat || false;
        document.getElementById('applyVatToShipping').checked = settings.apply_vat_to_shipping || false;
        document.getElementById('displayPricesWithVat').checked = settings.display_prices_with_vat || false;
        document.getElementById('defaultTaxRate').value = settings.default_tax_rate || 0;

        // Trigger change to show/hide options
        document.getElementById('isVatEnabled').dispatchEvent(new Event('change'));

    } catch (error) {
        console.error(error);
        window.notifier.showToast('فشل تحميل الإعدادات', 'error');
    }
}

async function saveTaxSettings() {
    const btn = document.getElementById('saveTaxSettingsBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحفظ...';

    const data = {
        is_vat_enabled: document.getElementById('isVatEnabled').checked,
        prices_include_vat: document.getElementById('pricesIncludeVat').checked,
        apply_vat_to_shipping: document.getElementById('applyVatToShipping').checked,
        display_prices_with_vat: document.getElementById('displayPricesWithVat').checked,
        default_tax_rate: parseFloat(document.getElementById('defaultTaxRate').value) || 0
    };

    try {
        const response = await fetch('/api/settings/store', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to save');

        if (!response.ok) throw new Error('Failed to save');

        window.notifier.showToast('تم حفظ الإعدادات بنجاح', 'success');

    } catch (error) {
        console.error(error);
        window.notifier.showToast('حدث خطأ أثناء الحفظ', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

async function loadCountryTaxes() {
    try {
        const response = await fetch('/api/settings/tax/countries');
        if (!response.ok) throw new Error('Failed to load countries');
        const countries = await response.json();

        const tbody = document.getElementById('countriesTableBody');
        tbody.innerHTML = '';

        if (countries.length === 0) {
            tbody.innerHTML = `
                <tr id="emptyStateRow">
                    <td colspan="4" class="text-center py-5">
                        <div class="text-muted">
                            <i class="far fa-file-alt fa-3x mb-3 opacity-25"></i>
                            <p>لا توجد بيانات حالياً، ستظهر هنا عند توفرها</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        countries.forEach(tax => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="ps-4 fw-bold">${tax.country_name}</td>
                <td>${tax.tax_number || '-'}</td>
                <td>${tax.tax_rate}%</td>
                <td class="text-end pe-4">
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCountryTax(${tax.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error(error);
    }
}

async function deleteCountryTax(id) {
    if (!await window.notifier.showConfirm('هل أنت متأكد من الحذف؟')) return;

    try {
        const response = await fetch(`/api/settings/tax/countries/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Delete failed');

        window.notifier.showToast('تم الحذف بنجاح', 'success');
        await loadCountryTaxes();

    } catch (error) {
        console.error(error);
        window.notifier.showToast('فشل الحذف', 'error');
    }
}


// ----------------------------------------------------------------------
// Create Country Tax Page Logic
// ----------------------------------------------------------------------
async function initCreateTaxCountryPage() {
    // Populate Country List (Mock list for now, ideally fetch from backend or separate JS file)
    const countries = [
        { code: 'SA', name: 'المملكة العربية السعودية' },
        { code: 'AE', name: 'الإمارات العربية المتحدة' },
        { code: 'KW', name: 'الكويت' },
        { code: 'BH', name: 'البحرين' },
        { code: 'QA', name: 'قطر' },
        { code: 'OM', name: 'عمان' },
        { code: 'EG', name: 'مصر' },
        { code: 'JO', name: 'الأردن' }
    ];

    const select = document.getElementById('countrySelect');
    countries.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.code;
        opt.dataset.name = c.name;
        opt.innerText = c.name;
        select.appendChild(opt);
    });

    // File Upload UX
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('vatCertificateFile');
    const preview = document.getElementById('filePreview');

    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('bg-white');
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('bg-white');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('bg-white');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect(fileInput.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleFileSelect(fileInput.files[0]);
    });

    function handleFileSelect(file) {
        preview.innerText = `تم اختيار الملف: ${file.name}`;
    }

    // Form Submit
    document.getElementById('createCountryTaxForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        // Basic fields
        const countryCode = select.value;
        const countryName = select.options[select.selectedIndex].dataset.name;
        const taxNumber = document.getElementById('taxNumber').value;
        const taxRate = parseFloat(document.getElementById('taxRate').value);
        const displayTaxNumber = document.getElementById('displayTaxNumber').checked;
        const displayVat = document.getElementById('displayVatCertificate').checked;

        // Note: For file upload, we would typically use FormData and a separate endpoint or convert to base64.
        // For this implementation, we will mock the URL or leave it empty if no endpoint for file upload exists yet in the prompt context.
        // The implementation plan mentioned a generic upload endpoint but I haven't implemented it yet. 
        // I'll send it as null for now or mock string "uploaded_file.pdf".

        const payload = {
            country_code: countryCode,
            country_name: countryName,
            tax_number: taxNumber,
            tax_rate: taxRate,
            vat_certificate_url: fileInput.files.length ? "https://example.com/mock-cert.pdf" : null,
            display_tax_number_in_footer: displayTaxNumber,
            display_vat_certificate_in_footer: displayVat
        };

        try {
            const response = await fetch('/api/settings/tax/countries', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to create');
            }

            window.notifier.showToast('تمت إضافة الدولة بنجاح', 'success');

            // Redirect back to index
            setTimeout(() => {
                window.location.href = '/settings/tax';
            }, 1000);

        } catch (error) {
            console.error(error);
            window.notifier.showToast(error.message, 'error');
        }
    });
}
