"""
app.py
------
Flask web app for Smart Waste Classification (with user accounts).

Routes
  /                 - form to enter waste features        (login required)
  /predict          - POST: run the 4 models + vote       (login required)
  /history          - the logged-in user's past results   (login required)
  /compare          - model comparison page               (public)
  /signup /login /logout
  /admin            - totals + charts                     (admin only)
  /admin/export.csv - download all predictions as CSV     (admin only)
  /feedback         - POST: submit feedback on prediction (login required)
"""
import csv
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import sys
from collections import Counter
from functools import wraps
from urllib.parse import urlparse
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from flask import (Flask, Response, abort, flash, g, jsonify, redirect,
                    render_template, request, session, url_for)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import db
from disposal_guide import DISPOSAL_GUIDE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Render / deployment compatibility: some repos keep model files at project root.
if not os.path.isdir(MODEL_DIR):
    root_model_files = [
        os.path.join(BASE_DIR, "model_comparison.json"),
        os.path.join(BASE_DIR, "decision_tree.joblib"),
        os.path.join(BASE_DIR, "random_forest.joblib"),
        os.path.join(BASE_DIR, "svm.joblib"),
        os.path.join(BASE_DIR, "naive_bayes.joblib"),
    ]
    if any(os.path.exists(path) for path in root_model_files):
        MODEL_DIR = BASE_DIR
    else:
        os.makedirs(MODEL_DIR, exist_ok=True)

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_secret_key():
    """Use SECRET_KEY from the environment if set; otherwise create and reuse
    a random key stored in instance/secret_key (so logins survive restarts)."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    path = os.path.join(INSTANCE_DIR, "secret_key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app = Flask(__name__)
app.config.update(
    SECRET_KEY=get_secret_key(),
    DATABASE=os.environ.get("DATABASE_PATH", os.path.join(INSTANCE_DIR, "waste.db")),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Set SESSION_COOKIE_SECURE=1 once you deploy on HTTPS
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE") == "1",
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB max file size
)
db.init_app(app)

# Rate limiting configuration
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Use redis:// in production for distributed systems
    strategy="fixed-window",
)

# Confidence threshold for "uncertain" predictions
CONFIDENCE_THRESHOLD = 0.65  # If max probability < 65%, flag as uncertain

# Allowed values for each form field (dropdowns + validation)
OPTIONS = {
    "material_type": ["plastic", "paper", "cardboard", "glass", "metal",
                      "food", "vegetable", "textile", "e-waste", "other"],
    "wet_or_dry": ["wet", "dry"],
    "texture": ["soft", "hard", "smooth", "rough", "flexible"],
    "biodegradable": ["yes", "no"],
}
FEATURES = list(OPTIONS)
MODEL_NAMES = ["Decision Tree", "Random Forest", "SVM", "Naive Bayes"]
CATEGORIES = list(DISPOSAL_GUIDE)


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
def get_model_paths():
    """Return the expected model and metadata file paths."""
    return {
        "metrics": os.path.join(MODEL_DIR, "model_comparison.json"),
        "models": {
            name: os.path.join(MODEL_DIR, name.lower().replace(" ", "_") + ".joblib")
            for name in MODEL_NAMES
        },
    }


def load_metrics():
    """Load model comparison metrics without crashing if missing."""
    path = get_model_paths()["metrics"]
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Could not read model comparison data: %s", e)
    logger.warning("Model comparison metadata not found at %s. Using empty metrics.", path)
    return {}


def load_models():
    """Load all trained models with validation."""
    models = {}
    logger.info("Loading ML models from %s...", MODEL_DIR)
    for name, path in get_model_paths()["models"].items():
        if not os.path.exists(path):
            logger.error(f"Model not found: {path}")
            raise FileNotFoundError(
                f"{path} not found. Run 'python generate_data.py' and 'python train.py' first."
            )
        try:
            models[name] = joblib.load(path)
            logger.info(f"✓ Loaded {name}")
        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")
            raise
    return models


def validate_models():
    """Health check: ensure models can make predictions."""
    if not MODELS:
        return
    test_input = pd.DataFrame([{
        "material_type": "plastic",
        "wet_or_dry": "dry",
        "texture": "smooth",
        "biodegradable": "no"
    }], columns=FEATURES)

    for name, model in MODELS.items():
        try:
            model.predict(test_input)
            model.predict_proba(test_input)
            logger.info(f"✓ {name} health check passed")
        except Exception as e:
            logger.error(f"✗ {name} health check failed: {e}")
            raise


METRICS = load_metrics()
MODELS = {}

try:
    MODELS = load_models()
    validate_models()
    logger.info("All models validated successfully!")
except Exception as e:
    logger.critical(f"Model validation failed: {e}")
    if os.environ.get("FLASK_DEBUG") == "1":
        raise


def ensure_models_ready():
    """Initialize models on first use if they were not available at startup."""
    global MODELS, METRICS
    if MODELS:
        return True
    try:
        MODELS = load_models()
        validate_models()
        METRICS = load_metrics()
        logger.info("Models loaded lazily after startup failure.")
        return True
    except Exception as e:
        logger.critical("Lazy model load failed: %s", e)
        return False


def get_confidence_score(model_predictions_proba):
    """
    Calculate overall confidence based on model agreement.
    Returns: (confidence_score, is_uncertain)
    """
    # Get the predicted class for each model
    predictions = [pred.argmax() for pred in model_predictions_proba.values()]

    # Count agreement
    counter = Counter(predictions)
    most_common_count = counter.most_common(1)[0][1]
    agreement_ratio = most_common_count / len(predictions)

    # Get average max probability across models
    avg_max_prob = np.mean([pred.max() for pred in model_predictions_proba.values()])

    # Combined confidence: weight both agreement and individual model confidence
    confidence = (agreement_ratio * 0.6) + (avg_max_prob * 0.4)
    is_uncertain = confidence < CONFIDENCE_THRESHOLD

    return round(confidence * 100, 2), is_uncertain


def majority_vote(predictions):
    """Most common prediction wins; ties go to the most accurate model."""
    counts = Counter(predictions.values())
    top = max(counts.values())
    tied = [label for label, c in counts.items() if c == top]
    if len(tied) == 1:
        return tied[0], top
    best = max(predictions, key=lambda m: METRICS.get(m, {}).get("accuracy", 0) if predictions[m] in tied else -1)
    return predictions[best], top


def detect_suspicious_input(values):
    """
    Detect logically impossible or suspicious combinations.
    Returns: (is_suspicious, warning_message)
    """
    warnings = []

    # Food that's non-biodegradable is suspicious
    if values["material_type"] in ["food", "vegetable"] and values["biodegradable"] == "no":
        warnings.append("⚠️ Food/vegetable waste is typically biodegradable.")

    # Hard + wet combination is unusual
    if values["texture"] == "hard" and values["wet_or_dry"] == "wet":
        warnings.append("⚠️ Hard + wet combination is unusual.")

    # E-waste being biodegradable is impossible
    if values["material_type"] == "e-waste" and values["biodegradable"] == "yes":
        warnings.append("⚠️ E-waste cannot be biodegradable.")

    # Metal/glass being biodegradable is impossible
    if values["material_type"] in ["metal", "glass"] and values["biodegradable"] == "yes":
        warnings.append("⚠️ Metal/glass cannot be biodegradable.")

    return len(warnings) > 0, warnings


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_and_process_image(filepath, max_size=(1024, 1024)):
    """
    Validate uploaded image and optimize it.
    Returns True if valid, False otherwise.
    """
    try:
        from PIL import Image

        # Open and verify image
        img = Image.open(filepath)
        img.verify()  # Check if it's a valid image

        # Re-open after verify (verify() closes the file)
        img = Image.open(filepath)

        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Resize if too large (saves disk space)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save optimized version
        img.save(filepath, optimize=True, quality=85)

        logger.info(f"Image validated and optimized: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Invalid image file: {e}")
        # Delete invalid file
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


# ----------------------------------------------------------------------------
# Auth helpers
# ----------------------------------------------------------------------------
@app.before_request
def load_user_and_check_csrf():
    g.user = None
    uid = session.get("user_id")
    if uid is not None:
        g.user = db.get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if g.user is None:
            session.clear()

    # CSRF protection for every POST
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, "Invalid or missing CSRF token. Please go back and try again.")


@app.context_processor
def inject_globals():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return {"csrf_token": session["csrf_token"], "current_user": g.get("user")}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.path))
        if not g.user["is_admin"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def safe_next(target):
    """Only allow redirects to paths on this site (prevents open redirects)."""
    if target and target.startswith("/") and not target.startswith("//") \
            and not urlparse(target).netloc:
        return target
    return url_for("index")


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.route("/health")
def health():
    """Simple health check for Render and deployment monitoring."""
    status = {
        "ok": True,
        "models_loaded": bool(MODELS),
        "metrics_loaded": bool(METRICS),
        "database_ok": True,
    }
    try:
        db.get_db().execute("SELECT 1").fetchone()
    except Exception as e:
        status["database_ok"] = False
        status["ok"] = False
        status["database_error"] = str(e)
    return jsonify(status)


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per hour")  # Prevent signup spam
def signup():
    if g.user:
        return redirect(url_for("index"))
    form = {"username": "", "email": ""}
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        form = {"username": username, "email": email}

        error = None
        if not USERNAME_RE.match(username):
            error = "Username must be 3-30 characters: letters, numbers, _ . -"
        elif not EMAIL_RE.match(email) or len(email) > 120:
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."

        if error is None:
            try:
                cur = db.get_db().execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password)),
                )
                db.get_db().commit()
            except sqlite3.IntegrityError:
                error = "That username or email is already registered."
            else:
                session.clear()
                session["user_id"] = cur.lastrowid
                flash("Account created. Welcome!", "success")
                return redirect(url_for("index"))
        flash(error, "danger")
    return render_template("signup.html", form=form), (400 if request.method == "POST" else 200)


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # Prevent brute force
def login():
    if g.user:
        return redirect(url_for("index"))
    if request.method == "POST":
        ident = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = db.get_db().execute(
            "SELECT * FROM users WHERE username = ? OR email = ?", (ident, ident)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(safe_next(request.args.get("next")))
        flash("Incorrect username/email or password.", "danger")
        return render_template("login.html"), 401
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ----------------------------------------------------------------------------
# Classifier pages
# ----------------------------------------------------------------------------
def validate(form):
    values = {}
    for field, allowed in OPTIONS.items():
        value = (form.get(field) or "").strip().lower()
        if not value:
            return None, f"Please select a value for '{field.replace('_', ' ')}'."
        if value not in allowed:
            return None, f"'{value}' is not a valid option for '{field.replace('_', ' ')}'."
        values[field] = value
    return values, None


@app.route("/")
@login_required
def index():
    if not ensure_models_ready():
        return "ML models are unavailable. Please try again later.", 503
    return render_template("index.html", options=OPTIONS, error=None, selected={}, supports_image=True)


@app.route("/predict", methods=["POST"])
@login_required
@limiter.limit("30 per minute")  # Prevent prediction spam
def predict():
    if not ensure_models_ready():
        return "ML models are unavailable. Please try again later.", 503

    # Handle image upload
    image_filename = None
    if 'waste_image' in request.files:
        file = request.files['waste_image']
        if file and file.filename and allowed_file(file.filename):
            # Generate secure filename with UUID to prevent collisions
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_filename = secure_filename(file.filename)[:50]  # Limit length
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{g.user['id']}_{timestamp}_{unique_id}_{original_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save temporarily
            file.save(filepath)

            # Validate and optimize image
            if validate_and_process_image(filepath):
                image_filename = filename
                logger.info(f"Image uploaded and validated: {filename} by user {g.user['username']}")
            else:
                flash("Invalid image file. Please upload a valid image.", "danger")
                return render_template("index.html", options=OPTIONS, error="Invalid image file",
                                     selected=request.form, supports_image=True), 400

    values, error = validate(request.form)
    if error:
        return render_template("index.html", options=OPTIONS, error=error,
                               selected=request.form, supports_image=True), 400

    # Check for suspicious input combinations
    is_suspicious, warnings = detect_suspicious_input(values)

    row = pd.DataFrame([values], columns=FEATURES)

    # Get predictions with probabilities
    predictions = {}
    predictions_proba = {}

    for name, model in MODELS.items():
        pred = str(model.predict(row)[0])
        predictions[name] = pred

        # Get probability distribution
        try:
            proba = model.predict_proba(row)[0]
            predictions_proba[name] = proba
        except AttributeError:
            # Some models might not support predict_proba
            logger.warning(f"{name} does not support predict_proba")
            predictions_proba[name] = np.array([1.0 if predictions[name] == cat else 0.0
                                              for cat in CATEGORIES])

    final, votes = majority_vote(predictions)
    confidence, is_uncertain = get_confidence_score(predictions_proba)

    # Save this prediction with confidence score and image
    conn = db.get_db()
    cursor = conn.execute(
        """INSERT INTO predictions
           (user_id, material_type, wet_or_dry, texture, biodegradable, final_category,
            decision_tree, random_forest, svm, naive_bayes, confidence, is_uncertain, image_filename)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (g.user["id"], values["material_type"], values["wet_or_dry"], values["texture"],
         values["biodegradable"], final, predictions["Decision Tree"],
         predictions["Random Forest"], predictions["SVM"], predictions["Naive Bayes"],
         confidence, 1 if is_uncertain else 0, image_filename),
    )
    prediction_id = cursor.lastrowid
    conn.commit()

    logger.info(f"Prediction {prediction_id} by user {g.user['username']}: {final} (confidence: {confidence}%)")

    return render_template(
        "result.html", inputs=values, predictions=predictions, final=final,
        votes=votes, total=len(predictions), guide=DISPOSAL_GUIDE[final],
        guides=DISPOSAL_GUIDE, confidence=confidence, is_uncertain=is_uncertain,
        is_suspicious=is_suspicious, warnings=warnings, prediction_id=prediction_id,
        image_filename=image_filename,
    )


