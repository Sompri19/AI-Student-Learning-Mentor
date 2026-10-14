"""
Profile Routes for AI Student Learning Mentor.
Handles student profile display, academic background, goals, and profile updates.
"""
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from services.auth_middleware import login_required
from services.auth_service import get_user_by_id
from services.profile_service import (
    get_student_profile, upsert_student_profile, calculate_profile_completion
)

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Student Profile management page.
    Allows logged-in students to view, create, and update their academic profile.
    Strictly limits operations to the authenticated user's ID.
    """
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    if request.method == 'POST':
        profile_data = {
            'education_level': request.form.get('education_level', ''),
            'course': request.form.get('course', ''),
            'semester': request.form.get('semester', ''),
            'skill_level': request.form.get('skill_level', ''),
            'learning_goal': request.form.get('learning_goal', ''),
            'preferred_study_time': request.form.get('preferred_study_time', '')
        }

        success, message = upsert_student_profile(user_id, profile_data)
        if success:
            flash("Your student profile has been updated successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash(message, "danger")

    # Fetch existing profile for form population
    current_profile = get_student_profile(user_id) or {}
    completion = calculate_profile_completion(current_profile)

    return render_template(
        'profile/profile.html',
        user=user,
        profile=current_profile,
        completion=completion
    )
