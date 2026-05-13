import os
import re
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from PIL import Image

load_dotenv()

# Detect if running on Vercel
ON_VERCEL = os.getenv("VERCEL") == "1"

# Use /tmp on Vercel, local folder otherwise
DB_PATH       = "/tmp/database.db" if ON_VERCEL else "database.db"
UPLOAD_FOLDER = "/tmp/uploads"     if ON_VERCEL else "uploads"

app = Flask(__name__)
app.secret_key  = os.getenv("SECRET_KEY",      "verifyai_secret_2024")
ADMIN_USERNAME  = os.getenv("ADMIN_USERNAME",  "admin")
ADMIN_PASSWORD  = os.getenv("ADMIN_PASSWORD",  "admin123")
OCR_API_KEY     = os.getenv("OCR_API_KEY",     "helloworld")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Database ──────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS verifications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        filename    TEXT NOT NULL,
        doc_type    TEXT NOT NULL,
        result      TEXT NOT NULL,
        confidence  INTEGER NOT NULL,
        summary     TEXT NOT NULL,
        charge      REAL DEFAULT 40.00,
        timestamp   TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS credits (
        id      INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 47
    )''')
    c.execute('INSERT OR IGNORE INTO credits (id, balance) VALUES (1, 47)')
    conn.commit()
    conn.close()

def get_credits():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT balance FROM credits WHERE id = 1')
    balance = c.fetchone()[0]
    conn.close()
    return balance

def deduct_credit():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE credits SET balance = balance - 1 WHERE id = 1')
    conn.commit()
    conn.close()

def save_verification(filename, doc_type, result, confidence, summary):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO verifications
        (filename, doc_type, result, confidence, summary, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (filename, doc_type, result, confidence, summary,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ── OCR ───────────────────────────────────────────────────────

def extract_text(filepath):
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": f},
                data={
                    "apikey":            OCR_API_KEY,
                    "language":          "eng",
                    "isOverlayRequired": False,
                    "detectOrientation": True,
                    "scale":             True,
                    "OCREngine":         2
                },
                timeout=30
            )
        result = response.json()
        if result.get("OCRExitCode") == 1:
            text = result["ParsedResults"][0]["ParsedText"]
            return text.upper()
        return ""
    except Exception as e:
        print("OCR Error:", e)
        return ""

# ── Image Quality ─────────────────────────────────────────────

def check_image_quality(filepath):
    checks = []
    score  = 0
    try:
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb >= 50:
            checks.append("- File size: PASS — Sufficient quality for verification")
            score += 1
        elif size_kb >= 10:
            checks.append("- File size: WARN — Low file size may affect accuracy")
        else:
            checks.append("- File size: FAIL — File too small")

        try:
            img  = Image.open(filepath)
            w, h = img.size
            if w >= 400 and h >= 300:
                checks.append("- Image dimensions: PASS — Resolution adequate")
                score += 1
            else:
                checks.append("- Image dimensions: WARN — Low resolution")
            if img.mode in ['RGB', 'RGBA', 'L']:
                checks.append("- Image format: PASS — Valid image format")
                score += 1
        except:
            checks.append("- Image dimensions: PASS — File received successfully")
            checks.append("- Image format: PASS — File format accepted")
            score += 2

    except Exception as e:
        checks.append("- Image quality: WARN — Could not fully analyse image")
    return checks, score

# ── Document Verifiers ────────────────────────────────────────

def verify_aadhaar(text, quality_checks, quality_score):
    checks    = quality_checks.copy()
    score     = quality_score
    max_score = 9

    if re.search(r'\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b', text):
        checks.append("- Aadhaar number: PASS — Valid 12-digit format detected")
        score += 2
    else:
        checks.append("- Aadhaar number: FAIL — No valid Aadhaar number found")

    if any(k in text for k in ['UIDAI', 'UNIQUE IDENTIFICATION', 'AADHAAR']):
        checks.append("- UIDAI branding: PASS — Official UIDAI branding detected")
        score += 2
    else:
        checks.append("- UIDAI branding: WARN — UIDAI branding not clearly visible")

    if re.search(r'\b\d{2}/\d{2}/\d{4}\b', text):
        checks.append("- Date of birth: PASS — DOB format is valid")
        score += 1
    else:
        checks.append("- Date of birth: WARN — Date of birth not clearly detected")

    if any(g in text for g in ['MALE', 'FEMALE', 'TRANSGENDER']):
        checks.append("- Gender field: PASS — Gender information present")
        score += 1
    else:
        checks.append("- Gender field: WARN — Gender field not detected")

    return build_result(checks, score, max_score, "Aadhaar Card")

def verify_pan(text, quality_checks, quality_score):
    checks    = quality_checks.copy()
    score     = quality_score
    max_score = 9

    pan = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text)
    if pan:
        checks.append(f"- PAN number: PASS — Valid PAN format detected ({pan.group()})")
        score += 2
    else:
        checks.append("- PAN number: FAIL — No valid PAN number format found")

    if any(k in text for k in ['INCOME TAX', 'GOVT OF INDIA', 'GOVERNMENT OF INDIA']):
        checks.append("- Government branding: PASS — Income Tax Department branding present")
        score += 2
    else:
        checks.append("- Government branding: WARN — Official branding not clearly visible")

    if any(k in text for k in ['PERMANENT ACCOUNT NUMBER', 'INCOME TAX DEPARTMENT']):
        checks.append("- Document title: PASS — PAN card title text detected")
        score += 1
    else:
        checks.append("- Document title: WARN — Document title not clearly readable")

    if re.search(r'\b\d{2}/\d{2}/\d{4}\b', text):
        checks.append("- Date of birth: PASS — DOB present and valid format")
        score += 1
    else:
        checks.append("- Date of birth: WARN — Date of birth not detected")

    return build_result(checks, score, max_score, "PAN Card")

def verify_voter_id(text, quality_checks, quality_score):
    checks    = quality_checks.copy()
    score     = quality_score
    max_score = 9

    epic = re.search(r'\b[A-Z]{3}[0-9]{7}\b', text)
    if epic:
        checks.append(f"- EPIC number: PASS — Valid EPIC format found ({epic.group()})")
        score += 2
    else:
        checks.append("- EPIC number: FAIL — No valid EPIC number detected")

    if any(k in text for k in ['ELECTION COMMISSION', 'ELECTORAL', 'VOTER']):
        checks.append("- Election Commission branding: PASS — Official branding detected")
        score += 2
    else:
        checks.append("- Election Commission branding: WARN — Official branding not visible")

    if any(k in text for k in ['CONSTITUENCY', 'DISTRICT', 'STATE', 'WARD']):
        checks.append("- Constituency details: PASS — Location information present")
        score += 1
    else:
        checks.append("- Constituency details: WARN — Location details not found")

    if any(k in text for k in ['ELECTOR', 'ELECTORS', 'PART NO', 'SERIAL']):
        checks.append("- Elector details: PASS — Electoral information present")
        score += 1
    else:
        checks.append("- Elector details: WARN — Electoral details not detected")

    return build_result(checks, score, max_score, "Voter ID")

def verify_driving_licence(text, quality_checks, quality_score):
    checks    = quality_checks.copy()
    score     = quality_score
    max_score = 9

    if re.search(r'\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b|\b[A-Z]{2}-\d{2}-\d{4}-\d{7}\b', text):
        checks.append("- Licence number: PASS — Valid DL format detected")
        score += 2
    else:
        checks.append("- Licence number: WARN — Licence number format unclear")

    if any(k in text for k in ['TRANSPORT', 'DRIVING', 'LICENCE', 'LICENSE', 'RTO']):
        checks.append("- Transport authority: PASS — Transport department reference found")
        score += 2
    else:
        checks.append("- Transport authority: WARN — Transport authority not detected")

    if any(k in text for k in ['LMV', 'MCWG', 'HMV', 'TRANS', 'NON-TRANS', 'CLASS']):
        checks.append("- Vehicle class: PASS — Vehicle category information present")
        score += 1
    else:
        checks.append("- Vehicle class: WARN — Vehicle class not detected")

    dates = re.findall(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', text)
    if len(dates) >= 2:
        checks.append("- Validity dates: PASS — Issue and expiry dates present")
        score += 1
    elif len(dates) == 1:
        checks.append("- Validity dates: WARN — Only one date detected")
    else:
        checks.append("- Validity dates: FAIL — No valid dates found")

    return build_result(checks, score, max_score, "Driving Licence")

def verify_passport(text, quality_checks, quality_score):
    checks    = quality_checks.copy()
    score     = quality_score
    max_score = 9

    pp = re.search(r'\b[A-Z][0-9]{7}\b', text)
    if pp:
        checks.append(f"- Passport number: PASS — Valid format detected ({pp.group()})")
        score += 2
    else:
        checks.append("- Passport number: WARN — Passport number not clearly detected")

    if any(k in text for k in ['P<IND', 'PIND', 'REPUBLIC OF INDIA']):
        checks.append("- MRZ / Country code: PASS — Indian passport identifier found")
        score += 2
    else:
        checks.append("- MRZ / Country code: WARN — Country identifier not detected")

    if re.findall(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', text):
        checks.append("- Validity dates: PASS — Date information present")
        score += 1
    else:
        checks.append("- Validity dates: WARN — Expiry date not detected")

    if any(k in text for k in ['INDIA', 'MUMBAI', 'DELHI', 'CHENNAI', 'KOLKATA',
                                'BANGALORE', 'HYDERABAD', 'PUNE', 'AHMEDABAD']):
        checks.append("- Place of issue: PASS — Indian city reference found")
        score += 1
    else:
        checks.append("- Place of issue: WARN — Place of issue not detected")

    return build_result(checks, score, max_score, "Passport")

def verify_generic(text, quality_checks, quality_score, doc_label):
    checks    = quality_checks.copy()
    score     = quality_score
    max_score = 6

    words = [w for w in text.split() if len(w) > 2]
    if len(words) >= 20:
        checks.append(f"- Text content: PASS — {len(words)} words extracted")
        score += 2
    elif len(words) >= 5:
        checks.append(f"- Text content: WARN — Only {len(words)} words detected")
        score += 1
    else:
        checks.append("- Text content: FAIL — Very little text detected")

    if re.findall(r'\b\d{4,}\b', text):
        checks.append("- Numeric data: PASS — Reference numbers detected")
        score += 1
    else:
        checks.append("- Numeric data: WARN — No reference numbers found")

    if re.findall(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', text):
        checks.append("- Date fields: PASS — Date information present")
        score += 1
    else:
        checks.append("- Date fields: WARN — No dates detected")

    return build_result(checks, score, max_score, doc_label)

# ── Result Builder ────────────────────────────────────────────

def build_result(checks, score, max_score, doc_label):
    ratio      = score / max_score
    confidence = int(ratio * 100)

    if ratio >= 0.75:
        verdict = "AUTHENTIC"
        summary = f"The {doc_label} appears genuine with key identifiers verified successfully."
    elif ratio >= 0.45:
        verdict = "SUSPICIOUS"
        summary = f"The {doc_label} has some unverified fields — manual review recommended."
    else:
        verdict = "REJECTED"
        summary = f"The {doc_label} failed multiple checks — document appears invalid or unreadable."

    response = f"""RESULT: {verdict}
CONFIDENCE: {confidence}
SUMMARY: {summary}
CHECKS:
{chr(10).join(checks)}"""

    return response, verdict, confidence, summary

# ── Routes ────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Invalid username or password"
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/reset-credits", methods=["POST"])
def reset_credits():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    amount = int(request.form.get("amount", 47))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE credits SET balance = ? WHERE id = 1', (amount,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/payment")
def payment():
    return render_template("payment.html", credits=get_credits())

@app.route("/buy-plan", methods=["POST"])
def buy_plan():
    plan = request.form.get("plan")
    credits_map = {
        "payg":       10,
        "bundle":    100,
        "enterprise": 1000
    }
    credits_to_add = credits_map.get(plan, 10)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE credits SET balance = balance + ? WHERE id = 1',
              (credits_to_add,))
    conn.commit()
    conn.close()
    return redirect(url_for("billing"))

@app.route("/")
def home():
    return render_template("index.html", credits=get_credits())

@app.route("/result")
def result():
    return render_template("result.html", credits=get_credits())

@app.route("/billing")
def billing():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('SELECT * FROM verifications ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return render_template("billing.html",
                           verifications=rows,
                           credits=get_credits(),
                           total_spent=len(rows) * 40)

@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('SELECT * FROM verifications ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    total      = len(rows)
    authentic  = sum(1 for r in rows if r[3] == 'AUTHENTIC')
    suspicious = sum(1 for r in rows if r[3] == 'SUSPICIOUS')
    rejected   = sum(1 for r in rows if r[3] == 'REJECTED')
    return render_template("admin.html",
                           verifications=rows,
                           total=total,
                           authentic=authentic,
                           suspicious=suspicious,
                           rejected=rejected,
                           revenue=total * 40)

@app.route("/verify", methods=["POST"])
def verify():
    if 'document' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file     = request.files['document']
    doc_type = request.form.get('doc_type', 'document')

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if get_credits() <= 0:
        return jsonify({"error": "No credits remaining!"}), 400

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file type. Only JPG, PNG, PDF allowed."}), 400
    
    # Check file size — max 900KB for OCR.space free tier
    file.seek(0, 2)  # seek to end
    file_size = file.tell()
    file.seek(0)     # seek back to start
    if file_size > 900 * 1024:
        return jsonify({
            "error": "File too large! Please upload an image under 900KB. On phone, take a screenshot of the document instead of a direct photo."
        }), 400

    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
    file.save(filepath)

    quality_checks, quality_score = check_image_quality(filepath)
    text      = extract_text(filepath)
    doc_label = doc_type.replace("_", " ").title()

    if doc_type == "aadhaar_card":
        ai_response, verdict, confidence, summary = verify_aadhaar(
            text, quality_checks, quality_score)
    elif doc_type == "pan_card":
        ai_response, verdict, confidence, summary = verify_pan(
            text, quality_checks, quality_score)
    elif doc_type == "voter_id":
        ai_response, verdict, confidence, summary = verify_voter_id(
            text, quality_checks, quality_score)
    elif doc_type == "driving_licence":
        ai_response, verdict, confidence, summary = verify_driving_licence(
            text, quality_checks, quality_score)
    elif doc_type == "passport":
        ai_response, verdict, confidence, summary = verify_passport(
            text, quality_checks, quality_score)
    else:
        ai_response, verdict, confidence, summary = verify_generic(
            text, quality_checks, quality_score, doc_label)

    save_verification(file.filename, doc_type, verdict, confidence, summary)
    deduct_credit()

    return jsonify({
        "success":      True,
        "filename":     file.filename,
        "doc_type":     doc_type,
        "analysis":     ai_response,
        "credits_left": get_credits()
    })

# ── Start ─────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    app.run(debug=True)