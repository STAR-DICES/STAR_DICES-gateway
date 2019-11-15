from flask import Blueprint, redirect, render_template, request, url_for, abort
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.database import db, User, Story, Follow, isFollowing, getStats
from monolith.auth import admin_required, current_user
from sqlalchemy.exc import IntegrityError

users = Blueprint('users', __name__)

"""
This route returns to a logged user the list of the writers in the social network and
their last published story (if any).
"""
@users.route('/users')
@login_required
def _users():
    users = []  # TODO: retrieve users from users microservice
    data = []
    for user in users:
        story = None  # TODO: retrieve last story from user from stories microservice
        data.append((user, story))
    return render_template("users.html", data=data)

"""
This route returns to a logged user his own wall with his score, pending drafts and published 
stories.
"""
@users.route('/my_wall')
@login_required
def my_wall():
    published = []  # TODO: retrieve my published stories from stories microservice
    drafts = []  # TODO: retrieve my unpublished stories from stories microservice
    return render_template("mywall.html", published=published, drafts=drafts, stats=getStats(current_user.id))

"""
This route returns to a logged user the public wall of a user, displaying his last 
published stories.
"""
@users.route('/wall/<int:author_id>', methods=['GET'])
@login_required
def wall(author_id):
    author = None  # TODO: retrieve user from user microservice
    if author is None:
        message = "Ooops.. Writer not found!"
        return render_template("message.html", message=message)

    stories = []  # TODO: retrieve author's published stories from stories microservice
    return render_template("wall.html", stories=stories, author=author,
                            current_user=current_user, alreadyFollowing = isFollowing(author_id, current_user.id))

"""
This route lets a logged user follow another user.
"""
@users.route('/wall/<int:author_id>/follow', methods=['GET'])
@login_required
def follow(author_id):
    if author_id == current_user.id:
        message = "Cannot follow yourself"
    else:
        author = None  # TODO: retrieve user from user microservice
        if author is None:
            abort(404)
            
        response = False  # TODO: send follow request to follows microservice
        if response:
            message = "Following!"
        else:
            message = "Already following!"
    return render_template('message.html', message = message)

"""
This route lets a logged user unfollow a followed user.
"""
@users.route('/wall/<int:author_id>/unfollow', methods=['GET'])
@login_required
def unfollow(author_id):
    if author_id == current_user.id:
        message = "Cannot unfollow yourself"
    else:
        author = None  # TODO: retrieve user from user microservice
        if author is None:
            abort(404)
            
        response = False  # TODO: send follow request to follows microservice
        if response:
            message = "Unfollowed!"
        else:
            message = "You were not following that particular user!"
    return render_template('message.html', message = message)

"""
This route lets a logged user see his own followers.
"""
@users.route('/my_wall/followers', methods=['GET'])
@login_required
def my_followers():
    followers = []  # TODO: retrieve my followers from followers microservice
    return render_template('myfollowers.html', followers=followers)
