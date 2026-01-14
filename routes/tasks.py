from flask import Blueprint, jsonify, request, g
from models import db, Task
from middleware import token_required

tasks_bp = Blueprint("tasks", __name__)


# Helper to get cache (deferred import to avoid circular dependency)
def get_cache():
    from app import cache
    return cache


def make_cache_key():
    """Create a unique cache key based on user and query params."""
    user_id = g.current_user.id
    args = request.args.to_dict()
    return f"tasks:{user_id}:{hash(frozenset(args.items()))}"


def clear_user_cache():
    """Clear cache for the current user when data changes."""
    cache = get_cache()
    # Simple approach: clear all cache (in production, use Redis with pattern delete)
    cache.clear()


@tasks_bp.route("/tasks", methods=["GET"])
@token_required
def get_all_tasks():
    """
    GET /tasks - Retrieve tasks with pagination, filtering, and sorting
    (Protected: requires authentication)
    Cached for 60 seconds per user+query combination.
    """
    cache = get_cache()
    cache_key = make_cache_key()

    # Try to get from cache
    cached_response = cache.get(cache_key)
    if cached_response:
        return jsonify(cached_response), 200

    # Build query
    query = Task.query.filter_by(user_id=g.current_user.id)

    # --- FILTERING ---
    completed_param = request.args.get("completed")
    if completed_param is not None:
        completed = completed_param.lower() == "true"
        query = query.filter(Task.completed == completed)

    # --- SORTING ---
    sort_field = request.args.get("sort", "id")
    sort_order = request.args.get("order", "asc")

    allowed_sort_fields = {"id", "title", "completed"}
    if sort_field not in allowed_sort_fields:
        return jsonify({"error": f"Invalid sort field. Allowed: {allowed_sort_fields}"}), 400

    sort_column = getattr(Task, sort_field)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # --- PAGINATION ---
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    if page < 1:
        return jsonify({"error": "Page must be >= 1"}), 400
    if limit < 1 or limit > 100:
        return jsonify({"error": "Limit must be between 1 and 100"}), 400

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    response = {
        "data": [task.to_dict() for task in paginated.items],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": paginated.total,
            "total_pages": paginated.pages,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev
        }
    }

    # Store in cache for 60 seconds
    cache.set(cache_key, response, timeout=60)

    return jsonify(response), 200


@tasks_bp.route("/tasks/<int:task_id>", methods=["GET"])
@token_required
def get_task(task_id):
    """
    GET /tasks/:id - Retrieve a single task by ID
    (Protected: requires authentication)
    """
    cache = get_cache()
    cache_key = f"task:{g.current_user.id}:{task_id}"

    cached_response = cache.get(cache_key)
    if cached_response:
        return jsonify(cached_response), 200

    task = Task.query.get(task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if task.user_id != g.current_user.id:
        return jsonify({"error": "Access denied"}), 403

    response = task.to_dict()
    cache.set(cache_key, response, timeout=60)

    return jsonify(response), 200


@tasks_bp.route("/tasks", methods=["POST"])
@token_required
def create_task():
    """
    POST /tasks - Create a new task
    (Protected: requires authentication)
    """
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400

    new_task = Task(
        title=data["title"],
        description=data.get("description", ""),
        completed=False,
        user_id=g.current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    # Clear cache since data changed
    clear_user_cache()

    return jsonify(new_task.to_dict()), 201


@tasks_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@token_required
def update_task(task_id):
    """
    PUT /tasks/:id - Update an existing task
    (Protected: requires authentication)
    """
    task = Task.query.get(task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if task.user_id != g.current_user.id:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "completed" in data:
        task.completed = data["completed"]

    db.session.commit()

    # Clear cache since data changed
    clear_user_cache()

    return jsonify(task.to_dict()), 200


@tasks_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(task_id):
    """
    DELETE /tasks/:id - Delete a task
    (Protected: requires authentication)
    """
    task = Task.query.get(task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if task.user_id != g.current_user.id:
        return jsonify({"error": "Access denied"}), 403

    db.session.delete(task)
    db.session.commit()

    # Clear cache since data changed
    clear_user_cache()

    return "", 204
