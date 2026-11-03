
from flask import Flask, render_template, request, redirect, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "campus-complaint-secret-key-change-this"

# Change YOUR_MYSQL_PASSWORD to your local MySQL password
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PRANATHI$123",
    "database": "campus_complaints_new"
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def login_required(role=None):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect("/login")

            if role and session.get("role") != role:
                return redirect("/dashboard")

            return function(*args, **kwargs)
        return wrapper
    return decorator


# Home page
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("home.html")


# Student and Faculty Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if role not in ["student", "faculty"]:
            flash("Please select a valid login type.")
            return redirect("/login")

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND role=%s",
            (email, role)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect("/dashboard")

        flash("Invalid email or password.")

    return render_template("login.html")


# Student Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must have at least 6 characters.")
            return redirect("/register")

        password_hash = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, 'student')
                """,
                (name, email, password_hash)
            )
            conn.commit()
            flash("Registration successful. Please login.")
            return redirect("/login")

        except mysql.connector.IntegrityError:
            flash("This email is already registered.")

        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")


# Dashboard
@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "student":
        return render_template("student.html")

    return render_template("faculty.html")


# Submit complaint and view complaints
@app.route("/api/complaints", methods=["GET", "POST"])
@login_required()
def complaints():

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        if session["role"] != "student":
            cursor.close()
            conn.close()
            return jsonify({"error": "Only students can submit complaints"}), 403

        data = request.get_json(silent=True) or {}

        category = data.get("category", "").strip()
        description = data.get("description", "").strip()
        priority = data.get("priority", "Medium")

        if not category or not description:
            cursor.close()
            conn.close()
            return jsonify({"error": "Please fill all complaint details"}), 400

        if priority not in ["Low", "Medium", "High", "Urgent"]:
            priority = "Medium"

        cursor.execute(
            """
            INSERT INTO complaints
            (student_id, category, description, priority)
            VALUES (%s, %s, %s, %s)
            """,
            (session["user_id"], category, description, priority)
        )

        complaint_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO complaint_history
            (complaint_id, changed_by, old_status, new_status, remarks)
            VALUES (%s, %s, NULL, 'Submitted', 'Complaint submitted')
            """,
            (complaint_id, session["user_id"])
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Complaint submitted successfully"})

    if session["role"] == "student":
        cursor.execute(
            """
            SELECT * FROM complaints
            WHERE student_id=%s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )
    else:
        cursor.execute(
            """
            SELECT complaints.*, users.name AS student_name
            FROM complaints
            JOIN users ON complaints.student_id = users.user_id
            ORDER BY complaints.created_at DESC
            """
        )

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(result)


# Faculty updates a complaint
@app.route("/api/complaints/<int:cid>/update", methods=["POST"])
@login_required("faculty")
def update_complaint(cid):

    data = request.get_json(silent=True) or {}

    assigned_to = data.get("assigned_to", "").strip()
    status = data.get("status", "").strip()
    resolution = data.get("resolution", "").strip()

    allowed_statuses = [
        "Submitted", "Assigned", "In Progress", "Resolved", "Rejected"
    ]

    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT status FROM complaints WHERE complaint_id=%s",
        (cid,)
    )
    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found"}), 404

    old_status = complaint["status"]

    cursor.execute(
        """
        UPDATE complaints
        SET assigned_to=%s, status=%s, resolution=%s
        WHERE complaint_id=%s
        """,
        (assigned_to, status, resolution, cid)
    )

    if old_status != status or resolution:
        cursor.execute(
            """
            INSERT INTO complaint_history
            (complaint_id, changed_by, old_status, new_status, remarks)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                cid,
                session["user_id"],
                old_status,
                status,
                resolution or "Complaint updated"
            )
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Complaint updated successfully"})


# View complaint history
@app.route("/api/complaints/<int:cid>/history")
@login_required()
def complaint_history(cid):

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if session["role"] == "student":
        cursor.execute(
            """
            SELECT complaint_id FROM complaints
            WHERE complaint_id=%s AND student_id=%s
            """,
            (cid, session["user_id"])
        )
    else:
        cursor.execute(
            "SELECT complaint_id FROM complaints WHERE complaint_id=%s",
            (cid,)
        )

    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Complaint not found or access denied"}), 404

    cursor.execute(
        """
        SELECT complaint_history.*, users.name AS changed_by_name
        FROM complaint_history
        LEFT JOIN users
        ON complaint_history.changed_by = users.user_id
        WHERE complaint_history.complaint_id=%s
        ORDER BY complaint_history.changed_at DESC
        """,
        (cid,)
    )

    history = cursor.fetchall()

    for item in history:
        if item["changed_at"]:
            item["changed_at"] = item["changed_at"].strftime("%Y-%m-%d %H:%M:%S")

    cursor.close()
    conn.close()

    return jsonify(history)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
