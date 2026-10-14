"""
Study Plan Routes for AI Student Learning Mentor.
Handles personalized study plan generation, task scheduling, progress updates, and study plan APIs.
"""
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, abort, jsonify
)
from services.auth_middleware import login_required
from services.content_service import get_all_subjects, get_topics_by_subject
from services.profile_service import get_student_profile
from services.study_plan_service import (
    create_study_plan, get_user_study_plans, get_study_plan_detail,
    toggle_task_completion, update_study_plan, delete_study_plan
)

study_plan_bp = Blueprint('study_plan', __name__)


# -------------------------------------------------------------------------
# Web Template Routes
# -------------------------------------------------------------------------

@study_plan_bp.route('/study-plans', methods=['GET'])
@login_required
def study_plans_list():
    """
    Lists all study plans created by the logged-in student.
    """
    user_id = session['user_id']
    plans = get_user_study_plans(user_id)
    return render_template('study_plan/study_plans.html', plans=plans)


@study_plan_bp.route('/study-plans/create', methods=['GET', 'POST'])
@login_required
def study_plan_create():
    """
    Form and submission handler to generate a personalized study plan.
    """
    user_id = session['user_id']
    profile = get_student_profile(user_id) or {}
    subjects = get_all_subjects()
    # Attach topics to each subject for dynamic UI rendering
    for s in subjects:
        s['topics'] = get_topics_by_subject(s['id'])

    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        topic_ids = request.form.getlist('topic_ids')
        duration_days = request.form.get('duration_days', type=int)
        goal = request.form.get('goal', '').strip()
        skill_level = request.form.get('skill_level', 'Beginner').strip()
        preferred_study_time = request.form.get('preferred_study_time', 'Flexible').strip()

        success, message, new_plan_id = create_study_plan(
            user_id=user_id,
            subject_id=subject_id,
            topic_ids=topic_ids,
            duration_days=duration_days,
            goal=goal,
            skill_level=skill_level,
            preferred_study_time=preferred_study_time
        )

        if not success:
            flash(message, "danger")
            return render_template(
                'study_plan/setup.html',
                subjects=subjects,
                selected_subject_id=subject_id,
                selected_topic_ids=[int(t) for t in topic_ids if str(t).isdigit()],
                default_duration=duration_days,
                default_goal=goal,
                default_skill_level=skill_level,
                default_study_time=preferred_study_time
            ), 400

        flash(message, "success")
        return redirect(url_for('study_plan_detail', plan_id=new_plan_id))

    preselected_subj = request.args.get('subject_id', type=int)
    return render_template(
        'study_plan/setup.html',
        subjects=subjects,
        selected_subject_id=preselected_subj,
        default_skill_level=profile.get('skill_level', 'Beginner'),
        default_study_time=profile.get('preferred_study_time', 'Flexible'),
        default_goal=profile.get('learning_goal', ''),
        default_duration=7
    )


@study_plan_bp.route('/study-plans/<int:plan_id>', methods=['GET'])
@login_required
def study_plan_detail(plan_id: int):
    """
    Displays a student's study plan and daily task schedule.
    Enforces user isolation: unauthorized users receive 404.
    """
    user_id = session['user_id']
    detail = get_study_plan_detail(plan_id, user_id)
    if not detail:
        abort(404, description=f"Study plan #{plan_id} not found or you do not have permission to view it.")

    return render_template(
        'study_plan/plan.html',
        plan=detail['plan'],
        items=detail['items'],
        topics=detail['topics'],
        total_tasks=detail['total_tasks'],
        completed_tasks=detail['completed_tasks'],
        completion_percentage=detail['completion_percentage']
    )


