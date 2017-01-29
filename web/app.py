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
from dp2.resource import County, Area, RegionStats, Question, Property
from dp2 import PROPERTY_TYPES

## Util functions

def counties_dropdown(N):
    counties = [(n.code, n.label) for n in N]
    choices = sorted(counties, key=lambda x: x[1])
    choices.insert(0, (0, '---'))

    return choices

def areas_dropdown(N):
    areas = [(n.code, n.label) for n in N]
    choices = sorted(areas, key=lambda x: x[1])

    return choices

def translate_region(region):
    return {
        'county': County.from_code(redis, region.county).label,
        'area': Area.from_code(redis, region.area).label,
        'property_type': region.property_type,
        'sha': region.sha,
        'stats': RegionStats.from_code(redis, region.sha),
        'last_scraped': region.last_scraped,
        }

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

    @classmethod
    def from_form(cls, form):
        self = cls()
        self.username = form.username.data
        self.password = form.password.data

        return self

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

class Region(db.Model):
    __tablename__ = 'region'

    county = db.Column(db.String, primary_key=True)
    area = db.Column(db.String, primary_key=True)
    property_type = db.Column(db.String, primary_key=True)
    sha = db.Column(db.String, unique=True)
    last_scraped = db.Column(db.DateTime, nullable=True)

    @classmethod
    def from_form(cls, form):
        self = cls()

        self.county = form.county.data
        self.area = form.area.data
        self.property_type = form.property_type.data
        key = ":".join([self.county, self.area, self.property_type])
        self.sha = sha1(key).hexdigest()

        return self

    @classmethod
    def from_sha(cls, sha):
        self = cls()

class UserSubscription(db.Model):
    __tablename__ = 'usersubscription'

    username = db.Column(db.String, db.ForeignKey('user.username'), primary_key=True)
    region = db.Column(db.String, db.ForeignKey('region.sha'), primary_key=True)

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
    area = SelectField('Area', choices=[])
    property_type = SelectField('Property Type', choices=[(label, label) for label in PROPERTY_TYPES])

## Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = load_user(form.username.data)
        if user and user.password == form.password.data:
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return redirect('/user/{}'.format(user.username))

        flash("Incorrect username or password")
        return redirect('/login', code=303)

    return render_template('login.html', form=form)

@app.route('/new/user', methods=['GET', 'POST'])
def new_user():
    form = NewUserForm()
    if form.validate_on_submit():
        if form.password.data != form.password2.data:
            flash("Passwords don't match!")
            return redirect('/new/user', code=303)

        user = User.from_form(form)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash("That username is taken")
            return redirect('/new/user', code=303)
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
    subscriptions = UserSubscription.query.filter_by(
            username=user.username).all()
    region_shas = [sub.region for sub in subscriptions]
    regions = Region.query.filter(
            Region.sha.in_(region_shas)).all()
    data = [translate_region(r) for r in regions]
    awaiting_update = any([not row['last_scraped'] for row in data])
    return render_template(
            'user_profile.html',
            user=user,
            regions=data,
            awaiting_update=awaiting_update
            )

@app.route('/get/areas', methods=['POST'])
@login_required
def get_areas():
    key = request.form.keys()[0]
    if key:
        client = DaftClient(redis)
        areas = County.from_code(redis, key).areas
        data = areas_dropdown(areas)
        return json.dumps(data), 200
    return '[]', 400

@app.route('/new/region', methods=['GET', 'POST'])
@login_required
def new_region():
    client = DaftClient(redis)

    form = RegionForm()
    if form.is_submitted():
        region = Region.from_form(form)
        subscription = UserSubscription(current_user, region)

        try:
            db.session.add(region)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()

        try:
            db.session.add(subscription)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash("Duplicate region!")
            return redirect('/new/region', 303)
        except:
            db.session.rollback()
            raise

        return redirect('user/{}'.format(current_user.get_id()))

    form.county.choices = counties_dropdown(client.counties)

    return render_template('new_region.html', form=form)

@app.route('/region/<code>')
def region_profile(code):
    region = Region.query.filter(
            Region.sha.match(code)).first()
    return render_template(
            'region_profile.html', region=translate_region(region))

@app.route('/property/<code>')
def property_profile(code):
    prop = Property.from_code(redis, code)
    return render_template('property_profile.html', property=prop)

@app.route('/checklist')
def checklist():
    items = Question.get_all(redis)
    return render_template('checklist.html', items=items)

@app.route('/signout')
@login_required
def signout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect('/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
