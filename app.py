from flask import Flask, render_template, request, redirect, session
from database import init_db, get_db

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

app.secret_key = "campusconnect-secret-key"


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# AUTHENTICATION HELPERS
# ============================================================

def student_logged_in():
    """
    Returns True only when the current session belongs to a student.
    """
    return (
        session.get("user_type") == "student"
        and session.get("user_id") is not None
    )


def club_logged_in():
    """
    Returns True only when the current session belongs to a club.
    """
    return (
        session.get("user_type") == "club"
        and session.get("user_id") is not None
    )


def require_student():
    """
    Protect student-only routes.
    """
    if not student_logged_in():
        return redirect("/login?type=student")

    return None


def require_club():
    """
    Protect club-only routes.
    """
    if not club_logged_in():
        return redirect("/login?type=club")

    return None


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# STUDENT LANDING PAGE
# ============================================================

@app.route("/student")
def student():

    if student_logged_in():
        return redirect("/student/dashboard")

    # If a club is logged in, don't allow the club session
    # to accidentally access student pages.
    if club_logged_in():
        return redirect("/club/dashboard")

    return render_template("student.html")


# ============================================================
# CLUB LANDING PAGE
# ============================================================

@app.route("/club")
def club():

    if club_logged_in():
        return redirect("/club/dashboard")

    # If a student is logged in, keep the student session
    # away from club pages.
    if student_logged_in():
        return redirect("/student/dashboard")

    return render_template("club.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        login_type = request.args.get("type", "").strip().lower()

        if login_type not in ["student", "club"]:
            login_type = None

        # If already logged in, don't show the login page again.
        if student_logged_in():
            return redirect("/student/dashboard")

        if club_logged_in():
            return redirect("/club/dashboard")

        return render_template(
            "login.html",
            login_type=login_type
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user_type = request.form.get("user_type", "").strip().lower()

    # Validate account type.
    if user_type not in ["student", "club"]:
        return render_template(
            "login.html",
            error="Please select Student or Club.",
            login_type=user_type
        )

    # Validate credentials.
    if not email or not password:
        return render_template(
            "login.html",
            error="Please enter your email and password.",
            login_type=user_type
        )

    conn = get_db()

    try:

        # ----------------------------------------------------
        # STUDENT LOGIN
        # ----------------------------------------------------

        if user_type == "student":

            account = conn.execute(
                """
                SELECT *
                FROM users
                WHERE LOWER(email) = ?
                AND password = ?
                AND user_type = 'student'
                """,
                (
                    email,
                    password
                )
            ).fetchone()

        # ----------------------------------------------------
        # CLUB LOGIN
        # ----------------------------------------------------

        else:

            account = conn.execute(
                """
                SELECT *
                FROM clubs
                WHERE LOWER(email) = ?
                AND password = ?
                """,
                (
                    email,
                    password
                )
            ).fetchone()

    finally:
        conn.close()

    # Invalid credentials.
    if account is None:

        return render_template(
            "login.html",
            error="Invalid email or password.",
            login_type=user_type
        )

    # --------------------------------------------------------
    # CREATE CLEAN SESSION
    # --------------------------------------------------------

    session.clear()

    session["user_type"] = user_type
    session["user_id"] = account["id"]

    if user_type == "student":

        session["name"] = account["name"]

        return redirect("/student/dashboard")

    # Club
    session["name"] = account["club_name"]

    return redirect("/club/dashboard")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@app.route("/student/register", methods=["GET", "POST"])
def student_register():

    if student_logged_in():
        return redirect("/student/dashboard")

    if club_logged_in():
        return redirect("/club/dashboard")

    if request.method == "GET":
        return render_template("student_register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:

        return render_template(
            "student_register.html",
            error="All fields are required."
        )

    if len(password) < 6:

        return render_template(
            "student_register.html",
            error="Password must be at least 6 characters."
        )

    conn = get_db()

    try:

        # Check student accounts.
        existing_student = conn.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = ?
            """,
            (email,)
        ).fetchone()

        if existing_student:

            return render_template(
                "student_register.html",
                error="An account with this email already exists."
            )

        # Also prevent a club from using the same email.
        existing_club = conn.execute(
            """
            SELECT id
            FROM clubs
            WHERE LOWER(email) = ?
            """,
            (email,)
        ).fetchone()

        if existing_club:

            return render_template(
                "student_register.html",
                error="An account with this email already exists."
            )

        cursor = conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password,
                user_type,
                course,
                year,
                interests,
                skills,
                goals
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                password,
                "student",
                "",
                "",
                "",
                "",
                ""
            )
        )

        conn.commit()

        student_id = cursor.lastrowid

    except Exception as e:

        conn.rollback()

        return render_template(
            "student_register.html",
            error=f"Registration failed: {e}"
        )

    finally:
        conn.close()

    # Log in automatically.
    session.clear()

    session["user_type"] = "student"
    session["user_id"] = student_id
    session["name"] = name

    return redirect("/student/dashboard")


# ============================================================
# CLUB REGISTRATION
# ============================================================

@app.route("/club/register", methods=["GET", "POST"])
def club_register():

    if club_logged_in():
        return redirect("/club/dashboard")

    if student_logged_in():
        return redirect("/student/dashboard")

    if request.method == "GET":
        return render_template("club_register.html")

    club_name = request.form.get("club_name", "").strip()
    university = request.form.get("university", "").strip()
    category = request.form.get("category", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not club_name:

        return render_template(
            "club_register.html",
            error="Club name is required."
        )

    if not university:

        return render_template(
            "club_register.html",
            error="University is required."
        )

    if not category:

        return render_template(
            "club_register.html",
            error="Club category is required."
        )

    if not email:

        return render_template(
            "club_register.html",
            error="Email is required."
        )

    if not password:

        return render_template(
            "club_register.html",
            error="Password is required."
        )

    if len(password) < 6:

        return render_template(
            "club_register.html",
            error="Password must be at least 6 characters."
        )

    conn = get_db()

    try:

        # Check club accounts.
        existing_club = conn.execute(
            """
            SELECT id
            FROM clubs
            WHERE LOWER(email) = ?
            """,
            (email,)
        ).fetchone()

        if existing_club:

            return render_template(
                "club_register.html",
                error="A club with this email already exists."
            )

        # Also prevent duplicate email across student accounts.
        existing_student = conn.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = ?
            """,
            (email,)
        ).fetchone()

        if existing_student:

            return render_template(
                "club_register.html",
                error="An account with this email already exists."
            )

        cursor = conn.execute(
            """
            INSERT INTO clubs
            (
                club_name,
                university,
                category,
                email,
                password,
                recruitment_status,
                description,
                benefits,
                notice
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                club_name,
                university,
                category,
                email,
                password,
                "Open",
                "",
                "",
                ""
            )
        )

        conn.commit()

        club_id = cursor.lastrowid

    except Exception as e:

        conn.rollback()

        return render_template(
            "club_register.html",
            error=f"Club registration failed: {e}"
        )

    finally:
        conn.close()

    # Log in automatically.
    session.clear()

    session["user_type"] = "club"
    session["user_id"] = club_id
    session["name"] = club_name

    return redirect("/club/dashboard")


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/student/dashboard")
def student_dashboard():

    auth_error = require_student()

    if auth_error:
        return auth_error

    student_id = session["user_id"]

    conn = get_db()

    try:

        student = conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            AND user_type = 'student'
            """,
            (student_id,)
        ).fetchone()

        if student is None:

            session.clear()

            return redirect("/login?type=student")

        application_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM applications
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()["total"]

        joined_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM applications
            WHERE student_id = ?
            AND status = 'Selected'
            """,
            (student_id,)
        ).fetchone()["total"]

        recent_applications = conn.execute(
            """
            SELECT
                applications.id,
                applications.status,
                applications.applied_at,
                clubs.club_name,
                clubs.category
            FROM applications
            JOIN clubs
                ON applications.club_id = clubs.id
            WHERE applications.student_id = ?
            ORDER BY applications.applied_at DESC
            LIMIT 5
            """,
            (student_id,)
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "student_dashboard.html",
        student=student,
        student_name=student["name"],
        application_count=application_count,
        joined_count=joined_count,
        recent_applications=recent_applications
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():

    auth_error = require_student()

    if auth_error:
        return auth_error

    student_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        course = request.form.get("course", "").strip()
        year = request.form.get("year", "").strip()
        interests = request.form.get("interests", "").strip()
        skills = request.form.get("skills", "").strip()
        goals = request.form.get("goals", "").strip()

        if not name or not email:

            student = conn.execute(
                """
                SELECT *
                FROM users
                WHERE id = ?
                AND user_type = 'student'
                """,
                (student_id,)
            ).fetchone()

            conn.close()

            return render_template(
                "student_profile.html",
                student=student,
                error="Name and email cannot be empty."
            )

        existing = conn.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = ?
            AND id != ?
            """,
            (
                email,
                student_id
            )
        ).fetchone()

        if existing:

            student = conn.execute(
                """
                SELECT *
                FROM users
                WHERE id = ?
                AND user_type = 'student'
                """,
                (student_id,)
            ).fetchone()

            conn.close()

            return render_template(
                "student_profile.html",
                student=student,
                error="That email is already being used."
            )

        try:

            conn.execute(
                """
                UPDATE users
                SET
                    name = ?,
                    email = ?,
                    course = ?,
                    year = ?,
                    interests = ?,
                    skills = ?,
                    goals = ?
                WHERE id = ?
                AND user_type = 'student'
                """,
                (
                    name,
                    email,
                    course,
                    year,
                    interests,
                    skills,
                    goals,
                    student_id
                )
            )

            conn.commit()

            session["name"] = name

        except Exception as e:

            conn.rollback()
            conn.close()

            return render_template(
                "student_profile.html",
                error=f"Profile update failed: {e}"
            )

    student = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        AND user_type = 'student'
        """,
        (student_id,)
    ).fetchone()

    conn.close()

    if student is None:

        session.clear()

        return redirect("/login?type=student")

    profile_fields = [
        student["name"],
        student["email"],
        student["course"],
        student["year"],
        student["interests"],
        student["skills"],
        student["goals"]
    ]

    completed_fields = sum(
        1
        for field in profile_fields
        if field and str(field).strip()
    )

    profile_completion = round(
        (completed_fields / len(profile_fields)) * 100
    )

    return render_template(
        "student_profile.html",
        student=student,
        profile_completion=profile_completion
    )


# ============================================================
# STUDENT — BROWSE CLUBS
# ============================================================

@app.route("/student/clubs")
def student_clubs():

    auth_error = require_student()

    if auth_error:
        return auth_error

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    university = request.args.get("university", "").strip()

    conn = get_db()

    query = """
        SELECT
            id,
            club_name,
            university,
            category,
            recruitment_status,
            description,
            benefits,
            notice
        FROM clubs
        WHERE 1 = 1
    """

    params = []

    if search:

        query += """
            AND (
                LOWER(club_name) LIKE ?
                OR LOWER(university) LIKE ?
                OR LOWER(category) LIKE ?
                OR LOWER(description) LIKE ?
                OR LOWER(benefits) LIKE ?
            )
        """

        value = f"%{search.lower()}%"

        params.extend([
            value,
            value,
            value,
            value,
            value
        ])

    if category:

        query += """
            AND LOWER(category) = LOWER(?)
        """

        params.append(category)

    if university:

        query += """
            AND LOWER(university) = LOWER(?)
        """

        params.append(university)

    query += """
        ORDER BY club_name ASC
    """

    clubs = conn.execute(
        query,
        params
    ).fetchall()

    categories = conn.execute(
        """
        SELECT DISTINCT category
        FROM clubs
        WHERE category IS NOT NULL
        AND TRIM(category) != ''
        ORDER BY category ASC
        """
    ).fetchall()

    universities = conn.execute(
        """
        SELECT DISTINCT university
        FROM clubs
        WHERE university IS NOT NULL
        AND TRIM(university) != ''
        ORDER BY university ASC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "student_clubs.html",
        clubs=clubs,
        categories=categories,
        universities=universities,
        search=search,
        selected_category=category,
        selected_university=university
    )


