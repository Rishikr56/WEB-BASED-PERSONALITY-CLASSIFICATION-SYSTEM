import os
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, PersonalityResponse
import json
import pandas as pd
from Test import generate_chart

# Flask application setup
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abhishek%406206974833@localhost/personality_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables before the first request
@app.before_first_request
def create_tables():
    db.create_all()

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    questions = pd.read_csv('questions.csv').to_dict('records')  # Make sure this file exists
    return render_template('index.html', questions=questions)

# Submit route
@app.route('/submit', methods=['POST'])
@login_required
def submit():
    user_responses = {key: value for key, value in request.form.items()}
    user_responses_df = pd.DataFrame(user_responses, index=[0]).astype(int)

    personality_type, my_sums = generate_chart(user_responses_df)

    return render_template('results.html',
                           personality_type=personality_type,
                           labels=list(my_sums.columns[0:5]),
                           data=list(my_sums.values[0][0:5]))

# Admin route
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return "Unauthorized"
    all_results = PersonalityResponse.query.all()
    return render_template('admin.html', results=all_results)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ✅ Main app runner block (updated for deployment)
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
