import json
import os
import sqlite3
import uuid
from datetime import datetime

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")


def dict_factory(cursor, row):
    return {key: row[idx] for idx, key in enumerate([col[0] for col in cursor.description])}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT,
            organization TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            case_id TEXT NOT NULL UNIQUE,
            condition TEXT NOT NULL,
            story TEXT NOT NULL,
            location TEXT NOT NULL,
            hospital TEXT NOT NULL,
            doctor TEXT,
            amount_required REAL NOT NULL,
            amount_raised REAL NOT NULL DEFAULT 0,
            urgency TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            status TEXT NOT NULL,
            badges TEXT,
            image TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_name TEXT,
            child_age INTEGER,
            child_gender TEXT,
            location TEXT,
            guardian_name TEXT,
            contact_info TEXT,
            medical_condition TEXT,
            treatment_required TEXT,
            hospital_name TEXT,
            doctor_name TEXT,
            treatment_description TEXT,
            estimated_cost REAL,
            urgency TEXT,
            total_cost REAL,
            insurance_contribution REAL,
            family_contribution REAL,
            government_assistance REAL,
            other_assistance REAL,
            amount_requested REAL,
            status TEXT DEFAULT 'Draft',
            documents TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            donor_id INTEGER,
            amount REAL NOT NULL,
            receipt_number TEXT,
            status TEXT DEFAULT 'Confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def seed_demo_data():
    conn = get_db_connection()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        demo_users = [
            {
                "name": "Admin Demo",
                "email": "admin@demo.local",
                "password": "Admin@123",
                "role": "Admin",
                "phone": "+91 90000 00001",
                "organization": "Save Children’s Lives"
            },
            {
                "name": "Aarav Sharma",
                "email": "patient@demo.local",
                "password": "Patient@123",
                "role": "Patient",
                "phone": "+91 90000 00002",
                "organization": "Family Care"
            },
            {
                "name": "Priya Nair",
                "email": "donor@demo.local",
                "password": "Donor@123",
                "role": "Donor",
                "phone": "+91 90000 00003",
                "organization": "Kind Hearts"
            },
            {
                "name": "Dr. Meera Rao",
                "email": "hospital@demo.local",
                "password": "Hospital@123",
                "role": "Hospital",
                "phone": "+91 90000 00004",
                "organization": "Children Care Hospital"
            }
        ]
        for user in demo_users:
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, phone, organization) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user["name"],
                    user["email"],
                    generate_password_hash(user["password"]),
                    user["role"],
                    user["phone"],
                    user["organization"],
                ),
            )

    campaign_count = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
    if campaign_count == 0:
        default_campaigns = [
            {
                "name": "Aanya’s Brave Recovery",
                "case_id": "SCL-2024-001",
                "condition": "SMA Type 1",
                "story": "Aanya needs a life-saving treatment plan and continuous rehabilitation support after diagnosis.",
                "location": "Hyderabad",
                "hospital": "Global Children’s Hospital",
                "doctor": "Dr. Kiran Reddy",
                "amount_required": 980000,
                "amount_raised": 380000,
                "urgency": "Critical",
                "verification_status": "Verified",
                "status": "Active",
                "badges": json.dumps(["AI Verified", "Hospital Verified", "Demo Data"]),
                "image": "child.jpg"
            },
            {
                "name": "Rohan’s Cancer Journey",
                "case_id": "SCL-2024-002",
                "condition": "Childhood Cancer",
                "story": "Rohan's family is funding treatment, surgery, and long-term recovery support after diagnosis.",
                "location": "Bengaluru",
                "hospital": "Hope Oncology Centre",
                "doctor": "Dr. Neha Menon",
                "amount_required": 1700000,
                "amount_raised": 820000,
                "urgency": "High",
                "verification_status": "Verified",
                "status": "Active",
                "badges": json.dumps(["AI Verified", "Hospital Verified", "Demo Data"]),
                "image": "child.jpg"
            },
            {
                "name": "Sia’s Heart Transplant",
                "case_id": "SCL-2024-003",
                "condition": "Organ Transplant",
                "story": "Sia needs a transplant, pre-surgery care, and follow-up treatment at a specialist center.",
                "location": "Pune",
                "hospital": "Miracle Heart Institute",
                "doctor": "Dr. Arvind Kulkarni",
                "amount_required": 2200000,
                "amount_raised": 660000,
                "urgency": "Critical",
                "verification_status": "Pending Review",
                "status": "Active",
                "badges": json.dumps(["AI Review", "Hospital Pending", "Demo Data"]),
                "image": "child.jpg"
            },
            {
                "name": "Mira’s Surgery Recovery",
                "case_id": "SCL-2024-004",
                "condition": "Major Surgery",
                "story": "Mira needs surgery, post-operation recovery, and rehabilitation after a serious medical condition.",
                "location": "Chennai",
                "hospital": "Sankalp Child Centre",
                "doctor": "Dr. Kavya Iyer",
                "amount_required": 750000,
                "amount_raised": 210000,
                "urgency": "Moderate",
                "verification_status": "Verified",
                "status": "Active",
                "badges": json.dumps(["AI Verified", "Hospital Verified", "Demo Data"]),
                "image": "child.jpg"
            },
            {
                "name": "Vihaan’s Rare Disease Support",
                "case_id": "SCL-2024-005",
                "condition": "Rare Disease",
                "story": "Vihaan needs diagnostic evaluation, targeted medications, and additional life-support care.",
                "location": "Delhi",
                "hospital": "Lotus Children’s Medical Centre",
                "doctor": "Dr. Alok Sharma",
                "amount_required": 1300000,
                "amount_raised": 470000,
                "urgency": "High",
                "verification_status": "Additional Verification Required",
                "status": "Active",
                "badges": json.dumps(["AI Clarification", "Hospital Review", "Demo Data"]),
                "image": "child.jpg"
            },
            {
                "name": "Tara’s New Chance",
                "case_id": "SCL-2024-006",
                "condition": "SMA Type 2",
                "story": "Tara requires therapy, specialized equipment, and a long-term treatment package for mobility support.",
                "location": "Ahmedabad",
                "hospital": "Horizon Pediatric Hospital",
                "doctor": "Dr. Shreya Patel",
                "amount_required": 860000,
                "amount_raised": 430000,
                "urgency": "Moderate",
                "verification_status": "Verified",
                "status": "Active",
                "badges": json.dumps(["AI Verified", "Hospital Verified", "Demo Data"]),
                "image": "child.jpg"
            }
        ]
        for campaign in default_campaigns:
            conn.execute(
                """
                INSERT INTO campaigns (
                    name, case_id, condition, story, location, hospital, doctor,
                    amount_required, amount_raised, urgency, verification_status, status, badges, image
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign["name"],
                    campaign["case_id"],
                    campaign["condition"],
                    campaign["story"],
                    campaign["location"],
                    campaign["hospital"],
                    campaign["doctor"],
                    campaign["amount_required"],
                    campaign["amount_raised"],
                    campaign["urgency"],
                    campaign["verification_status"],
                    campaign["status"],
                    campaign["badges"],
                    campaign["image"],
                ),
            )

    notifications_count = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    if notifications_count == 0:
        demo_user = conn.execute("SELECT id FROM users WHERE email = ?", ("patient@demo.local",)).fetchone()
        if demo_user:
            conn.execute(
                "INSERT INTO notifications (user_id, title, message) VALUES (?, ?, ?)",
                (
                    demo_user[0],
                    "AI Verification Update",
                    "Your AI assessment completed with no major issues detected. Requesting hospital review.",
                ),
            )
            conn.execute(
                "INSERT INTO notifications (user_id, title, message) VALUES (?, ?, ?)",
                (
                    demo_user[0],
                    "Documents Received",
                    "All important medical documents were uploaded securely and stored privately.",
                ),
            )
    conn.commit()
    conn.close()


def add_user(name, email, password, role, phone=None, organization=None):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, phone, organization) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, generate_password_hash(password), role, phone, organization),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def authenticate_user(email, password, role):
    user = get_user_by_email(email)
    if not user:
        return None
    if user["role"] != role:
        return None
    return user if user and user["password_hash"] else None


def get_campaigns(filters=None):
    conn = get_db_connection()
    query = "SELECT * FROM campaigns WHERE 1=1"
    params = []
    if filters:
        if filters.get("disease"):
            query += " AND condition LIKE ?"
            params.append(f"%{filters['disease']}%")
        if filters.get("location"):
            query += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if filters.get("urgency"):
            query += " AND urgency = ?"
            params.append(filters["urgency"])
        if filters.get("verification_status"):
            query += " AND verification_status = ?"
            params.append(filters["verification_status"])
        if filters.get("query"):
            query += " AND (name LIKE ? OR condition LIKE ? OR location LIKE ? OR story LIKE ?)"
            search = f"%{filters['query']}%"
            params.extend([search, search, search, search])
    query += " ORDER BY created_at DESC"
    campaigns = conn.execute(query, params).fetchall()
    conn.close()
    normalized = []
    for item in campaigns:
        campaign = dict(item)
        badge_value = campaign.get("badges")
        try:
            campaign["badges_list"] = json.loads(badge_value) if badge_value else []
        except (TypeError, ValueError):
            campaign["badges_list"] = [badge_value] if badge_value else []
        normalized.append(campaign)
    return normalized


def get_campaign_by_id(campaign_id):
    conn = get_db_connection()
    campaign = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    conn.close()
    if not campaign:
        return None
    data = dict(campaign)
    badge_value = data.get("badges")
    try:
        data["badges_list"] = json.loads(badge_value) if badge_value else []
    except (TypeError, ValueError):
        data["badges_list"] = [badge_value] if badge_value else []
    return data


def save_application(user_id, data):
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO applications (
            user_id, child_name, child_age, child_gender, location, guardian_name, contact_info,
            medical_condition, treatment_required, hospital_name, doctor_name, treatment_description,
            estimated_cost, urgency, total_cost, insurance_contribution, family_contribution,
            government_assistance, other_assistance, amount_requested, status, documents
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data.get("child_name"),
            data.get("child_age"),
            data.get("child_gender"),
            data.get("location"),
            data.get("guardian_name"),
            data.get("contact_info"),
            data.get("medical_condition"),
            data.get("treatment_required"),
            data.get("hospital_name"),
            data.get("doctor_name"),
            data.get("treatment_description"),
            data.get("estimated_cost"),
            data.get("urgency"),
            data.get("total_cost"),
            data.get("insurance_contribution"),
            data.get("family_contribution"),
            data.get("government_assistance"),
            data.get("other_assistance"),
            data.get("amount_requested"),
            data.get("status", "Draft"),
            json.dumps(data.get("documents", [])),
        ),
    )
    conn.commit()
    conn.close()


def get_user_applications(user_id):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM applications WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(item) for item in rows]


def add_contact_message(name, email, subject, message):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)",
        (name, email, subject, message),
    )
    conn.commit()
    conn.close()


def add_donation(campaign_id, donor_id, amount):
    conn = get_db_connection()
    receipt = f"DEMO-{uuid.uuid4().hex[:8].upper()}"
    conn.execute(
        "INSERT INTO donations (campaign_id, donor_id, amount, receipt_number) VALUES (?, ?, ?, ?)",
        (campaign_id, donor_id, amount, receipt),
    )
    campaign = conn.execute("SELECT amount_raised, amount_required FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    if campaign:
        updated = float(campaign["amount_raised"]) + float(amount)
        remaining = max(float(campaign["amount_required"]) - updated, 0)
        conn.execute(
            "UPDATE campaigns SET amount_raised = ?, status = ? WHERE id = ?",
            (updated, "Active" if updated < float(campaign["amount_required"]) else "Funded", campaign_id),
        )
    conn.commit()
    conn.close()
    return receipt


def get_recent_notifications(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(item) for item in rows]


def get_admin_metrics():
    conn = get_db_connection()
    metrics = {
        "total_applications": conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
        "verified_cases": conn.execute("SELECT COUNT(*) FROM campaigns WHERE verification_status = 'Verified'").fetchone()[0],
        "pending_verification": conn.execute("SELECT COUNT(*) FROM campaigns WHERE verification_status IN ('Pending Review', 'Additional Verification Required')").fetchone()[0],
        "high_risk_alerts": 3,
        "total_demo_donations": conn.execute("SELECT SUM(amount) FROM donations").fetchone()[0] or 0,
        "active_campaigns": conn.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'Active'").fetchone()[0],
    }
    conn.close()
    return metrics


def get_ai_verification_checks():
    return [
        {"name": "Patient information consistency", "status": "pass"},
        {"name": "Age consistency", "status": "pass"},
        {"name": "Hospital consistency", "status": "pass"},
        {"name": "Doctor information consistency", "status": "warning"},
        {"name": "Treatment consistency", "status": "pass"},
        {"name": "Treatment cost consistency", "status": "warning"},
        {"name": "Date consistency", "status": "pass"},
        {"name": "Duplicate document detection", "status": "pass"},
        {"name": "Possible duplicate campaign detection", "status": "warning"},
        {"name": "Missing information", "status": "pass"},
        {"name": "Possible document alteration indicators", "status": "pass"},
        {"name": "Unusual application patterns", "status": "warning"},
    ]


def get_hospital_tasks():
    return [
        {
            "patient": "Aanya Sharma",
            "condition": "SMA Type 1",
            "status": "Identity Verified",
            "badges": ["Identity Verified", "Medical Documents Verified", "Hospital Verified", "Treatment Estimate Verified"],
        },
        {
            "patient": "Rohan Nair",
            "condition": "Childhood Cancer",
            "status": "Review in progress",
            "badges": ["Identity Verified", "Medical Documents Verified", "Hospital Verified"],
        },
    ]


def get_demo_case_metrics():
    conn = get_db_connection()
    totals = conn.execute("SELECT SUM(amount_required), SUM(amount_raised) FROM campaigns").fetchone()
    conn.close()
    total_required = float(totals[0] or 0)
    total_raised = float(totals[1] or 0)
    return {
        "total_required": total_required,
        "total_raised": total_raised,
        "remaining": max(total_required - total_raised, 0),
    }
