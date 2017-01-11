import os
import json
from hashlib import sha1

from flask import Flask, render_template, redirect, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_redis import FlaskRedis
from flask_login import login_required, LoginManager, login_user, logout_user, current_user
from wtforms import TextField, PasswordField, SelectField
from flask_wtf import Form
from dp2.client import DaftClient
from dp2 import PROPERTY_TYPES

## Util functions

def get_choices(N):
    choices = sorted(N.iteritems())
    choices.insert(0, (0, '---'))

    return choices

## Set up flask

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
app.config['CSRF_ENABLED'] = True
app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

login_manager = LoginManager()
login_manager.init_app(app)

redis = FlaskRedis()
redis.init_app(app)

## Models

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'

    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)

    def __init__(self, form):
        self.username = form.username.data
        self.password = form.password.data

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the username to satisfy Flask-Login's requirements."""
        return self.username

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

class TargetRegion(db.Model):
    __tablename__ = 'targetregion'

    county = db.Column(db.String, primary_key=True)
    region = db.Column(db.String, primary_key=True)
    property_type = db.Column(db.String, primary_key=True)
    sha = db.Column(db.String, unique=True)

    def __init__(self, form):
        self.county = form.county.data
        self.region = form.region.data
        self.property_type = form.property_type.data
        key = ":".join([self.county, self.region, self.property_type])
        self.sha = sha1(key).hexdigest()

class UserSubscription(db.Model):
    __tablename__ = 'usersubscription'

    username = db.Column(db.String, db.ForeignKey('user.username'), primary_key=True)
    region = db.Column(db.String, db.ForeignKey('targetregion.sha'), primary_key=True)

    def __init__(self, username, region):
        self.username = username.get_id()
        self.region = region.sha

@login_manager.user_loader
def load_user(username):
    return User.query.get(username)

db.create_all()

## Forms

class LoginForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')

class NewUserForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')
    password2 = PasswordField('Retype Password')

class RegionForm(Form):
    county = SelectField('County', choices=[])
    region = SelectField('Region', choices=[])
    property_type = SelectField('Property Type', choices=[(label, label) for label in PROPERTY_TYPES])

## Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = load_user(form.username.data)
        if not user:
            flash("Incorrect username or password")
            return redirect('/login', code=303)

        login_user(user)
        return redirect('/user/{}'.format(form.username.data))

    return render_template('login.html', form=form)

@app.route('/new_user', methods=['GET', 'POST'])
def new_user():
    form = NewUserForm()
    if form.validate_on_submit():
        if form.password.data != form.password2.data:
            flash("Passwords don't match!")
            return redirect('/new_user')

        user = User(form)

        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
            raise

        login_user(user)
        return redirect('/user/{}'.format(form.username.data))

    return render_template('new_user.html', form=form)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/user/<username>')
@login_required
def user_profile(username):
    user = load_user(username)
    subscriptions = UserSubscription.query.filter_by(username=user.username).all()
    region_ids = [sub.region for sub in subscriptions]
    regions = TargetRegion.query.filter(TargetRegion.sha.in_(region_ids)).all()
    client = DaftClient(redis)
    data = [{
        'county': client.get_county_label(r.county),
        'region': client.get_region_label(r.region),
        'property_type': r.property_type,
        'sha': r.sha,
        } for r in regions]
    return render_template('user_profile.html', user=user, regions=data)

@app.route('/get/regions', methods=['POST'])
@login_required
def get_regions():
    key = request.form.keys()[0]
    if key:
        client = DaftClient(redis)
        regions = client.get_region_codes(key)
        region_map = client.translate_regions(regions)
        data = sorted(region_map.iteritems())
        return json.dumps(data), 200
    return '[]', 400

@app.route('/new_region', methods=['GET', 'POST'])
@login_required
def new_region():
    client = DaftClient(redis)

    form = RegionForm()
    if form.is_submitted():
        region = TargetRegion(form)
        subscription = UserSubscription(current_user, region)

        try:
            db.session.add(region)
            db.session.add(subscription)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash("Couldn't add region!")
        except:
            db.session.rollback()
            raise

        return redirect('user/{}'.format(current_user.get_id()))

    form.county.choices = get_choices(client.counties)

    return render_template('new_region.html', form=form)

@app.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect('/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
