
const VALID_STATUSES = ['new', 'processing', 'ready', 'delivering', 'completed', 'cancelled'];
let currentEmails = [];
let currentNotifications = {};
let emailModal = null; // Bootstrap Modal instance

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Bootstrap Modal
    const modalEl = document.getElementById('addEmailModal');
    if (modalEl) {
        // eslint-disable-next-line no-undef
        if (typeof bootstrap !== 'undefined') {
            emailModal = new bootstrap.Modal(modalEl);
        }
    }

    await loadSettings();
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings/general');
        if (response.ok) {
            const data = await response.json();

            // Load Notifications
            if (data.staff_notifications) {
                currentNotifications = data.staff_notifications;
                updateToggles();
            } else {
                // Default all false if empty
                VALID_STATUSES.forEach(s => currentNotifications[s] = false);
            }

            // Load Emails
            if (data.staff_emails) {
                currentEmails = data.staff_emails;
            }
            renderEmails();
        } else {
            console.error('Failed to load settings');
            if (typeof notifier !== 'undefined') notifier.showToast('فشل تحميل الإعدادات', 'error');
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        if (typeof notifier !== 'undefined') notifier.showToast('حدث خطأ أثناء تحميل الإعدادات', 'error');
    }
}

function updateToggles() {
    VALID_STATUSES.forEach(status => {
        const checkbox = document.getElementById(`notify_${status}`);
        if (checkbox) {
            checkbox.checked = !!currentNotifications[status];
        }
    });
}

function renderEmails() {
    const list = document.getElementById('emailsList');
    const emptyState = document.getElementById('emptyEmailsState');

    if (!list) return;

    // Clear list
    list.innerHTML = '';

    if (currentEmails.length === 0) {
        if (emptyState) {
            list.appendChild(emptyState);
            emptyState.classList.remove('d-none');
        }
    } else {
        if (emptyState) emptyState.classList.add('d-none');
        // We still need to append emptyState to keep it in DOM for later, but hidden? 
        // Or re-create it? It is better to just keep it hidden in the list or outside.
        // My previous code appended it back.
        if (emptyState) list.appendChild(emptyState);

        currentEmails.forEach((email, index) => {
            const emailRow = document.createElement('div');
            emailRow.className = 'email-item';
            emailRow.innerHTML = `
                <div class="d-flex align-items-center gap-3">
                    <div class="email-icon-wrapper">
                        <i class="fa-regular fa-envelope"></i>
                    </div>
                    <span class="text-dark fw-medium">${escapeHtml(email)}</span>
                </div>
                <button onclick="removeEmail(${index})" class="btn btn-link text-secondary p-2 text-decoration-none" title="حذف">
                    <i class="fa-solid fa-trash-can hover-danger"></i>
                </button>
            `;
            list.appendChild(emailRow);
        });
    }
}

async function saveSettings() {
    // Collect toggle states
    const updatedNotifications = {};
    VALID_STATUSES.forEach(status => {
        const checkbox = document.getElementById(`notify_${status}`);
        if (checkbox) {
            updatedNotifications[status] = checkbox.checked;
        }
    });

    const payload = {
        staff_notifications: updatedNotifications,
        staff_emails: currentEmails
    };

    try {
        const response = await fetch('/api/settings/store', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            if (typeof notifier !== 'undefined') notifier.showToast('تم حفظ الإعدادات بنجاح', 'success');
        } else {
            console.error('Save failed', response.status);
            if (typeof notifier !== 'undefined') notifier.showToast('فشل حفظ الإعدادات', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        if (typeof notifier !== 'undefined') notifier.showToast('حدث خطأ أثناء حفظ الإعدادات', 'error');
    }
}

// Modal Functions
function openAddEmailModal() {
    if (emailModal) {
        document.getElementById('newEmailInput').value = '';
        document.getElementById('emailError').classList.add('d-none');
        emailModal.show();
        // Focus input after modal transition
        setTimeout(() => document.getElementById('newEmailInput').focus(), 500);
    } else {
        console.warn('Bootstrap modal not initialized');
    }
}

function closeAddEmailModal() {
    if (emailModal) {
        emailModal.hide();
    }
}

function confirmAddEmail() {
    const emailInput = document.getElementById('newEmailInput');
    const email = emailInput.value.trim();

    if (!validateEmail(email)) {
        document.getElementById('emailError').classList.remove('d-none');
        return;
    }

    if (currentEmails.includes(email)) {
        if (typeof notifier !== 'undefined') notifier.showToast('هذا البريد الإلكتروني مضاف بالفعل', 'warning');
        return;
    }

    currentEmails.push(email);
    renderEmails();
    closeAddEmailModal();
}

function removeEmail(index) {
    // Use notifier.showConfirm if available, otherwise native confirm
    if (typeof notifier !== 'undefined') {
        notifier.showConfirm('هل أنت متأكد من حذف هذا البريد؟').then(confirmed => {
            if (confirmed) {
                currentEmails.splice(index, 1);
                renderEmails();
            }
        });
    } else {
        if (confirm('هل أنت متأكد من حذف هذا البريد؟')) {
            currentEmails.splice(index, 1);
            renderEmails();
        }
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
