import sqlite3


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_NAME = "campusconnect.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# HELPER — CHECK COLUMN
# ============================================================

def column_exists(conn, table_name, column_name):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


# ============================================================
# HELPER — ADD COLUMN IF MISSING
# ============================================================

def add_column_if_missing(
    conn,
    table_name,
    column_name,
    column_definition
):

    if not column_exists(
        conn,
        table_name,
        column_name
    ):

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()

    try:

        # ====================================================
        # STUDENTS / USERS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                email TEXT UNIQUE NOT NULL,

                password TEXT NOT NULL,

                user_type TEXT NOT NULL,

                course TEXT DEFAULT '',

                year TEXT DEFAULT '',

                interests TEXT DEFAULT '',

                skills TEXT DEFAULT '',

                goals TEXT DEFAULT ''

            )
        """)

        # Existing databases may not have the profile fields.
        add_column_if_missing(
            conn,
            "users",
            "course",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "users",
            "year",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "users",
            "interests",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "users",
            "skills",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "users",
            "goals",
            "TEXT DEFAULT ''"
        )


        # ====================================================
        # CLUBS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS clubs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                club_name TEXT NOT NULL,

                university TEXT NOT NULL,

                category TEXT NOT NULL,

                email TEXT UNIQUE NOT NULL,

                password TEXT NOT NULL,

                recruitment_status TEXT
                    DEFAULT 'Open',

                description TEXT
                    DEFAULT '',

                benefits TEXT
                    DEFAULT '',

                notice TEXT
                    DEFAULT ''

            )
        """)

        add_column_if_missing(
            conn,
            "clubs",
            "recruitment_status",
            "TEXT DEFAULT 'Open'"
        )

        add_column_if_missing(
            conn,
            "clubs",
            "description",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "clubs",
            "benefits",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "clubs",
            "notice",
            "TEXT DEFAULT ''"
        )


        # ====================================================
        # CLUB MEMBERS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS club_members (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                club_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                email TEXT NOT NULL,

                role TEXT NOT NULL,

                FOREIGN KEY (club_id)
                    REFERENCES clubs(id)
                    ON DELETE CASCADE

            )
        """)


        # ====================================================
        # APPLICATIONS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                student_id INTEGER NOT NULL,

                club_id INTEGER NOT NULL,

                status TEXT
                    DEFAULT 'Pending',

                applied_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                skills TEXT
                    DEFAULT '',

                interests TEXT
                    DEFAULT '',

                why_join TEXT
                    DEFAULT '',

                portfolio TEXT
                    DEFAULT '',

                FOREIGN KEY (student_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (club_id)
                    REFERENCES clubs(id)
                    ON DELETE CASCADE

            )
        """)

        # Existing applications table migration
        add_column_if_missing(
            conn,
            "applications",
            "skills",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "applications",
            "interests",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "applications",
            "why_join",
            "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn,
            "applications",
            "portfolio",
            "TEXT DEFAULT ''"
        )


        # ====================================================
        # ANNOUNCEMENTS
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS announcements (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                club_id INTEGER NOT NULL,

                title TEXT NOT NULL,

                content TEXT NOT NULL,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (club_id)
                    REFERENCES clubs(id)
                    ON DELETE CASCADE

            )
        """)


        # ====================================================
        # INDEXES
        # ====================================================

        # These make searches and application lookups faster.

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_applications_student
            ON applications(student_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_applications_club
            ON applications(club_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_applications_status
            ON applications(status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_members_club
            ON club_members(club_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_announcements_club
            ON announcements(club_id)
        """)


        # ====================================================
        # CLEAN UP NULL PROFILE VALUES
        # ====================================================

        conn.execute("""
            UPDATE users
            SET course = ''
            WHERE course IS NULL
        """)

        conn.execute("""
            UPDATE users
            SET year = ''
            WHERE year IS NULL
        """)

        conn.execute("""
            UPDATE users
            SET interests = ''
            WHERE interests IS NULL
        """)

        conn.execute("""
            UPDATE users
            SET skills = ''
            WHERE skills IS NULL
        """)

        conn.execute("""
            UPDATE users
            SET goals = ''
            WHERE goals IS NULL
        """)


        # ====================================================
        # CLEAN UP NULL CLUB VALUES
        # ====================================================

        conn.execute("""
            UPDATE clubs
            SET recruitment_status = 'Open'
            WHERE recruitment_status IS NULL
               OR recruitment_status = ''
        """)

        conn.execute("""
            UPDATE clubs
            SET description = ''
            WHERE description IS NULL
        """)

        conn.execute("""
            UPDATE clubs
            SET benefits = ''
            WHERE benefits IS NULL
        """)

        conn.execute("""
            UPDATE clubs
            SET notice = ''
            WHERE notice IS NULL
        """)


        # ====================================================
        # COMMIT
        # ====================================================

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    init_db()

    print(
        "CampusConnect database initialized successfully."
    )