import requests
import json

from flask_login import current_user, login_user, logout_user, login_required
from flask import Blueprint, render_template, redirect, request, url_for, abort
from sqlalchemy.exc import IntegrityError
from flask import current_app as app

from gateway.forms import LoginForm, UserForm
from gateway.classes.user import User

auth = Blueprint('auth', __name__)
auth_url = "http://auth:5000"

"""
This route is used to display the form to let the user login.
"""
@auth.route('/login', methods=['GET', 'POST'])
def login(message=''):
    if not current_user.is_anonymous:
        return redirect("/", code=302)

    form = LoginForm()
    form.message = message
    if form.validate_on_submit():
        data = {
            'email': form.data['email'],
            'password': form.data['password']
        }
        r = requests.post(auth_url + "/login", json=data, timeout=1)
        if r.status_code == 200:
            user_info = r.json()
            user_id = user_info['user_id']
            firstname = user_info['firstname']
            user = User(user_id, firstname)
            app.users[str(user_id)] = user
            login_user(user)
            print('redirect')
            return redirect('/')
        elif r.status_code == 401:
            form.message = "User or Password not correct!"
        else:
            abort(500)

    return render_template('login.html', form=form, notlogged=True)

"""
This route is used to let the user logout.
"""
@auth.route("/logout")
@login_required
def logout():
    user_id = current_user.get_id()
    logout_user()
    del app.users[str(user_id)]
    return redirect('/')

"""
This route is used to let a new user signup.
"""
@auth.route('/signup', methods=['GET', 'POST'])
def create_user():
    if not current_user.is_anonymous:
        return redirect("/", code=302)

    form = UserForm()
    if form.validate_on_submit():
        new_user = {
			'email': form.email.data,
			'password': form.password.data,
			'firstname': form.firstname.data,
			'lastname': form.lastname.data,
			'dateofbirth': form.dateofbirth.data.strftime("%m/%d/%Y")
		}

        r = requests.post(auth_url + "/signup", json=new_user, timeout=1)
        if r.status_code == 200:
            user_info = r.json()
            user_id = user_info['user_id']
            firstname = user_info['firstname']
            user = User(user_id, firstname)
            app.users[str(user_id)] = user
            login_user(user)
            return redirect('/')
        elif r.status_code == 409:
            form.message = "Seems like this email is already used"
        else:
            abort(500)
 
    return render_template('create_user.html', form=form, notlogged=True)

