let isEnabled = false;
let dailySchedule = {}; // { dayKey: { enabled: bool, periods: [{from, to}] } }

const DAYS = [
    { key: 'sunday', label: 'الأحد' },
    { key: 'monday', label: 'الإثنين' },
    { key: 'tuesday', label: 'الثلاثاء' },
    { key: 'wednesday', label: 'الأربعاء' },
    { key: 'thursday', label: 'الخميس' },
    { key: 'friday', label: 'الجمعة' },
    { key: 'saturday', label: 'السبت' },
];

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings/general');
        if (!response.ok) throw new Error('Failed to load settings');

        const settings = await response.json();

        // State
        isEnabled = settings.maintenance_mode_enabled || false;
        dailySchedule = settings.maintenance_daily_schedule || {};

        // Initialize daily schedule object if empty
        DAYS.forEach(day => {
            if (!dailySchedule[day.key]) {
                dailySchedule[day.key] = { enabled: false, periods: [] };
            }
        });

        // Fields
        setRadioValue('maintenanceType', settings.maintenance_type || 'fully_closed');
        document.getElementById('periodType').value = settings.maintenance_period_type || 'unlimited';
        document.getElementById('maintenanceMinutes').value = settings.maintenance_minutes || '';
        document.getElementById('maintenanceHours').value = settings.maintenance_hours || '';
        document.getElementById('maintenanceStartAt').value = formatDateTime(settings.maintenance_start_at);
        document.getElementById('maintenanceEndAt').value = formatDateTime(settings.maintenance_end_at);
        document.getElementById('showCountdown').checked = settings.maintenance_show_countdown || false;

        document.getElementById('titleAr').value = settings.maintenance_title_ar || '';
        document.getElementById('titleEn').value = settings.maintenance_title_en || '';
        document.getElementById('messageAr').value = settings.maintenance_message_ar || '';
        document.getElementById('messageEn').value = settings.maintenance_message_en || '';

        // Render Scheduled Days
        renderDailySchedule();

        // Initial UI Update
        updateFeatureState();
        updateUI();

    } catch (error) {
        console.error('Error loading settings:', error);
        if (window.notifier) window.notifier.showToast('فشل تحميل الإعدادات', 'error');
    }
}

function updateFeatureState() {
    const content = document.getElementById('featureContent');
    const btn = document.getElementById('toggleFeatureBtn');

    if (isEnabled) {
        content.classList.remove('opacity-50');
        content.style.pointerEvents = 'auto';
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-outline-danger');
        btn.innerText = 'تعطيل الميزة';
    } else {
        content.classList.add('opacity-50');
        content.style.pointerEvents = 'none';
        btn.classList.remove('btn-outline-danger');
        btn.classList.add('btn-outline-primary');
        btn.innerText = 'تفعيل الميزة';
    }
}

function toggleFeature() {
    isEnabled = !isEnabled;
    updateFeatureState();
}

function updateUI() {
    const type = document.querySelector('input[name="maintenanceType"]:checked').value;
    const period = document.getElementById('periodType').value;

    // Warning Text
    const warningText = document.getElementById('warningText');
    if (type === 'fully_closed') {
        warningText.innerText = 'سيتم إغلاق متجرك بالكامل خلال الفترات المحددة. لن يتمكن العملاء من تصفح المتجر.';
    } else {
        warningText.innerText = 'لن يتمكن العملاء من إتمام عمليات الشراء أثناء تعليق المتجر، لكن يمكنهم تصفح المنتجات وإضافتها إلى السلة فقط.';
    }

    // Hide all groups first
    document.querySelectorAll('.period-group').forEach(el => el.classList.add('d-none'));

    // Show Unlimited Group
    if (period === 'unlimited') {
        document.getElementById('group_unlimited').classList.remove('d-none');
    }

    // Show Minutes Group
    if (period === 'minutes') {
        document.getElementById('group_minutes').classList.remove('d-none');
        document.getElementById('group_countdown').classList.remove('d-none');
    }

    // Show Hours Group
    if (period === 'hours') {
        document.getElementById('group_hours').classList.remove('d-none');
        document.getElementById('group_countdown').classList.remove('d-none');
    }

    // Show Scheduled Group
    if (period === 'scheduled') {
        document.getElementById('group_scheduled_start').classList.remove('d-none');
        document.getElementById('group_scheduled_end').classList.remove('d-none');
    }

    // Show Daily Schedule Group
    if (period === 'daily_schedule') {
        document.getElementById('group_daily_schedule').classList.remove('d-none');
    }
}

