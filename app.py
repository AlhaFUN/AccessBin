# app.py (FINAL VERSION)
import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, File
import click

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
app.config['INSTANCE_RELATIVE_CONFIG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Database & Login Manager Setup ---
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db.create_all()
    click.echo('Initialized the database.')

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

# NEW ROUTE: Displays the list of files for the logged-in user
@app.route('/my-files')
@login_required
def my_files():
    files = current_user.files
    return render_template('files.html', files=files)

# NEW ROUTE: Shows the dedicated download page for a file
@app.route('/download_page/<int:file_id>')
@login_required
def download_page(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You do not have permission to view this file.", "danger")
        return redirect(url_for('my_files'))
    return render_template('download.html', file=file)

# NEW ROUTE: This handles the actual file download action
@app.route('/download_file/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You do not have permission to download this file.", "danger")
        return redirect(url_for('my_files'))
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            file.stored_filename,
            as_attachment=True,
            download_name=file.original_filename # This tells the browser to use the original filename!
        )
    except FileNotFoundError:
        return "File not found on server.", 404

# --- Authentication & Upload Routes (Mostly the same) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('my_files'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400
        if file:
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            stored_filename = f"{uuid.uuid4()}{file_extension}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], stored_filename))
            new_file = File(original_filename=original_filename, stored_filename=stored_filename, owner=current_user)
            db.session.add(new_file)
            db.session.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, message=f'File "{original_filename}" uploaded successfully!')
            flash(f'File "{original_filename}" uploaded successfully!', 'success')
            return redirect(url_for('my_files'))
    return render_template('upload.html')

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
