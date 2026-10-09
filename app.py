import os
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import (
    add_contact_message,
    add_donation,
    add_user,
    authenticate_user,
    get_admin_metrics,
    get_ai_verification_checks,
    get_campaign_by_id,
    get_campaigns,
    get_demo_case_metrics,
    get_hospital_tasks,
    get_recent_notifications,
    get_user_applications,
    get_user_by_email,
    get_user_by_id,
    init_db,
    save_application,
    seed_demo_data,
)

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.context_processor
def inject_globals():
    user = None
    if session.get("user_id"):
        user = get_user_by_id(session["user_id"])
    return {
        "current_user": user,
        "app_name": app.config["APP_NAME"],
        "year": datetime.now().year,
        "lang": request.args.get("lang", "en"),
    }


def require_login():
    if not session.get("user_id"):
        flash("Please log in to continue.", "error")
        return redirect(url_for("index"))
    return None


def role_required(*allowed_roles):
    def decorator(func):
        def wrapper(*args, **kwargs):
            redirect_result = require_login()
            if redirect_result is not None:
                return redirect_result
            user = get_user_by_id(session["user_id"])
            if user and user["role"] in allowed_roles:
                return func(*args, **kwargs)
            flash("You do not have access to this section.", "error")
            return redirect(url_for("dashboard"))

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = os.urandom(16).hex()
    return session["csrf_token"]


def validate_csrf(form_token):
    expected = session.get("csrf_token")
    return bool(expected) and form_token == expected


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html", csrf_token=ensure_csrf_token())


