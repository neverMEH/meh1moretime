// Main application JavaScript
const API_BASE = window.location.origin;
let currentAccount = null;

// DOM Elements
const connectBtn = document.getElementById('connectBtn');
const dashboardBtn = document.getElementById('dashboardBtn');
const addAccountModal = document.getElementById('addAccountModal');
const successModal = document.getElementById('successModal');
const accountForm = document.getElementById('accountForm');
const cancelBtn = document.getElementById('cancelBtn');
const authorizeBtn = document.getElementById('authorizeBtn');
const loadingOverlay = document.getElementById('loadingOverlay');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkForOAuthCallback();
});

function setupEventListeners() {
    // Connect button
    if (connectBtn) {
        connectBtn.addEventListener('click', () => {
            showModal(addAccountModal);
        });
    }

    // Dashboard button
    if (dashboardBtn) {
        dashboardBtn.addEventListener('click', () => {
            window.location.href = '/dashboard';
        });
    }

    // Account form submission
    if (accountForm) {
        accountForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await createAccount();
        });
    }

    // Cancel button
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            hideModal(addAccountModal);
        });
    }

    // Authorize button
    if (authorizeBtn) {
        authorizeBtn.addEventListener('click', () => {
            if (currentAccount) {
                authorizeAccount(currentAccount);
            }
        });
    }

    // Close modal buttons
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                hideModal(modal);
            }
        });
    });

    // Click outside modal to close
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            hideModal(e.target);
        }
    });
}

async function createAccount() {
    const formData = new FormData(accountForm);
    const data = {
        account_name: formData.get('accountName'),
        client_id: formData.get('clientId'),
        client_secret: formData.get('clientSecret'),
        redirect_uri: formData.get('redirectUri') || window.location.origin + '/callback'
    };

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/web/accounts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            currentAccount = result;
            hideModal(addAccountModal);
            showModal(successModal);

            // Store account ID in session storage for OAuth flow
            sessionStorage.setItem('pendingAccountId', result.id);
            sessionStorage.setItem('pendingAccountName', result.account_name);
        } else {
            showToast('Error creating account: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to create account. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

function authorizeAccount(account) {
    // Get OAuth URL and redirect
    fetch(`${API_BASE}/web/oauth/${account.id}`, {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.auth_url) {
            // Open in same window for OAuth flow
            window.location.href = data.auth_url;
        }
    })
    .catch(error => {
        console.error('Error getting OAuth URL:', error);
        showToast('Failed to get authorization URL', 'error');
    });
}

function checkForOAuthCallback() {
    // Check if we're returning from OAuth
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');

    if (code) {
        // Handle OAuth callback
        handleOAuthCallback(code);
    } else if (error) {
        showToast('Authorization failed: ' + error, 'error');
        // Clear the URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

async function handleOAuthCallback(code) {
    const accountId = sessionStorage.getItem('pendingAccountId');
    const accountName = sessionStorage.getItem('pendingAccountName');

    if (!accountId) {
        showToast('No pending account found. Please start over.', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/web/callback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                account_id: accountId,
                code: code
            })
        });

        const result = await response.json();

        if (response.ok) {
            // Clear session storage
            sessionStorage.removeItem('pendingAccountId');
            sessionStorage.removeItem('pendingAccountName');

            // Show success message
            showSuccessMessage(accountName, result);

            // Redirect to dashboard after 3 seconds
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 3000);
        } else {
            showToast('Failed to complete authorization: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to complete authorization. Please try again.', 'error');
    } finally {
        hideLoading();
        // Clear the URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

function showSuccessMessage(accountName, tokenInfo) {
    const successHtml = `
        <div class="callback-card">
            <div class="callback-header">
                <i class="fas fa-check-circle success-icon"></i>
                <h1>Success!</h1>
            </div>
            <div class="callback-content">
                <p><strong>${accountName}</strong> has been connected successfully!</p>
                <p>Tokens are valid for ${tokenInfo.expires_in} seconds.</p>
                <p class="status-message">
                    <i class="fas fa-spinner fa-spin"></i>
                    Redirecting to dashboard...
                </p>
            </div>
        </div>
    `;

    // Create a temporary overlay to show success
    const overlay = document.createElement('div');
    overlay.className = 'modal show';
    overlay.innerHTML = successHtml;
    document.body.appendChild(overlay);
}

// Modal functions
function showModal(modal) {
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
    }
}

function hideModal(modal) {
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

// Loading functions
function showLoading() {
    if (loadingOverlay) {
        loadingOverlay.classList.add('show');
    }
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.classList.remove('show');
    }
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'exclamation-circle' :
                 type === 'warning' ? 'exclamation-triangle' : 'info-circle';

    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;

    // Add to page or create container
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    container.appendChild(toast);

    // Remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

// Helper function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Helper function to get time until expiry
function getTimeUntilExpiry(expiryDate) {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const diff = expiry - now;

    if (diff <= 0) {
        return 'Expired';
    }

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}