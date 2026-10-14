/**
 * AI Student Learning Mentor - Progress & Mastery Center JavaScript
 * Handles progress filters, search, and mastery visualization enhancements.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Topic mastery search / filter if table exists
    const searchInput = document.getElementById('progress-topic-filter');
    const tableRows = document.querySelectorAll('.mastery-table tbody tr');

    if (searchInput && tableRows.length > 0) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase().trim();
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    // Progress bar animations
    const progressFills = document.querySelectorAll('.progress-bar-fill');
    progressFills.forEach(bar => {
        const width = bar.style.width;
        bar.style.transition = 'width 0.6s ease-in-out';
    });
});