@app.route("/role-selection")
def role_selection():
    return render_template("role_selection.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        role = request.form.get("role") or "Patient"
        form_token = request.form.get("csrf_token")
        if not validate_csrf(form_token):
            flash("Session expired. Please try again.", "error")
            return redirect(url_for("index"))
        user = get_user_by_email(email)
        if user and user["role"] == role and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials for the selected role.", "error")
        return redirect(url_for("index"))
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        role = request.form.get("role") or "Patient"
        phone = (request.form.get("phone") or "").strip()
        organization = (request.form.get("organization") or "").strip()
        form_token = request.form.get("csrf_token")
        if not validate_csrf(form_token):
            flash("Session expired. Please try again.", "error")
            return redirect(url_for("register"))
        if not name or not email or not password or password != confirm_password:
            flash("All required fields must be completed and passwords must match.", "error")
            return redirect(url_for("register"))
        if "@" not in email:
            flash("Please enter a valid email format.", "error")
            return redirect(url_for("register"))
        if get_user_by_email(email):
            flash("An account with this email already exists.", "error")
            return redirect(url_for("register"))
        add_user(name, email, password, role, phone, organization)
        flash("Registration successful. Please sign in.", "success")
        return redirect(url_for("index"))
    return render_template("register.html", csrf_token=ensure_csrf_token())


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    redirect_result = require_login()
    if redirect_result is not None:
        return redirect_result
    user = get_user_by_id(session["user_id"])
    role = user["role"]
    if role == "Patient":
        return redirect(url_for("patient_dashboard"))
    if role == "Donor":
        return redirect(url_for("donor_dashboard"))
    if role == "Hospital":
        return redirect(url_for("hospital_dashboard"))
    if role == "Admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("index"))


@app.route("/patient-dashboard")
@role_required("Patient")
def patient_dashboard():
    user = get_user_by_id(session["user_id"])
    applications = get_user_applications(user["id"])
    notifications = get_recent_notifications(user["id"])
    return render_template(
        "patient_dashboard.html",
        user=user,
        applications=applications,
        notifications=notifications,
        status_steps=["Draft", "Submitted", "AI Verification", "Hospital Verification", "Approved", "Additional Information Required"],
    )


@app.route("/donor-dashboard")
@role_required("Donor")
def donor_dashboard():
    campaigns = get_campaigns({"verification_status": "Verified"})
    return render_template("donor_dashboard.html", campaigns=campaigns)


@app.route("/hospital-dashboard")
@role_required("Hospital")
def hospital_dashboard():
    tasks = get_hospital_tasks()
    return render_template("hospital_dashboard.html", tasks=tasks)


@app.route("/admin-dashboard")
@role_required("Admin")
def admin_dashboard():
    metrics = get_admin_metrics()
    return render_template(
        "admin_dashboard.html",
        metrics=metrics,
        risk_alerts=[
            {"title": "Possible duplicate document", "severity": "Medium"},
            {"title": "Treatment cost mismatch", "severity": "High"},
            {"title": "Possible duplicate campaign", "severity": "High"},
        ],
    )


@app.route("/fundraiser-form", methods=["GET", "POST"])
@role_required("Patient")
def fundraiser_form():
    if request.method == "POST":
        form_token = request.form.get("csrf_token")
        if not validate_csrf(form_token):
            flash("Session expired. Please try again.", "error")
            return redirect(url_for("fundraiser_form"))

        if not request.form.get("child_name"):
            flash("Please complete child details before submitting.", "error")
            return redirect(url_for("fundraiser_form"))

        total_cost = float(request.form.get("total_cost") or 0)
        insurance = float(request.form.get("insurance_contribution") or 0)
        family = float(request.form.get("family_contribution") or 0)
        government = float(request.form.get("government_assistance") or 0)
        other = float(request.form.get("other_assistance") or 0)
        amount_requested = total_cost - (insurance + family + government + other)

        if total_cost <= 0 or amount_requested < 0:
            flash("Total treatment cost and assistance values must produce a valid positive amount needed.", "error")
            return redirect(url_for("fundraiser_form"))

        documents = []
        for field_name in [
            "diagnosis_report",
            "doctor_prescription",
            "hospital_estimate",
            "medical_documents",
            "identity_documents",
        ]:
            uploaded = request.files.get(field_name)
            if uploaded and uploaded.filename:
                filename = secure_filename(uploaded.filename)
                allowed = {".pdf", ".png", ".jpg", ".jpeg"}
                if not any(filename.lower().endswith(ext) for ext in allowed):
                    flash("Only PDF, PNG, JPG, and JPEG uploads are allowed.", "error")
                    return redirect(url_for("fundraiser_form"))
                if uploaded.content_length and uploaded.content_length > app.config["MAX_CONTENT_LENGTH"]:
                    flash("Each uploaded file must be under 10MB.", "error")
                    return redirect(url_for("fundraiser_form"))
                unique_name = f"{os.urandom(8).hex()}_{filename}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                uploaded.save(save_path)
                documents.append(unique_name)

        save_application(
            session["user_id"],
            {
                "child_name": request.form.get("child_name"),
                "child_age": request.form.get("child_age"),
                "child_gender": request.form.get("child_gender"),
                "location": request.form.get("location"),
                "guardian_name": request.form.get("guardian_name"),
                "contact_info": request.form.get("contact_info"),
                "medical_condition": request.form.get("medical_condition"),
                "treatment_required": request.form.get("treatment_required"),
                "hospital_name": request.form.get("hospital_name"),
                "doctor_name": request.form.get("doctor_name"),
                "treatment_description": request.form.get("treatment_description"),
                "estimated_cost": request.form.get("estimated_treatment_cost"),
                "urgency": request.form.get("treatment_urgency"),
                "total_cost": total_cost,
                "insurance_contribution": insurance,
                "family_contribution": family,
                "government_assistance": government,
                "other_assistance": other,
                "amount_requested": amount_requested,
                "status": "Submitted",
                "documents": documents,
            },
        )
        flash("Fundraiser application submitted successfully. AI review has started.", "success")
        return redirect(url_for("ai_verification"))

    return render_template("fundraiser_form.html", csrf_token=ensure_csrf_token())


@app.route("/ai-verification")
@role_required("Patient")
def ai_verification():
    checks = get_ai_verification_checks()
    result = "No Major Issues Detected"
    warnings = sum(1 for item in checks if item["status"] == "warning")
    if warnings > 4:
        result = "High-Risk Indicators Detected"
    elif warnings > 1:
        result = "Additional Verification Required"
    return render_template("ai_verification.html", checks=checks, result=result)


@app.route("/find-children")
def find_children():
    filters = {
        "query": request.args.get("query", ""),
        "disease": request.args.get("disease", ""),
        "location": request.args.get("location", ""),
        "urgency": request.args.get("urgency", ""),
        "verification_status": request.args.get("verification_status", ""),
    }
    campaigns = get_campaigns(filters)
    return render_template("find_children.html", campaigns=campaigns, filters=filters)


@app.route("/campaign/<int:campaign_id>")
def campaign_detail(campaign_id):
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        flash("Campaign not found.", "error")
        return redirect(url_for("find_children"))
    milestones = [
        {"name": "Diagnosis", "required": 120000, "funded": 120000, "verified": True, "completed": True},
        {"name": "Treatment", "required": 220000, "funded": 180000, "verified": True, "completed": False},
        {"name": "Surgery / Procedure", "required": 400000, "funded": 220000, "verified": False, "completed": False},
        {"name": "Recovery", "required": 180000, "funded": 80000, "verified": True, "completed": False},
        {"name": "Follow-up", "required": 120000, "funded": 50000, "verified": False, "completed": False},
    ]
    metrics = get_demo_case_metrics()
    return render_template(
        "campaign_detail.html",
        campaign=campaign,
        milestones=milestones,
        metrics=metrics,
        badge_list=["AI Verified", "Hospital Verified", "Demo Data"],
        csrf_token=ensure_csrf_token(),
    )


@app.route("/donate/<int:campaign_id>", methods=["GET", "POST"])
def donate_campaign(campaign_id):
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        flash("Campaign not found.", "error")
        return redirect(url_for("find_children"))
    if request.method == "POST":
        amount = request.form.get("amount")
        if not amount:
            flash("Please choose or enter a donation amount.", "error")
            return redirect(url_for("campaign_detail", campaign_id=campaign_id))
        try:
            amount = float(amount)
        except ValueError:
            flash("Please enter a valid amount.", "error")
            return redirect(url_for("campaign_detail", campaign_id=campaign_id))
        if amount <= 0:
            flash("Donation amount must be positive.", "error")
            return redirect(url_for("campaign_detail", campaign_id=campaign_id))
        if not session.get("user_id"):
            flash("Please log in to make a demo donation.", "error")
            return redirect(url_for("index"))
        receipt = add_donation(campaign_id, session["user_id"], amount)
        flash(f"Demo donation of ₹{amount:,.0f} confirmed. Receipt {receipt}.", "success")
        return redirect(url_for("campaign_detail", campaign_id=campaign_id))
    return redirect(url_for("campaign_detail", campaign_id=campaign_id))


@app.route("/how-it-works")
def how_it_works():
    steps = [
        {"title": "Share child details", "description": "Guardians submit child details, documents and treatment needs."},
        {"title": "AI preliminary review", "description": "The platform checks for inconsistency, duplication and missing information."},
        {"title": "Hospital verification", "description": "Medical teams validate diagnosis, cost and treatment requirement."},
        {"title": "Campaign transparency", "description": "Fund tracking and milestones are shown publicly with demo figures."},
        {"title": "Community support", "description": "Donors can search, review and support verified campaigns."},
        {"title": "Milestone updates", "description": "Families and donors track treatment progress and fund utilization."},
    ]
    return render_template("how_it_works.html", steps=steps)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        form_token = request.form.get("csrf_token")
        if not validate_csrf(form_token):
            flash("Session expired. Please try again.", "error")
            return redirect(url_for("contact"))
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()
        if not name or not email or not subject or not message or "@" not in email:
            flash("Please complete all contact details with a valid email address.", "error")
            return redirect(url_for("contact"))
        add_contact_message(name, email, subject, message)
        flash("Your message has been recorded in the demo system.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", csrf_token=ensure_csrf_token())


@app.route("/notifications")
def notifications():
    redirect_result = require_login()
    if redirect_result is not None:
        return redirect_result
    user = get_user_by_id(session["user_id"])
    items = get_recent_notifications(user["id"])
    return render_template("notifications.html", notifications=items)


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    app.run(debug=True, host="0.0.0.0", port=5000)