# ============================================================
# STUDENT — CLUB DETAILS
# ============================================================

@app.route("/student/club/<int:club_id>")
def view_club(club_id):

    auth_error = require_student()

    if auth_error:
        return auth_error

    student_id = session["user_id"]

    conn = get_db()

    club = conn.execute(
        """
        SELECT *
        FROM clubs
        WHERE id = ?
        """,
        (club_id,)
    ).fetchone()

    if club is None:

        conn.close()

        return "Club not found.", 404

    members = conn.execute(
        """
        SELECT
            name,
            role
        FROM club_members
        WHERE club_id = ?
        ORDER BY
            CASE role
                WHEN 'President' THEN 1
                WHEN 'Vice President' THEN 2
                WHEN 'Secretary' THEN 3
                WHEN 'Treasurer' THEN 4
                WHEN 'Team Lead' THEN 5
                WHEN 'Member' THEN 6
                ELSE 7
            END,
            name ASC
        """,
        (club_id,)
    ).fetchall()

    application = conn.execute(
        """
        SELECT
            id,
            status,
            applied_at
        FROM applications
        WHERE student_id = ?
        AND club_id = ?
        """,
        (
            student_id,
            club_id
        )
    ).fetchone()

    conn.close()

    return render_template(
        "club_details.html",
        club=club,
        members=members,
        application=application
    )