@app.route("/history")
@login_required
def history():
    rows = db.get_db().execute(
        "SELECT * FROM predictions WHERE user_id = ? ORDER BY id DESC LIMIT 200",
        (g.user["id"],),
    ).fetchall()
    return render_template("history.html", rows=rows, guides=DISPOSAL_GUIDE)


@app.route("/feedback", methods=["POST"])
@login_required
@limiter.limit("50 per hour")
def submit_feedback():
    """Submit feedback on a prediction."""
    try:
        prediction_id = int(request.form.get("prediction_id"))
        is_correct = int(request.form.get("is_correct", 0))
        actual_category = request.form.get("actual_category", "").strip()
        comment = request.form.get("comment", "").strip()[:500]  # Limit comment length

        conn = db.get_db()

        # Verify prediction belongs to this user or user is admin
        pred = conn.execute(
            "SELECT user_id FROM predictions WHERE id = ?", (prediction_id,)
        ).fetchone()

        if not pred:
            return jsonify({"success": False, "error": "Prediction not found"}), 404

        if pred["user_id"] != g.user["id"] and not g.user["is_admin"]:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        # Check if feedback already exists
        existing = conn.execute(
            "SELECT id FROM feedback WHERE prediction_id = ? AND user_id = ?",
            (prediction_id, g.user["id"])
        ).fetchone()

        if existing:
            return jsonify({"success": False, "error": "Feedback already submitted"}), 400

        # Insert feedback
        conn.execute(
            """INSERT INTO feedback (prediction_id, user_id, is_correct, actual_category, comment)
               VALUES (?, ?, ?, ?, ?)""",
            (prediction_id, g.user["id"], is_correct, actual_category or None, comment or None)
        )
        conn.commit()

        logger.info(f"Feedback submitted for prediction {prediction_id} by user {g.user['username']}")
        return jsonify({"success": True, "message": "Thank you for your feedback!"})

    except ValueError:
        return jsonify({"success": False, "error": "Invalid input"}), 400
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500


