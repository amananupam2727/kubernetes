import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4096


def connect():
    # Psycopg reads PGHOST, PGDATABASE, PGUSER and PGPASSWORD.
    return psycopg.connect(connect_timeout=3, row_factory=dict_row)


def get_tasks():
    with connect() as conn:
        return conn.execute(
            "SELECT id, title, completed FROM tasks ORDER BY id"
        ).fetchall()


@app.get("/")
def index():
    return render_template("index.html", tasks=get_tasks())


@app.get("/api/tasks")
def list_tasks():
    return jsonify(get_tasks())


@app.post("/tasks")
def add_task():
    title = request.form.get("title", "").strip()
    if not title or len(title) > 200:
        return "Title must contain 1–200 characters", 400
    with connect() as conn:
        conn.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
    return redirect("/", code=303)


@app.post("/tasks/<int:task_id>/complete")
def complete_task(task_id):
    with connect() as conn:
        row = conn.execute(
            "UPDATE tasks SET completed = TRUE WHERE id = %s RETURNING id",
            (task_id,),
        ).fetchone()
    if row is None:
        return "Task not found", 404
    return redirect("/", code=303)


@app.get("/healthz")
def health():
    return {"status": "broken"}


@app.get("/readyz")
def ready():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ready"}


@app.errorhandler(psycopg.Error)
def database_error(error):
    app.logger.error("Database operation failed: %s", type(error).__name__)
    return {"error": "Database unavailable"}, 503