# ============================================================
# STUDENT — APPLY
# ============================================================

@app.route(
    "/student/apply/<int:club_id>",
    methods=["GET", "POST"]
)
def apply_to_club(club_id):

    auth_error = require_student()

    if auth_error:
        return auth_error

    student_id = session["user_id"]

    conn = get_db()

    club = conn.execute(
        """
        SELECT *
        FROM clubs
        WHERE id = ?
        """,
        (club_id,)
    ).fetchone()

    if club is None:

        conn.close()

        return "Club not found.", 404

    if club["recruitment_status"] != "Open":

        conn.close()

        return redirect(
            f"/student/club/{club_id}"
        )

    existing = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE student_id = ?
        AND club_id = ?
        """,
        (
            student_id,
            club_id
        )
    ).fetchone()

    if existing:

        conn.close()

        return redirect("/student/applications")

    student = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        AND user_type = 'student'
        """,
        (student_id,)
    ).fetchone()

    if student is None:

        conn.close()
        session.clear()

        return redirect("/login?type=student")

    if request.method == "GET":

        conn.close()

        return render_template(
            "student_apply.html",
            club=club,
            student=student
        )

    skills = request.form.get("skills", "").strip()
    interests = request.form.get("interests", "").strip()
    why_join = request.form.get("why_join", "").strip()
    portfolio = request.form.get("portfolio", "").strip()

    if not skills or not interests or not why_join:

        conn.close()

        return render_template(
            "student_apply.html",
            club=club,
            student=student,
            error="Please complete all required fields."
        )

    try:

        conn.execute(
            """
            INSERT INTO applications
            (
                student_id,
                club_id,
                status,
                skills,
                interests,
                why_join,
                portfolio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                club_id,
                "Pending",
                skills,
                interests,
                why_join,
                portfolio
            )
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        conn.close()

        return render_template(
            "student_apply.html",
            club=club,
            student=student,
            error=f"Application failed: {e}"
        )

    conn.close()

    return redirect("/student/applications")


# ============================================================
# STUDENT — APPLICATIONS
# ============================================================

@app.route("/student/applications")
def student_applications():

    auth_error = require_student()

    if auth_error:
        return auth_error

    student_id = session["user_id"]

    conn = get_db()

    applications = conn.execute(
        """
        SELECT
            applications.id,
            applications.club_id,
            applications.status,
            applications.applied_at,
            applications.skills,
            applications.interests,
            applications.why_join,
            applications.portfolio,
            clubs.club_name,
            clubs.university,
            clubs.category,
            clubs.recruitment_status
        FROM applications
        JOIN clubs
            ON applications.club_id = clubs.id
        WHERE applications.student_id = ?
        ORDER BY applications.applied_at DESC
        """,
        (student_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "student_applications.html",
        applications=applications
    )


# ============================================================
# STUDENT — CANCEL APPLICATION
# ============================================================

@app.route(
    "/student/application/<int:application_id>/cancel",
    methods=["POST"]
)
def cancel_application(application_id):

    auth_error = require_student()

    if auth_error:
        return auth_error

    student_id = session["user_id"]

    conn = get_db()

    application = conn.execute(
        """
        SELECT
            id,
            status
        FROM applications
        WHERE id = ?
        AND student_id = ?
        """,
        (
            application_id,
            student_id
        )
    ).fetchone()

    if application is None:

        conn.close()

        return "Application not found.", 404

    if application["status"] != "Pending":

        conn.close()

        return redirect("/student/applications")

    conn.execute(
        """
        DELETE FROM applications
        WHERE id = ?
        AND student_id = ?
        """,
        (
            application_id,
            student_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/student/applications")


# ============================================================
# CLUB DASHBOARD
# ============================================================

@app.route("/club/dashboard")
def club_dashboard():

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    club = conn.execute(
        """
        SELECT *
        FROM clubs
        WHERE id = ?
        """,
        (club_id,)
    ).fetchone()

    if club is None:

        conn.close()
        session.clear()

        return redirect("/login?type=club")

    recruitment_status = (
        club["recruitment_status"]
        or "Open"
    )

    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Pending'
                        THEN 1 ELSE 0
                    END
                ),
                0
            ) AS pending,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Under Review'
                        THEN 1 ELSE 0
                    END
                ),
                0
            ) AS under_review,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Eligible for Test'
                        THEN 1 ELSE 0
                    END
                ),
                0
            ) AS eligible_test,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Eligible for Interview'
                        THEN 1 ELSE 0
                    END
                ),
                0
            ) AS eligible_interview,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Selected'
                        THEN 1 ELSE 0
                    END
                ),
                0
            ) AS selected,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Rejected'
                        THEN 1 ELSE 0
                    END
                ),
                0
            ) AS rejected

        FROM applications
        WHERE club_id = ?
        """,
        (club_id,)
    ).fetchone()

    member_count = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM club_members
        WHERE club_id = ?
        """,
        (club_id,)
    ).fetchone()["total"]

    recent_applications = conn.execute(
        """
        SELECT
            applications.id,
            users.name,
            users.email,
            applications.status,
            applications.applied_at
        FROM applications
        JOIN users
            ON applications.student_id = users.id
        WHERE applications.club_id = ?
        ORDER BY applications.applied_at DESC
        LIMIT 5
        """,
        (club_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "club_dashboard.html",
        club=club,
        recruitment_status=recruitment_status,
        stats=stats,
        member_count=member_count,
        recent_applications=recent_applications
    )


# ============================================================
# CLUB — MEMBERS
# ============================================================

@app.route("/club/members")
def club_members():

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    club = conn.execute(
        """
        SELECT *
        FROM clubs
        WHERE id = ?
        """,
        (club_id,)
    ).fetchone()

    if club is None:

        conn.close()
        session.clear()

        return redirect("/login?type=club")

    members = conn.execute(
        """
        SELECT
            id,
            club_id,
            name,
            email,
            role
        FROM club_members
        WHERE club_id = ?
        ORDER BY
            CASE role
                WHEN 'President' THEN 1
                WHEN 'Vice President' THEN 2
                WHEN 'Secretary' THEN 3
                WHEN 'Treasurer' THEN 4
                WHEN 'Team Lead' THEN 5
                WHEN 'Member' THEN 6
                ELSE 7
            END,
            id DESC
        """,
        (club_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "club_member.html",
        members=members,
        club=club
    )


# ============================================================
# CLUB — ADD MEMBER
# ============================================================

@app.route(
    "/club/members/add",
    methods=["POST"]
)
def add_club_member():

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "").strip()

    if not name or not email or not role:
        return redirect("/club/members")

    allowed_roles = [
        "President",
        "Vice President",
        "Secretary",
        "Treasurer",
        "Team Lead",
        "Member"
    ]

    if role not in allowed_roles:
        return "Invalid member role.", 400

    conn = get_db()

    club = conn.execute(
        """
        SELECT id
        FROM clubs
        WHERE id = ?
        """,
        (club_id,)
    ).fetchone()

    if club is None:

        conn.close()
        session.clear()

        return redirect("/login?type=club")

    existing = conn.execute(
        """
        SELECT id
        FROM club_members
        WHERE club_id = ?
        AND LOWER(email) = LOWER(?)
        """,
        (
            club_id,
            email
        )
    ).fetchone()

    if existing:

        conn.close()

        return redirect("/club/members")

    try:

        conn.execute(
            """
            INSERT INTO club_members
            (
                club_id,
                name,
                email,
                role
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                club_id,
                name,
                email,
                role
            )
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        conn.close()

        return f"Could not add member: {e}", 500

    conn.close()

    return redirect("/club/members")