@app.route("/compare")
def compare():
    """Model comparison page with advanced metrics and visualizations."""
    if not ensure_models_ready():
        return "Model comparison is unavailable because the ML models failed to load.", 503

    # Load evaluation report if available
    report_path = os.path.join(MODEL_DIR, "evaluation_report.json")
    evaluation_report = None

    if os.path.exists(report_path):
        try:
            with open(report_path) as f:
                evaluation_report = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load evaluation report: {e}")

    # Check for available plots
    plots_dir = os.path.join(MODEL_DIR, "plots")
    available_plots = []

    if os.path.exists(plots_dir):
        plot_files = [
            'model_comparison.png',
            'cv_comparison.png',
            'decision_tree_confusion.png',
            'random_forest_confusion.png',
            'svm_confusion.png',
            'naive_bayes_confusion.png',
            'decision_tree_learning_curve.png',
            'random_forest_learning_curve.png',
            'decision_tree_importance.png',
            'random_forest_importance.png',
        ]

        for plot in plot_files:
            if os.path.exists(os.path.join(plots_dir, plot)):
                available_plots.append(plot)

    return render_template("compare.html",
                          metrics=METRICS,
                          evaluation_report=evaluation_report,
                          available_plots=available_plots)


# ----------------------------------------------------------------------------
# Admin
# ----------------------------------------------------------------------------
@app.route("/admin")
@admin_required
def admin():
    conn = db.get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    today_preds = conn.execute(
        "SELECT COUNT(*) FROM predictions WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    new_users_7d = conn.execute(
        "SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')"
    ).fetchone()[0]

    # Feedback statistics
    total_feedback = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    correct_feedback = conn.execute(
        "SELECT COUNT(*) FROM feedback WHERE is_correct = 1"
    ).fetchone()[0]
    incorrect_feedback = total_feedback - correct_feedback

    # Calculate real accuracy based on feedback
    real_accuracy = round((correct_feedback / total_feedback * 100), 2) if total_feedback > 0 else None

    # Uncertain predictions count
    uncertain_count = conn.execute(
        "SELECT COUNT(*) FROM predictions WHERE is_uncertain = 1"
    ).fetchone()[0]
    uncertain_pct = round((uncertain_count / total_preds * 100), 2) if total_preds > 0 else 0

    cat_counts = {r["final_category"]: r["n"] for r in conn.execute(
        "SELECT final_category, COUNT(*) AS n FROM predictions GROUP BY final_category")}
    categories = {c: cat_counts.get(c, 0) for c in CATEGORIES}

    daily = {r["d"]: r["n"] for r in conn.execute(
        """SELECT date(created_at) AS d, COUNT(*) AS n FROM predictions
           WHERE created_at >= datetime('now', '-13 days', 'start of day')
           GROUP BY d""")}
    days = [r[0] for r in conn.execute(
        "WITH RECURSIVE n(i) AS (SELECT 0 UNION ALL SELECT i+1 FROM n WHERE i < 13) "
        "SELECT date('now', '-' || (13 - i) || ' days') FROM n")]
    per_day = {"labels": days, "values": [daily.get(d, 0) for d in days]}

    # Get model-specific accuracy from feedback
    model_feedback = {}
    for model_name in MODEL_NAMES:
        col_name = model_name.lower().replace(" ", "_")
        query = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN f.is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM feedback f
            JOIN predictions p ON p.id = f.prediction_id
            WHERE p.{col_name} = p.final_category
        """
        result = conn.execute(query).fetchone()
        if result["total"] > 0:
            model_feedback[model_name] = {
                "total": result["total"],
                "accuracy": round((result["correct"] / result["total"] * 100), 2)
            }

    users = conn.execute(
        """SELECT u.id, u.username, u.email, u.is_admin, u.created_at,
                  COUNT(p.id) AS n_preds, MAX(p.created_at) AS last_active
           FROM users u LEFT JOIN predictions p ON p.user_id = u.id
           GROUP BY u.id ORDER BY u.id DESC LIMIT 100"""
    ).fetchall()

    # Recent feedback with details
    recent_feedback = conn.execute(
        """SELECT f.*, p.final_category, p.material_type, u.username, p.confidence
           FROM feedback f
           JOIN predictions p ON p.id = f.prediction_id
           JOIN users u ON u.id = f.user_id
           ORDER BY f.created_at DESC LIMIT 50"""
    ).fetchall()

    return render_template(
        "admin.html", total_users=total_users, total_preds=total_preds,
        today_preds=today_preds, new_users_7d=new_users_7d,
        categories=categories, per_day=per_day, users=users, guides=DISPOSAL_GUIDE,
        total_feedback=total_feedback, correct_feedback=correct_feedback,
        incorrect_feedback=incorrect_feedback, real_accuracy=real_accuracy,
        uncertain_count=uncertain_count, uncertain_pct=uncertain_pct,
        model_feedback=model_feedback, recent_feedback=recent_feedback,
    )


def csv_safe(value):
    """Stop spreadsheet formula injection: prefix risky cells with a quote."""
    s = str(value)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


@app.route("/admin/export.csv")
@admin_required
def export_csv():
    rows = db.get_db().execute(
        """SELECT p.id, p.created_at, u.username, u.email, p.material_type, p.wet_or_dry,
                  p.texture, p.biodegradable, p.final_category, p.decision_tree,
                  p.random_forest, p.svm, p.naive_bayes, p.confidence, p.is_uncertain,
                  f.is_correct, f.actual_category, f.comment
           FROM predictions p 
           JOIN users u ON u.id = p.user_id
           LEFT JOIN feedback f ON f.prediction_id = p.id
           ORDER BY p.id"""
    ).fetchall()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "created_at_utc", "username", "email", "material_type", "wet_or_dry",
                     "texture", "biodegradable", "final_category", "decision_tree",
                     "random_forest", "svm", "naive_bayes", "confidence", "is_uncertain",
                     "feedback_correct", "feedback_actual_category", "feedback_comment"])
    for r in rows:
        writer.writerow([csv_safe(v) for v in tuple(r)])

    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"},
    )


if __name__ == "__main__":
    # debug is OFF by default; run `FLASK_DEBUG=1 python app.py` while developing
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")


@app.route("/models/plots/<filename>")
def serve_plot(filename):
    """Serve plot images from models/plots directory."""
    from flask import send_from_directory
    plots_dir = os.path.join(MODEL_DIR, "plots")
    return send_from_directory(plots_dir, filename)
