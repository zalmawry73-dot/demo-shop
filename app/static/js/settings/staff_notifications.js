
const VALID_STATUSES = ['new', 'processing', 'ready', 'delivering', 'completed', 'cancelled'];
let currentEmails = [];
let currentNotifications = {
    "new": false,
    "processing": false,
    "ready": false,
    "delivering": false,
    "completed": false,
    "cancelled": false
};

document.addEventListener('DOMContentLoaded', async () => {
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
            }

            // Load Emails
            if (data.staff_emails) {
                currentEmails = data.staff_emails;
                renderEmails();
            }
        } else {
            console.error('Failed to load settings');
            NotificationManager.showToast('فشل تحميل الإعدادات', 'error');
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        NotificationManager.showToast('حدث خطأ أثناء تحميل الإعدادات', 'error');
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

    // Clear list (except empty state which is hidden/processed)
    list.innerHTML = '';
    list.appendChild(emptyState);

    if (currentEmails.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');

        currentEmails.forEach((email, index) => {
            const emailRow = document.createElement('div');
            emailRow.className = 'flex items-center justify-between py-3 border-b border-gray-50 last:border-0';
            emailRow.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-purple-50 flex items-center justify-center text-purple-600">
                        <i class="far fa-envelope"></i>
                    </div>
                    <span class="text-gray-700 font-medium">${escapeHtml(email)}</span>
                </div>
                <button onclick="removeEmail(${index})" class="text-gray-400 hover:text-red-500 transition-colors p-2">
                    <i class="fas fa-trash-alt"></i>
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
            NotificationManager.showToast('تم حفظ الإعدادات بنجاح', 'success');
        } else {
            NotificationManager.showToast('فشل حفظ الإعدادات', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        NotificationManager.showToast('حدث خطأ أثناء حفظ الإعدادات', 'error');
    }
}

// Modal Functions
function openAddEmailModal() {
    document.getElementById('addEmailModal').classList.remove('hidden');
    document.getElementById('newEmailInput').value = '';
    document.getElementById('emailError').classList.add('hidden');
    document.getElementById('newEmailInput').focus();
}

function closeAddEmailModal() {
    document.getElementById('addEmailModal').classList.add('hidden');
}

function confirmAddEmail() {
    const emailInput = document.getElementById('newEmailInput');
    const email = emailInput.value.trim();

    if (!validateEmail(email)) {
        document.getElementById('emailError').classList.remove('hidden');
        return;
    }

    if (currentEmails.includes(email)) {
        NotificationManager.showToast('هذا البريد الإلكتروني مضاف بالفعل', 'warning');
        return;
    }

    currentEmails.push(email);
    renderEmails();
    closeAddEmailModal();
    // Optional: Auto-save or wait for main save button? 
    // User requirement: "When clicking 'Add Email', a window opens to add and save the email."
    // This implies adding it to the list. Usually "Save" on the page is needed to persist to DB 
    // unless the modal specifically says "Save" and performs an API call. 
    // The "Save" button on the top right usually saves EVERYTHING.
    // However, to be safe and interactive, I'll just update local state and let user click "Save" on top, 
    // OR I can save immediately. Given the UI has a global "Save" button, it's better to just update local state.
    // BUT the modal button says "Hafz" (Save). 
    // I will stick to updating local state for now to allow bulk edits, but if the user wants immediate save, I can add it.
    // For now, consistent with common patterns: Modal adds to list, Page Save commits to DB.
}

function removeEmail(index) {
    if (confirm('هل أنت متأكد من حذف هذا البريد؟')) {
        currentEmails.splice(index, 1);
        renderEmails();
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
