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
const TOKEN_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

function saveApiKey(apiKey) {
    localStorage.setItem(AUTH_KEY, apiKey);
}

function getApiKey() {
    return localStorage.getItem(AUTH_KEY);
}

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function clearTokens() {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
}

function isAuthenticated() {
    return !!getAccessToken() || !!getApiKey();
}

// ============================================
// API HELPERS
// ============================================

async function apiCall(url, options = {}) {
    const token = getAccessToken();
    const apiKey = getApiKey();
    const skipAuth = options.skipAuth || false;
    // Flag to prevent infinite loops if refresh fails
    const isRetry = options.isRetry || false;

    if (!token && !apiKey && !skipAuth) {
        window.location.href = '/dashboard/login';
        throw new Error('No autenticado');
    }

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Prefer JWT Token
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    } else if (apiKey && options.useApiKey) {
        // Only send API Key if explicitly requested (e.g. for initial user validation)
        headers['X-User-Key'] = apiKey;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    // Handle 401 Unauthorized (Token Expired?)
    if (response.status === 401 && !isRetry && !skipAuth) {
        const refreshToken = localStorage.getItem(REFRESH_KEY);

        if (refreshToken) {
            try {
                // Attempt to refresh
                console.log('🔄 Token expired, attempting refresh...');
                const refreshResponse = await fetch('/api/v1/auth/refresh', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refreshToken })
                });

                if (refreshResponse.ok) {
                    const data = await refreshResponse.json();

                    // Save new access token
                    localStorage.setItem(TOKEN_KEY, data.access_token);
                    console.log('✅ Token refreshed successfully');

                    // Retry original request with new token
                    // We need to pass isRetry=true to avoid infinite loop if it fails again
                    return await apiCall(url, { ...options, isRetry: true });
                } else {
                    console.warn('❌ Refresh token invalid or expired');
                    // Refresh failed, clear everything and logout
                    logout();
                    throw new Error('Sesión expirada');
                }
            } catch (err) {
                console.error('Refresh attempt failed:', err);
                logout();
                throw err;
            }
        } else {
            // No refresh token available
            logout(); // Or clearTokens()
            throw new Error('No autenticado');
        }
    }

    // Si es 403 Forbidden (Auth válida pero sin permisos)
    if (response.status === 403) {
        // Podríamos mostrar un alert sin redirigir, o redirigir según caso
        throw new Error('Acceso denegado');
    }

    return response;
}

async function validateApiKey(apiKey) {
    try {
        // This endpoint generates OTP now, but we use it here just to validate key existence
        // For validation purposes only in legacy flow
        // Actually, we should probably check if key format is correct or try a lighter endpoint
        // But users/me is fine for now
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
    clearTokens();
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

    // If we have a token, we assume it's valid (middleware checks it)
    // If it expires, apiCall will redirect to login.
    // For legacy API key, we might want to validate (but optimization suggests trusting localStorage until 401)

    return true;
}