# ============================================================
# CLUB — REMOVE MEMBER
# ============================================================

@app.route(
    "/club/members/<int:member_id>/remove",
    methods=["POST"]
)
def remove_club_member(member_id):

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    member = conn.execute(
        """
        SELECT id
        FROM club_members
        WHERE id = ?
        AND club_id = ?
        """,
        (
            member_id,
            club_id
        )
    ).fetchone()

    if member is None:

        conn.close()

        return "Member not found.", 404

    conn.execute(
        """
        DELETE FROM club_members
        WHERE id = ?
        AND club_id = ?
        """,
        (
            member_id,
            club_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/club/members")


# ============================================================
# CLUB PROFILE
# ============================================================

@app.route(
    "/club/profile",
    methods=["GET", "POST"]
)
def club_profile():

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        club_name = request.form.get(
            "club_name",
            ""
        ).strip()

        university = request.form.get(
            "university",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        benefits = request.form.get(
            "benefits",
            ""
        ).strip()

        notice = request.form.get(
            "notice",
            ""
        ).strip()

        if (
            not club_name
            or not university
            or not category
            or not email
        ):

            club = conn.execute(
                """
                SELECT *
                FROM clubs
                WHERE id = ?
                """,
                (club_id,)
            ).fetchone()

            conn.close()

            return render_template(
                "club_profile.html",
                club=club,
                error=(
                    "Club name, university, category "
                    "and email are required."
                )
            )

        existing = conn.execute(
            """
            SELECT id
            FROM clubs
            WHERE LOWER(email) = ?
            AND id != ?
            """,
            (
                email,
                club_id
            )
        ).fetchone()

        if existing:

            club = conn.execute(
                """
                SELECT *
                FROM clubs
                WHERE id = ?
                """,
                (club_id,)
            ).fetchone()

            conn.close()

            return render_template(
                "club_profile.html",
                club=club,
                error="That email is already being used."
            )

        try:

            conn.execute(
                """
                UPDATE clubs
                SET
                    club_name = ?,
                    university = ?,
                    category = ?,
                    email = ?,
                    description = ?,
                    benefits = ?,
                    notice = ?
                WHERE id = ?
                """,
                (
                    club_name,
                    university,
                    category,
                    email,
                    description,
                    benefits,
                    notice,
                    club_id
                )
            )

            conn.commit()

            session["name"] = club_name

        except Exception as e:

            conn.rollback()
            conn.close()

            return render_template(
                "club_profile.html",
                error=f"Club profile update failed: {e}"
            )

    club = conn.execute(
        """
        SELECT *
        FROM clubs
        WHERE id = ?
        """,
        (club_id,)
    ).fetchone()

    conn.close()

    if club is None:

        session.clear()

        return redirect("/login?type=club")

    return render_template(
        "club_profile.html",
        club=club
    )


# ============================================================
# CLUB — RECRUITMENT STATUS
# ============================================================

@app.route(
    "/club/status",
    methods=["POST"]
)
def club_status():

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [
        "Open",
        "Under Review",
        "Closed",
        "Coming Soon"
    ]

    if status not in allowed_statuses:
        return "Invalid recruitment status.", 400

    conn = get_db()

    conn.execute(
        """
        UPDATE clubs
        SET recruitment_status = ?
        WHERE id = ?
        """,
        (
            status,
            club_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/club/dashboard")


# ============================================================
# CLUB — APPLICATIONS
# ============================================================

@app.route("/club/applications")
def club_applications():

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    applications = conn.execute(
        """
        SELECT
            applications.id,
            applications.student_id,
            applications.status,
            applications.applied_at,
            applications.skills,
            applications.interests,
            applications.why_join,
            applications.portfolio,
            users.name,
            users.email,
            users.course,
            users.year
        FROM applications
        JOIN users
            ON applications.student_id = users.id
        WHERE applications.club_id = ?
        ORDER BY applications.applied_at DESC
        """,
        (club_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "club_applications.html",
        applications=applications
    )


# ============================================================
# CLUB — APPLICATION DETAILS
# ============================================================

@app.route(
    "/club/application/<int:application_id>"
)
def view_application(application_id):

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    application = conn.execute(
        """
        SELECT
            applications.id,
            applications.student_id,
            applications.club_id,
            applications.status,
            applications.applied_at,
            applications.skills,
            applications.interests,
            applications.why_join,
            applications.portfolio,
            users.name,
            users.email,
            users.course,
            users.year,
            users.goals
        FROM applications
        JOIN users
            ON applications.student_id = users.id
        WHERE applications.id = ?
        AND applications.club_id = ?
        """,
        (
            application_id,
            club_id
        )
    ).fetchone()

    conn.close()

    if application is None:
        return "Application not found.", 404

    return render_template(
        "application_details.html",
        application=application
    )


# ============================================================
# CLUB — UPDATE APPLICATION STATUS
# ============================================================

@app.route(
    "/club/application/<int:application_id>/status",
    methods=["POST"]
)
def update_application_status(application_id):

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [
        "Pending",
        "Under Review",
        "Eligible for Test",
        "Eligible for Interview",
        "Selected",
        "Rejected"
    ]

    if status not in allowed_statuses:
        return "Invalid application status.", 400

    conn = get_db()

    application = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE id = ?
        AND club_id = ?
        """,
        (
            application_id,
            club_id
        )
    ).fetchone()

    if application is None:

        conn.close()

        return "Application not found.", 404

    conn.execute(
        """
        UPDATE applications
        SET status = ?
        WHERE id = ?
        AND club_id = ?
        """,
        (
            status,
            application_id,
            club_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/club/applications")


# ============================================================
# CLUB — ACCEPT APPLICATION
# ============================================================

@app.route(
    "/club/application/<int:application_id>/accept",
    methods=["POST"]
)
def accept_application(application_id):

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    application = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE id = ?
        AND club_id = ?
        """,
        (
            application_id,
            club_id
        )
    ).fetchone()

    if application is None:

        conn.close()

        return "Application not found.", 404

    conn.execute(
        """
        UPDATE applications
        SET status = 'Selected'
        WHERE id = ?
        AND club_id = ?
        """,
        (
            application_id,
            club_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/club/applications")


# ============================================================
# CLUB — REJECT APPLICATION
# ============================================================

@app.route(
    "/club/application/<int:application_id>/reject",
    methods=["POST"]
)
def reject_application(application_id):

    auth_error = require_club()

    if auth_error:
        return auth_error

    club_id = session["user_id"]

    conn = get_db()

    application = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE id = ?
        AND club_id = ?
        """,
        (
            application_id,
            club_id
        )
    ).fetchone()

    if application is None:

        conn.close()

        return "Application not found.", 404

    conn.execute(
        """
        UPDATE applications
        SET status = 'Rejected'
        WHERE id = ?
        AND club_id = ?
        """,
        (
            application_id,
            club_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/club/applications")


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return (
        """
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for does not exist.</p>
        <p>
            <a href="/">Return to CampusConnect</a>
        </p>
        """,
        404
    )


@app.errorhandler(500)
def internal_server_error(error):

    return (
        """
        <h1>500 - Internal Server Error</h1>
        <p>Something went wrong.</p>
        <p>
            <a href="/">Return to CampusConnect</a>
        </p>
        """,
        500
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)