/**
 * AI Student Learning Mentor - Dashboard JavaScript
 * Handles interactive enhancements on the student dashboard.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Interactive card hover or click interactions
    const statCards = document.querySelectorAll('.dashboard-grid .info-card');
    statCards.forEach(card => {
        card.setAttribute('tabindex', '0');
    });

    // Auto-dismissible status banners or notices if needed
    const banner = document.querySelector('.status-banner-card');
    if (banner) {
        banner.setAttribute('role', 'status');
    }
});
