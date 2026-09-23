from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import time
from datetime import datetime
import random
from flask import session, flash
from flask_mail import Message


import re
import time

from werkzeug.security import generate_password_hash

from dotenv import load_dotenv
from flask_mail import Mail, Message
from ml_model import complete_ai_analysis

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
app = Flask(__name__)
app.secret_key = o.getenv("SECRET_KEY")


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "change-this-secret-key"
)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================
# ============================================================
# EMAIL CONFIGURATION
# ============================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

# TEST_EMAIL is optional. If not set, /test-email sends to the
# configured MAIL_USERNAME account.
mail = Mail(app)

@app.route("/test-email")
def test_email():

    try:
        msg = Message(
            subject="Online Quiz Master - Test Email",
            sender=app.config["MAIL_USERNAME"],
            recipients=[os.getenv("TEST_EMAIL", app.config["MAIL_USERNAME"])]
        )

        msg.body = """
Hello,

This is a test email from Online Quiz Master.

If you received this email, Flask-Mail is working correctly.

Thank you.
"""

        mail.send(msg)

        print("========================================")
        print("EMAIL SENT SUCCESSFULLY")
        print("========================================")

        return "EMAIL SENT SUCCESSFULLY! Check your Gmail inbox."

    except Exception as e:

        print("========================================")
        print("EMAIL SEND FAILED")
        print("ERROR:", str(e))
        print("========================================")

        return f"EMAIL FAILED: {str(e)}"
# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    conn = sqlite3.connect("database/quiz.db")

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================
def init_db():

    os.makedirs("database", exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            username TEXT NOT NULL UNIQUE,

            password TEXT NOT NULL

        )
    """)

    # =========================
    # QUIZ HISTORY TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            subject TEXT NOT NULL,

            level TEXT NOT NULL,

            total INTEGER NOT NULL,

            correct INTEGER NOT NULL,

            wrong INTEGER NOT NULL,

            skipped INTEGER NOT NULL,

            time_taken INTEGER NOT NULL,

            accuracy REAL NOT NULL,

            performance_score REAL NOT NULL,

            cognitive_level TEXT,

            recommended_level TEXT,

            strength TEXT,

            weakness TEXT,

            learning_profile TEXT,

            confidence REAL,

            recommendation TEXT,

            created_at TEXT NOT NULL

        )
    """)
        # =========================
    # QUESTIONS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            section TEXT,
            level TEXT NOT NULL,
            question_type TEXT,
            topic TEXT,
            company TEXT,
            year INTEGER,
            passage TEXT,
            question TEXT NOT NULL,
            option1 TEXT,
            option2 TEXT,
            option3 TEXT,
            option4 TEXT,
            answer TEXT NOT NULL,
            explanation TEXT,
            hint TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
# ============================================================
# SEND RESULT EMAIL
# ============================================================

def send_result_email(
    email,
    username,
    subject,
    level,
    total,
    correct,
    wrong,
    skipped,
    cognitive_level,
    performance_score,
    timeout=False
):

    if not email:

        raise ValueError(
            "User email address is empty."
        )

    if not app.config["MAIL_USERNAME"]:

        raise ValueError(
            "MAIL_USERNAME is missing from .env"
        )

    if not app.config["MAIL_PASSWORD"]:

        raise ValueError(
            "MAIL_PASSWORD is missing from .env"
        )

    if timeout:

        status = "TIME OUT"

    else:

        status = "QUIZ COMPLETED"


    message = Message(

        subject="Online Quiz Master - Quiz Result",

        sender=app.config["MAIL_USERNAME"],

        recipients=[email]

    )


    message.body = f"""
Hello {username},

Your Online Quiz Master result is ready.

========================================

Subject: {subject}

Level: {level}

Status: {status}

========================================

Total Questions: {total}

Correct Answers: {correct}

Wrong Answers: {wrong}

Skipped Questions: {skipped}

Performance Score: {performance_score}%

Cognitive Level: {cognitive_level}

========================================

Thank you for using Online Quiz Master.

Keep learning and keep practicing!

Online Quiz Master
"""


    mail.send(message)

    print()
    print("========================================")
    print("EMAIL SENT SUCCESSFULLY")
    print("TO:", email)
    print("========================================")
    print()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return redirect(
        url_for("register")
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    # ==========================================
    # REGISTRATION PROCESS
    #
    # STEP 1 → Full Name + Email
    # STEP 2 → Verify Email OTP
    # STEP 3 → Username + Password
    # ==========================================

    if request.method == "POST":

        action = request.form.get("action", "").strip()

        # ==================================================
        # STEP 1: SEND VERIFICATION CODE
        # ==================================================

        if action == "send_code":

            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()

            # ------------------------------------------
            # CHECK FULL NAME AND EMAIL
            # ------------------------------------------

            if not name or not email:
                return render_template(
                    "register.html",
                    step=1,
                    error="Please enter your full name and email address."
                )

            # ------------------------------------------
            # CHECK EMAIL FORMAT
            # ------------------------------------------

            email_pattern = (
                r"^[A-Za-z0-9._%+-]+@"
                r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            )

            if not re.fullmatch(email_pattern, email):
                return render_template(
                    "register.html",
                    step=1,
                    error="Please enter a valid email address."
                )

            # ------------------------------------------
            # REJECT DOUBLE DOTS
            # ------------------------------------------

            if ".." in email:
                return render_template(
                    "register.html",
                    step=1,
                    error="Please enter a valid email address."
                )

            # ------------------------------------------
            # GENERATE 6-DIGIT OTP
            # ------------------------------------------

            verification_code = str(
                random.randint(100000, 999999)
            )

            # ------------------------------------------
            # SAVE TEMPORARY REGISTRATION DATA
            # ------------------------------------------

            session["pending_registration"] = {
                "name": name,
                "email": email
            }

            session["email_verification_code"] = verification_code
            session["email_code_time"] = time.time()
            session["email_verified"] = False

            # ------------------------------------------
            # SEND OTP TO EMAIL
            # ------------------------------------------

            try:

                message = Message(
                    subject="Quiz Master - Email Verification Code",
                    recipients=[email]
                )

                message.body = f"""
Hello {name},

Welcome to Quiz Master!

Your email verification code is:

{verification_code}

This code is valid for 10 minutes.

Please do not share this code with anyone.

Thank you,
Quiz Master
"""

                mail.send(message)

            except Exception as e:

                print("EMAIL CODE ERROR:", e)

                session.pop("pending_registration", None)
                session.pop("email_verification_code", None)
                session.pop("email_code_time", None)
                session.pop("email_verified", None)

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Unable to send verification code. "
                        "Please check the email address and try again."
                    )
                )

            # ------------------------------------------
            # SHOW STEP 2
            # ------------------------------------------

            return render_template(
                "register.html",
                step=2,
                success=(
                    "Verification code sent to your email. "
                    "Please check your inbox."
                )
            )

        # ==================================================
        # STEP 2: RESEND VERIFICATION CODE
        # ==================================================

        elif action == "resend_code":

            pending_data = session.get(
                "pending_registration"
            )

            # ------------------------------------------
            # CHECK REGISTRATION SESSION
            # ------------------------------------------

            if not pending_data:

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Registration session expired. "
                        "Please enter your name and email again."
                    )
                )

            name = pending_data.get("name", "")
            email = pending_data.get("email", "")

            if not name or not email:

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Registration session expired. "
                        "Please try again."
                    )
                )

            # ------------------------------------------
            # GENERATE NEW OTP
            # ------------------------------------------

            verification_code = str(
                random.randint(100000, 999999)
            )

            # ------------------------------------------
            # SAVE NEW OTP
            # ------------------------------------------

            session["email_verification_code"] = verification_code
            session["email_code_time"] = time.time()
            session["email_verified"] = False

            # ------------------------------------------
            # SEND NEW OTP
            # ------------------------------------------

            try:

                message = Message(
                    subject="Quiz Master - New Email Verification Code",
                    recipients=[email]
                )

                message.body = f"""
Hello {name},

Your new Quiz Master email verification code is:

{verification_code}

This code is valid for 10 minutes.

Please do not share this code with anyone.

Thank you,
Quiz Master
"""

                mail.send(message)

            except Exception as e:

                print("RESEND EMAIL ERROR:", e)

                return render_template(
                    "register.html",
                    step=2,
                    error=(
                        "Unable to resend the verification code. "
                        "Please try again."
                    )
                )

            # ------------------------------------------
            # SHOW STEP 2 AGAIN
            # ------------------------------------------

            return render_template(
                "register.html",
                step=2,
                success=(
                    "A new verification code has been sent "
                    "to your email."
                )
            )

        # ==================================================
        # STEP 2: VERIFY EMAIL CODE
        # ==================================================

        elif action == "verify_code":

            entered_code = request.form.get(
                "verification_code",
                ""
            ).strip()

            pending_data = session.get(
                "pending_registration"
            )

            saved_code = session.get(
                "email_verification_code"
            )

            saved_time = session.get(
                "email_code_time",
                0
            )

            # ------------------------------------------
            # CHECK SESSION
            # ------------------------------------------

            if not pending_data or not saved_code:

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Please enter your name and email again."
                    )
                )

            # ------------------------------------------
            # CHECK OTP LENGTH
            # ------------------------------------------

            if (
                not entered_code
                or len(entered_code) != 6
                or not entered_code.isdigit()
            ):

                return render_template(
                    "register.html",
                    step=2,
                    error=(
                        "Please enter the 6-digit "
                        "verification code."
                    )
                )

            # ------------------------------------------
            # CHECK OTP EXPIRY
            # ------------------------------------------

            if time.time() - saved_time > 600:

                session.pop(
                    "pending_registration",
                    None
                )

                session.pop(
                    "email_verification_code",
                    None
                )

                session.pop(
                    "email_code_time",
                    None
                )

                session.pop(
                    "email_verified",
                    None
                )

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Verification code expired. "
                        "Please request a new code."
                    )
                )

            # ------------------------------------------
            # CHECK OTP
            # ------------------------------------------

            if entered_code != saved_code:

                return render_template(
                    "register.html",
                    step=2,
                    error=(
                        "Incorrect verification code. "
                        "Please try again."
                    )
                )

            # ------------------------------------------
            # EMAIL VERIFIED
            # ------------------------------------------

            session["email_verified"] = True

            session.pop(
                "email_verification_code",
                None
            )

            session.pop(
                "email_code_time",
                None
            )

            # ------------------------------------------
            # SHOW STEP 3
            # ------------------------------------------

            return render_template(
                "register.html",
                step=3,
                success=(
                    "Email verified successfully! "
                    "Now create your username and password."
                )
            )

        # ==================================================
        # STEP 3: CREATE ACCOUNT
        # ==================================================

        elif action == "create_account":

            # ------------------------------------------
            # CHECK EMAIL VERIFICATION
            # ------------------------------------------

            if not session.get("email_verified"):

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Please verify your email "
                        "before creating an account."
                    )
                )

            # ------------------------------------------
            # GET TEMPORARY REGISTRATION DATA
            # ------------------------------------------

            pending_data = session.get(
                "pending_registration"
            )

            if not pending_data:

                return render_template(
                    "register.html",
                    step=1,
                    error=(
                        "Registration session expired. "
                        "Please start again."
                    )
                )

            # ------------------------------------------
            # GET USERNAME
            # ------------------------------------------

            username = request.form.get(
                "username",
                ""
            ).strip()

            # ------------------------------------------
            # GET PASSWORD
            # ------------------------------------------

            password = request.form.get(
                "password",
                ""
            ).strip()

            # ------------------------------------------
            # GET CONFIRM PASSWORD
            # ------------------------------------------

            confirm_password = request.form.get(
                "confirm_password",
                ""
            ).strip()

            # ------------------------------------------
            # CHECK ALL ACCOUNT FIELDS
            # ------------------------------------------

            if (
                not username
                or not password
                or not confirm_password
            ):

                return render_template(
                    "register.html",
                    step=3,
                    error="Please fill all the account fields."
                )

            # ------------------------------------------
            # CHECK USERNAME LENGTH
            # ------------------------------------------

            if len(username) < 3:

                return render_template(
                    "register.html",
                    step=3,
                    error=(
                        "Username must contain at least "
                        "3 characters."
                    )
                )

            # ------------------------------------------
            # CHECK PASSWORD MATCH
            # ------------------------------------------

            if password != confirm_password:

                return render_template(
                    "register.html",
                    step=3,
                    error=(
                        "Password and confirm password "
                        "do not match."
                    )
                )

            # ------------------------------------------
            # CHECK PASSWORD LENGTH
            # ------------------------------------------

            if len(password) < 6:

                return render_template(
                    "register.html",
                    step=3,
                    error=(
                        "Password must contain at least "
                        "6 characters."
                    )
                )

            # ------------------------------------------
            # DATABASE CONNECTION
            # ------------------------------------------

            conn = get_db_connection()

            try:

                # ======================================
                # CHECK ONLY USERNAME
                #
                # Full Name is NOT checked here.
                # Therefore:
                #
                # Full Name = B Kavana
                # Username  = B Kavana
                #
                # is allowed if the username is available.
                # ======================================

                existing_user = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(TRIM(username))
                          = LOWER(TRIM(?))
                    """,
                    (username,)
                ).fetchone()

                if existing_user:

                    return render_template(
                        "register.html",
                        step=3,
                        error=(
                            "Username already exists. "
                            "Please choose another username."
                        )
                    )

                # --------------------------------------
                # HASH PASSWORD
                # --------------------------------------

                hashed_password = generate_password_hash(
                    password
                )

                # --------------------------------------
                # CREATE ACCOUNT
                #
                # Duplicate email is allowed.
                # Username must be unique.
                # Full Name can be same as Username.
                # --------------------------------------

                conn.execute(
                    """
                    INSERT INTO users
                    (
                        name,
                        email,
                        username,
                        password
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        pending_data["name"],
                        pending_data["email"],
                        username,
                        hashed_password
                    )
                )

                conn.commit()

            except Exception as e:

                conn.rollback()

                print(
                    "REGISTRATION ERROR:",
                    e
                )

                return render_template(
                    "register.html",
                    step=3,
                    error=(
                        "Unable to create account. "
                        "Please try again."
                    )
                )

            finally:

                conn.close()

            # ------------------------------------------
            # CLEAR REGISTRATION SESSION
            # ------------------------------------------

            session.pop(
                "pending_registration",
                None
            )

            session.pop(
                "email_verified",
                None
            )

            session.pop(
                "email_verification_code",
                None
            )

            session.pop(
                "email_code_time",
                None
            )

            # ------------------------------------------
            # GO TO LOGIN
            # ------------------------------------------

            return redirect(
                url_for("login")
            )

        # ==================================================
        # INVALID ACTION
        # ==================================================

        else:

            return render_template(
                "register.html",
                step=1,
                error="Invalid registration request."
            )

    # ==================================================
    # DEFAULT REGISTER PAGE
    # ==================================================

    return render_template(
        "register.html",
        step=1
    )

@app.route("/verify-email", methods=["GET", "POST"])
def verify_email():

    # ==========================================
    # CHECK PENDING REGISTRATION
    # ==========================================

    if (
        "pending_registration" not in session
        or "register_otp" not in session
    ):
        return redirect(
            url_for("register")
        )

    if request.method == "POST":

        entered_otp = request.form.get(
            "otp",
            ""
        ).strip()

        # ==========================================
        # CHECK OTP EXPIRY
        # ==========================================

        otp_time = session.get(
            "otp_time",
            0
        )

        if time.time() - otp_time > 600:

            session.pop("pending_registration", None)
            session.pop("register_otp", None)
            session.pop("otp_time", None)

            return render_template(
                "verify_email.html",
                error="OTP expired. Please register again."
            )

        # ==========================================
        # CHECK OTP
        # ==========================================

        if entered_otp != session.get("register_otp"):

            return render_template(
                "verify_email.html",
                error="Invalid OTP. Please enter the correct OTP."
            )

        # ==========================================
        # OTP CORRECT
        # CREATE ACCOUNT
        # ==========================================

        data = session["pending_registration"]

        conn = get_db_connection()

        try:

            # Check username again
            existing_user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (data["username"],)
            ).fetchone()

            if existing_user:

                return render_template(
                    "verify_email.html",
                    error=(
                        "Username already exists. "
                        "Please register with another username."
                    )
                )

            hashed_password = generate_password_hash(
                data["password"]
            )

            conn.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    username,
                    password
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    data["name"],
                    data["email"],
                    data["username"],
                    hashed_password
                )
            )

            conn.commit()

        except Exception as e:

            conn.rollback()

            print("REGISTRATION ERROR:", e)

            return render_template(
                "verify_email.html",
                error="Registration failed. Please try again."
            )

        finally:

            conn.close()

        # ==========================================
        # CLEAR TEMPORARY DATA
        # ==========================================

        session.pop("pending_registration", None)
        session.pop("register_otp", None)
        session.pop("otp_time", None)

        # ==========================================
        # REDIRECT TO LOGIN
        # ==========================================

        return redirect(
            url_for("login")
        )

    return render_template("verify_email.html")
# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        conn = get_db_connection()


        user = conn.execute(
            """
            SELECT
                id,
                name,
                email,
                username,
                password
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()


        conn.close()


        if user:

            stored_password = user["password"]


            try:

                password_correct = check_password_hash(
                    stored_password,
                    password
                )

            except Exception:

                # Supports old plain-text passwords
                password_correct = (
                    stored_password == password
                )


            if password_correct:

                session.clear()

                session["user"] = user["username"]

                return redirect(
                    url_for("dashboard")
                )


        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )


    return render_template(
        "login.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        return redirect(
            url_for("login")
        )


    username = session["user"]


    conn = get_db_connection()


    stats = conn.execute(
        """
        SELECT

            COUNT(*) AS attempts,

            COALESCE(
                MAX(accuracy),
                0
            ) AS best_score,

            COALESCE(
                AVG(accuracy),
                0
            ) AS average_score

        FROM quiz_history

        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    subject_count = conn.execute(
        """
        SELECT
            COUNT(DISTINCT subject) AS count

        FROM quiz_history

        WHERE username = ?
        """,
        (username,)
    ).fetchone()["count"]


    recent = conn.execute(
        """
        SELECT

            subject,
            level,
            accuracy,
            cognitive_level,
            created_at

        FROM quiz_history

        WHERE username = ?

        ORDER BY id DESC

        LIMIT 5
        """,
        (username,)
    ).fetchall()


    conn.close()


    return render_template(

        "dashboard.html",

        username=username,

        subjects=list(quizzes.keys()),

        attempts=stats["attempts"],

        best_score=round(
            stats["best_score"],
            2
        ),

        average_score=round(
            stats["average_score"],
            2
        ),

        subject_count=subject_count,

        recent=recent

    )


# ============================================================
# LEVEL
# ============================================================

@app.route("/level/<path:subject>")
def level(subject):

    if "user" not in session:
        return redirect(url_for("login"))

    # Allow Placement Preparation
    if subject == "Placement Preparation":
        return render_template(
            "level.html",
            subject="Placement Preparation"
        )

    # Check other quiz subjects
    if subject not in quizzes:
        return "Subject not found", 404

    return render_template(
        "level.html",
        subject=subject
    )

# ============================================================
# QUIZ HISTORY
# ============================================================

@app.route("/history")
def history():

    if "user" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db_connection()


    rows = conn.execute(
        """
        SELECT *

        FROM quiz_history

        WHERE username = ?

        ORDER BY id DESC
        """,
        (session["user"],)
    ).fetchall()


    conn.close()


    return render_template(
        "history.html",
        history=rows
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile")
def profile():

    if "user" not in session:

        return redirect(
            url_for("login")
        )


    username = session["user"]


    conn = get_db_connection()


    user = conn.execute(
        """
        SELECT
            name,
            email,
            username

        FROM users

        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    stats = conn.execute(
        """
        SELECT

            COUNT(*) AS attempts,

            COALESCE(
                MAX(accuracy),
                0
            ) AS best_score,

            COALESCE(
                AVG(accuracy),
                0
            ) AS average_score

        FROM quiz_history

        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    conn.close()


    return render_template(

        "profile.html",

        user=user,

        attempts=stats["attempts"],

        best_score=round(
            stats["best_score"],
            2
        ),

        average_score=round(
            stats["average_score"],
            2
        )

    )



quizzes = {
    "Python Programming": {
        "Easy": [
    {
        "question": "Python is a ______ language.",
        "options": ["High Level", "Low Level", "Machine", "Assembly"],
        "answer": "High Level"
    },
    {
        "question": "Who developed Python?",
        "options": ["James Gosling", "Guido van Rossum", "Dennis Ritchie", "Bjarne Stroustrup"],
        "answer": "Guido van Rossum"
    },
    {
        "question": "Which symbol is used for comments?",
        "options": ["//", "#", "/*", "--"],
        "answer": "#"
    },
    {
        "question": "Which function displays output?",
        "options": ["print()", "display()", "show()", "echo()"],
        "answer": "print()"
    },
    {
        "question": "Which keyword defines a function?",
        "options": ["function", "fun", "def", "define"],
        "answer": "def"
    },
    {
        "question": "Python files have extension?",
        "options": [".py", ".java", ".cpp", ".html"],
        "answer": ".py"
    },
    {
        "question": "Which function takes user input?",
        "options": ["input()", "print()", "scan()", "read()"],
        "answer": "input()"
    },
    {
        "question": "Which data type stores text?",
        "options": ["str", "int", "float", "bool"],
        "answer": "str"
    },
    {
        "question": "Which loop repeats for a known number of times?",
        "options": ["for", "while", "repeat", "do"],
        "answer": "for"
    },
    {
        "question": "Which brackets are used for a list?",
        "options": ["( )", "[ ]", "{ }", "< >"],
        "answer": "[ ]"
    }
],
        "Medium": [
    {
        "question": "Which keyword is used to create a class in Python?",
        "options": ["class", "Class", "define", "object"],
        "answer": "class"
    },
    {
        "question": "Which data type is immutable?",
        "options": ["List", "Dictionary", "Tuple", "Set"],
        "answer": "Tuple"
    },
    {
        "question": "Which operator is used for exponentiation?",
        "options": ["^", "**", "%", "//"],
        "answer": "**"
    },
    {
        "question": "Which function returns the length of a list?",
        "options": ["count()", "size()", "len()", "length()"],
        "answer": "len()"
    },
    {
        "question": "Which keyword exits a loop?",
        "options": ["break", "continue", "stop", "exit"],
        "answer": "break"
    },
    {
        "question": "Which function converts a string into an integer?",
        "options": ["str()", "float()", "int()", "bool()"],
        "answer": "int()"
    },
    {
        "question": "Which operator checks equality?",
        "options": ["=", "==", "!=", ">"],
        "answer": "=="
    },
    {
        "question": "Which collection stores key-value pairs?",
        "options": ["Tuple", "List", "Dictionary", "Set"],
        "answer": "Dictionary"
    },
    {
        "question": "Which method removes the last item from a list?",
        "options": ["append()", "pop()", "remove()", "delete()"],
        "answer": "pop()"
    },
    {
        "question": "Which loop executes while a condition is True?",
        "options": ["for", "repeat", "while", "foreach"],
        "answer": "while"
    }
],
        "Hard": [
    {
        "question": "Which module is used for regular expressions?",
        "options": ["regex", "re", "pattern", "pyregex"],
        "answer": "re"
    },
    {
        "question": "Which keyword is used to handle exceptions?",
        "options": ["try", "catch", "except", "throw"],
        "answer": "try"
    },
    {
        "question": "Which keyword catches an exception?",
        "options": ["catch", "except", "throw", "finally"],
        "answer": "except"
    },
    {
        "question": "Which function opens a file?",
        "options": ["file()", "open()", "read()", "load()"],
        "answer": "open()"
    },
    {
        "question": "Which method adds an item to a list?",
        "options": ["append()", "insert()", "add()", "push()"],
        "answer": "append()"
    },
    {
        "question": "Which collection does NOT allow duplicate values?",
        "options": ["List", "Tuple", "Set", "Dictionary"],
        "answer": "Set"
    },
    {
        "question": "Which keyword imports a module?",
        "options": ["include", "using", "import", "require"],
        "answer": "import"
    },
    {
        "question": "Which function creates an anonymous function?",
        "options": ["lambda", "anonymous", "def", "func"],
        "answer": "lambda"
    },
    {
        "question": "Which keyword skips the current loop iteration?",
        "options": ["continue", "break", "skip", "pass"],
        "answer": "continue"
    },
    {
        "question": "Which keyword is used to define a generator?",
        "options": ["yield", "return", "generate", "next"],
        "answer": "yield"
    }
],
    },
    "Java Programming": {

        "Easy": [

        {
            "question": "Java was developed by?",
            "options": ["Microsoft", "Sun Microsystems", "IBM", "Google"],
            "answer": "Sun Microsystems"
        },
        {
            "question": "Java is a ______ language.",
            "options": ["Object-Oriented", "Machine", "Assembly", "Low Level"],
            "answer": "Object-Oriented"
        },
        {
            "question": "Java file extension is?",
            "options": [".java", ".py", ".cpp", ".html"],
            "answer": ".java"
        },
        {
            "question": "Which keyword defines a class?",
            "options": ["class", "Class", "define", "object"],
            "answer": "class"
        },
        {
            "question": "Which method starts execution?",
            "options": ["main()", "run()", "start()", "execute()"],
            "answer": "main()"
        },
        {
            "question": "JVM stands for?",
            "options": ["Java Virtual Machine", "Java Variable Machine", "Java Version Manager", "Joint Virtual Machine"],
            "answer": "Java Virtual Machine"
        },
        {
            "question": "Which keyword creates an object?",
            "options": ["new", "create", "make", "object"],
            "answer": "new"
        },
        {
            "question": "Java is platform ______.",
            "options": ["Independent", "Dependent", "Specific", "Limited"],
            "answer": "Independent"
        },
        {
            "question": "Which symbol ends a statement?",
            "options": [";", ".", ":", ","],
            "answer": ";"
        },
        {
            "question": "Which package is imported automatically?",
            "options": ["java.lang", "java.io", "java.util", "java.net"],
            "answer": "java.lang"
        }

    ],

        "Medium": [

        {
            "question": "Which keyword is used for inheritance?",
            "options": ["extends", "implements", "inherits", "super"],
            "answer": "extends"
        },
        {
            "question": "Which keyword implements an interface?",
            "options": ["implements", "extends", "interface", "inherit"],
            "answer": "implements"
        },
        {
            "question": "Which keyword refers to current object?",
            "options": ["this", "self", "current", "super"],
            "answer": "this"
        },
        {
            "question": "Which keyword prevents inheritance?",
            "options": ["final", "private", "static", "const"],
            "answer": "final"
        },
        {
            "question": "Which loop executes at least once?",
            "options": ["do-while", "while", "for", "foreach"],
            "answer": "do-while"
        },
        {
            "question": "Which collection allows duplicate values?",
            "options": ["ArrayList", "HashSet", "TreeSet", "Set"],
            "answer": "ArrayList"
        },
        {
            "question": "Parent class of every Java class?",
            "options": ["Object", "Main", "Class", "System"],
            "answer": "Object"
        },
        {
            "question": "Which exception occurs while dividing by zero?",
            "options": ["ArithmeticException", "IOException", "NullPointerException", "NumberFormatException"],
            "answer": "ArithmeticException"
        },
        {
            "question": "Java supports ______ inheritance using classes.",
            "options": ["Single", "Multiple", "Hybrid", "None"],
            "answer": "Single"
        },
        {
            "question": "Which keyword throws an exception?",
            "options": ["throw", "throws", "try", "catch"],
            "answer": "throw"
        }

    ],

        "Hard": [

        {
            "question": "Scanner class belongs to?",
            "options": ["java.util", "java.io", "java.lang", "java.net"],
            "answer": "java.util"
        },
        {
            "question": "Which collection doesn't allow duplicates?",
            "options": ["HashSet", "ArrayList", "LinkedList", "Vector"],
            "answer": "HashSet"
        },
        {
            "question": "Thread execution starts with?",
            "options": ["start()", "run()", "execute()", "begin()"],
            "answer": "start()"
        },
        {
            "question": "Constant variables are declared using?",
            "options": ["final", "const", "fixed", "static"],
            "answer": "final"
        },
        {
            "question": "Which method compares strings?",
            "options": ["equals()", "==", "compare()", "same()"],
            "answer": "equals()"
        },
        {
            "question": "Java supports multithreading?",
            "options": ["Yes", "No", "Sometimes", "Linux only"],
            "answer": "Yes"
        },
        {
            "question": "Bytecode executes on?",
            "options": ["JVM", "JDK", "Compiler", "JRE"],
            "answer": "JVM"
        },
        {
            "question": "Current owner of Java?",
            "options": ["Oracle", "IBM", "Microsoft", "Google"],
            "answer": "Oracle"
        },
        {
            "question": "Which operator compares object references?",
            "options": ["==", "equals()", "===", "compare()"],
            "answer": "=="
        },
        {
            "question": "Which keyword imports packages?",
            "options": ["import", "include", "using", "require"],
            "answer": "import"
        }

    ]
    

},
    "Data Structures": {

        "Easy": [
        {
            "question": "What is a Data Structure?",
            "options": ["Way of organizing data", "Programming language", "Database", "Compiler"],
            "answer": "Way of organizing data"
        },
        {
            "question": "Which data structure follows FIFO?",
            "options": ["Stack", "Queue", "Tree", "Graph"],
            "answer": "Queue"
        },
        {
            "question": "Which data structure follows LIFO?",
            "options": ["Queue", "Stack", "Array", "Tree"],
            "answer": "Stack"
        },
        {
            "question": "Which data structure stores elements in contiguous memory?",
            "options": ["Array", "Linked List", "Tree", "Graph"],
            "answer": "Array"
        },
        {
            "question": "Which data structure uses nodes?",
            "options": ["Array", "Linked List", "String", "Matrix"],
            "answer": "Linked List"
        },
        {
            "question": "Which operation adds an element to a stack?",
            "options": ["Push", "Pop", "Insert", "Delete"],
            "answer": "Push"
        },
        {
            "question": "Which operation removes an element from a stack?",
            "options": ["Push", "Pop", "Peek", "Insert"],
            "answer": "Pop"
        },
        {
            "question": "Which data structure is used for recursion?",
            "options": ["Queue", "Stack", "Tree", "Graph"],
            "answer": "Stack"
        },
        {
            "question": "Which data structure is linear?",
            "options": ["Array", "Tree", "Graph", "Heap"],
            "answer": "Array"
        },
        {
            "question": "Queue insertion operation is called?",
            "options": ["Enqueue", "Dequeue", "Push", "Pop"],
            "answer": "Enqueue"
        }
    ],

            "Medium": [
        {
            "question": "Queue deletion operation is called?",
            "options": ["Pop", "Delete", "Dequeue", "Remove"],
            "answer": "Dequeue"
        },
        {
            "question": "Which traversal visits Left-Root-Right?",
            "options": ["Inorder", "Preorder", "Postorder", "Level Order"],
            "answer": "Inorder"
        },
        {
            "question": "Which traversal visits Root-Left-Right?",
            "options": ["Preorder", "Postorder", "Inorder", "BFS"],
            "answer": "Preorder"
        },
        {
            "question": "Which traversal visits Left-Right-Root?",
            "options": ["Postorder", "Preorder", "Inorder", "DFS"],
            "answer": "Postorder"
        },
        {
            "question": "Binary tree maximum children?",
            "options": ["2", "3", "4", "Unlimited"],
            "answer": "2"
        },
        {
            "question": "Graph consists of?",
            "options": ["Vertices and Edges", "Nodes only", "Edges only", "Arrays"],
            "answer": "Vertices and Edges"
        },
        {
            "question": "Which searching algorithm works on sorted arrays?",
            "options": ["Linear Search", "Binary Search", "DFS", "BFS"],
            "answer": "Binary Search"
        },
        {
            "question": "Worst case of Linear Search?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            "answer": "O(n)"
        },
        {
            "question": "Binary Search complexity?",
            "options": ["O(log n)", "O(n)", "O(n²)", "O(1)"],
            "answer": "O(log n)"
        },
        {
            "question": "Tree with one root is called?",
            "options": ["Binary Tree", "General Tree", "Rooted Tree", "AVL Tree"],
            "answer": "Rooted Tree"
        }
    ],

        "Hard": [
    {
        "question": "Which data structure is used in Breadth First Search (BFS)?",
        "options": ["Stack", "Queue", "Linked List", "Tree"],
        "answer": "Queue"
    },
    {
        "question": "Which data structure is used in Depth First Search (DFS)?",
        "options": ["Queue", "Stack", "Array", "Graph"],
        "answer": "Stack"
    },
    {
        "question": "AVL Tree is a ______ tree.",
        "options": ["Balanced Binary Search Tree", "General Tree", "Heap", "Graph"],
        "answer": "Balanced Binary Search Tree"
    },
    {
        "question": "Which sorting algorithm has the best average-case complexity?",
        "options": ["Bubble Sort", "Selection Sort", "Merge Sort", "Insertion Sort"],
        "answer": "Merge Sort"
    },
    {
        "question": "Worst-case time complexity of Bubble Sort is?",
        "options": ["O(n)", "O(log n)", "O(n²)", "O(n log n)"],
        "answer": "O(n²)"
    },
    {
        "question": "Which sorting algorithm repeatedly selects the smallest element?",
        "options": ["Selection Sort", "Merge Sort", "Quick Sort", "Heap Sort"],
        "answer": "Selection Sort"
    },
    {
        "question": "Heap is a type of?",
        "options": ["Binary Tree", "Graph", "Linked List", "Queue"],
        "answer": "Binary Tree"
    },
    {
        "question": "Which data structure is best for implementing a priority queue?",
        "options": ["Heap", "Array", "Stack", "Linked List"],
        "answer": "Heap"
    },
    {
        "question": "Which tree traversal is used to delete a tree?",
        "options": ["Preorder", "Inorder", "Postorder", "Level Order"],
        "answer": "Postorder"
    },
    {
        "question": "Time complexity of inserting an element into a Binary Search Tree (average case)?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
        "answer": "O(log n)"
    }
]

},
    
    "Database Management System": {

    "Easy": [
        {
            "question": "DBMS stands for?",
            "options": ["Database Management System", "Data Management System", "Digital Base Management System", "Database Memory System"],
            "answer": "Database Management System"
        },
        {
            "question": "Which language is used to manage databases?",
            "options": ["Python", "Java", "SQL", "C"],
            "answer": "SQL"
        },
        {
            "question": "Which command is used to retrieve data?",
            "options": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "answer": "SELECT"
        },
        {
            "question": "Which command adds new records?",
            "options": ["ADD", "INSERT", "CREATE", "UPDATE"],
            "answer": "INSERT"
        },
        {
            "question": "Rows in a table are called?",
            "options": ["Records", "Fields", "Columns", "Keys"],
            "answer": "Records"
        },
        {
            "question": "Columns in a table are called?",
            "options": ["Fields", "Rows", "Tables", "Indexes"],
            "answer": "Fields"
        },
        {
            "question": "Which key uniquely identifies a record?",
            "options": ["Foreign Key", "Primary Key", "Candidate Key", "Super Key"],
            "answer": "Primary Key"
        },
        {
            "question": "Which SQL command removes a table?",
            "options": ["DELETE", "DROP", "REMOVE", "ERASE"],
            "answer": "DROP"
        },
        {
            "question": "Which SQL command modifies existing data?",
            "options": ["UPDATE", "ALTER", "INSERT", "CREATE"],
            "answer": "UPDATE"
        },
        {
            "question": "Which SQL command deletes records?",
            "options": ["DELETE", "DROP", "REMOVE", "ERASE"],
            "answer": "DELETE"
        }
    ],

    "Medium": [
        {
            "question": "Which key creates a relationship between tables?",
            "options": ["Primary Key", "Foreign Key", "Candidate Key", "Unique Key"],
            "answer": "Foreign Key"
        },
        {
            "question": "DDL stands for?",
            "options": ["Data Definition Language", "Data Design Language", "Database Development Language", "Data Description Logic"],
            "answer": "Data Definition Language"
        },
        {
            "question": "DML stands for?",
            "options": ["Data Manipulation Language", "Database Management Language", "Data Modeling Language", "Data Main Language"],
            "answer": "Data Manipulation Language"
        },
        {
            "question": "Which SQL clause filters records?",
            "options": ["WHERE", "ORDER BY", "GROUP BY", "HAVING"],
            "answer": "WHERE"
        },
        {
            "question": "Which SQL clause sorts records?",
            "options": ["ORDER BY", "GROUP BY", "SORT", "WHERE"],
            "answer": "ORDER BY"
        },
        {
            "question": "Which normal form removes partial dependency?",
            "options": ["1NF", "2NF", "3NF", "BCNF"],
            "answer": "2NF"
        },
        {
            "question": "Which command changes table structure?",
            "options": ["ALTER", "UPDATE", "MODIFY", "CHANGE"],
            "answer": "ALTER"
        },
        {
            "question": "Which JOIN returns matching records only?",
            "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"],
            "answer": "INNER JOIN"
        },
        {
            "question": "Which function counts rows?",
            "options": ["COUNT()", "SUM()", "AVG()", "TOTAL()"],
            "answer": "COUNT()"
        },
        {
            "question": "Which SQL operator searches a pattern?",
            "options": ["LIKE", "IN", "BETWEEN", "ANY"],
            "answer": "LIKE"
        }
    ],

    "Hard": [
    {
        "question": "Which normal form removes transitive dependency?",
        "options": ["1NF", "2NF", "3NF", "BCNF"],
        "answer": "3NF"
    },
    {
        "question": "Which SQL function returns the highest value?",
        "options": ["MAX()", "HIGH()", "TOP()", "UPPER()"],
        "answer": "MAX()"
    },
    {
        "question": "Which SQL function returns the lowest value?",
        "options": ["LOW()", "MIN()", "BOTTOM()", "SMALL()"],
        "answer": "MIN()"
    },
    {
        "question": "Which SQL function calculates the average?",
        "options": ["AVERAGE()", "AVG()", "MEAN()", "TOTAL()"],
        "answer": "AVG()"
    },
    {
        "question": "Which SQL command permanently removes a table and its data?",
        "options": ["DELETE", "DROP", "TRUNCATE", "REMOVE"],
        "answer": "DROP"
    },
    {
        "question": "Which SQL command removes all rows but keeps the table?",
        "options": ["DELETE", "TRUNCATE", "DROP", "REMOVE"],
        "answer": "TRUNCATE"
    },
    {
        "question": "Which key uniquely identifies each record in a table?",
        "options": ["Primary Key", "Foreign Key", "Composite Key", "Candidate Key"],
        "answer": "Primary Key"
    },
    {
        "question": "Which transaction property ensures all operations are completed or none?",
        "options": ["Consistency", "Atomicity", "Isolation", "Durability"],
        "answer": "Atomicity"
    },
    {
        "question": "ACID stands for?",
        "options": [
            "Atomicity Consistency Isolation Durability",
            "Access Control Integration Data",
            "Automatic Connection Internal Database",
            "Applied Computing Integrated Data"
        ],
        "answer": "Atomicity Consistency Isolation Durability"
    },
    {
        "question": "Which SQL clause groups rows with the same values?",
        "options": ["GROUP BY", "ORDER BY", "WHERE", "HAVING"],
        "answer": "GROUP BY"
    }
],

},
"Operating System": {

    "Easy": [
        {
            "question": "What is an Operating System?",
            "options": ["System Software", "Application Software", "Compiler", "Database"],
            "answer": "System Software"
        },
        {
            "question": "Which OS is open source?",
            "options": ["Linux", "Windows", "macOS", "DOS"],
            "answer": "Linux"
        },
        {
            "question": "Which OS is developed by Microsoft?",
            "options": ["Linux", "Windows", "Ubuntu", "Android"],
            "answer": "Windows"
        },
        {
            "question": "Which of these is not an Operating System?",
            "options": ["Python", "Linux", "Windows", "Android"],
            "answer": "Python"
        },
        {
            "question": "Which key opens the Start Menu in Windows?",
            "options": ["Ctrl", "Alt", "Windows", "Shift"],
            "answer": "Windows"
        },
        {
            "question": "The brain of the computer is?",
            "options": ["CPU", "RAM", "ROM", "Hard Disk"],
            "answer": "CPU"
        },
        {
            "question": "RAM stands for?",
            "options": ["Random Access Memory", "Read Access Memory", "Random Allocate Memory", "Read Allocate Memory"],
            "answer": "Random Access Memory"
        },
        {
            "question": "ROM stands for?",
            "options": ["Read Only Memory", "Random Only Memory", "Read Open Memory", "Run Only Memory"],
            "answer": "Read Only Memory"
        },
        {
            "question": "Which memory is temporary?",
            "options": ["RAM", "ROM", "Hard Disk", "SSD"],
            "answer": "RAM"
        },
        {
            "question": "Which memory is permanent?",
            "options": ["ROM", "RAM", "Cache", "Registers"],
            "answer": "ROM"
        }
    ],

    "Medium": [
        {
            "question": "Which scheduling algorithm follows First Come First Serve?",
            "options": ["FCFS", "SJF", "Round Robin", "Priority"],
            "answer": "FCFS"
        },
        {
            "question": "Which scheduling algorithm gives minimum average waiting time?",
            "options": ["SJF", "FCFS", "Round Robin", "FIFO"],
            "answer": "SJF"
        },
        {
            "question": "Round Robin scheduling mainly uses?",
            "options": ["Time Quantum", "Priority", "Shortest Job", "FIFO"],
            "answer": "Time Quantum"
        },
        {
            "question": "A process in execution is called?",
            "options": ["Running Process", "Thread", "Program", "File"],
            "answer": "Running Process"
        },
        {
            "question": "Which memory management technique divides memory into pages?",
            "options": ["Paging", "Segmentation", "Swapping", "Partitioning"],
            "answer": "Paging"
        },
        {
            "question": "Deadlock occurs when?",
            "options": ["Processes wait forever", "CPU is idle", "RAM is full", "Disk is empty"],
            "answer": "Processes wait forever"
        },
        {
            "question": "Which command lists files in Linux?",
            "options": ["ls", "dir", "list", "show"],
            "answer": "ls"
        },
        {
            "question": "Which command changes directory in Linux?",
            "options": ["cd", "pwd", "ls", "mkdir"],
            "answer": "cd"
        },
        {
            "question": "Which command shows current directory?",
            "options": ["pwd", "ls", "cd", "dir"],
            "answer": "pwd"
        },
        {
            "question": "Which command creates a directory?",
            "options": ["mkdir", "rmdir", "touch", "cd"],
            "answer": "mkdir"
        }
    ],

    "Hard": [
    {
        "question": "Which scheduling algorithm uses a fixed time slice?",
        "options": ["Round Robin", "FCFS", "SJF", "Priority"],
        "answer": "Round Robin"
    },
    {
        "question": "Which scheduling algorithm is non-preemptive?",
        "options": ["FCFS", "Round Robin", "SRTF", "Priority (Preemptive)"],
        "answer": "FCFS"
    },
    {
        "question": "Which page replacement algorithm replaces the oldest page?",
        "options": ["FIFO", "LRU", "Optimal", "LFU"],
        "answer": "FIFO"
    },
    {
        "question": "Which page replacement algorithm gives the best performance?",
        "options": ["Optimal", "FIFO", "LRU", "Random"],
        "answer": "Optimal"
    },
    {
        "question": "Deadlock can be prevented by eliminating which condition?",
        "options": ["Circular Wait", "Compilation", "Scheduling", "Swapping"],
        "answer": "Circular Wait"
    },
    {
        "question": "Which memory is fastest?",
        "options": ["Cache Memory", "RAM", "Hard Disk", "SSD"],
        "answer": "Cache Memory"
    },
    {
        "question": "Which Linux command removes a directory?",
        "options": ["rmdir", "rmfile", "delete", "erase"],
        "answer": "rmdir"
    },
    {
        "question": "Which Linux command creates an empty file?",
        "options": ["touch", "create", "new", "file"],
        "answer": "touch"
    },
    {
        "question": "Which component manages all processes in an operating system?",
        "options": ["Kernel", "Compiler", "Assembler", "Interpreter"],
        "answer": "Kernel"
    },
    {
        "question": "Which of the following is not a process state?",
        "options": ["Running", "Waiting", "Ready", "Compiled"],
        "answer": "Compiled"
    }
]

},
"Computer Networks": {

    "Easy": [
        {
            "question": "What does LAN stand for?",
            "options": ["Local Area Network", "Large Area Network", "Line Area Network", "Long Area Network"],
            "answer": "Local Area Network"
        },
        {
            "question": "What does WAN stand for?",
            "options": ["Wide Area Network", "Wireless Area Network", "World Area Network", "Web Area Network"],
            "answer": "Wide Area Network"
        },
        {
            "question": "Which device connects multiple computers in a LAN?",
            "options": ["Switch", "Printer", "Monitor", "Keyboard"],
            "answer": "Switch"
        },
        {
            "question": "Which protocol is used to browse websites?",
            "options": ["HTTP", "FTP", "SMTP", "POP3"],
            "answer": "HTTP"
        },
        {
            "question": "Which device connects different networks?",
            "options": ["Router", "Hub", "Switch", "Repeater"],
            "answer": "Router"
        },
        {
            "question": "IP stands for?",
            "options": ["Internet Protocol", "Internal Process", "Input Protocol", "Internet Process"],
            "answer": "Internet Protocol"
        },
        {
            "question": "Which cable is commonly used in LAN?",
            "options": ["UTP", "Coaxial", "Fiber", "All of these"],
            "answer": "UTP"
        },
        {
            "question": "Which topology connects all devices to a central hub?",
            "options": ["Star", "Ring", "Bus", "Mesh"],
            "answer": "Star"
        },
        {
            "question": "Which network covers a city?",
            "options": ["MAN", "LAN", "PAN", "CAN"],
            "answer": "MAN"
        },
        {
            "question": "Which layer is responsible for routing in the OSI model?",
            "options": ["Network Layer", "Physical Layer", "Transport Layer", "Session Layer"],
            "answer": "Network Layer"
        }
    ],

    "Medium": [
        {
            "question": "How many layers are there in the OSI model?",
            "options": ["7", "5", "6", "4"],
            "answer": "7"
        },
        {
            "question": "How many layers are there in the TCP/IP model?",
            "options": ["4", "5", "6", "7"],
            "answer": "4"
        },
        {
            "question": "Which protocol transfers files?",
            "options": ["FTP", "HTTP", "SMTP", "POP3"],
            "answer": "FTP"
        },
        {
            "question": "SMTP is used for?",
            "options": ["Sending Emails", "Receiving Emails", "Browsing", "File Transfer"],
            "answer": "Sending Emails"
        },
        {
            "question": "POP3 is used for?",
            "options": ["Receiving Emails", "Sending Emails", "Browsing", "Routing"],
            "answer": "Receiving Emails"
        },
        {
            "question": "DNS converts?",
            "options": ["Domain Name to IP Address", "IP to MAC", "MAC to IP", "URL to Email"],
            "answer": "Domain Name to IP Address"
        },
        {
            "question": "Which topology has no central device?",
            "options": ["Bus", "Star", "Tree", "Mesh"],
            "answer": "Bus"
        },
        {
            "question": "Which device forwards packets between networks?",
            "options": ["Router", "Switch", "Hub", "Bridge"],
            "answer": "Router"
        },
        {
            "question": "Which protocol provides secure web browsing?",
            "options": ["HTTPS", "HTTP", "FTP", "SMTP"],
            "answer": "HTTPS"
        },
        {
            "question": "Which address is unique for every network interface?",
            "options": ["MAC Address", "IP Address", "Port Number", "DNS"],
            "answer": "MAC Address"
        }
    ],

    "Hard": [
    {
        "question": "Which protocol is connection-oriented?",
        "options": ["TCP", "UDP", "IP", "ICMP"],
        "answer": "TCP"
    },
    {
        "question": "Which protocol is connectionless?",
        "options": ["UDP", "TCP", "HTTP", "FTP"],
        "answer": "UDP"
    },
    {
        "question": "Which OSI layer is responsible for error detection and flow control?",
        "options": ["Data Link Layer", "Network Layer", "Transport Layer", "Application Layer"],
        "answer": "Data Link Layer"
    },
    {
        "question": "Which protocol is used to automatically assign IP addresses?",
        "options": ["DHCP", "DNS", "FTP", "SMTP"],
        "answer": "DHCP"
    },
    {
        "question": "Which command is used to check network connectivity?",
        "options": ["ping", "copy", "mkdir", "move"],
        "answer": "ping"
    },
    {
        "question": "Which device works at the Data Link Layer?",
        "options": ["Switch", "Router", "Hub", "Gateway"],
        "answer": "Switch"
    },
    {
        "question": "Which layer of the OSI model is responsible for encryption and decryption?",
        "options": ["Presentation Layer", "Session Layer", "Application Layer", "Network Layer"],
        "answer": "Presentation Layer"
    },
    {
        "question": "What is the default port number of HTTP?",
        "options": ["80", "21", "25", "443"],
        "answer": "80"
    },
    {
        "question": "What is the default port number of HTTPS?",
        "options": ["443", "80", "20", "110"],
        "answer": "443"
    },
    {
        "question": "Which topology provides the highest reliability?",
        "options": ["Mesh", "Bus", "Ring", "Star"],
        "answer": "Mesh"
    }
]

},
"Software Engineering": {

    "Easy": [
        {
            "question": "What does SDLC stand for?",
            "options": ["Software Development Life Cycle", "System Development Life Cycle", "Software Design Life Cycle", "System Design Life Cycle"],
            "answer": "Software Development Life Cycle"
        },
        {
            "question": "Which is the first phase of SDLC?",
            "options": ["Planning", "Testing", "Design", "Maintenance"],
            "answer": "Planning"
        },
        {
            "question": "Which model follows a sequential approach?",
            "options": ["Waterfall", "Agile", "Spiral", "RAD"],
            "answer": "Waterfall"
        },
        {
            "question": "Which document contains software requirements?",
            "options": ["SRS", "UML", "DFD", "ER Diagram"],
            "answer": "SRS"
        },
        {
            "question": "What does UML stand for?",
            "options": ["Unified Modeling Language", "Universal Modeling Language", "Unified Machine Language", "Universal Machine Language"],
            "answer": "Unified Modeling Language"
        },
        {
            "question": "Which testing is done by developers?",
            "options": ["Unit Testing", "Acceptance Testing", "System Testing", "Beta Testing"],
            "answer": "Unit Testing"
        },
        {
            "question": "Which testing is performed by end users?",
            "options": ["Acceptance Testing", "Unit Testing", "Integration Testing", "Regression Testing"],
            "answer": "Acceptance Testing"
        },
        {
            "question": "A software bug is a?",
            "options": ["Error", "Feature", "Requirement", "Module"],
            "answer": "Error"
        },
        {
            "question": "Which diagram shows system interactions?",
            "options": ["Use Case Diagram", "Pie Chart", "Bar Chart", "Flow Chart"],
            "answer": "Use Case Diagram"
        },
        {
            "question": "Which phase comes after coding?",
            "options": ["Testing", "Planning", "Analysis", "Design"],
            "answer": "Testing"
        }
    ],

    "Medium": [
        {
            "question": "Agile development is based on?",
            "options": ["Iterations", "Sequential Phases", "Single Delivery", "No Planning"],
            "answer": "Iterations"
        },
        {
            "question": "Which model is suitable for changing requirements?",
            "options": ["Agile", "Waterfall", "V-Model", "Prototype"],
            "answer": "Agile"
        },
        {
            "question": "Which UML diagram shows object interactions over time?",
            "options": ["Sequence Diagram", "Class Diagram", "Activity Diagram", "State Diagram"],
            "answer": "Sequence Diagram"
        },
        {
            "question": "Which UML diagram represents classes and relationships?",
            "options": ["Class Diagram", "Use Case Diagram", "Activity Diagram", "Component Diagram"],
            "answer": "Class Diagram"
        },
        {
            "question": "Which testing combines different modules?",
            "options": ["Integration Testing", "Unit Testing", "Alpha Testing", "Beta Testing"],
            "answer": "Integration Testing"
        },
        {
            "question": "Regression testing ensures?",
            "options": ["Old features still work", "New features are added", "Database is optimized", "UI is redesigned"],
            "answer": "Old features still work"
        },
        {
            "question": "What is the purpose of maintenance?",
            "options": ["Fix and improve software", "Write code", "Gather requirements", "Design database"],
            "answer": "Fix and improve software"
        },
        {
            "question": "Which model uses repeated risk analysis?",
            "options": ["Spiral Model", "Waterfall", "RAD", "V-Model"],
            "answer": "Spiral Model"
        },
        {
            "question": "Black-box testing focuses on?",
            "options": ["Inputs and Outputs", "Source Code", "Database", "Algorithm"],
            "answer": "Inputs and Outputs"
        },
        {
            "question": "White-box testing focuses on?",
            "options": ["Internal Code", "User Interface", "Database", "Requirements"],
            "answer": "Internal Code"
        }
    ],

    "Hard": [
    {
        "question": "Which SDLC model is best suited for high-risk projects?",
        "options": ["Spiral Model", "Waterfall Model", "RAD Model", "Prototype Model"],
        "answer": "Spiral Model"
    },
    {
        "question": "Which testing is performed after code modifications?",
        "options": ["Regression Testing", "Unit Testing", "Acceptance Testing", "Integration Testing"],
        "answer": "Regression Testing"
    },
    {
        "question": "Which document describes functional and non-functional requirements?",
        "options": ["SRS", "UML", "DFD", "ER Diagram"],
        "answer": "SRS"
    },
    {
        "question": "Cyclomatic complexity is used to measure?",
        "options": ["Code Complexity", "Database Size", "Memory Usage", "Network Speed"],
        "answer": "Code Complexity"
    },
    {
        "question": "Which testing verifies the complete system?",
        "options": ["System Testing", "Unit Testing", "Alpha Testing", "Smoke Testing"],
        "answer": "System Testing"
    },
    {
        "question": "Which UML diagram represents workflow?",
        "options": ["Activity Diagram", "Class Diagram", "Use Case Diagram", "Component Diagram"],
        "answer": "Activity Diagram"
    },
    {
        "question": "What is the main purpose of version control?",
        "options": ["Track Code Changes", "Compile Programs", "Design UI", "Create Database"],
        "answer": "Track Code Changes"
    },
    {
        "question": "Which software quality attribute refers to ease of modification?",
        "options": ["Maintainability", "Reliability", "Efficiency", "Portability"],
        "answer": "Maintainability"
    },
    {
        "question": "Which testing checks whether the software meets customer requirements?",
        "options": ["Acceptance Testing", "Unit Testing", "Integration Testing", "Stress Testing"],
        "answer": "Acceptance Testing"
    },
    {
        "question": "Which model delivers software in small increments?",
        "options": ["Incremental Model", "Waterfall Model", "V-Model", "Big Bang Model"],
        "answer": "Incremental Model"
    }
]

},
"Web Technology": {

    "Easy": [
        {
            "question": "HTML stands for?",
            "options": ["Hyper Text Markup Language", "High Text Markup Language", "Hyper Tool Markup Language", "Hyper Transfer Markup Language"],
            "answer": "Hyper Text Markup Language"
        },
        {
            "question": "CSS stands for?",
            "options": ["Cascading Style Sheets", "Creative Style Sheets", "Computer Style Sheets", "Colorful Style Sheets"],
            "answer": "Cascading Style Sheets"
        },
        {
            "question": "Which tag creates a hyperlink?",
            "options": ["<a>", "<link>", "<href>", "<url>"],
            "answer": "<a>"
        },
        {
            "question": "Which HTML tag inserts an image?",
            "options": ["<img>", "<image>", "<picture>", "<src>"],
            "answer": "<img>"
        },
        {
            "question": "Which HTML tag creates a paragraph?",
            "options": ["<p>", "<para>", "<paragraph>", "<text>"],
            "answer": "<p>"
        },
        {
            "question": "Which HTML tag creates the largest heading?",
            "options": ["<h1>", "<h6>", "<head>", "<title>"],
            "answer": "<h1>"
        },
        {
            "question": "Which CSS property changes text color?",
            "options": ["color", "background", "font-color", "text-style"],
            "answer": "color"
        },
        {
            "question": "Which CSS property changes background color?",
            "options": ["background-color", "bgcolor", "color", "background"],
            "answer": "background-color"
        },
        {
            "question": "Which language is used for web page styling?",
            "options": ["CSS", "HTML", "Python", "Java"],
            "answer": "CSS"
        },
        {
            "question": "Which language adds interactivity to web pages?",
            "options": ["JavaScript", "HTML", "CSS", "SQL"],
            "answer": "JavaScript"
        }
    ],

    "Medium": [
        {
            "question": "Which HTML tag creates a table?",
            "options": ["<table>", "<tr>", "<td>", "<tab>"],
            "answer": "<table>"
        },
        {
            "question": "Which tag creates a table row?",
            "options": ["<tr>", "<td>", "<th>", "<table>"],
            "answer": "<tr>"
        },
        {
            "question": "Which tag creates a table cell?",
            "options": ["<td>", "<tr>", "<th>", "<cell>"],
            "answer": "<td>"
        },
        {
            "question": "Which HTML tag is used for forms?",
            "options": ["<form>", "<input>", "<button>", "<label>"],
            "answer": "<form>"
        },
        {
            "question": "Which input type hides typed characters?",
            "options": ["password", "text", "email", "hidden"],
            "answer": "password"
        },
        {
            "question": "Which CSS property changes font size?",
            "options": ["font-size", "text-size", "size", "font-style"],
            "answer": "font-size"
        },
        {
            "question": "Which CSS property aligns text?",
            "options": ["text-align", "align", "font-align", "position"],
            "answer": "text-align"
        },
        {
            "question": "Which JavaScript keyword declares a variable?",
            "options": ["let", "define", "int", "varies"],
            "answer": "let"
        },
        {
            "question": "Which JavaScript function displays a popup message?",
            "options": ["alert()", "print()", "display()", "show()"],
            "answer": "alert()"
        },
        {
            "question": "Which symbol is used for single-line comments in JavaScript?",
            "options": ["//", "#", "/* */", "--"],
            "answer": "//"
        }
    ],

    "Hard": [
    {
        "question": "Which HTML5 element is used for navigation links?",
        "options": ["<nav>", "<menu>", "<navigate>", "<section>"],
        "answer": "<nav>"
    },
    {
        "question": "Which CSS property makes an element a flex container?",
        "options": ["display: flex", "position: flex", "flex: display", "layout: flex"],
        "answer": "display: flex"
    },
    {
        "question": "Which CSS property controls the stacking order of elements?",
        "options": ["z-index", "index", "position", "layer"],
        "answer": "z-index"
    },
    {
        "question": "Which JavaScript event occurs when a button is clicked?",
        "options": ["onclick", "onchange", "onload", "onmouseover"],
        "answer": "onclick"
    },
    {
        "question": "Which JavaScript method selects an element by its ID?",
        "options": [
            "document.getElementById()",
            "document.querySelectorAll()",
            "document.getElementsByClassName()",
            "document.getElementsByTagName()"
        ],
        "answer": "document.getElementById()"
    },
    {
        "question": "Which HTTP method is commonly used to submit form data?",
        "options": ["POST", "GET", "PUT", "DELETE"],
        "answer": "POST"
    },
    {
        "question": "Which CSS property adds space inside an element's border?",
        "options": ["padding", "margin", "spacing", "border-spacing"],
        "answer": "padding"
    },
    {
        "question": "Which CSS property adds space outside an element's border?",
        "options": ["margin", "padding", "spacing", "outline"],
        "answer": "margin"
    },
    {
        "question": "Which JavaScript loop executes while a condition is true?",
        "options": ["while", "for", "foreach", "repeat"],
        "answer": "while"
    },
    {
        "question": "Which HTML tag is used to include JavaScript code?",
        "options": ["<script>", "<javascript>", "<js>", "<code>"],
        "answer": "<script>"
    }
]

},
"Placement Preparation": {

    "Aptitude": {
    "Easy": [
        {
            "question": "The cost price of 10 articles is equal to the selling price of 9 articles. Find the overall profit percentage.",
            "options": ["10%", "11.11%", "12.5%", "15%"],
            "answer": "11.11%",
            "explanation": "Let CP of 1 article be ₹1. CP of 10 articles = ₹10. SP of 9 articles = ₹10. CP of 9 articles = ₹9. Profit = ₹10 - ₹9 = ₹1. Profit percentage = (1/9) × 100 = 11.11%.",
            "company": "Wipro WILP",
            "year": 2023
        },

        {
            "question": "A product's price increases from ₹500 to ₹575. What is the percentage increase?",
            "options": ["10%", "12%", "15%", "20%"],
            "answer": "15%",
            "explanation": "Increase in price = ₹575 - ₹500 = ₹75. Percentage increase = (75/500) × 100 = 15%.",
            "company": "Wipro WILP",
            "year": 2025
        },

        {
            "question": "The average score of a cricketer in 10 matches is 45 runs. If he scores 89 runs in the 11th match, find his new average.",
            "options": ["47", "48", "49", "50"],
            "answer": "49",
            "explanation": "Total runs in 10 matches = 10 × 45 = 450. After 11th match total = 450 + 89 = 539. New average = 539 ÷ 11 = 49 runs.",
            "company": "TCS Smart Hiring",
            "year": 2023
        },

        {
            "question": "A certain sum doubles itself in 8 years under simple interest. Find the rate of interest per annum.",
            "options": ["10%", "12.5%", "15%", "20%"],
            "answer": "12.5%",
            "explanation": "When money doubles, Simple Interest = Principal. Using SI = (P×R×T)/100, P = (P×R×8)/100. Therefore R = 100/8 = 12.5%.",
            "company": "Wipro WILP",
            "year": 2024
        },

        {
            "question": "A train 120 meters long passes an electric pole in 6 seconds. What is its speed?",
            "options": ["54 km/h", "60 km/h", "72 km/h", "80 km/h"],
            "answer": "72 km/h",
            "explanation": "Speed = Distance/Time = 120/6 = 20 m/s. Convert into km/h: 20 × 18/5 = 72 km/h.",
            "company": "TCS Smart Hiring",
            "year": 2025
        },

        {
            "question": "In how many distinct ways can the letters of the word LEMON be arranged?",
            "options": ["60", "100", "120", "150"],
            "answer": "120",
            "explanation": "LEMON contains 5 different letters. Number of arrangements = 5! = 5×4×3×2×1 = 120.",
            "company": "TCS NQT",
            "year": 2024
        },

        {
            "question": "Two dice are thrown simultaneously. What is the probability of getting a total sum of 7?",
            "options": ["1/3", "1/4", "1/6", "1/12"],
            "answer": "1/6",
            "explanation": "Total possible outcomes = 6×6 = 36. Favorable outcomes for sum 7 are (1,6),(2,5),(3,4),(4,3),(5,2),(6,1) = 6. Probability = 6/36 = 1/6.",
            "company": "Infosys Operations",
            "year": 2025
        },

        {
            "question": "A motorist travels at 40 km/h and returns at 60 km/h. What is the average speed?",
            "options": ["45 km/h", "48 km/h", "50 km/h", "52 km/h"],
            "answer": "48 km/h",
            "explanation": "For equal distances, average speed = (2xy)/(x+y). = (2×40×60)/(40+60) = 4800/100 = 48 km/h.",
            "company": "Wipro WILP",
            "year": 2023
        },

        {
            "question": "Find the largest four-digit number exactly divisible by 15, 25 and 30.",
            "options": ["9800", "9850", "9900", "9950"],
            "answer": "9900",
            "explanation": "LCM of 15, 25 and 30 = 150. Largest 4-digit number is 9999. 9999 divided by 150 leaves remainder 99. Required number = 9999 - 99 = 9900.",
            "company": "Infosys Placements",
            "year": 2023
        },

        {
            "question": "Evaluate: 45 - [38 - {60 ÷ 3 - (6 - 9 ÷ 3)}].",
            "options": ["20", "22", "24", "26"],
            "answer": "24",
            "explanation": "Solve brackets first: 9÷3=3, so (6-3)=3. 60÷3=20. Curly bracket = 20-3=17. Square bracket = 38-17=21. Final = 45-21=24.",
            "company": "Wipro WILP",
            "year": 2024
        }
    ],
    "Medium": [
        {
            "question": "If 12 men can complete a work in 10 days, and 20 women can complete the same work in 12 days, how many days will 8 men and 4 women take together?",
            "options": ["10 days", "12 days", "14 days", "16 days"],
            "answer": "12 days",
            "explanation": "12 men complete work in 10 days = 120 man-days. 20 women complete work in 12 days = 240 woman-days. Therefore, 1 man = 2 women. 8 men = 16 women. Total efficiency = 16 + 4 = 20 women. Total work = 240 units. Time = 240 ÷ 20 = 12 days.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },

        {
            "question": "At what rate of compound interest will ₹34,000 become ₹37,485 in exactly 2 years?",
            "options": ["4%", "5%", "6%", "7%"],
            "answer": "5%",
            "explanation": "Using A = P(1 + R/100)². 37485 = 34000(1 + R/100)². 37485/34000 = 1.1025. Square root of 1.1025 = 1.05. Therefore R = 5%.",
            "company": "TCS Smart Hiring",
            "year": 2022
        },

        {
            "question": "A bag contains ₹1, 50p and 25p coins in the ratio 5:6:8. If total value is ₹210, find the number of 50p coins.",
            "options": ["100", "120", "126", "140"],
            "answer": "126",
            "explanation": "Value ratio = 5×1 : 6×0.5 : 8×0.25 = 5:3:2. Total parts = 10. Value of 50p coins = (3/10)×210 = ₹63. Number of 50p coins = 63 ÷ 0.5 = 126.",
            "company": "Infosys Placements",
            "year": 2025
        },

        {
            "question": "In what ratio must tea costing ₹60/kg be mixed with tea costing ₹65/kg to obtain a mixture worth ₹62/kg?",
            "options": ["2:3", "3:2", "3:4", "4:3"],
            "answer": "3:2",
            "explanation": "Using alligation: Cheaper : Dearer = (65-62):(62-60) = 3:2. Therefore, tea costing ₹60 and ₹65 should be mixed in the ratio 3:2.",
            "company": "Wipro WILP",
            "year": 2022
        },

        {
            "question": "Pipe A fills a tank in 6 hours and Pipe B empties it in 12 hours. If both are opened together, how long will it take to fill the tank?",
            "options": ["6 hours", "8 hours", "10 hours", "12 hours"],
            "answer": "12 hours",
            "explanation": "A fills 1/6 tank per hour. B empties 1/12 tank per hour. Net filling rate = 1/6 - 1/12 = 1/12. Time required = 12 hours.",
            "company": "TCS Smart Hiring",
            "year": 2023
        },

        {
            "question": "The ratio of father's age to son's age is 7:3. Their total age is 60 years. Find the father's age.",
            "options": ["40 years", "42 years", "45 years", "48 years"],
            "answer": "42 years",
            "explanation": "Let father and son ages be 7x and 3x. 7x+3x=60. 10x=60, x=6. Father's age = 7×6 = 42 years.",
            "company": "Infosys Placements",
            "year": 2024
        },

        {
            "question": "The HCF of two numbers is 11 and their LCM is 693. If one number is 77, find the other.",
            "options": ["88", "99", "108", "121"],
            "answer": "99",
            "explanation": "Product of two numbers = HCF × LCM. 77 × Other number = 11 × 693. Other number = (11×693)/77 = 99.",
            "company": "TCS Smart Hiring",
            "year": 2022
        },

        {
            "question": "If the side of a square is increased by 20%, what is the percentage increase in area?",
            "options": ["20%", "40%", "44%", "48%"],
            "answer": "44%",
            "explanation": "New side = 120% of original. Area depends on side². Increase = (1.2² - 1)×100 = (1.44-1)×100 = 44%.",
            "company": "Wipro WILP",
            "year": 2025
        },

        {
            "question": "If 15 men build a 100-meter wall in 6 days, how many days will 20 men take?",
            "options": ["3.5", "4", "4.5", "5"],
            "answer": "4.5",
            "explanation": "Work is constant, so Men × Days = constant. 15×6 = 20×D. D = 90/20 = 4.5 days.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },

        {
            "question": "A and B invest in a business in the ratio 3:2. If 5% profit goes to charity and A receives ₹855, find total profit.",
            "options": ["₹1200", "₹1500", "₹1800", "₹2000"],
            "answer": "₹1500",
            "explanation": "Remaining profit after charity = 95% of total profit. A's share = 3/5 of remaining profit. (3/5)×(95/100)×Total Profit = 855. Total Profit = ₹1500.",
            "company": "Infosys Operations",
            "year": 2023
        }
    ],
    "Hard": [
        {
            "question": "By selling an item for ₹270, a shopkeeper incurs a loss of 10%. At what price should he sell it to gain 10%?",
            "options": ["₹300", "₹320", "₹330", "₹350"],
            "answer": "₹330",
            "explanation": "Selling at ₹270 is a 10% loss, so Cost Price = 270 ÷ 0.9 = ₹300. For a 10% gain, Selling Price = 300 × 1.10 = ₹330.",
            "company": "TCS NQT",
            "year": 2025
        },
        {
            "question": "Find the present worth of ₹1320 due 2 years hence at 5% simple interest.",
            "options": ["₹1100", "₹1150", "₹1200", "₹1250"],
            "answer": "₹1200",
            "explanation": "Present Value = Future Value ÷ (1 + RT/100) = 1320 ÷ (1 + 5×2/100) = 1320 ÷ 1.10 = ₹1200.",
            "company": "TCS Smart Hiring",
            "year": 2022
        },
        {
            "question": "A man spends 40% of salary on food and 20% on rent and saves ₹12,000. Find his salary.",
            "options": ["₹20,000", "₹25,000", "₹30,000", "₹35,000"],
            "answer": "₹30,000",
            "explanation": "Food + Rent = 60% of salary. Savings = 40% = ₹12,000. Salary = 12,000 ÷ 0.40 = ₹30,000.",
            "company": "Infosys Operations",
            "year": 2023
        },
        {
            "question": "Two trains of lengths 100 m and 120 m travel in opposite directions at 54 km/h and 36 km/h. How long do they take to cross each other?",
            "options": ["7.8 sec", "8.8 sec", "9.8 sec", "10.8 sec"],
            "answer": "8.8 sec",
            "explanation": "Total distance = 100 + 120 = 220 m. Relative speed = 54 + 36 = 90 km/h = 25 m/s. Time = 220 ÷ 25 = 8.8 seconds.",
            "company": "Wipro WILP",
            "year": 2024
        },
        {
            "question": "A is twice as efficient as B. Together they complete a work in 14 days. How many days will A alone take?",
            "options": ["18", "21", "24", "28"],
            "answer": "21",
            "explanation": "Efficiency ratio A:B = 2:1. Together = 3 units complete work in 14 days. A alone takes (3 ÷ 2) × 14 = 21 days.",
            "company": "Wipro WILP",
            "year": 2025
        },
        {
            "question": "A clock gains 5 minutes every hour. If set right at 8:00 AM, what time will it show at 6:00 PM?",
            "options": ["6:40 PM", "6:50 PM", "7:00 PM", "7:10 PM"],
            "answer": "6:50 PM",
            "explanation": "From 8 AM to 6 PM is 10 hours. Clock gains 5 minutes every hour, so total gain = 10 × 5 = 50 minutes. It will show 6:50 PM.",
            "company": "Infosys Placements",
            "year": 2025
        },
        {
            "question": "If January 1, 2024 was Monday, what day was January 1, 2025?",
            "options": ["Monday", "Tuesday", "Wednesday", "Thursday"],
            "answer": "Wednesday",
            "explanation": "2024 is a leap year with 366 days. 366 mod 7 = 2, so the day advances by two days. Monday + 2 = Wednesday.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },
        {
            "question": "Find the income from 100 shares of ₹20 each at ₹4 premium when dividend is 8%.",
            "options": ["₹120", "₹140", "₹160", "₹180"],
            "answer": "₹160",
            "explanation": "Dividend is calculated on face value only. Dividend per share = 8% of ₹20 = ₹1.60. Income = 100 × 1.60 = ₹160.",
            "company": "TCS NQT",
            "year": 2023
        },
        {
            "question": "If A:B = 2:3 and B:C = 4:5, find A:B:C.",
            "options": ["6:9:10", "8:12:15", "8:10:15", "4:6:5"],
            "answer": "8:12:15",
            "explanation": "Make B common. LCM of 3 and 4 is 12. Therefore A:B = 8:12 and B:C = 12:15. Hence A:B:C = 8:12:15.",
            "company": "Infosys Operations",
            "year": 2024
        },
        {
            "question": "Two distinct positive integers p and q leave remainder 2 when divided by 9. What is the remainder when the 3-digit number pq5 is divided by 9?",
            "options": ["0", "1", "2", "5"],
            "answer": "0",
            "explanation": "Since p ≡ 2 (mod 9) and q ≡ 2 (mod 9), the digit sum is 2 + 2 + 5 = 9. A number divisible by 9 has remainder 0.",
            "company": "Infosys Operations",
            "year": 2024
        }
        ]


},
"Logical Reasoning": {
    "Easy": [
        {
            "question": "Complete the sequence: 36, 34, 30, 28, 24, ?",
            "options": ["20", "21", "22", "23"],
            "answer": "22",
            "explanation": "The pattern is subtracting alternate numbers: 36-2=34, 34-4=30, 30-2=28, 28-4=24. Next: 24-2=22.",
            "company": "Wipro WILP",
            "year": 2024
        },

        {
            "question": "If APPLE is coded as BQQMF, how is MANGO coded?",
            "options": ["NBOHP", "NBNHP", "MBOHP", "NCOHQ"],
            "answer": "NBOHP",
            "explanation": "Each letter is shifted one position forward. M→N, A→B, N→O, G→H, O→P. Therefore MANGO becomes NBOHP.",
            "company": "TCS Smart Hiring",
            "year": 2023
        },

        {
            "question": "Light : Darkness :: Knowledge : ?",
            "options": ["Wisdom", "Ignorance", "Truth", "Learning"],
            "answer": "Ignorance",
            "explanation": "Light is the opposite of darkness. Similarly, knowledge is the opposite of ignorance.",
            "company": "Infosys Placements",
            "year": 2023
        },

        {
            "question": "Find the odd one out: 27, 64, 125, 144, 216.",
            "options": ["27", "64", "144", "216"],
            "answer": "144",
            "explanation": "27=3³, 64=4³, 125=5³, 216=6³. Only 144 is not a cube number; it is 12².",
            "company": "Wipro WILP",
            "year": 2022
        },

        {
            "question": "If '+' means ×, '-' means ÷, '×' means + and '÷' means -, calculate 20 - 4 + 3 × 2.",
            "options": ["15", "17", "20", "22"],
            "answer": "17",
            "explanation": "Replace symbols: 20 ÷ 4 × 3 + 2. Using BODMAS: 20÷4=5, 5×3=15, 15+2=17.",
            "company": "Infosys Operations",
            "year": 2025
        },

        {
            "question": "Ashok ranks 14th from top and 28th from bottom. Find total students.",
            "options": ["40", "41", "42", "43"],
            "answer": "41",
            "explanation": "Total students = Rank from top + Rank from bottom - 1 = 14 + 28 - 1 = 41.",
            "company": "Wipro WILP",
            "year": 2023
        },

        {
            "question": "Find the missing item: SCD, TEF, UGH, ?, WKL.",
            "options": ["VIJ", "VHI", "VJK", "UIJ"],
            "answer": "VIJ",
            "explanation": "First letters: S,T,U,V,W. Remaining letters follow CD, EF, GH, IJ, KL. Missing term is VIJ.",
            "company": "Infosys Placements",
            "year": 2024
        },

        {
            "question": "Find the next term: A, Z, B, Y, C, X, ?",
            "options": ["D", "W", "E", "V"],
            "answer": "D",
            "explanation": "Two sequences are combined: A,B,C,D and Z,Y,X. After C,X comes D.",
            "company": "TCS Smart Hiring",
            "year": 2023
        },

        {
            "question": "A cube painted on all faces is cut into 27 equal cubes. How many have only one face painted?",
            "options": ["4", "6", "8", "12"],
            "answer": "6",
            "explanation": "27 cubes means 3×3×3 cube. One-face painted cubes are middle cubes of each face: 6(3-2)² = 6.",
            "company": "Wipro WILP",
            "year": 2024
        },

        {
            "question": "If 2 + 3 = 10 and 3 + 4 = 21, then 4 + 5 = ?",
            "options": ["30", "32", "36", "40"],
            "answer": "36",
            "explanation": "Pattern: First number × (First number + Second number). 2×(2+3)=10, 3×(3+4)=21. Therefore 4×(4+5)=36.",
            "company": "Infosys Operations",
            "year": 2024
        }
    ],
    "Medium": [
        {
            "question": "If ROSE is written as TQUG, how is BISCUIT written?",
            "options": ["DKUEWKV", "CJTDVJU", "DKVFWKV", "EJUEXKW"],
            "answer": "DKUEWKV",
            "explanation": "Each letter is shifted forward by two places in the alphabet. B→D, I→K, S→U, C→E, U→W, I→K, T→V. Hence the code is DKUEWKV.",
            "company": "TCS Smart Hiring",
            "year": 2022
        },
        {
            "question": "What is the angle between the hour and minute hands at 3:40?",
            "options": ["120°", "130°", "140°", "150°"],
            "answer": "130°",
            "explanation": "Minute hand at 40 minutes = 40 × 6 = 240°. Hour hand at 3:40 = (3 × 30) + (40 × 0.5) = 110°. Difference = 240° − 110° = 130°.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },
        {
            "question": "A traveler walks 3 km North and 4 km East. Find direct displacement.",
            "options": ["4 km", "5 km", "6 km", "7 km"],
            "answer": "5 km",
            "explanation": "The path forms a right triangle with sides 3 km and 4 km. Using Pythagoras theorem: √(3² + 4²) = √25 = 5 km.",
            "company": "Wipro WILP",
            "year": 2024
        },
        {
            "question": "If GO is coded as 32 using reverse alphabetical values, how is SHE coded?",
            "options": ["47", "49", "51", "53"],
            "answer": "49",
            "explanation": "Using reverse alphabetical values (A=26, B=25, ..., Z=1): S=8, H=19, E=22. Sum = 8 + 19 + 22 = 49.",
            "company": "TCS Smart Hiring",
            "year": 2022
        },
        {
            "question": "Find A in: 2A + 3A = 62.",
            "options": ["4", "5", "6", "7"],
            "answer": "Not Correct (Correct Answer = 12.4)",
            "explanation": "2A + 3A = 5A = 62. Therefore A = 62 ÷ 5 = 12.4. None of the given options are correct. If the intended equation was 2A + 3A = 30, then A = 6.",
            "company": "Infosys Placements",
            "year": 2024
        },
        {
            "question": "Arrange logically: Member, Community, Family, Locality.",
            "options": ["1,3,4,2", "1,4,3,2", "3,1,4,2", "1,2,3,4"],
            "answer": "1,3,4,2",
            "explanation": "A member belongs to a family, families form a locality, and localities together form a community.",
            "company": "TCS NQT",
            "year": 2025
        },
        {
            "question": "If the day before yesterday was Thursday, what day will it be day after tomorrow?",
            "options": ["Sunday", "Monday", "Tuesday", "Wednesday"],
            "answer": "Monday",
            "explanation": "Day before yesterday = Thursday → Yesterday = Friday → Today = Saturday → Tomorrow = Sunday → Day after tomorrow = Monday.",
            "company": "Wipro WILP",
            "year": 2025
        },
        {
            "question": "If A + B means A is brother of B and A - B means A is sister of B, what does M + N - O represent?",
            "options": ["Brother of O", "Sister of O", "Father of O", "Mother of O"],
            "answer": "Brother of O",
            "explanation": "M + N means M is the brother of N. N - O means N is the sister of O. Therefore M is also the brother of O.",
            "company": "TCS NQT",
            "year": 2025
        },
        {
            "question": "Is X an integer? Statement 1: X/3 is an integer. Statement 2: 3X is an integer. Which is sufficient?",
            "options": ["Statement 1 only", "Statement 2 only", "Both", "Neither"],
            "answer": "Statement 1 only",
            "explanation": "If X/3 is an integer, then X must be an integer multiple of 3. But if only 3X is an integer, X could still be a fraction (e.g., X = 1/3). Therefore only Statement 1 is sufficient.",
            "company": "Infosys Operations",
            "year": 2023
        },
        {
            "question": "Identify the relationship: Seconds, Minutes, Hours.",
            "options": ["Three overlapping circles", "Three concentric circles", "Three separate circles", "Two circles"],
            "answer": "Three concentric circles",
            "explanation": "Seconds are part of minutes, and minutes are part of hours. This hierarchical inclusion is best represented using three concentric circles.",
            "company": "Wipro WILP",
            "year": 2022
        }
    ],
    "Hard": [
        {
            "question": "Five friends P, Q, R, S and T sit in a row facing North. T is at the extreme left, Q is second from the right, R is next to Q and S is next to P. Who is immediately right of P?",
            "options": ["Q", "R", "S", "T"],
            "answer": "Q",
            "explanation": "Arrange the seats from left to right. T is at the extreme left (1st position). Q is second from the right (4th position). R sits next to Q, so R occupies the 5th position. The remaining positions are 2 and 3 for P and S. Since S is next to P, P must be in the 3rd position and S in the 2nd position. Therefore, Q is immediately to the right of P.",
            "company": "Infosys Placements",
            "year": 2025
        },
        {
            "question": "All stones are bricks. All bricks are walls. Which conclusion follows?",
            "options": ["All stones are walls", "Some walls are stones", "Both I and II", "Neither"],
            "answer": "Both I and II",
            "explanation": "Since every stone is a brick and every brick is a wall, all stones are definitely walls. Therefore Conclusion I is true. Because stones exist and are walls, some walls are stones. Hence both conclusions follow.",
            "company": "TCS NQT",
            "year": 2024
        },
        {
            "question": "A woman says about a man: 'His mother is the only daughter of my father.' How is the woman related to the man?",
            "options": ["Sister", "Mother", "Aunt", "Daughter"],
            "answer": "Mother",
            "explanation": "The only daughter of the woman's father is the woman herself. Therefore, the man's mother is the woman. Hence, she is the man's mother.",
            "company": "Infosys Operations",
            "year": 2024
        },
        {
            "question": "A man walks 5 km East, turns right for 4 km and then left for 5 km. Which direction is he facing?",
            "options": ["North", "South", "East", "West"],
            "answer": "East",
            "explanation": "He first faces East. Turning right makes him face South. Turning left from South makes him face East again. Therefore, he is finally facing East.",
            "company": "Wipro WILP",
            "year": 2025
        },
        {
            "question": "A lady's husband is the only son of John's mother. How is John related to the lady?",
            "options": ["Brother", "Husband", "Father", "Son"],
            "answer": "Husband",
            "explanation": "John's mother has only one son, who is John himself. The lady's husband is that only son. Therefore, John is the lady's husband.",
            "company": "TCS NQT",
            "year": 2024
        },
        {
            "question": "A, B, C and D sit around a circular table. A is opposite C and B is to the right of A. Who is to the left of C?",
            "options": ["A", "B", "C", "D"],
            "answer": "B",
            "explanation": "Place A anywhere. C sits opposite A. Since B is immediately to the right of A, D occupies the remaining seat. From C's position, the person on the left is B.",
            "company": "Infosys Placements",
            "year": 2023
        },
        {
            "question": "A statement says: 'Please do not use cell phones inside the examination hall.' Which assumptions are implicit?",
            "options": ["I only", "II only", "Both I and II", "Neither"],
            "answer": "Both I and II",
            "explanation": "The instruction assumes that people may carry cell phones into the examination hall and that using them is not permitted. Hence both assumptions are implicit.",
            "company": "TCS Smart Hiring",
            "year": 2025
        },
        {
            "question": "Find the missing value: [3,5,7], [8,1,?] if each row totals 15.",
            "options": ["5", "6", "7", "8"],
            "answer": "6",
            "explanation": "The first row sums to 3 + 5 + 7 = 15. Therefore, the second row must also total 15. So, 8 + 1 + ? = 15 ⇒ ? = 6.",
            "company": "Infosys Operations",
            "year": 2025
        },
        {
            "question": "If GO is coded using reverse alphabetical values, what is the code for SHE?",
            "options": ["47", "48", "49", "50"],
            "answer": "49",
            "explanation": "Reverse alphabetical values are A=26, B=25, ..., Z=1. Therefore, S=8, H=19, and E=22. Their sum is 8 + 19 + 22 = 49.",
            "company": "TCS Smart Hiring",
            "year": 2022
        },
        {
            "question": "Which person is the only son of John's mother in the statement: 'Her husband is the only son of my mother'?",
            "options": ["John", "The lady", "Her father", "Her brother"],
            "answer": "John",
            "explanation": "The statement indicates that the only son of the speaker's mother is John. Therefore, John's mother has only one son, who is John himself.",
            "company": "TCS NQT",
            "year": 2024
        }
        ]

},
"Verbal Ability": {
    "Easy": [
        {
            "question": "Choose the closest meaning of ABANDON.",
            "options": ["Retain", "Forsake", "Adopt", "Cherish"],
            "answer": "Forsake",
            "explanation": "Abandon means to leave something completely or give up. The closest meaning is Forsake.",
            "company": "Wipro WILP",
            "year": 2023
        },

        {
            "question": "What is the antonym of ARTIFICIAL?",
            "options": ["Solid", "Natural", "Factitious", "Synthetic"],
            "answer": "Natural",
            "explanation": "Artificial means man-made or fake. The opposite meaning is Natural.",
            "company": "Infosys Operations",
            "year": 2025
        },

        {
            "question": "What does 'Spill the beans' mean?",
            "options": ["Cook food", "Reveal a secret", "Waste time", "Make noise"],
            "answer": "Reveal a secret",
            "explanation": "'Spill the beans' is an idiom that means to reveal confidential information or tell a secret.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },

        {
            "question": "Choose the synonym of BRAVE.",
            "options": ["Coward", "Courageous", "Weak", "Afraid"],
            "answer": "Courageous",
            "explanation": "Brave means showing courage. Courageous is the synonym of brave.",
            "company": "Wipro WILP",
            "year": 2024
        },

        {
            "question": "Choose the correctly spelled word.",
            "options": ["Enviroment", "Environment", "Envirnment", "Enviornment"],
            "answer": "Environment",
            "explanation": "The correct spelling is Environment.",
            "company": "Infosys Placements",
            "year": 2023
        },

        {
            "question": "Fill in the blank: She is good ___ mathematics.",
            "options": ["in", "on", "at", "for"],
            "answer": "at",
            "explanation": "The correct preposition used with 'good' for skills or subjects is 'at'.",
            "company": "TCS NQT",
            "year": 2024
        },

        {
            "question": "Choose the opposite of EXPAND.",
            "options": ["Increase", "Grow", "Contract", "Extend"],
            "answer": "Contract",
            "explanation": "Expand means to become larger. The opposite is Contract, which means to reduce or become smaller.",
            "company": "Wipro WILP",
            "year": 2023
        },

        {
            "question": "Identify the noun in the sentence: 'The boy plays football.'",
            "options": ["The", "Boy", "Plays", "The"],
            "answer": "Boy",
            "explanation": "A noun is the name of a person, place, animal, or thing. 'Boy' is a noun.",
            "company": "Infosys Operations",
            "year": 2024
        },

        {
            "question": "Choose the correct passive voice: 'They completed the project.'",
            "options": [
                "The project was completed by them.",
                "The project is completed by them.",
                "The project completed them.",
                "The project has completed."
            ],
            "answer": "The project was completed by them.",
            "explanation": "In passive voice, the object becomes the subject. 'The project' receives the action, so 'was completed' is correct.",
            "company": "TCS Smart Hiring",
            "year": 2023
        },

        {
            "question": "Choose the correct meaning of 'Once in a blue moon'.",
            "options": [
                "Very often",
                "Very rarely",
                "Every day",
                "Immediately"
            ],
            "answer": "Very rarely",
            "explanation": "'Once in a blue moon' means something that happens very rarely.",
            "company": "Wipro WILP",
            "year": 2025
        }
    ],
    "Medium": [
        {
            "question": "Choose the synonym of 'METICULOUS'.",
            "options": ["Careless", "Careful", "Lazy", "Rude"],
            "answer": "Careful",
            "explanation": "Meticulous means showing great attention to detail or being very careful and precise.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },
        {
            "question": "Choose the antonym of 'OPTIMISTIC'.",
            "options": ["Hopeful", "Positive", "Pessimistic", "Confident"],
            "answer": "Pessimistic",
            "explanation": "Optimistic means expecting positive outcomes, while pessimistic means expecting negative outcomes.",
            "company": "Infosys Placements",
            "year": 2023
        },
        {
            "question": "Fill in the blank: She ______ to the office before the meeting started.",
            "options": ["go", "went", "had gone", "going"],
            "answer": "had gone",
            "explanation": "The past perfect tense ('had gone') is used because the action happened before another action in the past.",
            "company": "Wipro WILP",
            "year": 2025
        },
        {
            "question": "Identify the correctly spelled word.",
            "options": ["Accomodate", "Acommodate", "Accommodate", "Acomodate"],
            "answer": "Accommodate",
            "explanation": "'Accommodate' is the correct spelling with double 'c' and double 'm'.",
            "company": "TCS NQT",
            "year": 2024
        },
        {
            "question": "Choose the correct passive voice: 'The teacher praised the student.'",
            "options": [
                "The student praised the teacher.",
                "The student was praised by the teacher.",
                "The teacher was praised by the student.",
                "The student is praised by the teacher."
            ],
            "answer": "The student was praised by the teacher.",
            "explanation": "In passive voice, the object becomes the subject and the verb changes to 'was praised'.",
            "company": "Infosys Operations",
            "year": 2024
        },
        {
            "question": "Choose the correct indirect speech: He said, 'I am busy.'",
            "options": [
                "He said that he is busy.",
                "He said that I was busy.",
                "He said that he was busy.",
                "He said he busy."
            ],
            "answer": "He said that he was busy.",
            "explanation": "In reported speech, the present tense changes to the past tense ('am' → 'was').",
            "company": "Wipro WILP",
            "year": 2023
        },
        {
            "question": "Select the word that best completes the sentence: The manager appreciated her ______ approach to problem-solving.",
            "options": ["logic", "logical", "logically", "logician"],
            "answer": "logical",
            "explanation": "An adjective is required to describe the noun 'approach'. 'Logical' is the correct adjective.",
            "company": "TCS Smart Hiring",
            "year": 2025
        },
        {
            "question": "Choose the correct meaning of the idiom 'Hit the nail on the head'.",
            "options": [
                "Miss the target",
                "Say exactly the right thing",
                "Work very hard",
                "Break something"
            ],
            "answer": "Say exactly the right thing",
            "explanation": "The idiom means to describe or identify something exactly correctly.",
            "company": "Infosys Placements",
            "year": 2025
        },
        {
            "question": "Arrange the sentence correctly: 'always / honesty / the best / policy / is'.",
            "options": [
                "Always honesty is the best policy.",
                "Honesty is always the best policy.",
                "The best policy honesty is always.",
                "Honesty always policy is the best."
            ],
            "answer": "Honesty is always the best policy.",
            "explanation": "This is the grammatically correct arrangement with proper subject, verb, and complement.",
            "company": "TCS NQT",
            "year": 2023
        },
        {
            "question": "Choose the grammatically correct sentence.",
            "options": [
                "Neither of the students were present.",
                "Neither of the students was present.",
                "Neither students was present.",
                "Neither the students were present."
            ],
            "answer": "Neither of the students was present.",
            "explanation": "'Neither' is singular, so it takes the singular verb 'was'.",
            "company": "Wipro WILP",
            "year": 2024
        }
        ],
        "Hard": [
        {
            "question": "Choose the word nearest in meaning to 'OBSOLETE'.",
            "options": ["Modern", "Outdated", "Useful", "Ancient"],
            "answer": "Outdated",
            "explanation": "Obsolete means no longer in use or out of date. Therefore, 'Outdated' is the correct synonym.",
            "company": "TCS NQT",
            "year": 2025
        },
        {
            "question": "Choose the antonym of 'BENEVOLENT'.",
            "options": ["Kind", "Generous", "Cruel", "Helpful"],
            "answer": "Cruel",
            "explanation": "Benevolent means kind and well-meaning. Its opposite is 'Cruel'.",
            "company": "Infosys Placements",
            "year": 2024
        },
        {
            "question": "Choose the correct sentence.",
            "options": [
                "No sooner had he reached than it started raining.",
                "No sooner had he reached when it started raining.",
                "No sooner had he reached than it had started raining.",
                "No sooner had he reached than it started raining."
            ],
            "answer": "No sooner had he reached than it started raining.",
            "explanation": "The correct structure is 'No sooner...than...'.",
            "company": "Wipro WILP",
            "year": 2025
        },
        {
            "question": "Fill in the blank: Had she studied harder, she ______ the examination.",
            "options": ["will pass", "would pass", "would have passed", "passed"],
            "answer": "would have passed",
            "explanation": "This is a third conditional sentence referring to an unreal past situation, so 'would have passed' is correct.",
            "company": "TCS Smart Hiring",
            "year": 2024
        },
        {
            "question": "Identify the sentence with the correct use of punctuation.",
            "options": [
                "Let's eat Grandma!",
                "Let's eat, Grandma!",
                "Lets eat, Grandma!",
                "Let's eat Grandma."
            ],
            "answer": "Let's eat, Grandma!",
            "explanation": "The comma separates the person being addressed from the rest of the sentence.",
            "company": "Infosys Operations",
            "year": 2023
        },
        {
            "question": "Choose the correct passive voice: 'People believe that he is honest.'",
            "options": [
                "He is believed to be honest.",
                "He believes to be honest.",
                "He was believed honest.",
                "People are believed him honest."
            ],
            "answer": "He is believed to be honest.",
            "explanation": "The correct passive structure is 'He is believed to be...'.",
            "company": "TCS NQT",
            "year": 2025
        },
        {
            "question": "What does the idiom 'Burn the midnight oil' mean?",
            "options": [
                "Waste electricity",
                "Study or work late into the night",
                "Start a fire",
                "Sleep peacefully"
            ],
            "answer": "Study or work late into the night",
            "explanation": "The idiom refers to working or studying until very late at night.",
            "company": "Infosys Placements",
            "year": 2024
        },
        {
            "question": "Choose the correctly spelled word.",
            "options": [
                "Conscience",
                "Consciense",
                "Conscince",
                "Conshience"
            ],
            "answer": "Conscience",
            "explanation": "'Conscience' is the correct spelling, meaning a person's moral sense of right and wrong.",
            "company": "Wipro WILP",
            "year": 2023
        },
        {
            "question": "Choose the most appropriate word: His explanation was so ______ that everyone understood the concept immediately.",
            "options": ["Ambiguous", "Lucid", "Vague", "Confusing"],
            "answer": "Lucid",
            "explanation": "'Lucid' means clear and easy to understand, making it the correct answer.",
            "company": "TCS Smart Hiring",
            "year": 2025
        },
        {
            "question": "Choose the correct indirect speech: The teacher said, 'Complete your homework before tomorrow.'",
            "options": [
                "The teacher advised the students to complete their homework before the next day.",
                "The teacher said complete your homework before tomorrow.",
                "The teacher asked that complete homework.",
                "The teacher says to complete homework."
            ],
            "answer": "The teacher advised the students to complete their homework before the next day.",
            "explanation": "Imperative sentences are converted to indirect speech using verbs like 'advised', 'told', or 'asked' followed by the infinitive ('to complete').",
            "company": "Infosys Operations",
            "year": 2025
        }
    ]
},
    "Passage":{
        "Easy":[

        {
            "topic": "Main Idea",
            "company": "TCS",
            "year": 2024,
            "level": "Easy",
            "passage": "Nature provides us with various resources. Water is essential for survival. However, many people waste it. Conserving water is our collective responsibility.",

            "question": "What is the main message of the passage?",

            "options": [
                "Water is not important.",
                "Nature provides only water.",
                "We should conserve water.",
                "People do not use water."
            ],

            "answer": "We should conserve water.",

            "explanation": "The passage explains that water is essential for survival, people waste it, and therefore conserving water is everyone's responsibility. Hence, option C is correct.",

            "hint": "Read the final sentence carefully. It gives the main idea."
        },

        {
            "topic": "Specific Detail",
            "company": "Infosys",
            "year": 2025,
            "level": "Easy",
            "passage": "Time management is a crucial skill for professionals. It helps in completing tasks on time and reducing stress. Good time management leads to better productivity.",

            "question": "According to the passage, what is a direct benefit of good time management?",

            "options": [
                "It increases workplace stress.",
                "It helps in completing tasks on time.",
                "It reduces employee productivity.",
                "It intentionally wastes valuable time."
            ],

            "answer": "It helps in completing tasks on time.",

            "explanation": "The passage directly states that good time management helps professionals complete their work on time and improves productivity. Therefore, option B is correct.",

            "hint": "Look for the words 'helps in'."
        },

        {
            "topic": "Title / Theme",
            "company": "Wipro",
            "year": 2024,
            "level": "Easy",
            "passage": "Reading books expands our knowledge and improves our vocabulary. It is a healthy habit that stimulates the mind. Many successful leaders credit reading for their success.",

            "question": "Which is the most suitable title for the passage?",

            "options": [
                "How to Write a Book",
                "The Dangers of Reading",
                "The Habit of Reading",
                "Children's Education"
            ],

            "answer": "The Habit of Reading",

            "explanation": "Every sentence discusses the benefits of reading as a habit. Therefore, 'The Habit of Reading' best summarizes the passage.",

            "hint": "Choose the title that covers the whole passage."
        },

        {
            "topic": "Fact Identification",
            "company": "IBM",
            "year": 2024,
            "level": "Easy",
            "passage": "Regular data backups are critical for every organization. Cyber attacks and hardware failures can cause permanent data loss. Secure backups help organizations recover important files quickly.",

            "question": "Why are regular backups important?",

            "options": [
                "They remove hardware.",
                "They protect against permanent data loss.",
                "They increase cyber attacks.",
                "They reduce internet speed."
            ],

            "answer": "They protect against permanent data loss.",

            "explanation": "The passage explains that backups prevent permanent loss of important files after hardware failures or cyber attacks.",

            "hint": "Find what backups help prevent."
        },

        {
            "topic": "Cause and Effect",
            "company": "Infosys",
            "year": 2026,
            "level": "Easy",
            "passage": "E-commerce has transformed the way people shop. Customers can purchase products online from home. This has made shopping more convenient.",

            "question": "What advantage of e-commerce is mentioned?",

            "options": [
                "Shopping has become more convenient.",
                "People must visit stores.",
                "Shopping is difficult.",
                "Buying choices are limited."
            ],

            "answer": "Shopping has become more convenient.",

            "explanation": "The final sentence clearly states that online shopping has made shopping more convenient.",

            "hint": "Read the last sentence."
        },

        {
            "topic": "Specific Detail",
            "company": "TCS",
            "year": 2025,
            "level": "Easy",
            "passage": "Healthy employee relationships improve workplace morale. Open communication reduces misunderstandings and makes project execution smoother.",

            "question": "What decreases because of open communication?",

            "options": [
                "Workplace morale",
                "Misunderstandings",
                "Project quality",
                "Employee confidence"
            ],

            "answer": "Misunderstandings",

            "explanation": "The passage directly states that open communication reduces misunderstandings.",

            "hint": "Look at the second sentence."
        },

        {
            "topic": "Sentence Detail",
            "company": "IBM",
            "year": 2025,
            "level": "Easy",
            "passage": "Cloud automation simplifies software deployment. It reduces manual work, allowing engineers to focus on innovation and better software design.",

            "question": "What do engineers focus on after manual work is reduced?",

            "options": [
                "Innovation and software design",
                "Manual testing",
                "Paper documentation",
                "Hardware repairs"
            ],

            "answer": "Innovation and software design",

            "explanation": "The passage clearly states that reducing manual work allows engineers to spend more time on innovation and design.",

            "hint": "Read the last part of the passage."
        },

        {
            "topic": "Fact Identification",
            "company": "Wipro",
            "year": 2025,
            "level": "Easy",
            "passage": "Corporate mentorship helps fresh graduates adapt to professional life. Experienced mentors provide guidance and industry knowledge.",

            "question": "What do mentors provide?",

            "options": [
                "Industry knowledge",
                "Exam papers",
                "Salary increases",
                "Office equipment"
            ],

            "answer": "Industry knowledge",

            "explanation": "The passage states that mentors guide fresh graduates by sharing industry knowledge and experience.",

            "hint": "Find what mentors share."
        },

        {
            "topic": "Inference",
            "company": "TCS",
            "year": 2026,
            "level": "Easy",
            "passage": "Agile development divides projects into small sprints. Teams can quickly respond to customer feedback and improve the product continuously.",

            "question": "What is one benefit of Agile development?",

            "options": [
                "Quick adaptation to customer feedback",
                "Ignoring customer suggestions",
                "Long development cycles",
                "No testing is required"
            ],

            "answer": "Quick adaptation to customer feedback",

            "explanation": "The passage explains that Agile allows teams to respond quickly to changing customer needs.",

            "hint": "Look for the benefit of using sprints."
        },

        {
            "topic": "Fact Extraction",
            "company": "Infosys",
            "year": 2024,
            "level": "Easy",
            "passage": "Ergonomic office furniture reduces strain on the body. Proper back support prevents posture-related health problems during long working hours.",

            "question": "What helps prevent posture problems?",

            "options": [
                "Proper back support",
                "Long working hours",
                "Ignoring posture",
                "Standing all day"
            ],

            "answer": "Proper back support",

            "explanation": "The passage states that appropriate back support helps prevent posture-related health issues.",

            "hint": "Read the second sentence carefully."
        }

        

        ],
        "Medium":[
        
        {
            "topic": "Complex Inference",
            "company": "Wipro",
            "year": 2026,
            "level": "Medium",
            "passage": "Remote work has fundamentally changed the employment landscape. While it offers employees flexibility and eliminates commuting time, it requires strong self-discipline. Employers can access a global talent pool but must also develop new strategies to maintain team collaboration and company culture.",

            "question": "What can be inferred from the passage?",

            "options": [
                "Only employees benefit from remote work.",
                "Remote work removes the need for discipline.",
                "Both employees and employers must adapt.",
                "Remote work is unsuitable for modern companies."
            ],

            "answer": "Both employees and employers must adapt.",

            "explanation": "The passage highlights advantages and challenges for both employees and employers. Therefore, both groups need to adapt to make remote work successful.",

            "hint": "Look for benefits and challenges mentioned for both employees and employers."
        },

        {
            "topic": "Vocabulary in Context",
            "company": "TCS",
            "year": 2026,
            "level": "Medium",
            "passage": "The company's innovative product launch was a massive success, rendering its closest competitors obsolete in the market. Consumers quickly switched to the new product because of its advanced features.",

            "question": "What does the word 'obsolete' mean in the passage?",

            "options": [
                "Expensive",
                "Outdated",
                "Popular",
                "Modern"
            ],

            "answer": "Outdated",

            "explanation": "The passage states that customers left the old products and preferred the new one. Therefore, the competitors became outdated or obsolete.",

            "hint": "Think about what happens to old technology when better technology arrives."
        },

        {
            "topic": "Author's Purpose",
            "company": "Infosys",
            "year": 2025,
            "level": "Medium",
            "passage": "Financial literacy is an essential life skill. Understanding budgeting, investing and debt management helps people make better financial decisions. Schools should include financial education as part of their curriculum.",

            "question": "What is the author's main purpose?",

            "options": [
                "To explain banking history",
                "To criticize students",
                "To encourage financial education in schools",
                "To advertise investment plans"
            ],

            "answer": "To encourage financial education in schools",

            "explanation": "The passage concludes by recommending that schools include financial literacy in their curriculum.",

            "hint": "Read the final sentence carefully."
        },

        {
            "topic": "Fact Identification",
            "company": "Wipro",
            "year": 2025,
            "level": "Medium",
            "passage": "Cloud computing enables businesses to store data online instead of relying only on local hardware. It reduces infrastructure costs, improves collaboration and allows resources to scale easily.",

            "question": "Which of the following is NOT mentioned as a benefit?",

            "options": [
                "Lower infrastructure cost",
                "Improved collaboration",
                "Scalable resources",
                "Removing internet-based storage"
            ],

            "answer": "Removing internet-based storage",

            "explanation": "The passage explains that cloud computing stores data over the internet, so removing internet storage is not a benefit.",

            "hint": "Compare every option with the passage."
        },

        {
            "topic": "Contextual Inference",
            "company": "TCS",
            "year": 2024,
            "level": "Medium",
            "passage": "A city rewarded residents who recycled plastic and paper for three months. Participation increased significantly, and landfill waste reduced noticeably.",

            "question": "What does the reduction in landfill waste suggest?",

            "options": [
                "The program failed.",
                "People stopped recycling.",
                "The recycling initiative was successful.",
                "Landfills became larger."
            ],

            "answer": "The recycling initiative was successful.",

            "explanation": "Since more people participated and landfill waste decreased, the initiative clearly achieved its goal.",

            "hint": "Connect increased participation with reduced landfill waste."
        },

        {
            "topic": "Analytical Inference",
            "company": "IBM",
            "year": 2026,
            "level": "Medium",
            "passage": "Open-source software allows anyone to inspect and improve the source code. While this encourages innovation, attackers may also study the code to discover security vulnerabilities before they are fixed.",

            "question": "Which risk of open-source software is highlighted?",

            "options": [
                "It prevents innovation.",
                "It increases software cost.",
                "Attackers can discover vulnerabilities.",
                "Developers cannot modify the code."
            ],

            "answer": "Attackers can discover vulnerabilities.",

            "explanation": "The passage states that public access to source code may allow attackers to identify security weaknesses before updates are released.",

            "hint": "Read the sentence beginning with 'While...'."
        },

        {
            "topic": "Inference",
            "company": "IBM",
            "year": 2025,
            "level": "Medium",
            "passage": "Machine learning systems detect fraudulent transactions within seconds by examining hundreds of data points simultaneously. Manual reviews usually require much more time.",

            "question": "What advantage do machine learning systems have?",

            "options": [
                "They examine fewer data points.",
                "They require more manual work.",
                "They detect fraud much faster.",
                "They cannot identify suspicious transactions."
            ],

            "answer": "They detect fraud much faster.",

            "explanation": "The passage explains that machine learning analyzes hundreds of variables instantly, making fraud detection much faster than manual reviews.",

            "hint": "Compare machine learning with manual review."
        },

        {
            "topic": "Paragraph Evaluation",
            "company": "Infosys",
            "year": 2024,
            "level": "Medium",
            "passage": "User Experience (UX) design should guide users naturally. Excessive animations and bright colors may distract users and reduce usability.",

            "question": "What warning does the passage give?",

            "options": [
                "Animations always improve usability.",
                "Bright colors always improve design.",
                "Too many animations may reduce usability.",
                "UX is only about decoration."
            ],

            "answer": "Too many animations may reduce usability.",

            "explanation": "The passage clearly warns that excessive animations and bright colors distract users from the interface.",

            "hint": "Find what 'distracts' users."
        },

        {
            "topic": "Main Objective",
            "company": "Wipro",
            "year": 2024,
            "level": "Medium",
            "passage": "Smart traffic management systems adjust traffic signals using real-time data. This reduces congestion and lowers pollution in cities.",

            "question": "What is the main purpose of smart traffic systems?",

            "options": [
                "Increase traffic jams",
                "Reduce congestion and pollution",
                "Make signals random",
                "Increase fuel consumption"
            ],

            "answer": "Reduce congestion and pollution",

            "explanation": "The passage explains that smart systems optimize signal timings to reduce traffic congestion and pollution.",

            "hint": "Look at the final sentence."
        },

        {
            "topic": "Fact Extraction",
            "company": "TCS",
            "year": 2025,
            "level": "Medium",
            "passage": "Companies must follow strict data compliance rules. Failure to protect customer information can lead to legal penalties and loss of reputation.",

            "question": "Why is data compliance important?",

            "options": [
                "It is optional.",
                "It prevents legal penalties and reputation loss.",
                "It reduces company profits.",
                "It removes customer information."
            ],

            "answer": "It prevents legal penalties and reputation loss.",

            "explanation": "The passage clearly states that companies failing to secure customer information face legal action and damage to their reputation.",

            "hint": "Read the second sentence carefully."
        }

        ],

                        
                

        "Hard":[
        {
            "topic": "Logical Assumption",
            "company": "Infosys",
            "year": 2024,
            "level": "Hard",

            "passage": "The gig economy relies heavily on independent contractors who trade job security for autonomy. Advocates argue this model maximizes flexibility and labor efficiency. Critics, however, point out that without benefits such as health insurance and retirement plans, workers face significant financial risks during economic downturns.",

            "question": "Which assumption made by supporters of the gig economy is challenged by the critics?",

            "options": [
                "Flexibility fully compensates for the lack of employee benefits.",
                "Independent contractors earn higher salaries.",
                "Economic recessions never affect freelancers.",
                "Traditional jobs offer no benefits."
            ],

            "answer": "Flexibility fully compensates for the lack of employee benefits.",

            "explanation": "Supporters believe flexibility is enough to offset the absence of traditional employment benefits. Critics disagree, arguing that workers remain financially vulnerable without health insurance and retirement plans.",

            "hint": "Identify the belief that the critics directly oppose."
        },

        {
            "topic": "Author's Tone",
            "company": "TCS",
            "year": 2025,
            "level": "Hard",

            "passage": "Biometric surveillance systems are often promoted as essential for public safety. However, excessive surveillance may gradually reduce privacy and personal freedom. When every movement is constantly monitored, society risks sacrificing civil liberties for an illusion of complete security.",

            "question": "What is the author's attitude toward biometric surveillance?",

            "options": [
                "Strongly supportive",
                "Completely neutral",
                "Concerned about privacy and civil liberties",
                "Interested only in technology"
            ],

            "answer": "Concerned about privacy and civil liberties",

            "explanation": "The author repeatedly warns about reduced privacy, constant monitoring, and loss of civil liberties, indicating a concerned and cautious tone.",

            "hint": "Notice the negative words like 'reduce privacy' and 'sacrificing civil liberties'."
        },

        {
            "topic": "Inference",
            "company": "Wipro",
            "year": 2026,
            "level": "Hard",

            "passage": "Digital media has made information more accessible than ever before. Surprisingly, instead of encouraging balanced opinions, personalized recommendation algorithms often expose users only to content matching their existing beliefs. This creates echo chambers where opposing viewpoints are rarely encountered.",

            "question": "Which statement best explains the author's observation?",

            "options": [
                "Access to more information always improves critical thinking.",
                "Algorithms encourage users to see diverse opinions.",
                "People often receive information that reinforces existing beliefs.",
                "Digital media has reduced internet usage."
            ],

            "answer": "People often receive information that reinforces existing beliefs.",

            "explanation": "The passage explains that recommendation algorithms show similar viewpoints repeatedly, creating echo chambers instead of balanced discussions.",

            "hint": "Focus on the phrase 'existing beliefs'."
        },

        {
            "topic": "Conceptual Understanding",
            "company": "Infosys",
            "year": 2026,
            "level": "Hard",

            "passage": "Traditional manufacturing focuses on producing goods in very large quantities to reduce cost per unit. Modern smart manufacturing instead uses automation, artificial intelligence, and flexible production systems to efficiently produce customized products according to customer demand.",

            "question": "What is the major difference between smart manufacturing and traditional manufacturing?",

            "options": [
                "Traditional manufacturing uses artificial intelligence.",
                "Smart manufacturing supports flexible and customized production.",
                "Traditional manufacturing focuses on customization.",
                "Smart manufacturing completely eliminates production costs."
            ],

            "answer": "Smart manufacturing supports flexible and customized production.",

            "explanation": "Traditional manufacturing emphasizes mass production, whereas smart manufacturing focuses on flexible, AI-driven customization based on customer requirements.",

            "hint": "Compare 'mass production' with 'customized production'."
        },

        {
            "topic": "Critical Reasoning",
            "company": "IBM",
            "year": 2025,
            "level": "Hard",

            "passage": "Artificial intelligence is transforming healthcare by assisting doctors in disease diagnosis, predicting medical risks, and recommending treatment plans. Nevertheless, experts caution that AI should complement medical professionals rather than replace them, because ethical judgment and human empathy remain essential in patient care.",

            "question": "Which conclusion is best supported by the passage?",

            "options": [
                "Artificial intelligence can completely replace doctors.",
                "Healthcare no longer requires human interaction.",
                "AI should assist doctors but not replace human decision-making.",
                "Medical professionals should stop using AI."
            ],

            "answer": "AI should assist doctors but not replace human decision-making.",

            "explanation": "The passage praises AI's capabilities but clearly states that ethical decisions and empathy require human doctors. Therefore, AI is a support tool rather than a replacement.",

            "hint": "Read the final sentence carefully."
        },
        
        {
            "topic": "Critical Reasoning",
            "company": "Infosys",
            "year": 2025,
            "passage": "A company introduced a four-day workweek for six months. Employee satisfaction increased significantly, while overall productivity remained the same. The management concluded that reducing working days improves employee well-being without affecting business performance.",
            "question": "Which statement weakens the management's conclusion?",
            "options": [
                "The company also hired additional temporary employees during the six-month period.",
                "Employees appreciated the extra day off.",
                "The company received positive media attention.",
                "Other companies are considering similar policies."
            ],
            "answer": "The company also hired additional temporary employees during the six-month period.",
            "explanation": "If additional employees were hired, productivity may have been maintained because of the extra workforce rather than the four-day workweek. Therefore, the conclusion is weakened.",
            "hint": "Look for another factor that could explain the unchanged productivity."
        },
        {
            "topic": "Author's Tone",
            "company": "TCS",
            "year": 2025,
            "passage": "Artificial Intelligence has transformed industries by automating repetitive tasks. However, organizations must implement ethical guidelines to prevent misuse and ensure transparency in decision-making.",
            "question": "What is the author's tone?",
            "options": [
                "Critical",
                "Balanced and cautious",
                "Humorous",
                "Completely negative"
            ],
            "answer": "Balanced and cautious",
            "explanation": "The author appreciates the benefits of AI while also emphasizing ethical concerns, showing a balanced and cautious viewpoint.",
            "hint": "Notice that both advantages and precautions are discussed."
        },
        {
            "topic": "Inference",
            "company": "Wipro",
            "year": 2026,
            "passage": "Many organizations now invest heavily in employee training programs. Continuous learning enables employees to adapt to new technologies and improve innovation within the organization.",
            "question": "What can be inferred from the passage?",
            "options": [
                "Training programs reduce employee salaries.",
                "Organizations value adaptability and innovation.",
                "Technology never changes.",
                "Training is unnecessary for experienced employees."
            ],
            "answer": "Organizations value adaptability and innovation.",
            "explanation": "The passage connects training with adapting to technology and increasing innovation, implying organizations value these qualities.",
            "hint": "Focus on why companies spend money on training."
        },
        {
            "topic": "Vocabulary in Context",
            "company": "IBM",
            "year": 2026,
            "passage": "The CEO's pragmatic approach helped the company recover quickly from financial losses by focusing on practical solutions instead of unrealistic expectations.",
            "question": "What does the word 'pragmatic' mean in the passage?",
            "options": [
                "Emotional",
                "Practical",
                "Confusing",
                "Creative"
            ],
            "answer": "Practical",
            "explanation":"The passage explains that the CEO focused on practical solutions, which defines the meaning of 'pragmatic'.",
            "hint": "Read the phrase immediately after the word 'pragmatic'."
        },
        {
            "topic": "Main Conclusion",
            "company": "Infosys",
            "year": 2024,
            "passage": "Cybersecurity threats continue to evolve every year. Organizations that regularly update their software and educate employees are less likely to experience security breaches.",
            "question": "What is the main conclusion of the passage?",
            "options": [
                "Cybersecurity is becoming less important.",
                "Regular updates and awareness improve security.",
                "Software updates are unnecessary.",
                "Employees should avoid using computers."
            ],
            "answer": "Regular updates and awareness improve security.",
            "explanation":"The passage concludes that keeping software updated and educating employees helps reduce security risks.",
            "hint": "Look at the final sentence."}
        ]
        
        


    }
}
}

# ==============================
# PLACEMENT PREPARATION
# ==============================

@app.route("/placement")
def placement():
    return render_template("placement.html")


# ==============================
# PLACEMENT CATEGORY PAGES
# ==============================

@app.route("/aptitude")
def aptitude():
    return render_template(
        "difficulty.html",
        title="Aptitude",
        route="aptitude_quiz"
    )


@app.route("/logical")
def logical():
    return render_template(
        "difficulty.html",
        title="Logical Reasoning",
        route="logical_quiz"
    )


@app.route("/verbal")
def verbal():
    return render_template(
        "difficulty.html",
        title="Verbal Ability",
        route="verbal_quiz"
    )


@app.route("/passage")
def passage():
    return render_template(
        "difficulty.html",
        title="Reading Comprehension",
        route="passage_quiz"
    )


# ==============================
# PLACEMENT QUIZ ROUTES
# ==============================

@app.route("/aptitude/<level>")
def aptitude_quiz(level):
    return redirect(
        url_for(
            "quiz",
            subject="Placement Preparation/Aptitude",
            level=level
        )
    )


@app.route("/logical/<level>")
def logical_quiz(level):
    return redirect(
        url_for(
            "quiz",
            subject="Placement Preparation/Logical Reasoning",
            level=level
        )
    )


@app.route("/verbal/<level>")
def verbal_quiz(level):
    return redirect(
        url_for(
            "quiz",
            subject="Placement Preparation/Verbal Ability",
            level=level
        )
    )


@app.route("/passage/<level>")
def passage_quiz(level):
    return redirect(
        url_for(
            "quiz",
            subject="Placement Preparation/Passage",
            level=level
        )
    )

# ============================================================
# LOAD ADMIN-ADDED QUESTIONS FROM DATABASE
# ============================================================

def get_admin_questions(subject, level, section=None):

    conn = get_db_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # PLACEMENT QUESTIONS
    # --------------------------------------------------------

    if section:

        rows = cursor.execute(
            """
            SELECT *
            FROM questions
            WHERE subject = ?
            AND section = ?
            AND level = ?
            ORDER BY id ASC
            """,
            (
                subject,
                section,
                level
            )
        ).fetchall()

    # --------------------------------------------------------
    # NORMAL SUBJECT QUESTIONS
    # --------------------------------------------------------

    else:

        rows = cursor.execute(
            """
            SELECT *
            FROM questions
            WHERE subject = ?
            AND (section IS NULL OR section = '')
            AND level = ?
            ORDER BY id ASC
            """,
            (
                subject,
                level
            )
        ).fetchall()

    conn.close()

    questions = []

    # --------------------------------------------------------
    # CONVERT DATABASE ROWS INTO YOUR QUIZ FORMAT
    # --------------------------------------------------------

    for row in rows:

        options = []

        if row["option1"]:
            options.append(row["option1"])

        if row["option2"]:
            options.append(row["option2"])

        if row["option3"]:
            options.append(row["option3"])

        if row["option4"]:
            options.append(row["option4"])

        question_data = {

            "topic": row["topic"] or "",

            "company": row["company"] or "",

            "year": row["year"] or "",

            "level": row["level"] or level,

            "type": row["question_type"] or "mcq",

            "question": row["question"] or "",

            "options": options,

            "answer": row["answer"] or "",

            "explanation": row["explanation"] or "",

            "hint": row["hint"] or "",

            "passage": row["passage"] or ""

        }

        questions.append(question_data)

    return questions
# ---------------- HOME ----------------


# ================= QUIZ =================

@app.route("/quiz/<path:subject>/<level>", methods=["GET", "POST"])
def quiz(subject, level):

    if "user" not in session:
        return redirect(url_for("login"))

    # ==========================================
    # NORMALIZE SUBJECT AND LEVEL
    # ==========================================

    normalized_subject = subject.strip().lower()
    normalized_level = level.strip().lower()

    questions = None
    quiz_subject = subject

    # ==========================================
    # PLACEMENT PREPARATION
    # ==========================================

    placement_data = quizzes.get("Placement Preparation")

    if isinstance(placement_data, dict):

        requested_category = None

        # -------------------------------
        # FIND PLACEMENT CATEGORY
        # -------------------------------

        if normalized_subject in [
            "placement preparation/aptitude",
            "aptitude"
        ]:
            requested_category = "Aptitude"

        elif normalized_subject in [
            "placement preparation/logical reasoning",
            "logical reasoning",
            "logical"
        ]:
            requested_category = "Logical Reasoning"

        elif normalized_subject in [
            "placement preparation/verbal ability",
            "verbal ability",
            "verbal"
        ]:
            requested_category = "Verbal Ability"

        elif normalized_subject in [
            "placement preparation/passage",
            "passage",
            "reading comprehension"
        ]:
            requested_category = "Passage"

        # -------------------------------
        # FIND CATEGORY INSIDE PLACEMENT
        # -------------------------------

        if requested_category is not None:

            category_data = None

            for category_key, category_value in placement_data.items():

                if (
                    str(category_key).strip().lower()
                    == requested_category.lower()
                ):
                    category_data = category_value
                    quiz_subject = requested_category
                    break

            # -------------------------------
            # FIND LEVEL INSIDE CATEGORY
            # -------------------------------

            if isinstance(category_data, dict):

                for level_key, level_value in category_data.items():

                    if (
                        str(level_key).strip().lower()
                        == normalized_level
                    ):
                        questions = level_value
                        break

    # ==========================================
    # SUPPORT TOP-LEVEL SUBJECTS
    # ==========================================

    if questions is None:

        actual_subject = None

        for key in quizzes.keys():

            if (
                str(key).strip().lower()
                == normalized_subject
            ):
                actual_subject = key
                break

        if actual_subject is not None:

            quiz_subject = actual_subject

            subject_data = quizzes[actual_subject]

            if isinstance(subject_data, dict):

                actual_level = None

                for key in subject_data.keys():

                    if (
                        str(key).strip().lower()
                        == normalized_level
                    ):
                        actual_level = key
                        break

                if actual_level is not None:

                    questions = subject_data[actual_level]
        # ==========================================
    # ADD QUESTIONS CREATED BY ADMIN
    # ==========================================

    admin_subject = None
    admin_section = None


    # ------------------------------------------
    # NORMAL SUBJECTS
    # ------------------------------------------

    if normalized_subject in [
        "python",
        "python programming"
    ]:

        admin_subject = "Python Programming"


    elif normalized_subject in [
        "java",
        "java programming"
    ]:

        admin_subject = "Java Programming"


    elif normalized_subject == "dbms":

        admin_subject = "DBMS"


    # ------------------------------------------
    # PLACEMENT PREPARATION
    # ------------------------------------------

    elif normalized_subject in [
        "placement preparation/aptitude",
        "aptitude"
    ]:

        admin_subject = "Placement Preparation"
        admin_section = "Aptitude"


    elif normalized_subject in [
        "placement preparation/logical reasoning",
        "logical reasoning",
        "logical"
    ]:

        admin_subject = "Placement Preparation"
        admin_section = "Logical Reasoning"


    elif normalized_subject in [
        "placement preparation/verbal ability",
        "verbal ability",
        "verbal"
    ]:

        admin_subject = "Placement Preparation"
        admin_section = "Verbal Ability"


    elif normalized_subject in [
        "placement preparation/passage",
        "passage",
        "reading comprehension"
    ]:

        admin_subject = "Placement Preparation"
        admin_section = "Passage"


    # ------------------------------------------
    # LOAD DATABASE QUESTIONS
    # ------------------------------------------

    if admin_subject:

        database_questions = get_admin_questions(
            admin_subject,
            level,
            admin_section
        )

        if questions is None:

            questions = database_questions

        else:

            questions = list(questions)

            questions.extend(
                database_questions
            )
    # ==========================================
# LOAD QUESTIONS ADDED BY ADMIN
# ==========================================

    admin_subject = None
    admin_section = None

    # Normal subjects
    if normalized_subject in [
        "python",
        "python programming"
    ]:
        admin_subject = "Python Programming"

    elif normalized_subject in [
        "java",
        "java programming"
    ]:
        admin_subject = "Java Programming"

    elif normalized_subject == "dbms":
        admin_subject = "DBMS"


    # Placement Preparation
    elif normalized_subject in [
        "placement preparation/aptitude",
        "aptitude"
    ]:
        admin_subject = "Placement Preparation"
        admin_section = "Aptitude"

    elif normalized_subject in [
        "placement preparation/logical reasoning",
        "logical reasoning",
        "logical"
    ]:
        admin_subject = "Placement Preparation"
        admin_section = "Logical Reasoning"

    elif normalized_subject in [
        "placement preparation/verbal ability",
        "verbal ability",
        "verbal"
    ]:
        admin_subject = "Placement Preparation"
        admin_section = "Verbal Ability"

    elif normalized_subject in [
        "placement preparation/passage",
        "passage",
        "reading comprehension"
    ]:
        admin_subject = "Placement Preparation"
        admin_section = "Passage"


    # Get questions from SQLite
    if admin_subject:

        database_questions = get_admin_questions(
            admin_subject,
            level,
            admin_section
        )

        if questions is None:
            questions = database_questions

        else:
            questions = list(questions)
            questions.extend(database_questions)
        # ==========================================
        # QUESTION NOT FOUND
        # ==========================================

        if questions is None:

            available_subjects = []

            if isinstance(placement_data, dict):

                available_subjects = [
                    str(key)
                    for key in placement_data.keys()
                ]

            return (
                f"""
                <html>
                <head>
                    <title>Questions Not Found</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background: #f4f6f8;
                            padding: 40px;
                        }}

                        .box {{
                            max-width: 700px;
                            margin: auto;
                            background: white;
                            padding: 30px;
                            border-radius: 15px;
                            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
                        }}

                        h2 {{
                            color: #e74c3c;
                        }}

                        p {{
                            font-size: 17px;
                        }}
                    </style>
                </head>

                <body>

                    <div class="box">

                        <h2>
                            Placement Preparation Question Not Found
                        </h2>

                        <p>
                            <b>Subject:</b> {subject}
                        </p>

                        <p>
                            <b>Level:</b> {level}
                        </p>

                        <p>
                            <b>Available Placement Categories:</b>
                            {", ".join(available_subjects)}
                        </p>

                        <p>
                            Please check your quiz data structure.
                        </p>

                    </div>

                </body>
                </html>
                """,
                404
            )

    # ==========================================
    # CHECK QUESTIONS
    # ==========================================

    if not questions:

        return (
            "No questions available for this subject and level",
            404
        )

    total_questions = len(questions)

    # ==========================================
    # TIMER
    # ==========================================

    time_limit = total_questions * 60

    quiz_key = f"{quiz_subject}_{normalized_level}"

    # ==========================================
    # START NEW QUIZ
    # ==========================================

    if session.get("quiz_key") != quiz_key:

        session["quiz_key"] = quiz_key
        session["question_index"] = 0
        session["answers"] = {}
        session["quiz_start_time"] = time.time()
        # Reset result-email status for every new quiz attempt
        session["quiz_email_sent"] = False
        session.pop("quiz_email_error", None)

        session.modified = True

    current = session.get(
        "question_index",
        0
    )

    answers = session.get(
        "answers",
        {}
    )

    # ==========================================
    # TIMER
    # ==========================================

    start_time = session.get(
        "quiz_start_time",
        time.time()
    )

    elapsed = int(
        time.time() - start_time
    )

    remaining_time = max(
        0,
        time_limit - elapsed
    )

    # ==========================================
    # TIMEOUT
    # ==========================================

    if remaining_time <= 0:

        session["question_index"] = total_questions

        return redirect(
            url_for(
                "quiz_result",
                subject=subject,
                level=level
            )
        )

    # ==========================================
    # POST
    # ==========================================

    if request.method == "POST":

        action = request.form.get(
            "action"
        )

        answer = request.form.get(
            "answer"
        )

        # ======================================
        # SAVE ANSWER
        # ======================================

        if answer is not None:

            answers[str(current)] = answer

        session["answers"] = answers

        # ======================================
        # PREVIOUS
        # ======================================

        if action == "previous":

            if current > 0:

                current -= 1

            session["question_index"] = current

            session.modified = True

            return redirect(
                url_for(
                    "quiz",
                    subject=subject,
                    level=level
                )
            )

        # ======================================
        # NEXT / SKIP
        # ======================================

        if action in [
            "next",
            "skip"
        ]:

            if current < total_questions - 1:

                current += 1

                session["question_index"] = current

                session.modified = True

                return redirect(
                    url_for(
                        "quiz",
                        subject=subject,
                        level=level
                    )
                )

            # ==================================
            # FINISH QUIZ
            # ==================================

            score = 0

            review = []

            for i, q in enumerate(questions):

                user_answer = answers.get(
                    str(i)
                )

                correct_answer = q.get(
                    "answer",
                    ""
                )

                is_correct = (
                    user_answer == correct_answer
                )

                if is_correct:

                    score += 1

                    status = "Correct"

                elif not user_answer:

                    status = "Skipped"

                else:

                    status = "Incorrect"

                review.append({

                    "number": i + 1,

                    "question": q.get(
                        "question",
                        ""
                    ),

                    "options": q.get(
                        "options",
                        []
                    ),

                    "user_answer": (
                        user_answer
                        if user_answer
                        else "Not Answered"
                    ),

                    "correct_answer": correct_answer,

                    "is_correct": is_correct,

                    "status": status,

                    "explanation": q.get(
                        "explanation",
                        "Explanation not available."
                    ),

                    "hint": q.get(
                        "hint",
                        ""
                    ),

                    "passage": q.get(
                        "passage",
                        ""
                    ),

                    "topic": q.get(
                        "topic",
                        ""
                    ),

                    "company": q.get(
                        "company",
                        ""
                    ),

                    "year": q.get(
                        "year",
                        ""
                    ),

                    # Placement section
                    "section": q.get(
                        "section",
                        ""
                    )
                })

            # ==================================
            # SAVE RESULT
            # ==================================

            session["quiz_score"] = score

            session["quiz_total"] = total_questions

            session["quiz_review"] = review

            session.modified = True

            return redirect(
                url_for(
                    "quiz_result",
                    subject=subject,
                    level=level
                )
            )

    # ==========================================
    # CURRENT QUESTION
    # ==========================================

    current = session.get(
        "question_index",
        0
    )

    if current >= total_questions:

        current = total_questions - 1

        session["question_index"] = current

    question = questions[current]

    selected_answer = answers.get(
        str(current)
    )

    # ==========================================
    # DISPLAY SUBJECT
    # ==========================================

    if normalized_subject in [
        "placement preparation/aptitude",
        "aptitude"
    ]:

        display_subject = "Aptitude"

    elif normalized_subject in [
        "placement preparation/logical reasoning",
        "logical reasoning",
        "logical"
    ]:

        display_subject = "Logical Reasoning"

    elif normalized_subject in [
        "placement preparation/verbal ability",
        "verbal ability",
        "verbal"
    ]:

        display_subject = "Verbal Ability"

    elif normalized_subject in [
        "placement preparation/passage",
        "passage",
        "reading comprehension"
    ]:

        display_subject = "Reading Comprehension"

    else:

        display_subject = quiz_subject

    # ==========================================
    # DISPLAY QUIZ
    # ==========================================

    return render_template(
        "quiz.html",

        subject=display_subject,

        category=display_subject,

        level=level,

        question=question,

        current_question=current + 1,

        total_questions=total_questions,

        has_previous=current > 0,

        selected_answer=selected_answer,

        remaining_time=remaining_time
    )
# ==============================
# QUIZ RESULT
# ==============================
@app.route("/quiz_result/<path:subject>/<level>")
def quiz_result(subject, level):

    # =========================================================
    # LOGIN CHECK
    # =========================================================

    if "user" not in session:
        return redirect(url_for("login"))

    # =========================================================
    # NORMALIZE SUBJECT
    # =========================================================

    normalized_subject = str(subject).strip().lower()

    # =========================================================
    # CHECK PLACEMENT PREPARATION
    # =========================================================

    is_placement = (
        normalized_subject == "placement preparation"
        or normalized_subject.startswith("placement preparation/")
        or normalized_subject in [
            "aptitude",
            "logical reasoning",
            "logical",
            "verbal ability",
            "verbal",
            "passage",
            "reading comprehension"
        ]
    )

    # =========================================================
    # GET QUIZ DATA FROM SESSION
    # =========================================================

    score = session.get("quiz_score", 0)
    total = session.get("quiz_total", 0)
    review = session.get("quiz_review", [])

    # Make sure review is a list
    if not isinstance(review, list):
        review = []

    # =========================================================
    # FIX REVIEW DATA
    # =========================================================
    # Make sure explanation and hint are available for
    # Placement Preparation questions.
    #
    # Normal subjects will NOT display explanation because
    # quiz_result.html will check is_placement.
    # =========================================================

    fixed_review = []

    for item in review:

        if not isinstance(item, dict):
            continue

        fixed_item = dict(item)

        # -----------------------------------------------------
        # EXPLANATION
        # -----------------------------------------------------

        explanation = fixed_item.get("explanation", "")

        if explanation is None:
            explanation = ""

        fixed_item["explanation"] = str(explanation).strip()

        # -----------------------------------------------------
        # HINT
        # -----------------------------------------------------

        hint = fixed_item.get("hint", "")

        if hint is None:
            hint = ""

        fixed_item["hint"] = str(hint).strip()

        # -----------------------------------------------------
        # OTHER PLACEMENT DETAILS
        # -----------------------------------------------------

        fixed_item["company"] = fixed_item.get("company", "")
        fixed_item["year"] = fixed_item.get("year", "")
        fixed_item["topic"] = fixed_item.get("topic", "")
        fixed_item["section"] = fixed_item.get("section", "")
        fixed_item["passage"] = fixed_item.get("passage", "")

        fixed_review.append(fixed_item)

    review = fixed_review

    # =========================================================
    # CONVERT SCORE
    # =========================================================

    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0

    # =========================================================
    # CONVERT TOTAL
    # =========================================================

    try:
        total = int(total)
    except (ValueError, TypeError):
        total = len(review)

    # =========================================================
    # FIX TOTAL
    # =========================================================

    if total <= 0 and review:
        total = len(review)

    if total < 0:
        total = 0

    # =========================================================
    # CALCULATE PERCENTAGE
    # =========================================================

    percentage = 0

    if total > 0:
        percentage = round((score / total) * 100, 2)

    # =========================================================
    # COUNT CORRECT / WRONG / SKIPPED
    # =========================================================

    correct = 0
    wrong = 0
    skipped = 0

    for item in review:

        status = str(
            item.get("status", "")
        ).strip().lower()

        if status == "correct":
            correct += 1

        elif status in ["wrong", "incorrect"]:
            wrong += 1

        elif status == "skipped":
            skipped += 1

    # =========================================================
    # TIME TAKEN
    # =========================================================

    time_taken = session.get("time_taken", 0)

    try:
        time_taken = int(time_taken)
    except (ValueError, TypeError):
        time_taken = 0

    # =========================================================
    # COGNITIVE LEVEL
    # =========================================================

    if percentage >= 90:

        cognitive_level = "Expert"

    elif percentage >= 75:

        cognitive_level = "Advanced"

    elif percentage >= 60:

        cognitive_level = "Intermediate"

    elif percentage >= 40:

        cognitive_level = "Developing"

    else:

        cognitive_level = "Beginner"

    # =========================================================
    # RECOMMENDED LEVEL
    # =========================================================

    if percentage >= 85:

        recommended_level = "Hard"

    elif percentage >= 60:

        recommended_level = "Medium"

    else:

        recommended_level = "Easy"

    # =========================================================
    # PERFORMANCE SCORE
    # =========================================================

    performance_score = percentage

    # =========================================================
    # CONFIDENCE
    # =========================================================

    confidence = round(
        min(100, percentage + 5),
        2
    )

    # =========================================================
    # PREDICTION
    # =========================================================

    if percentage >= 75:

        prediction = "High Performance"

    elif percentage >= 50:

        prediction = "Moderate Performance"

    else:

        prediction = "Needs Improvement"

    # =========================================================
    # STRENGTH
    # =========================================================

    if percentage >= 75:

        strength = "Good conceptual understanding"

    elif percentage >= 50:

        strength = "Basic understanding of concepts"

    else:

        strength = "Shows willingness to learn"

    # =========================================================
    # WEAKNESS
    # =========================================================

    if percentage >= 85:

        weakness = "Minor mistakes"

    elif percentage >= 60:

        weakness = "Needs more practice with difficult questions"

    else:

        weakness = "Needs improvement in concepts and accuracy"

    # =========================================================
    # LEARNING PROFILE
    # =========================================================

    if percentage >= 85:

        learning_profile = "Fast and accurate learner"

    elif percentage >= 60:

        learning_profile = "Developing learner"

    else:

        learning_profile = "Learner requiring additional practice"

    # =========================================================
    # AVERAGE RESPONSE TIME
    # =========================================================

    if total > 0:

        average_response_time = round(
            time_taken / total,
            2
        )

    else:

        average_response_time = 0

    # =========================================================
    # RECOMMENDATION
    # =========================================================

    if percentage >= 85:

        recommendation = (
            "Excellent performance. Try the Hard level "
            "and continue practicing advanced questions."
        )

    elif percentage >= 60:

        recommendation = (
            "Good performance. Practice more questions "
            "and try the Medium level."
        )

    else:

        recommendation = (
            "Review the concepts and explanations carefully "
            "before attempting the next level."
        )

    # =========================================================
    # AI / ML ANALYSIS
    # =========================================================

    ai_analysis = {

        "prediction": prediction,

        "confidence": confidence,

        "performance_score": performance_score,

        "cognitive_level": cognitive_level,

        "recommended_level": recommended_level,

        "strength": strength,

        "weakness": weakness,

        "learning_profile": learning_profile,

        "average_response_time": average_response_time,

        "recommendation": recommendation
    }
    # =========================================================
    # SEND QUIZ RESULT EMAIL TO LOGGED-IN USER
    # =========================================================

    email_sent = session.get("quiz_email_sent", False)
    email_error = session.get("quiz_email_error", "")

    # Send only once for this quiz attempt. This prevents duplicate
    # emails when the user refreshes the result page.
    if not email_sent:
        try:
            username = session.get("user")

            if not username:
                raise ValueError("User session not found.")

            conn = get_db_connection()

            user = conn.execute(
                """
                SELECT name, email
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

            conn.close()

            if not user:
                raise ValueError("Logged-in user was not found in the database.")

            user_email = str(user["email"] or "").strip()

            if not user_email:
                raise ValueError("User email address is empty.")

            send_result_email(
                email=user_email,
                username=user["name"],
                subject=subject,
                level=level,
                total=total,
                correct=correct,
                wrong=wrong,
                skipped=skipped,
                cognitive_level=cognitive_level,
                performance_score=performance_score,
                timeout=session.get("quiz_timeout", False)
            )

            session["quiz_email_sent"] = True
            session.pop("quiz_email_error", None)
            email_sent = True
            email_error = ""

            print("========================================")
            print("RESULT EMAIL SENT SUCCESSFULLY")
            print("TO:", user_email)
            print("SUBJECT:", subject)
            print("LEVEL:", level)
            print("========================================")

        except Exception as e:
            email_error = str(e)
            session["quiz_email_sent"] = False
            session["quiz_email_error"] = email_error

            print("========================================")
            print("RESULT EMAIL FAILED")
            print("ERROR:", email_error)
            print("========================================")
    # =========================================================
# SAVE QUIZ HISTORY
# =========================================================

    try:

        username = session.get("user")

        if not username:
            raise ValueError("User session not found.")

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO quiz_history (
                username,
                subject,
                level,
                total,
                correct,
                wrong,
                skipped,
                time_taken,
                accuracy,
                performance_score,
                cognitive_level,
                recommended_level,
                strength,
                weakness,
                learning_profile,
                confidence,
                recommendation,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                username,
                subject,
                level,
                total,
                correct,
                wrong,
                skipped,
                time_taken,
                percentage,
                performance_score,
                cognitive_level,
                recommended_level,
                strength,
                weakness,
                learning_profile,
                confidence,
                recommendation,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

        print("========================================")
        print("QUIZ HISTORY SAVED SUCCESSFULLY")
        print("User:", username)
        print("Subject:", subject)
        print("Level:", level)
        print("Score:", score, "/", total)
        print("========================================")

    except Exception as e:

        print("========================================")
        print("QUIZ HISTORY SAVE ERROR")
        print("ERROR:", e)
        print("========================================")
        # =========================================================
        # SAVE FIXED REVIEW BACK TO SESSION
    # =========================================================

    session["quiz_review"] = review

    # =========================================================
    # RENDER RESULT PAGE
    # =========================================================

    return render_template(

        "quiz_result.html",

        subject=subject,

        # IMPORTANT
        # This tells HTML that this is Placement Preparation
        is_placement=is_placement,

        level=level,

        score=score,

        total=total,

        percentage=percentage,

        correct=correct,

        wrong=wrong,

        skipped=skipped,

        review=review,

        time_taken=time_taken,

        ai_analysis=ai_analysis,

        cognitive_level=cognitive_level,

        recommended_level=recommended_level,

        timeout=session.get(
            "quiz_timeout",
            False
        ),

        # Email status for the result page
        email_sent=email_sent,
        email_error=email_error
    )
# ==========================
# ADMIN LOGIN
# ==========================

@app.route(
    '/admin_login',
    methods=['GET', 'POST']
)
def admin_login():

    if request.method == "POST":

        username = request.form['username']

        password = request.form['password']

        if (
            username == "kavana"
            and password == "kavana123"
        ):

            session['admin'] = "admin"

            return redirect(
                url_for("admin_dashboard")
            )

        return render_template(
            "admin_login.html",
            error="Invalid Admin Username or Password"
        )

    return render_template(
        "admin_login.html"
    )


# ==========================
# ADMIN USERS
# ==========================

@app.route('/admin/users')
def admin_users():

    if 'admin' not in session:

        return redirect(
            url_for('admin_login')
        )

    conn = sqlite3.connect(
        "database/quiz.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            username
        FROM users
        ORDER BY id DESC
    """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users
    )


# ==========================
# ADMIN QUESTIONS
# ==========================
# ============================================================
# ADMIN - ADD QUESTIONS
# ============================================================

@app.route(
    "/admin/questions",
    methods=["GET", "POST"]
)
def admin_questions():

    # --------------------------------------------------------
    # CHECK ADMIN LOGIN
    # --------------------------------------------------------

    if "admin" not in session:
        return redirect(
            url_for("admin_login")
        )


    # --------------------------------------------------------
    # GET PAGE
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "admin_questions.html"
        )


    # --------------------------------------------------------
    # POST - ADD QUESTION
    # --------------------------------------------------------

    subject = request.form.get(
        "subject",
        ""
    ).strip()

    level = request.form.get(
        "level",
        ""
    ).strip()

    section = request.form.get(
        "section",
        ""
    ).strip()

    question_type = request.form.get(
        "question_type",
        ""
    ).strip()

    topic = request.form.get(
        "topic",
        ""
    ).strip()

    company = request.form.get(
        "company",
        ""
    ).strip()

    year_text = request.form.get(
        "year",
        ""
    ).strip()

    passage = request.form.get(
        "passage",
        ""
    ).strip()

    question = request.form.get(
        "question",
        ""
    ).strip()

    option1 = request.form.get(
        "option1",
        ""
    ).strip()

    option2 = request.form.get(
        "option2",
        ""
    ).strip()

    option3 = request.form.get(
        "option3",
        ""
    ).strip()

    option4 = request.form.get(
        "option4",
        ""
    ).strip()

    answer = request.form.get(
        "answer",
        ""
    ).strip()

    explanation = request.form.get(
        "explanation",
        ""
    ).strip()

    hint = request.form.get(
        "hint",
        ""
    ).strip()


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not subject:

        flash(
            "Please select a subject.",
            "danger"
        )

        return redirect(
            url_for("admin_questions")
        )


    if not level:

        flash(
            "Please select a level.",
            "danger"
        )

        return redirect(
            url_for("admin_questions")
        )


    if not question:

        flash(
            "Please enter the question.",
            "danger"
        )

        return redirect(
            url_for("admin_questions")
        )


    if not answer:

        flash(
            "Please enter the correct answer.",
            "danger"
        )

        return redirect(
            url_for("admin_questions")
        )


    # --------------------------------------------------------
    # PLACEMENT VALIDATION
    # --------------------------------------------------------

    if subject == "Placement Preparation":

        valid_sections = [
            "Aptitude",
            "Logical Reasoning",
            "Verbal Ability",
            "Passage"
        ]

        if section not in valid_sections:

            flash(
                "Please select a Placement section.",
                "danger"
            )

            return redirect(
                url_for("admin_questions")
            )

    else:

        # Normal subjects don't need section
        section = ""


    # --------------------------------------------------------
    # CONVERT SUBJECT NAME
    # --------------------------------------------------------

    subject_map = {

        "Python":
            "Python Programming",

        "Java":
            "Java Programming",

        "DBMS":
            "DBMS",

        "Python Programming":
            "Python Programming",

        "Java Programming":
            "Java Programming"
    }


    database_subject = subject_map.get(
        subject,
        subject
    )


    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    year = None

    if year_text:

        try:

            year = int(year_text)

        except ValueError:

            year = None


    # --------------------------------------------------------
    # DATABASE CONNECTION
    # --------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()


    try:

        # ----------------------------------------------------
        # PREVENT EXACT DUPLICATE QUESTION
        # ----------------------------------------------------
        # Check whether the same question already exists
        # for the same subject and level.
        # ----------------------------------------------------

        existing_question = cursor.execute(
            """
            SELECT id
            FROM questions
            WHERE subject = ?
              AND level = ?
              AND question = ?
            LIMIT 1
            """,
            (
                database_subject,
                level,
                question
            )
        ).fetchone()


        if existing_question:

            conn.close()

            flash(
                "This question already exists. Duplicate question was not added.",
                "warning"
            )

            return redirect(
                url_for("admin_questions")
            )


        # ----------------------------------------------------
        # INSERT QUESTION
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO questions
            (
                subject,
                section,
                level,
                question_type,
                topic,
                company,
                year,
                passage,
                question,
                option1,
                option2,
                option3,
                option4,
                answer,
                explanation,
                hint,
                created_at
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?
            )
            """,

            (
                database_subject,
                section,
                level,
                question_type,
                topic,
                company,
                year,
                passage,
                question,
                option1,
                option2,
                option3,
                option4,
                answer,
                explanation,
                hint,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )


        # ----------------------------------------------------
        # SAVE ONLY ONCE
        # ----------------------------------------------------

        conn.commit()


    except Exception as e:

        conn.rollback()

        print(
            "ERROR ADDING QUESTION:",
            e
        )

        flash(
            "Error adding question: " + str(e),
            "danger"
        )

        conn.close()

        return redirect(
            url_for("admin_questions")
        )


    finally:

        try:
            conn.close()
        except:
            pass


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    flash(
        "Question added successfully! It is permanently saved.",
        "success"
    )


    # --------------------------------------------------------
    # POST-REDIRECT-GET
    # --------------------------------------------------------
    # Prevents browser refresh from submitting the same
    # POST request again.
    # --------------------------------------------------------

    return redirect(
        url_for("admin_questions")
    )
# ============================================================
# ADMIN - DELETE QUESTIONS PAGE
# ============================================================

# ============================================================
# ADMIN - DELETE QUESTIONS
# ============================================================

@app.route("/admin/delete_questions", methods=["GET"])
def admin_delete_questions():

    # --------------------------------------------------------
    # CHECK ADMIN LOGIN
    # --------------------------------------------------------

    if "admin" not in session:
        return redirect(url_for("admin_login"))


    # --------------------------------------------------------
    # CONNECT DATABASE
    # --------------------------------------------------------

    conn = get_db_connection()
    cursor = conn.cursor()


    # --------------------------------------------------------
    # GET ALL QUESTIONS FROM DATABASE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            subject,
            section,
            level,
            question_type,
            topic,
            company,
            year,
            passage,
            question,
            option1,
            option2,
            option3,
            option4,
            answer,
            explanation,
            hint,
            created_at
        FROM questions
        ORDER BY subject ASC, level ASC, id DESC
    """)


    rows = cursor.fetchall()

    conn.close()


    # --------------------------------------------------------
    # GROUP QUESTIONS BY SUBJECT
    # --------------------------------------------------------

    subject_groups = {}


    for row in rows:

        subject = row["subject"]

        if subject not in subject_groups:

            subject_groups[subject] = []


        subject_groups[subject].append(row)


    # --------------------------------------------------------
    # TOTAL QUESTIONS
    # --------------------------------------------------------

    total_questions = len(rows)


    # --------------------------------------------------------
    # SEND TO HTML
    # --------------------------------------------------------

    return render_template(
        "admin_delete_questions.html",
        subject_groups=subject_groups,
        total_questions=total_questions
    )


# ============================================================
# ADMIN - DELETE ONE QUESTION
# ============================================================

@app.route(
    "/admin/delete_question/<int:question_id>",
    methods=["POST"]
)
def admin_delete_question(question_id):

    # --------------------------------------------------------
    # CHECK ADMIN LOGIN
    # --------------------------------------------------------

    if "admin" not in session:
        return redirect(url_for("admin_login"))


    try:

        # ----------------------------------------------------
        # CONNECT DATABASE
        # ----------------------------------------------------

        conn = get_db_connection()
        cursor = conn.cursor()


        # ----------------------------------------------------
        # CHECK QUESTION EXISTS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id, subject, question
            FROM questions
            WHERE id = ?
            """,
            (question_id,)
        )


        question = cursor.fetchone()


        if question is None:

            conn.close()

            flash(
                "Question not found.",
                "danger"
            )

            return redirect(
                url_for("admin_delete_questions")
            )


        # ----------------------------------------------------
        # DELETE QUESTION
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM questions
            WHERE id = ?
            """,
            (question_id,)
        )


        conn.commit()

        conn.close()


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        flash(
            "Question deleted successfully!",
            "success"
        )


    except Exception as e:

        print()
        print("========================================")
        print("DELETE QUESTION ERROR")
        print("========================================")
        print(e)
        print("========================================")
        print()


        flash(
            "Error deleting question.",
            "danger"
        )


    # --------------------------------------------------------
    # BACK TO DELETE PAGE
    # --------------------------------------------------------

    return redirect(
        url_for("admin_delete_questions")
    )
@app.route('/admin/results')
def admin_results():

    if 'admin' not in session:

        return redirect(
            url_for('admin_login')
        )

    conn = get_db_connection()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            subject,
            level,
            total,
            correct,
            wrong,
            skipped,
            accuracy,
            performance_score,
            created_at
        FROM quiz_history
        ORDER BY id DESC
    """)

    history = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_results.html",
        history=history
    )


# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route('/admin_dashboard')
def admin_dashboard():

    if 'admin' not in session:

        return redirect(
            url_for('admin_login')
        )

    conn = sqlite3.connect(
        "database/quiz.db"
    )

    cursor = conn.cursor()

    # --------------------------
    # TOTAL USERS
    # --------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    # --------------------------
    # TOTAL QUESTIONS
    # --------------------------

    try:

        cursor.execute(
            "SELECT COUNT(*) FROM questions"
        )

        total_questions = cursor.fetchone()[0]

    except:

        total_questions = 0

    # --------------------------
    # TOTAL RESULTS
    # --------------------------

    try:

        cursor.execute(
            "SELECT COUNT(*) FROM results"
        )

        total_results = cursor.fetchone()[0]

    except:

        total_results = 0

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_questions=total_questions,
        total_results=total_results
    )


# ==========================
# ADMIN LOGOUT
# ==========================

@app.route('/admin_logout')
def admin_logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for('admin_login')
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route(
    "/forgot_password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        conn = sqlite3.connect(
            "database/quiz.db"
        )

        conn.row_factory = sqlite3.Row

        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cur.fetchone()

        conn.close()

        if not user:

            return render_template(
                "forgot_password.html",
                error="Email not found!"
            )

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        session["otp"] = otp

        session["reset_email"] = email

        msg = Message(
            "Quiz Master Password Reset OTP",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = f"""
Hello,

Your OTP for resetting your password is:

{otp}

This OTP is valid for 10 minutes.

Quiz Master
"""

        mail.send(msg)

        return redirect(
            url_for("verify_otp")
        )

    return render_template(
        "forgot_password.html"
    )


# ============================================================
# VERIFY OTP
# ============================================================

@app.route(
    "/verify_otp",
    methods=["GET", "POST"]
)
def verify_otp():

    if request.method == "POST":

        entered_otp = request.form["otp"]

        if entered_otp == session.get("otp"):

            return redirect(
                url_for("reset_password")
            )

        return render_template(
            "verify_otp.html",
            error="Invalid OTP!"
        )

    return render_template(
        "verify_otp.html"
    )


# ============================================================
# RESET PASSWORD
# ============================================================

@app.route(
    "/reset_password",
    methods=["GET", "POST"]
)
def reset_password():

    if request.method == "POST":

        password = request.form["password"]

        confirm = request.form[
            "confirm_password"
        ]

        if password != confirm:

            return render_template(
                "reset_password.html",
                error="Passwords do not match!"
            )

        email = session.get(
            "reset_email"
        )

        conn = sqlite3.connect(
            "database/quiz.db"
        )

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET password=?
            WHERE email=?
            """,
            (
                password,
                email
            )
        )

        conn.commit()

        conn.close()

        session.pop(
            "otp",
            None
        )

        session.pop(
            "reset_email",
            None
        )

        flash(
            "Password changed successfully! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset_password.html"
    )


# ============================================================
# ADMIN
# ============================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin():

    if request.method == "POST":

        username = request.form[
            "username"
        ]

        password = request.form[
            "password"
        ]

        if (
            username == "admin"
            and password == "admin123"
        ):

            return redirect(
                url_for("admin_dashboard")
            )

        return render_template(
            "admin_login.html",
            error="Invalid Login"
        )

    return render_template(
        "admin_login.html"
    )


    # ---------------------------------------------------------
    # CHECK ADMIN LOGIN
    # ---------------------------------------------------------
    if "admin" not in session:
        return redirect(url_for("login"))

    # ---------------------------------------------------------
    # OPTIONAL ADMIN CHECK
    # ---------------------------------------------------------
    # If your project already has an admin check, you can
    # replace this part with your existing admin logic.

    if request.method == "POST":

        # -----------------------------------------------------
        # GET FORM DATA
        # -----------------------------------------------------

        subject = request.form.get("subject", "").strip()
        level = request.form.get("level", "").strip()
        section = request.form.get("section", "").strip()

        question_type = request.form.get(
            "question_type", ""
        ).strip()

        company = request.form.get(
            "company", ""
        ).strip()

        year = request.form.get(
            "year", ""
        ).strip()

        topic = request.form.get(
            "topic", ""
        ).strip()

        question = request.form.get(
            "question", ""
        ).strip()

        passage = request.form.get(
            "passage", ""
        ).strip()

        option1 = request.form.get(
            "option1", ""
        ).strip()

        option2 = request.form.get(
            "option2", ""
        ).strip()

        option3 = request.form.get(
            "option3", ""
        ).strip()

        option4 = request.form.get(
            "option4", ""
        ).strip()

        answer = request.form.get(
            "answer", ""
        ).strip()

        explanation = request.form.get(
            "explanation", ""
        ).strip()

        hint = request.form.get(
            "hint", ""
        ).strip()


        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------

        if not subject:
            flash("Please select a subject.", "danger")
            return redirect(url_for("admin_questions"))

        if not level:
            flash("Please select a level.", "danger")
            return redirect(url_for("admin_questions"))

        if not question:
            flash("Please enter a question.", "danger")
            return redirect(url_for("admin_questions"))

        if not question_type:
            flash("Please select a question type.", "danger")
            return redirect(url_for("admin_questions"))

        if not answer:
            flash("Please enter the correct answer.", "danger")
            return redirect(url_for("admin_questions"))


        # -----------------------------------------------------
        # CHECK SUBJECT
        # -----------------------------------------------------

        if subject not in quizzes:

            # Create subject if it doesn't already exist
            quizzes[subject] = {}


        # -----------------------------------------------------
        # PLACEMENT PREPARATION
        # -----------------------------------------------------

        if subject == "Placement Preparation":

            valid_sections = [
                "Aptitude",
                "Logical Reasoning",
                "Verbal Ability",
                "Passage"
            ]

            if section not in valid_sections:

                flash(
                    "Please select a valid Placement section.",
                    "danger"
                )

                return redirect(
                    url_for("admin_questions")
                )


            # Create section if it doesn't exist

            if section not in quizzes[subject]:

                quizzes[subject][section] = {}


            # Create level if it doesn't exist

            if level not in quizzes[subject][section]:

                quizzes[subject][section][level] = []


            question_list = quizzes[
                subject
            ][
                section
            ][
                level
            ]


        # -----------------------------------------------------
        # NORMAL SUBJECT
        # -----------------------------------------------------

        else:

            if level not in quizzes[subject]:

                quizzes[subject][level] = []


            question_list = quizzes[
                subject
            ][
                level
            ]


        # -----------------------------------------------------
        # CREATE OPTIONS
        # -----------------------------------------------------

        options = []

        if option1:
            options.append(option1)

        if option2:
            options.append(option2)

        if option3:
            options.append(option3)

        if option4:
            options.append(option4)


        # -----------------------------------------------------
        # CREATE QUESTION OBJECT
        # -----------------------------------------------------

        new_question = {

            "topic": topic,

            "company": company,

            "year": int(year) if year.isdigit() else "",

            "level": level,

            "type": question_type,

            "question": question,

            "options": options,

            "answer": answer,

            "explanation": explanation,

            "hint": hint
        }


        # -----------------------------------------------------
        # ADD PASSAGE ONLY IF PROVIDED
        # -----------------------------------------------------

        if passage:

            new_question["passage"] = passage


        # -----------------------------------------------------
        # ADD QUESTION
        # -----------------------------------------------------

        question_list.append(new_question)


        # -----------------------------------------------------
        # SUCCESS MESSAGE
        # -----------------------------------------------------

        flash(
            "Question added successfully!",
            "success"
        )

        return redirect(
            url_for("admin_questions")
        )


    # ---------------------------------------------------------
    # GET REQUEST
    # ---------------------------------------------------------

    return render_template(
        "admin_questions.html"
    )

# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    print()

    print("========================================")

    print("ONLINE QUIZ MASTER")

    print("========================================")

    print(
        "Mail sender:",
        app.config["MAIL_USERNAME"]
    )

    print("========================================")

    print()

    app.run(
        debug=True
    )

   
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
