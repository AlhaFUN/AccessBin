# models.py (NEW VERSION)
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # This creates a "relationship" so you can easily get all files for a user
    files = db.relationship('File', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

# NEW TABLE FOR STORING FILE INFORMATION
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(300), nullable=False)
    stored_filename = db.Column(db.String(300), unique=True, nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # This is the "foreign key" that links a file to a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)