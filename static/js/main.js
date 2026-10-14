/**
 * AI Student Learning Mentor - Main JavaScript
 * Phase 1: Foundation & Live Health Check
 */

document.addEventListener('DOMContentLoaded', () => {
    initHealthCheck();
    initSmoothScroll();
    initFeatureCards();
});

/**
 * Queries /api/health and updates header & monitor badges.
 */
async function initHealthCheck() {
    const badge = document.getElementById('system-status-badge');
    const dbStatus = document.getElementById('health-db-status');
    const msgBox = document.getElementById('health-monitor-msg');
    const refreshBtn = document.getElementById('refresh-health-btn');

    if (!badge && !dbStatus && !msgBox && !refreshBtn) {
        return;
    }

    async function checkHealth() {
        if (badge) {
            badge.className = 'badge status-checking';
            badge.textContent = 'Checking...';
        }
        if (dbStatus) dbStatus.textContent = 'Checking...';
        if (msgBox) msgBox.textContent = 'Contacting /api/health...';

        try {
            const response = await fetch('/api/health');
            const data = await response.json();

            const isHealthy = response.ok && data.status === 'healthy';

            if (badge) {
                if (isHealthy) {
                    badge.className = 'badge status-healthy';
                    badge.textContent = '● System Healthy';
                } else {
                    badge.className = 'badge status-unhealthy';
                    badge.textContent = '● Database Offline';
                }
            }

            if (dbStatus) {
                dbStatus.textContent = '';
                const span = document.createElement('span');
                if (data.database && data.database.connected) {
                    span.style.color = '#34d399';
                    span.textContent = 'Connected';
                    dbStatus.appendChild(span);
                    const dbName = data.database.database_name || 'student_learning_mentor';
                    dbStatus.appendChild(document.createTextNode(' (DB: ' + dbName + ')'));
                } else {
                    span.style.color = '#f87171';
                    span.textContent = 'Disconnected';
                    dbStatus.appendChild(span);
                    dbStatus.appendChild(document.createTextNode(' (Please start MySQL in XAMPP)'));
                }
            }

            if (msgBox) {
                if (isHealthy) {
                    msgBox.textContent = 'All system and database services are responsive and healthy.';
                } else {
                    const errMsg = (data.database && data.database.message) ? data.database.message : 'Database unavailable.';
                    msgBox.textContent = `Notice: ${errMsg} - Launch MySQL from XAMPP Control Panel.`;
                }
            }
        } catch (err) {
            if (badge) {
                badge.className = 'badge status-unhealthy';
                badge.textContent = '● Server Offline';
            }
            if (dbStatus) {
                dbStatus.textContent = '';
                const span = document.createElement('span');
                span.style.color = '#f87171';
                span.textContent = 'Error connecting to Flask backend';
                dbStatus.appendChild(span);
            }
            if (msgBox) {
                msgBox.textContent = 'Unable to reach backend health endpoint.';
            }
        }
    }

    // Initial check
    checkHealth();

    // Refresh button event listener
    if (refreshBtn) {
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            checkHealth();
        });
    }
}

/**
 * Returns active CSRF token from HTML meta tag.
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

/**
 * Smooth scrolling for in-page anchor buttons.
 */
function initSmoothScroll() {
    const cta = document.getElementById('cta-start-learning');
    if (cta && cta.getAttribute('href') && cta.getAttribute('href').startsWith('#')) {
        cta.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = cta.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
}

/**
 * Informational interaction on feature cards.
 */
function initFeatureCards() {
    const cards = document.querySelectorAll('.feature-card');
    cards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'article');
    });
}