@study_plan_bp.route('/study-plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def study_plan_edit(plan_id: int):
    """
    Allows a student to edit learning goal, skill level, study time, duration, or topics.
    Enforces user isolation.
    """
    user_id = session['user_id']
    detail = get_study_plan_detail(plan_id, user_id)
    if not detail:
        abort(404, description=f"Study plan #{plan_id} not found or you do not have permission to edit it.")

    plan = detail['plan']
    all_topics = get_topics_by_subject(plan['subject_id'])
    current_topic_ids = [t['id'] for t in detail['topics']]

    if request.method == 'POST':
        goal = request.form.get('goal', '').strip()
        skill_level = request.form.get('skill_level', 'Beginner').strip()
        preferred_study_time = request.form.get('preferred_study_time', 'Flexible').strip()
        duration_days = request.form.get('duration_days', type=int)
        topic_ids = request.form.getlist('topic_ids')

        success, message, _ = update_study_plan(
            plan_id=plan_id,
            user_id=user_id,
            goal=goal,
            skill_level=skill_level,
            preferred_study_time=preferred_study_time,
            duration_days=duration_days,
            topic_ids=topic_ids if topic_ids else None
        )

        if not success:
            flash(message, "danger")
            return render_template(
                'study_plan/study_plan_edit.html',
                plan=plan,
                all_topics=all_topics,
                selected_topic_ids=[int(t) for t in topic_ids if str(t).isdigit()]
            ), 400

        flash("Study plan updated successfully!", "success")
        return redirect(url_for('study_plan_detail', plan_id=plan_id))

    return render_template(
        'study_plan/study_plan_edit.html',
        plan=plan,
        all_topics=all_topics,
        selected_topic_ids=current_topic_ids
    )


@study_plan_bp.route('/study-plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def study_plan_delete(plan_id: int):
    """
    Deletes a study plan and cascades its task items.
    Enforces user isolation.
    """
    user_id = session['user_id']
    success, message = delete_study_plan(plan_id, user_id)
    if not success:
        abort(404, description=message)

    flash("Study plan deleted successfully.", "info")
    return redirect(url_for('study_plans_list'))


@study_plan_bp.route('/study-plans/<int:plan_id>/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def study_plan_toggle_item(plan_id: int, item_id: int):
    """
    Toggles daily task completion. Supports form submit and AJAX.
    Enforces user isolation.
    """
    user_id = session['user_id']
    success, message, result = toggle_task_completion(plan_id, item_id, user_id)

    if not success:
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "error", "message": message}), 404
        abort(404, description=message)

    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({"status": "success", "message": message, "data": result}), 200

    flash("Task status updated.", "success")
    return redirect(url_for('study_plan_detail', plan_id=plan_id))


# -------------------------------------------------------------------------
# Authenticated Study Plan APIs
# -------------------------------------------------------------------------

@study_plan_bp.route('/api/study-plans', methods=['GET'])
@login_required
def api_get_study_plans():
    """
    API: Retrieve all study plans belonging to the authenticated student.
    """
    user_id = session['user_id']
    plans = get_user_study_plans(user_id)
    return jsonify({
        "status": "success",
        "count": len(plans),
        "study_plans": plans
    }), 200


@study_plan_bp.route('/api/study-plans/<int:plan_id>', methods=['GET'])
@login_required
def api_get_study_plan_detail(plan_id: int):
    """
    API: Retrieve study plan detail and items. Enforces user isolation.
    """
    user_id = session['user_id']
    detail = get_study_plan_detail(plan_id, user_id)
    if not detail:
        return jsonify({
            "status": "error",
            "message": "Study plan not found or you do not have permission to access it."
        }), 404

    return jsonify({
        "status": "success",
        "study_plan": detail
    }), 200


@study_plan_bp.route('/api/study-plans/<int:plan_id>/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def api_toggle_study_plan_item(plan_id: int, item_id: int):
    """
    API: Toggle completion status of a daily task item.
    Optional JSON body: {"completed": true/false}
    """
    user_id = session['user_id']
    req_json = request.get_json(silent=True) or {}
    state = req_json.get('completed') if 'completed' in req_json else None

    success, message, result = toggle_task_completion(plan_id, item_id, user_id, state=state)
    if not success:
        return jsonify({
            "status": "error",
            "message": message
        }), 404

    return jsonify({
        "status": "success",
        "message": message,
        "data": result
    }), 200
