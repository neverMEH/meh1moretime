// Dashboard JavaScript
const API_BASE = window.location.origin;
let accounts = [];
let selectedAccount = null;

// DOM Elements
const accountsList = document.getElementById('accountsList');
const emptyState = document.getElementById('emptyState');
const totalAccounts = document.getElementById('totalAccounts');
const activeTokens = document.getElementById('activeTokens');
const expiringTokens = document.getElementById('expiringTokens');
const expiredTokens = document.getElementById('expiredTokens');
const accountModal = document.getElementById('accountModal');
const oauthModal = document.getElementById('oauthModal');
const loadingOverlay = document.getElementById('loadingOverlay');
const addAccountBtn = document.getElementById('addAccountBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadAccounts();

    // Refresh every 30 seconds
    setInterval(loadAccounts, 30000);
});

function setupEventListeners() {
    // Add account button
    if (addAccountBtn) {
        addAccountBtn.addEventListener('click', () => {
            window.location.href = '/';
        });
    }

    // OAuth form submission
    const oauthForm = document.getElementById('oauthForm');
    if (oauthForm) {
        oauthForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitAuthCode();
        });
    }

    // Close modal buttons
    document.querySelectorAll('.close, .close-modal').forEach(btn => {
        btn.addEventListener('click', (e) => {
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

async function loadAccounts() {
    try {
        const response = await fetch(`${API_BASE}/web/accounts`, {
            credentials: 'include'
        });

        if (response.ok) {
            accounts = await response.json();
            renderAccounts();
            updateStats();
        } else {
            showToast('Failed to load accounts', 'error');
        }
    } catch (error) {
        console.error('Error loading accounts:', error);
        showToast('Failed to load accounts', 'error');
    }
}

function renderAccounts() {
    if (accounts.length === 0) {
        accountsList.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    accountsList.style.display = 'grid';
    emptyState.style.display = 'none';

    accountsList.innerHTML = accounts.map(account => {
        const status = getAccountStatus(account);
        return `
            <div class="account-card" data-account-id="${account.id}">
                <div class="account-header">
                    <div class="account-name">${account.account_name}</div>
                    <div class="account-status status-${status.class}">
                        ${status.text}
                    </div>
                </div>

                <div class="account-info">
                    <div class="info-row">
                        <span class="info-label">Client ID:</span>
                        <span class="info-value">${account.client_id.substring(0, 20)}...</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Created:</span>
                        <span class="info-value">${formatDate(account.created_at)}</span>
                    </div>
                    ${account.token_info ? `
                        <div class="info-row">
                            <span class="info-label">Token Expires:</span>
                            <span class="info-value">${getTimeUntilExpiry(account.token_info.expires_at)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Refreshed:</span>
                            <span class="info-value">${account.token_info.refresh_count || 0} times</span>
                        </div>
                    ` : ''}
                </div>

                <div class="account-actions">
                    ${account.token_info && account.token_info.status === 'authenticated' ? `
                        <button class="btn-primary" onclick="viewToken('${account.id}')">
                            <i class="fas fa-key"></i> View Token
                        </button>
                        <button class="btn-secondary" onclick="refreshToken('${account.id}')">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    ` : `
                        <button class="btn-primary" onclick="authorizeAccount('${account.id}')">
                            <i class="fas fa-link"></i> Authorize
                        </button>
                    `}
                    <button class="btn-secondary" onclick="viewDetails('${account.id}')">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function getAccountStatus(account) {
    if (!account.token_info || account.token_info.status !== 'authenticated') {
        return { text: 'Not Authorized', class: 'expired' };
    }

    const expiresAt = new Date(account.token_info.expires_at);
    const now = new Date();
    const hoursUntilExpiry = (expiresAt - now) / (1000 * 60 * 60);

    if (hoursUntilExpiry <= 0) {
        return { text: 'Expired', class: 'expired' };
    } else if (hoursUntilExpiry <= 1) {
        return { text: 'Expiring Soon', class: 'expiring' };
    } else {
        return { text: 'Active', class: 'active' };
    }
}

function updateStats() {
    let active = 0;
    let expiring = 0;
    let expired = 0;

    accounts.forEach(account => {
        const status = getAccountStatus(account);
        if (status.text === 'Active') active++;
        else if (status.text === 'Expiring Soon') expiring++;
        else expired++;
    });

    totalAccounts.textContent = accounts.length;
    activeTokens.textContent = active;
    expiringTokens.textContent = expiring;
    expiredTokens.textContent = expired;
}

async function authorizeAccount(accountId) {
    const account = accounts.find(a => a.id === accountId);
    if (!account) return;

    try {
        const response = await fetch(`${API_BASE}/web/oauth/${accountId}`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (data.auth_url) {
            // Store account ID for callback
            sessionStorage.setItem('pendingAccountId', accountId);
            sessionStorage.setItem('pendingAccountName', account.account_name);

            // Open OAuth URL
            window.open(data.auth_url, '_blank');

            // Show modal for entering code
            selectedAccount = accountId;
            document.getElementById('accountId').value = accountId;
            showModal(oauthModal);

            showToast('Complete authorization in the new window, then paste the code here.', 'info');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to get authorization URL', 'error');
    }
}

async function submitAuthCode() {
    const formData = new FormData(document.getElementById('oauthForm'));
    const code = formData.get('authCode');
    const accountId = formData.get('accountId');

    if (!code || !accountId) {
        showToast('Please enter the authorization code', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/web/callback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                account_id: accountId,
                code: code
            })
        });

        const result = await response.json();

        if (response.ok) {
            hideModal(oauthModal);
            showToast('Account authorized successfully!', 'success');

            // Reload accounts
            await loadAccounts();
        } else {
            showToast('Authorization failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to complete authorization', 'error');
    } finally {
        hideLoading();
    }
}

async function viewToken(accountId) {
    showLoading();

    try {
        const response = await fetch(`${API_BASE}/web/accounts/${accountId}/token`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();

            // Show token in modal
            const modalContent = `
                <h3>Access Token</h3>
                <div class="token-info">
                    <div class="info-item">
                        <span class="info-label">Token (truncated):</span>
                        <div style="word-break: break-all; font-family: monospace; background: #f5f5f5; padding: 10px; border-radius: 4px; margin-top: 5px;">
                            ${data.access_token.substring(0, 50)}...
                        </div>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Expires in:</span>
                        <span class="info-value">${Math.floor(data.expires_in / 60)} minutes</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Expires at:</span>
                        <span class="info-value">${formatDate(data.expires_at)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Needs Refresh:</span>
                        <span class="info-value">${data.needs_refresh ? 'Yes' : 'No'}</span>
                    </div>
                </div>
                <div class="button-group" style="margin-top: 20px;">
                    <button onclick="copyTokenToClipboard('${data.access_token}')" class="btn-primary">
                        <i class="fas fa-copy"></i> Copy Full Token
                    </button>
                    <button onclick="downloadToken('${accountId}')" class="btn-secondary">
                        <i class="fas fa-download"></i> Download
                    </button>
                </div>
            `;

            document.getElementById('accountDetails').innerHTML = modalContent;
            showModal(accountModal);
        } else {
            showToast('Failed to get token', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to get token', 'error');
    } finally {
        hideLoading();
    }
}

async function refreshToken(accountId) {
    showLoading();

    try {
        const response = await fetch(`${API_BASE}/web/accounts/${accountId}/refresh`, {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            showToast('Token refreshed successfully!', 'success');

            // Reload accounts
            await loadAccounts();
        } else {
            showToast('Failed to refresh token', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to refresh token', 'error');
    } finally {
        hideLoading();
    }
}

async function viewDetails(accountId) {
    const account = accounts.find(a => a.id === accountId);
    if (!account) return;

    const modalContent = `
        <h3>${account.account_name}</h3>
        <div class="token-info">
            <div class="info-item">
                <span class="info-label">Account ID:</span>
                <span class="info-value">${account.id}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Client ID:</span>
                <span class="info-value" style="word-break: break-all;">${account.client_id}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Redirect URI:</span>
                <span class="info-value">${account.redirect_uri}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Created:</span>
                <span class="info-value">${formatDate(account.created_at)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Status:</span>
                <span class="info-value">${account.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            ${account.token_info ? `
                <h4 style="margin-top: 20px;">Token Information</h4>
                <div class="info-item">
                    <span class="info-label">Status:</span>
                    <span class="info-value">${account.token_info.status}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Expires at:</span>
                    <span class="info-value">${formatDate(account.token_info.expires_at)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Refresh Count:</span>
                    <span class="info-value">${account.token_info.refresh_count || 0}</span>
                </div>
                ${account.token_info.last_refreshed ? `
                    <div class="info-item">
                        <span class="info-label">Last Refreshed:</span>
                        <span class="info-value">${formatDate(account.token_info.last_refreshed)}</span>
                    </div>
                ` : ''}
            ` : '<p style="margin-top: 20px;">No token information available. Please authorize this account.</p>'}
        </div>
    `;

    document.getElementById('accountDetails').innerHTML = modalContent;
    showModal(accountModal);
}

// Helper functions
function copyTokenToClipboard(token) {
    navigator.clipboard.writeText(token).then(() => {
        showToast('Token copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy token', 'error');
    });
}

function downloadToken(accountId) {
    fetch(`${API_BASE}/web/accounts/${accountId}/token`, {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        const account = accounts.find(a => a.id === accountId);
        const tokenData = {
            account_name: account.account_name,
            account_id: accountId,
            access_token: data.access_token,
            expires_at: data.expires_at,
            downloaded_at: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(tokenData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `amazon-ads-token-${accountId}.json`;
        a.click();
        URL.revokeObjectURL(url);

        showToast('Token downloaded!', 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to download token', 'error');
    });
}

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

    const container = document.getElementById('toastContainer');
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

function getTimeUntilExpiry(expiryDate) {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const diff = expiry - now;

    if (diff <= 0) {
        return 'Expired';
    }

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 24) {
        const days = Math.floor(hours / 24);
        return `${days}d ${hours % 24}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}