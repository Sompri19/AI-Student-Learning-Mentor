/**
 * AI Student Learning Mentor - Quiz & Practice Engine JavaScript
 * Updates answered questions count, calculates progress percentage, and handles option selection.
 */

function updateQuizProgress() {
    const form = document.getElementById('quiz-form');
    if (!form) return;

    const totalQuestionsAttr = form.getAttribute('data-total-questions');
    const questionCards = document.querySelectorAll('.quiz-question-card, .question-block');
    const totalQuestions = parseInt(totalQuestionsAttr, 10) || questionCards.length || 1;

    const checkedInputs = form.querySelectorAll('input[type="radio"]:checked');
    const answeredCount = checkedInputs.length;

    // Update Counter
    const counterEl = document.getElementById('answered-counter');
    if (counterEl) counterEl.innerText = answeredCount;

    // Update Progress Bar
    const progressBar = document.getElementById('quiz-progress-bar');
    if (progressBar) {
        const pct = Math.round((answeredCount / totalQuestions) * 100);
        progressBar.style.width = pct + '%';
    }

    // Highlight selected option card
    document.querySelectorAll('.option-label').forEach(lbl => {
        const radio = lbl.querySelector('input[type="radio"]');
        if (radio && radio.checked) {
            lbl.classList.add('option-selected');
        } else {
            lbl.classList.remove('option-selected');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('quiz-form');
    if (form) {
        form.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', updateQuizProgress);
        });
        updateQuizProgress();
    }
});
