/**
 * Professional Notification System
 * Handles Toast Notifications (Transient) and Static Alerts (Persistent)
 */
class NotificationManager {
    constructor() {
        this.toastContainer = document.createElement('div');
        this.toastContainer.className = 'toast-container';
        document.body.appendChild(this.toastContainer);
    }

    /**
     * Show a transient toast notification
     * @param {string} message - The message to display
     * @param {string} type - 'success', 'info', 'error' (or 'danger'), 'warning'
     * @param {number} duration - Time in ms before auto-dismiss
     */
    showToast(message, type = 'success', duration = 4000) {
        // Normalize type
        if (type === 'error') type = 'danger';

        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type}`;

        let icon = 'fa-check-circle';
        if (type === 'info') icon = 'fa-info-circle';
        if (type === 'danger') icon = 'fa-exclamation-circle';
        if (type === 'warning') icon = 'fa-exclamation-triangle';

        toast.innerHTML = `
            <div class="d-flex align-items-center gap-2">
                <i class="fas ${icon} fa-lg"></i>
                <span class="toast-message">${message}</span>
            </div>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        `;

        this.toastContainer.appendChild(toast);

        // Slide in animation handled by CSS keyframes on .toast-item

        // Auto dismiss
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s forwards';
            toast.addEventListener('animationend', () => {
                toast.remove();
            });
        }, duration);
    }

    /**
     * Show a persistent static alert in a specific container
     * @param {string} containerId - ID of the element to append the alert to (e.g., 'main-content')
     * @param {string} message - The message to display
     * @param {string} type - 'warning', 'danger', 'info', 'success'
     * @param {boolean} isDismissible - Whether the user can close it
     */
    showAlert(containerId, message, type = 'warning', isDismissible = true) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found.`);
            return;
        }

        const alert = document.createElement('div');
        alert.className = `alert-static-banner alert-${type}`;

        let icon = 'fa-exclamation-triangle';
        if (type === 'danger') icon = 'fa-circle-xmark';
        if (type === 'info') icon = 'fa-info-circle';
        if (type === 'success') icon = 'fa-check-circle';

        alert.innerHTML = `
            <div class="d-flex align-items-center gap-3">
                <div class="alert-icon-wrapper">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="alert-content">
                    <span class="alert-message fw-bold">${message}</span>
                </div>
            </div>
            ${isDismissible ? '<button class="alert-close"><i class="fas fa-times"></i></button>' : ''}
        `;

        // Prepend to ensure it's at the top
        container.insertBefore(alert, container.firstChild);

        if (isDismissible) {
            alert.querySelector('.alert-close').addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
        }
    }

    /**
     * Show a confirmation modal
     * @param {string} message - The question to ask
     * @returns {Promise<boolean>} - Resolves true if confirmed, false otherwise
     */
    showConfirm(message) {
        return new Promise((resolve) => {
            const modalEl = document.getElementById('confirmationModal');
            if (!modalEl) {
                console.warn('Confirmation Modal not found in DOM');
                return resolve(window.confirm(message));
            }

            const msgEl = document.getElementById('confirmationMessage');
            if (msgEl) msgEl.textContent = message;

            const confirmBtn = document.getElementById('confirmActionBtn');
            const bsModal = new bootstrap.Modal(modalEl);

            let handled = false;

            const onConfirm = () => {
                handled = true;
                bsModal.hide();
                resolve(true);
            };

            const onDismiss = () => {
                if (!handled) resolve(false);
            };

            // Use onclick to avoid stacking listeners
            confirmBtn.onclick = onConfirm;

            modalEl.addEventListener('hidden.bs.modal', onDismiss, { once: true });

            bsModal.show();
        });
    }
    // --- Flash Toast Helpers ---
    showFlashToast(message, type = 'success') {
        sessionStorage.setItem('pending_toast', JSON.stringify({ message, type }));
    }

    checkPendingToast() {
        const pending = sessionStorage.getItem('pending_toast');
        if (pending) {
            try {
                const { message, type } = JSON.parse(pending);
                this.showToast(message, type);
            } catch (e) {
                console.error('Failed to parse pending toast', e);
            }
            sessionStorage.removeItem('pending_toast');
        }
    }
}

// Initialize on window load
window.addEventListener('DOMContentLoaded', () => {
    window.notifier = new NotificationManager();
    window.notifier.checkPendingToast();
});
