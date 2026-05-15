# VerifyAI — AI-Based Document Verification System

VerifyAI is a Flask-based web application that simulates an AI-powered document verification platform.  
Users can upload documents, receive authenticity analysis results, track billing usage, and manage credits through an admin dashboard.

---

## Features

- Upload and verify documents
- AI-style authenticity analysis
- Multiple document type support
- Billing and credit system
- Admin dashboard with audit logs
- Transaction history
- Responsive UI
- Vercel deployment support

---

## Supported Documents

- Aadhaar Card
- PAN Card
- Voter ID
- Driving Licence
- Passport
- Bank Statement
- Salary Slip
- ITR
- Utility Bill
- Rent Agreement

---

## Tech Stack

- Python
- Flask
- HTML
- CSS
- JavaScript
- SQLite
- Vercel

---

## Project Structure

```bash
VerifyAI/
│
├── static/
│   ├── style.css
│   ├── script.js
│   └── result.js
│
├── templates/
│   ├── index.html
│   ├── result.html
│   ├── billing.html
│   ├── payment.html
│   ├── admin.html
│   └── admin_login.html
│
├── uploads/
├── app.py
├── requirements.txt
├── vercel.json
├── .gitignore
└── README.md