function renderDailySchedule() {
    const container = document.getElementById('dailyScheduleContainer');
    container.innerHTML = '';

    DAYS.forEach(day => {
        const schedule = dailySchedule[day.key] || { enabled: false, periods: [] };
        const isDayEnabled = schedule.enabled;

        const dayRow = document.createElement('div');
        dayRow.className = 'card border-0 shadow-sm p-3 bg-light';
        dayRow.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span class="fw-bold">${day.label}</span>
                <div class="form-check form-switch fs-4 m-0">
                    <input class="form-check-input" type="checkbox" role="switch" 
                        onchange="toggleDay('${day.key}', this.checked)" ${isDayEnabled ? 'checked' : ''}>
                </div>
            </div>
            
            <div class="${isDayEnabled ? '' : 'd-none'} mt-3" id="periods_${day.key}">
                <div class="d-flex flex-column gap-2" id="periodsList_${day.key}">
                    <!-- Periods go here -->
                </div>
                <button class="btn btn-sm btn-outline-secondary mt-2 rounded-pill px-3" onclick="addPeriod('${day.key}')">
                    <i class="fa-solid fa-plus me-1"></i> إضافة فترة
                </button>
            </div>
        `;

        container.appendChild(dayRow);

        // Render existing periods
        if (isDayEnabled && schedule.periods) {
            schedule.periods.forEach((p, index) => renderPeriodRow(day.key, index, p.from, p.to));
        }
    });
}

function toggleDay(dayKey, checked) {
    dailySchedule[dayKey].enabled = checked;
    if (checked && dailySchedule[dayKey].periods.length === 0) {
        // Add default period if enabled and empty
        dailySchedule[dayKey].periods.push({ from: '09:00', to: '17:00' });
    }
    renderDailySchedule();
}

function addPeriod(dayKey) {
    // defaults
    dailySchedule[dayKey].periods.push({ from: '09:00', to: '17:00' });
    renderDailySchedule();
}

function removePeriod(dayKey, index) {
    dailySchedule[dayKey].periods.splice(index, 1);
    renderDailySchedule();
}

function updatePeriodValue(dayKey, index, field, value) {
    dailySchedule[dayKey].periods[index][field] = value;
}

function renderPeriodRow(dayKey, index, fromVal, toVal) {
    const list = document.getElementById(`periodsList_${dayKey}`);

    // Create element with standard JS to avoid innerHTML reload issues
    const row = document.createElement('div');
    row.className = 'd-flex gap-2 align-items-center bg-white p-2 rounded border';

    // Generate Time Options helper
    const timeOptions = generateTimeOptions();

    row.innerHTML = `
        <div class="flex-grow-1">
            <select class="form-select form-select-sm" onchange="updatePeriodValue('${dayKey}', ${index}, 'from', this.value)">
                ${timeOptions.map(t => `<option value="${t}" ${t === fromVal ? 'selected' : ''}>${formatTimeLabel(t)}</option>`).join('')}
            </select>
        </div>
        <span class="text-muted">إلى</span>
        <div class="flex-grow-1">
            <select class="form-select form-select-sm" onchange="updatePeriodValue('${dayKey}', ${index}, 'to', this.value)">
                ${timeOptions.map(t => `<option value="${t}" ${t === toVal ? 'selected' : ''}>${formatTimeLabel(t)}</option>`).join('')}
            </select>
        </div>
        <button class="btn btn-link text-danger p-0 ms-2" onclick="removePeriod('${dayKey}', ${index})">
            <i class="fa-solid fa-trash-can"></i>
        </button>
    `;
    list.appendChild(row);
}

function generateTimeOptions() {
    const times = [];
    for (let i = 0; i < 24; i++) {
        for (let j = 0; j < 60; j += 15) {
            const h = i.toString().padStart(2, '0');
            const m = j.toString().padStart(2, '0');
            times.push(`${h}:${m}`);
        }
    }
    times.push('23:59'); // Add end of day
    return times;
}

function formatTimeLabel(time) {
    // 13:00 -> 01:00 PM
    const [h, m] = time.split(':');
    let hour = parseInt(h);
    const ampm = hour >= 12 ? 'م' : 'ص';
    hour = hour % 12;
    hour = hour ? hour : 12; // the hour '0' should be '12'
    return `${hour}:${m} ${ampm}`;
}

async function saveSettings() {
    const btn = document.getElementById('saveBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'جاري الحفظ...';

    const payload = {
        maintenance_mode_enabled: isEnabled,
        maintenance_type: document.querySelector('input[name="maintenanceType"]:checked').value,
        maintenance_period_type: document.getElementById('periodType').value,
        maintenance_minutes: parseInt(document.getElementById('maintenanceMinutes').value) || null,
        maintenance_hours: parseInt(document.getElementById('maintenanceHours').value) || null,
        maintenance_start_at: document.getElementById('maintenanceStartAt').value || null,
        maintenance_end_at: document.getElementById('maintenanceEndAt').value || null,
        maintenance_show_countdown: document.getElementById('showCountdown').checked,

        maintenance_title_ar: document.getElementById('titleAr').value,
        maintenance_title_en: document.getElementById('titleEn').value,
        maintenance_message_ar: document.getElementById('messageAr').value,
        maintenance_message_en: document.getElementById('messageEn').value,

        maintenance_daily_schedule: dailySchedule
    };

    try {
        const response = await fetch('/api/settings/store', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to save');
        if (window.notifier) window.notifier.showToast('تم حفظ إعدادات ساعات العمل بنجاح', 'success');

    } catch (error) {
        console.error('Error saving:', error);
        if (window.notifier) window.notifier.showToast('فشل حفظ الإعدادات', 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

function showExample() {
    const modal = new bootstrap.Modal(document.getElementById('exampleModal'));

    // Update Preview Content
    const title = document.getElementById('titleAr').value || 'المتجر تحت التطوير';
    const message = document.getElementById('messageAr').value || 'نعتذر عن إغلاق المتجر مؤقتاً...';

    document.getElementById('previewTitle').innerText = title;
    document.getElementById('previewMessage').innerText = message;

    const type = document.querySelector('input[name="maintenanceType"]:checked').value;
    const period = document.getElementById('periodType').value;
    const showCountdown = document.getElementById('showCountdown').checked;

    const countdownEl = document.getElementById('previewCountdown');
    const stopOrdersEl = document.getElementById('previewStopOrders');

    countdownEl.classList.add('d-none');
    stopOrdersEl.classList.add('d-none');

    if (type === 'fully_closed' && (period === 'minutes' || period === 'hours') && showCountdown) {
        countdownEl.classList.remove('d-none');
    }

    if (type === 'stop_orders') {
        stopOrdersEl.classList.remove('d-none');
    }

    modal.show();
}

// Helpers
function setRadioValue(name, value) {
    const radios = document.getElementsByName(name);
    for (const radio of radios) {
        if (radio.value === value) {
            radio.checked = true;
            break;
        }
    }
}

function formatDateTime(isoString) {
    if (!isoString) return '';
    // Convert generic ISO to datetime-local format (YYYY-MM-DDTHH:MM)
    return new Date(isoString).toISOString().slice(0, 16);
}
