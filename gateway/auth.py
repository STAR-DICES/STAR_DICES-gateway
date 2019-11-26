import functools

from gateway.classes.User import User

from flask_login import current_user, LoginManager
from flask import current_app as app


login_manager = LoginManager()

def admin_required(func):
    @functools.wraps(func)
    def _admin_required(*args, **kw):
        admin = current_user.is_authenticated and current_user.is_admin
        if not admin:
            return login_manager.unauthorized()
        return func(*args, **kw)
    return _admin_required

@login_manager.user_loader
def load_user(user_id):
    user_id = str(user_id)
    if user_id in app.users:
        user = app.users[user_id]
    else:
        user = None

    if user is not None:
        user.is_authenticated = True

    return user
