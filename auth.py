from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import os
import random
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

# --- Email OTP Sender ---
def send_otp_email(to_email, otp):
    sender_email = 'prashantlawaniya577@gmail.com'         # Replace with your email
    sender_password = 'phyo pifo ptal zwpj'         # Use Gmail App Password

    msg = EmailMessage()
    msg['Subject'] = 'Your Verification OTP'
    msg['From'] = sender_email
    msg['To'] = to_email
    msg.set_content(f'Your OTP for Resume Scorer signup is: {otp}')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

# --- Load/Save Users ---
def load_users():
    if not os.path.exists('users.json'):
        return []
    with open('users.json', 'r') as f:
        return json.load(f).get("users", [])

def save_user(new_user):
    users = load_users()
    users.append(new_user)
    with open('users.json', 'w') as f:
        json.dump({"users": users}, f, indent=4)

# --- Signup with OTP Step ---
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()

        if any(u['email'] == email for u in users):
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.signup'))

        # Generate OTP and store temp user in session
        otp = str(random.randint(100000, 999999))
        session['temp_user'] = {"email": email, "password": generate_password_hash(password)}
        session['otp'] = otp
        send_otp_email(email, otp)
        flash('OTP sent to your email.', 'success')
        return redirect(url_for('auth.verify'))

    return render_template('signup.html')

# --- OTP Verification Route ---
@auth.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            temp_user = session.get('temp_user')
            if temp_user:
                save_user(temp_user)
                session.pop('temp_user', None)
                session.pop('otp', None)
                flash('Email verified and account created. Please login.', 'success')
                return redirect(url_for('auth.login'))
        flash('Invalid OTP. Please try again.', 'error')
        return redirect(url_for('auth.verify'))

    return render_template('verify.html')

# --- Login ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        for u in users:
            if u['email'] == email and check_password_hash(u['password'], password):
                session['user'] = email
                return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

# --- Logout ---
@auth.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))
