/**
 * AI Student Learning Mentor - Study Plan Engine JavaScript
 * Handles subject-topic dynamic selection, duration shortcuts, and asynchronous task toggling.
 */

function handleSubjectChange(subjectId) {
    // Hide all subject-specific topic groups
    document.querySelectorAll('.subject-topics-group').forEach(el => {
        el.style.display = 'none';
        // Uncheck boxes in hidden groups to avoid accidental submission of wrong topics
        el.querySelectorAll('.topic-input').forEach(chk => {
            chk.checked = false;
        });
    });

    const placeholder = document.getElementById('no-subject-placeholder');
    const batchActions = document.getElementById('batch-actions');
    const activeGroup = document.getElementById('subject-topics-' + subjectId);

    if (activeGroup) {
        if (placeholder) placeholder.style.display = 'none';
        activeGroup.style.display = 'block';
        if (batchActions) batchActions.style.display = 'inline-flex';
        // Automatically check all topics for the selected subject initially for student convenience
        activeGroup.querySelectorAll('.topic-input').forEach(chk => {
            chk.checked = true;
        });
    } else {
        if (placeholder) placeholder.style.display = 'block';
        if (batchActions) batchActions.style.display = 'none';
    }
}

function toggleAllTopics(checkedState) {
    const subjectSelect = document.getElementById('subject_id');
    if (!subjectSelect) return;
    const subjectId = subjectSelect.value;
    if (!subjectId) return;
    const activeGroup = document.getElementById('subject-topics-' + subjectId);
    if (activeGroup) {
        activeGroup.querySelectorAll('.topic-input').forEach(chk => {
            chk.checked = checkedState;
        });
    }
}

function setDuration(days) {
    const input = document.getElementById('duration_days');
    if (input) {
        input.value = days;
    }
}

async function handleTaskToggle(event, planId, itemId) {
    if (event) event.preventDefault();
    const btn = document.getElementById('toggle-btn-' + itemId);
    const card = document.getElementById('task-card-' + itemId);
    const statusPill = document.getElementById('status-pill-' + itemId);

    if (btn) btn.disabled = true;

    try {
        const response = await fetch(`/api/study-plans/${planId}/items/${itemId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            // Fallback: submit standard form if API route behaves unexpectedly
            if (event && event.target && typeof event.target.submit === 'function') {
                event.target.submit();
            }
            return;
        }

        const data = await response.json();
        if (data.status === 'success' && data.data) {
            const isCompleted = data.data.completed;
            const stats = data.data;

            // Update card UI
            if (card && statusPill && btn) {
                if (isCompleted) {
                    card.classList.add('task-completed');
                    statusPill.className = 'task-status-pill status-done';
                    statusPill.innerText = '✓ Completed';
                    btn.className = 'btn btn-sm btn-outline-warning toggle-btn';
                    btn.innerText = 'Mark Incomplete';
                } else {
                    card.classList.remove('task-completed');
                    statusPill.className = 'task-status-pill status-pending';
                    statusPill.innerText = 'Pending';
                    btn.className = 'btn btn-sm btn-success toggle-btn';
                    btn.innerText = '✓ Mark Done';
                }
            }

            // Update Progress bar & stats
            const pctText = document.getElementById('progress-percentage-text');
            const fillBar = document.getElementById('progress-bar-fill');
            const counterText = document.getElementById('progress-counter-text');

            if (pctText) pctText.innerText = stats.completion_percentage + '%';
            if (fillBar) fillBar.style.width = stats.completion_percentage + '%';
            if (counterText) counterText.innerText = `(${stats.completed_tasks} of ${stats.total_tasks} tasks completed)`;
        }
    } catch (err) {
        console.error('Task toggle error:', err);
        if (event && event.target && typeof event.target.submit === 'function') {
            event.target.submit();
        }
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Initial state on page load
document.addEventListener('DOMContentLoaded', () => {
    const subjectSelect = document.getElementById('subject_id');
    if (subjectSelect && subjectSelect.value) {
        const batchActions = document.getElementById('batch-actions');
        if (batchActions) batchActions.style.display = 'inline-flex';
    }
});
