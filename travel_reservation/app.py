# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    travel_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')
    
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    destination = db.relationship('Destination', backref=db.backref('bookings', lazy=True))

# Create tables
with app.app_context():
    db.create_all()
    
    # Add admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@luxtravel.com',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        
    # Add sample destinations if none exist
    if not Destination.query.first():
        sample_destinations = [
            Destination(
                name="Bali Paradise",
                description="Experience the ultimate tropical getaway with pristine beaches and luxury resorts.",
                image_url="https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
                price=1200,
                location="Bali, Indonesia",
                rating=4.8,
                featured=True
            ),
            Destination(
                name="Santorini Escape",
                description="Stay in iconic white-washed buildings with breathtaking views of the Aegean Sea.",
                image_url="https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80",
                price=1800,
                location="Santorini, Greece",
                rating=4.9,
                featured=True
            ),
            Destination(
                name="Swiss Alps Retreat",
                description="Luxury mountain cabins with stunning alpine views and world-class skiing.",
                image_url="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
                price=1600,
                location="Swiss Alps, Switzerland",
                rating=4.7,
                featured=False
            ),
            Destination(
                name="Tokyo Urban Experience",
                description="Immerse yourself in the vibrant culture and cutting-edge technology of Tokyo.",
                image_url="https://media.istockphoto.com/id/904453184/photo/composite-image-of-mt-fuji-and-tokyo-skyline.jpg?s=612x612&w=0&k=20&c=EAJrI5nVsDuIkiv7o3NY1LsaZHRCcOWUOvk2g9FfFD0=",
                price=1400,
                location="Tokyo, Japan",
                rating=4.6,
                featured=False
            )
        ]
        
        for dest in sample_destinations:
            db.session.add(dest)
        db.session.commit()

# Routes
@app.route('/')
def index():
    featured_destinations = Destination.query.filter_by(featured=True).all()
    all_destinations = Destination.query.all()
    return render_template('index.html', 
                         featured_destinations=featured_destinations,
                         all_destinations=all_destinations)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        destinations = Destination.query.filter(
            Destination.name.ilike(f'%{query}%') | 
            Destination.location.ilike(f'%{query}%')
        ).all()
    else:
        destinations = []
    
    return render_template('search.html', destinations=destinations, query=query)

@app.route('/booking/<int:destination_id>', methods=['GET', 'POST'])
def booking(destination_id):
    if 'user_id' not in session:
        flash('Please log in to make a booking', 'error')
        return redirect(url_for('login'))
    
    destination = Destination.query.get_or_404(destination_id)
    
    if request.method == 'POST':
        travel_date = request.form.get('travel_date')
        guests = int(request.form.get('guests'))
        
        # Calculate total price
        total_price = destination.price * guests
        
        # Create booking
        new_booking = Booking(
            user_id=session['user_id'],
            destination_id=destination_id,
            travel_date=datetime.strptime(travel_date, '%Y-%m-%d'),
            guests=guests,
            total_price=total_price
        )
        
        db.session.add(new_booking)
        db.session.commit()
        
        flash('Booking confirmed!', 'success')
        return redirect(url_for('my_bookings'))
    
    return render_template('booking.html', destination=destination)

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        flash('Please log in to view your bookings', 'error')
        return redirect(url_for('login'))
    
    user_bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_bookings.html', bookings=user_bookings)

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    total_users = User.query.count()
    total_destinations = Destination.query.count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_destinations=total_destinations,
                         total_bookings=total_bookings,
                         recent_bookings=recent_bookings)

@app.route('/admin/destinations')
def admin_destinations():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    destinations = Destination.query.all()
    return render_template('admin/destinations.html', destinations=destinations)

@app.route('/admin/add_destination', methods=['GET', 'POST'])
def add_destination():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        price = float(request.form.get('price'))
        location = request.form.get('location')
        rating = float(request.form.get('rating'))
        featured = True if request.form.get('featured') else False
        
        new_destination = Destination(
            name=name,
            description=description,
            image_url=image_url,
            price=price,
            location=location,
            rating=rating,
            featured=featured
        )
        
        db.session.add(new_destination)
        db.session.commit()
        
        flash('Destination added successfully!', 'success')
        return redirect(url_for('admin_destinations'))
    
    return render_template('admin/add_destination.html')

@app.route('/admin/edit_destination/<int:destination_id>', methods=['GET', 'POST'])
def edit_destination(destination_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    destination = Destination.query.get_or_404(destination_id)
    
    if request.method == 'POST':
        destination.name = request.form.get('name')
        destination.description = request.form.get('description')
        destination.image_url = request.form.get('image_url')
        destination.price = float(request.form.get('price'))
        destination.location = request.form.get('location')
        destination.rating = float(request.form.get('rating'))
        destination.featured = True if request.form.get('featured') else False
        
        db.session.commit()
        
        flash('Destination updated successfully!', 'success')
        return redirect(url_for('admin_destinations'))
    
    return render_template('admin/edit_destination.html', destination=destination)

@app.route('/admin/bookings')
def admin_bookings():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    bookings = Booking.query.all()
    return render_template('admin/bookings.html', bookings=bookings)

# Error handler
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

if __name__ == '__main__':
    app.run(debug=True)