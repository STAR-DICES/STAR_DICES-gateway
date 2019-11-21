import requests
import json

from flask import Blueprint, render_template, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

from gateway.forms import LoginForm, UserForm
from gateway.classes.Login import Login
from gateway.classes.User import User

auth = Blueprint('auth', __name__)
auth_url = "http://127.0.0.1:5000"

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

        r = requests.post(auth_url + "/login", data=json.dumps(data))
        if r.status_code == 200:
            user_info = json.loads(r.json())
            login_user(user_info)  # TODO: store user_id and username somewhere.
            return redirect('/')
        elif r.status_code == 401:
            form.message = "User or Password not correct!"
        else
            abort(500)

    return render_template('login.html', form=form, notlogged=True)

"""
This route is used to let the user logout.
"""
@auth.route("/logout")
@login_required
def logout():
    logout_user()  # TODO: remove user_id and username (?).
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
        new_user = User()
        form.populate_obj(new_user)
        new_user.set_password(form.password.data)

        r = requests.post(auth_url + "/signup", data=json.dump(new_user))
        if r.status_code == 200:
            user_info = json.loads(r.json())
            login_user(user_info)
            return redirect('/')
        elif r.status_code == 409:
            form.message = "Seems like this email is already used"
        else
            abort(500)
 
    return render_template('create_user.html', form=form, notlogged=True)

