import os
import json

from flask import Flask, render_template, redirect, flash, request, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask_login import login_required, LoginManager, login_user, logout_user, current_user
from wtforms import TextField, PasswordField, SelectField
from flask_wtf import Form
from dp2.client import DaftClient

## Env vars

DAFT_USER = os.environ['DAFT_USER']
DAFT_PASSWD = os.environ['DAFT_PASSWD']

## Util functions

def get_choices(N):
    choices = [(key, key) for key, val in N.iteritems()]
    choices.insert(0, (0, '---'))

    return choices

## Set up flask

app = Flask(__name__)

app.config['SECRET_KEY'] =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
app.config['CSRF_ENABLED'] = True

login_manager = LoginManager()
login_manager.init_app(app)

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

class Region(db.Model):
    __tablename__ = 'region'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String, default=False)
    county = db.Column(db.String, default=False)
    region = db.Column(db.String, default=False)

    def __init__(self, userid, form):
        self.userid = userid
        self.county = form.county.data
        self.region = form.region.data

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

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
    regions = Region.query.filter_by(userid=user.username).all()
    return render_template('user_profile.html', user=user, regions=regions)

@app.route('/get/regions', methods=['POST'])
@login_required
def get_regions():
    key = request.form.keys()[0]
    if key:
        client = DaftClient(DAFT_USER, DAFT_PASSWD)
        data = client.get_regions(key)
        return json.dumps(data), 200
    return '[]', 400

@app.route('/new_region', methods=['GET', 'POST'])
@login_required
def new_region():
    client = DaftClient(DAFT_USER, DAFT_PASSWD)

    form = RegionForm()
    if form.is_submitted():
        region = Region(current_user.get_id(), form)

        try:
            db.session.add(region)
            db.session.commit()
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
