/**
 * AI Student Learning Mentor - AI Doubt Assistant Chat
 * Handles question character counting and submission loading.
 */

document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('question');
    const charCounter = document.getElementById('char-counter');
    const form = document.getElementById('ai-ask-form');
    const submitBtn = document.getElementById('submit-btn');
    const loadingBox = document.getElementById('ai-loading');

    // Character counter
    function updateCharCount() {
        if (questionInput && charCounter) {
            const count = questionInput.value.length;
            charCounter.textContent = count + ' / 2000';
            if (count > 1900) {
                charCounter.classList.add('char-limit-near');
            } else {
                charCounter.classList.remove('char-limit-near');
            }
        }
    }

    if (questionInput) {
        questionInput.addEventListener('input', updateCharCount);
        updateCharCount();
    }

    // Show loading state on submission
    if (form) {
        form.addEventListener('submit', function() {
            if (questionInput && questionInput.value.trim().length >= 3) {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Contacting AI Mentor...';
                }
                if (loadingBox) {
                    loadingBox.style.display = 'flex';
                }
            }
        });
    }
});
