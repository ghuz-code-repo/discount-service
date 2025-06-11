from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, default='')
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    def __repr__(self):
        return f'<User {self.login}>'
    
class DiscountObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mpp_discount = db.Column(db.Float, default=0.0)
    opt_discount = db.Column(db.Float, default=0.0)
    kd_discount = db.Column(db.Float, default=0.0)
    complex_id = db.Column(db.Integer, db.ForeignKey('complex.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('property_type.id'), nullable=False)
    payment_type_id = db.Column(db.Integer, db.ForeignKey('payment_type.id'), nullable=False)
    
class Complex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    def __repr__(self):
        return f'<Complex {self.name}>'
    
class PropertyType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    def __repr__(self):
        return f'<PropType {self.name}>'
    
class PaymentType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    def __repr__(self):
        return f'<PayType {self.name}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
