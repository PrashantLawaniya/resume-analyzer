from flask import Flask, render_template, request, session, redirect, url_for
import os
import PyPDF2
import spacy
import re
import json
import random
from email.message import EmailMessage
import smtplib
import subprocess
import importlib.util
from werkzeug.utils import secure_filename

from auth import auth  # Import auth blueprint

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for login session

# Register the login/signup blueprint
app.register_blueprint(auth)

# Uploads folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load spaCy NLP model with auto-download if missing
if not importlib.util.find_spec("en_core_web_sm"):
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])

nlp = spacy.load("en_core_web_sm")

# Skill list
SKILLS = [
    "python", "java", "c++", "html", "css", "javascript", "sql", "flask",
    "django", "react", "node", "machine learning", "data analysis", "git",
    "github", "bootstrap", "excel", "vscode", "mongodb", "rest api"
]

def extract_skills(text):
    text = text.lower()
    return list(set([skill for skill in SKILLS if skill in text]))

def send_otp_email(to_email, otp):
    sender_email = 'your_email@gmail.com'  # Replace with your email
    sender_password = 'your_app_password'  # Use App Password

    msg = EmailMessage()
    msg['Subject'] = 'Your Verification OTP'
    msg['From'] = sender_email
    msg['To'] = to_email
    msg.set_content(f'Your OTP for email verification is: {otp}')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

@app.route('/')
def home():
    return redirect(url_for('auth.login'))  # Redirect to login page

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if 'resume' not in request.files or request.form.get('jd', '').strip() == '':
        return 'Resume or Job Description missing'

    file = request.files['resume']
    jd_text = request.form['jd']

    if file.filename == '':
        return 'No selected file'

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        text = ""
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        except Exception as e:
            return f'Error processing PDF: {e}'

        resume_text = re.sub(r'\s+', ' ', text).lower()
        jd_text = re.sub(r'\s+', ' ', jd_text).lower()

        doc = nlp(resume_text)
        entities = [(ent.label_, ent.text) for ent in doc.ents]

        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(jd_text)

        matched_skills = set(resume_skills) & set(jd_skills)
        total_jd_skills = len(set(jd_skills))
        match_percentage = round((len(matched_skills) / total_jd_skills) * 100, 2) if total_jd_skills else 0

        return render_template('result.html',
            match_percentage=match_percentage,
            matched_skills=matched_skills,
            resume_skills=resume_skills,
            jd_skills=jd_skills,
            entities=entities
        )

    return 'Only PDF files are allowed'

if __name__ == '__main__':
    app.run(debug=True)
