// Dashboard JavaScript Helpers

// ============================================
// DEVICE DETECTION (Desktop Only)
// ============================================

(function () {
    const isMobileOrTablet = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isSmallScreen = window.innerWidth < 1024;

    if (isMobileOrTablet || isSmallScreen) {
        // Redirect to desktop-only page
        if (!window.location.pathname.includes('/desktop-only')) {
            window.location.href = '/dashboard/desktop-only';
        }
    }
})();

// ============================================
// LOCALSTORAGE MANAGEMENT
// ============================================

const AUTH_KEY = 'sonqobase_user_key';

function saveApiKey(apiKey) {
    localStorage.setItem(AUTH_KEY, apiKey);
}

function getApiKey() {
    return localStorage.getItem(AUTH_KEY);
}

function clearApiKey() {
    localStorage.removeItem(AUTH_KEY);
}

function isAuthenticated() {
    return !!getApiKey();
}

// ============================================
// API HELPERS
// ============================================

async function apiCall(url, options = {}) {
    const apiKey = getApiKey();

    if (!apiKey && !options.skipAuth) {
        window.location.href = '/dashboard/login';
        throw new Error('No autenticado');
    }

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (apiKey && !options.skipAuth) {
        headers['X-User-Key'] = apiKey;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    // Si es 401 o 403, redirigir a login
    if (response.status === 401 || response.status === 403) {
        clearApiKey();
        window.location.href = '/dashboard/login';
        throw new Error('Autenticación fallida');
    }

    return response;
}

async function validateApiKey(apiKey) {
    try {
        const response = await fetch('/api/v1/users/me', {
            headers: {
                'X-User-Key': apiKey,
            },
        });

        if (response.ok) {
            return await response.json();
        }

        return null;
    } catch (error) {
        console.error('Error validando API key:', error);
        return null;
    }
}

// ============================================
// UI HELPERS
// ============================================

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.auth-card') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function setLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<span class="spinner"></span> Cargando...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
}

// ============================================
// LOGOUT
// ============================================

function logout() {
    clearApiKey();
    window.location.href = '/dashboard/login';
}

// ============================================
// REDIRECT IF AUTHENTICATED
// ============================================

function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = '/dashboard';
    }
}

// ============================================
// REQUIRE AUTHENTICATION
// ============================================

async function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/dashboard/login';
        return false;
    }

    // Validate API key
    const apiKey = getApiKey();
    const user = await validateApiKey(apiKey);

    if (!user) {
        clearApiKey();
        window.location.href = '/dashboard/login';
        return false;
    }

    return user;
}
