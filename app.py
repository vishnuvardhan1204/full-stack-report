from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object('config.Config')

# Ensure database directory exists
os.makedirs('database', exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    expense_type = db.Column(db.String(20), default='expense')  # 'income' or 'expense'
    date = db.Column(db.Date, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user=current_user).all()
    
    total_income = sum(e.amount for e in expenses if e.expense_type == 'income')
    total_expense = sum(e.amount for e in expenses if e.expense_type == 'expense')
    net_balance = total_income - total_expense
    
    # Category data for chart
    category_data = defaultdict(float)
    for e in expenses:
        if e.expense_type == 'expense':
            category_data[e.category] += e.amount
    
    labels = list(category_data.keys())
    values = list(category_data.values())
    
    return render_template('dashboard.html', 
                         expenses=expenses, 
                         total_income=total_income,
                         total_expense=total_expense,
                         net_balance=net_balance,
                         labels=labels, 
                         values=values)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        category = request.form['category']
        expense_type = request.form['expense_type']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        
        expense = Expense(title=title, amount=amount, category=category, 
                         expense_type=expense_type, date=date, user=current_user)
        db.session.add(expense)
        db.session.commit()
        flash(f'{expense_type.title()} added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html')

@app.route('/view')
@login_required
def view_expenses():
    expenses = Expense.query.filter_by(user=current_user).order_by(Expense.date.desc()).all()
    return render_template('view_expenses.html', expenses=expenses)

@app.route('/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user == current_user:
        db.session.delete(expense)
        db.session.commit()
        flash('Entry deleted successfully!', 'success')
    return redirect(url_for('view_expenses'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user != current_user:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        expense.title = request.form['title']
        expense.amount = float(request.form['amount'])
        expense.category = request.form['category']
        expense.expense_type = request.form['expense_type']
        expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        db.session.commit()
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('view_expenses'))
    
    return render_template('edit_expense.html', expense=expense)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)