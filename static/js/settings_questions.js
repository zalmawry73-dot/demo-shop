document.addEventListener('DOMContentLoaded', async function () {
    await loadSettings();
});

let currentSettings = {};

async function loadSettings() {
    try {
        const response = await fetch('/api/settings/general');

        if (!response.ok) throw new Error('Failed to load settings');

        const settings = await response.json();
        currentSettings = settings;

        // Set toggles
        document.getElementById('customerNotificationToggle').checked = settings.is_question_customer_notification_enabled || false;
        document.getElementById('merchantNotificationToggle').checked = settings.is_question_merchant_notification_enabled || false;

        // Handle Merchant Email Section visibility
        toggleMerchantEmailSection(settings.is_question_merchant_notification_enabled);

        // Set Email Display
        const email = settings.question_notification_email || 'demostorezid@gmail.com';
        document.getElementById('currentEmailDisplay').innerText = email;

        // Setup Toggles Event Listeners
        document.getElementById('merchantNotificationToggle').addEventListener('change', function (e) {
            toggleMerchantEmailSection(e.target.checked);
        });

    } catch (error) {
        console.error('Error loading settings:', error);
        if (window.notifier) window.notifier.showToast('فشل في تحميل الإعدادات', 'error');
    }
}

function toggleMerchantEmailSection(show) {
    const section = document.getElementById('merchantEmailSection');
    if (show) {
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
}

async function saveSettings() {
    const customerEnabled = document.getElementById('customerNotificationToggle').checked;
    const merchantEnabled = document.getElementById('merchantNotificationToggle').checked;

    // Fallback if user toggles but didn't open modal, we keep existing email or default if not set
    // Ideally we should send the email currently in state/display if we wanted to be sure, 
    // but the backend only updates fields present in payload schema if we send them. 
    // The StoreSettingsUpdate schema has all fields optional.

    const payload = {
        is_question_customer_notification_enabled: customerEnabled,
        is_question_merchant_notification_enabled: merchantEnabled
    };

    try {
        const response = await fetch('/api/settings/store', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to save settings');

        if (window.notifier) window.notifier.showToast('تم حفظ الإعدادات بنجاح', 'success');

    } catch (error) {
        console.error('Error saving settings:', error);
        if (window.notifier) window.notifier.showToast('فشل في حفظ الإعدادات', 'error');
    }
}

// Modal Functions
function openPreviewModal() {
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

function openEmailModal() {
    const modal = new bootstrap.Modal(document.getElementById('emailModal'));

    // Populate dropdown
    const select = document.getElementById('teamMemberSelect');
    select.innerHTML = ''; // Clear

    // Add current or default option
    const options = [
        { name: 'متجر تجريبي (demostorezid@gmail.com)', value: 'demostorezid@gmail.com' }
    ];

    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.text = opt.name;
        if (opt.value === (currentSettings.question_notification_email || 'demostorezid@gmail.com')) {
            option.selected = true;
        }
        select.appendChild(option);
    });

    modal.show();
}

async function saveEmailChange() {
    const select = document.getElementById('teamMemberSelect');
    const selectedEmail = select.value;

    if (!selectedEmail) {
        return;
    }

    // Update local display immediately
    document.getElementById('currentEmailDisplay').innerText = selectedEmail;

    // Persist to backend
    try {
        const response = await fetch('/api/settings/store', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_notification_email: selectedEmail
            })
        });

        if (!response.ok) throw new Error('Failed to update email');

        currentSettings.question_notification_email = selectedEmail;
        if (window.notifier) window.notifier.showToast('تم تحديث البريد الإلكتروني بنجاح', 'success');

        // Close modal
        const modalEl = document.getElementById('emailModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();

    } catch (error) {
        console.error('Error updating email:', error);
        if (window.notifier) window.notifier.showToast('فشل في تحديث البريد الإلكتروني', 'error');
    }
}

function navigateToAddMember() {
    if (window.notifier) window.notifier.showToast('سيتم توجيهك لصفحة الفريق (قيد التطوير)', 'info');
}
