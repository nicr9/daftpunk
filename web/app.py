import os

from flask import Flask, render_template, redirect, flash, request, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask_login import login_required, LoginManager, login_user
from wtforms import TextField, PasswordField
from wtforms.fields.html5 import EmailField
from flask_wtf import Form


app = Flask(__name__)

app.config['SECRET_KEY'] =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
app.config['CSRF_ENABLED'] = True

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'

    email = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

db.create_all()

## Routes

class LoginForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')

class NewUserForm(Form):
    email = EmailField('Email')
    username = TextField('Username')
    password = PasswordField('Password')
    password2 = PasswordField('Retype Password')

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
        # TODO: Add user to DB
        # Login user
        # Redirect to /user/{username}
        pass

    return render_template('new_user.html', form=form)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/user/<user>')
@login_required
def user_profile(user):
    return render_template('user_profile.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
