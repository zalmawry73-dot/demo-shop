/**
 * Customer Form (Create/Edit) JavaScript
 * Handles dynamic country/city dropdowns and form submission
 */

let countriesCitiesData = {};
const isEdit = window.location.pathname.includes('/edit');
const customerId = window.location.pathname.split('/')[2];

// Initialize
document.addEventListener('DOMContentLoaded', async function () {
    await loadCountriesCities();
    initializeForm();
    bindFormEvents();
});

async function loadCountriesCities() {
    try {
        const response = await fetch('/static/data/countries_cities.json');
        countriesCitiesData = await response.json();
        populateCountries();
    } catch (error) {
        console.error('Error loading countries/cities:', error);
    }
}

function populateCountries() {
    const countrySelect = document.querySelector('select[name="country"]');
    if (!countrySelect) return;

    // Get current value if exists
    const currentValue = countrySelect.value;

    // Populate countries
    countrySelect.innerHTML = Object.keys(countriesCitiesData)
        .map(country => `<option value="${country}" ${country === currentValue ? 'selected' : ''}>${country}</option>`)
        .join('');

    // If there's a current country, load its cities
    if (currentValue && countriesCitiesData[currentValue]) {
        populateCities(currentValue);
    }
}

function populateCities(country) {
    const citySelect = document.querySelector('select[name="city"]') || document.querySelector('input[name="city"]');
    if (!citySelect) return;

    const cities = countriesCitiesData[country] || [];
    const currentCity = citySelect.value;

    // Convert input to select if needed
    if (citySelect.tagName === 'INPUT') {
        const newSelect = document.createElement('select');
        newSelect.name = 'city';
        newSelect.className = citySelect.className;
        citySelect.parentNode.replaceChild(newSelect, citySelect);
        citySelect = newSelect;
    }

    if (cities.length > 0) {
        citySelect.innerHTML = '<option value="">اختر المدينة...</option>' +
            cities.map(city => `<option value="${city}" ${city === currentCity ? 'selected' : ''}>${city}</option>`)
                .join('');
    } else {
        // No cities available, convert back to input
        const newInput = document.createElement('input');
        newInput.type = 'text';
        newInput.name = 'city';
        newInput.className = citySelect.className;
        newInput.value = currentCity;
        newInput.placeholder = 'المدينة';
        citySelect.parentNode.replaceChild(newInput, citySelect);
    }
}

function initializeForm() {
    // If editing, the template already populated the form
    // Just set up country-based city loading
    const countrySelect = document.querySelector('select[name="country"]');
    if (countrySelect && countrySelect.value) {
        populateCities(countrySelect.value);
    }
}

function bindFormEvents() {
    // Country change event
    const countrySelect = document.querySelector('select[name="country"]');
    countrySelect?.addEventListener('change', function (e) {
        populateCities(e.target.value);
    });

    // Form submission
    const form = document.getElementById('customerForm');
    form?.addEventListener('submit', handleFormSubmit);
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    // Cleanup empty strings
    for (let key in data) {
        if (data[key] === '') delete data[key];
    }

    // Validate
    if (!data.name || data.name.length < 2) {
        if (window.notifier) notifier.showToast('الاسم يجب أن يكون حرفين على الأقل', 'error');
        return;
    }

    if (data.email && !isValidEmail(data.email)) {
        if (window.notifier) notifier.showToast('البريد الإلكتروني غير صحيح', 'error');
        return;
    }

    if (data.mobile && !isValidSaudiMobile(data.mobile)) {
        if (window.notifier) notifier.showToast('رقم الجوال غير صحيح. يجب أن يكون رقم سعودي', 'error');
        return;
    }

    try {
        const url = isEdit ? `/api/customers/${customerId}` : '/api/customers';
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            if (window.notifier) notifier.showFlashToast('تم حفظ العميل بنجاح', 'success');
            window.location.href = '/customers';
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'فشل الحفظ');
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.notifier) notifier.showToast(error.message || 'حدث خطأ أثناء الحفظ', 'error');
    }
}

// Validation helpers
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidSaudiMobile(mobile) {
    // Saudi mobile: starts with 966, 00966, +966, or 5, followed by 9 digits
    return /^(966|00966|\+966)?5[0-9]{8}$/.test(mobile);
}
