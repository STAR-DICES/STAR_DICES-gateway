import requests

from flask import Blueprint, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_user, logout_user, login_required

from gateway.auth import admin_required, current_user


users = Blueprint('users', __name__)
stories_url = "http://127.0.0.1:7000"
stats_url = "http://127.0.0.1:9000"
followers_url = "http://127.0.0.1:8000"

"""
This route returns to a logged user the list of the writers in the social network and
their last published story (if any).
"""
@users.route('/users')
@login_required
def _users():
    r = requests.get(stories_url + "/writers-last-stories")
    if r.status_code != 200:
        abort(500)

    data = r.json()['stories']
    return render_template("users.html", writers=data)

"""
This route returns to a logged user his own wall with his score, pending drafts and published 
stories.
"""
@users.route('/my_wall')
@login_required
def my_wall():
    r = requests.get(stories_url + "/stories?drafts=true&writer_id=" + str(current_user.get_id()))
    if r.status_code == 200:
        my_stories = r.json()['stories']
        drafts = [my_story for my_story in my_stories if not my_story['published']]
        published = [my_story for my_story in my_stories if my_story['published']]
    elif r.status_code == 404:
        drafts = []
        published = []
    else:
        abort(500)

    r = requests.get(stats_url + "/stats/" + str(current_user.get_id()))
    if r.status_code != 200:
        abort(500)

    stats = r.json()['score']
    return render_template("mywall.html", published=published, drafts=drafts, stats=stats)

"""
This route returns to a logged user the public wall of a user, displaying his last 
published stories.
"""
@users.route('/wall/<int:author_id>', methods=['GET'])
@login_required
def wall(author_id):
    r = requests.get(stories_url + "/stories?drafts=false&writer_id=" + str(author_id))
    if r.status_code == 404:
        message = "Ooops.. Writer not found!"
        return render_template("message.html", message=message)
    elif r.status_code != 200:
        abort(500)

    stories = r.json()['stories']
    if not stories:
        # Only users with published stories are considered writers.
        message = "Ooops.. Writer not found!"
        return render_template("message.html", message=message)

    author = {
        'id': author_id,
        'name': stories[0]['author_name']
    }
    return render_template("wall.html", stories=stories, author=author, current_user=current_user)

"""
This route lets a logged user follow another user.
"""
@users.route('/wall/<int:author_id>/follow', methods=['GET'])
@login_required
def follow(author_id):
    data = {
        'user_id': current_user.get_id(),
        'followee_id': author_id,
        'user_name': current_user.firstname
    }
    r = requests.post(followers_url + "/follow", json=data)
    if r.status_code == 200:
        message = "Following!"
    elif r.status_code == 409:
        message = "Already following!"
    elif r.status_code == 404:
        abort(404)
    elif r.status_code == 401:
        message = "Cannot follow yourself"
    else:
        abort(500)

    return render_template('message.html', message=message)

"""
This route lets a logged user unfollow a followed user.
"""
@users.route('/wall/<int:author_id>/unfollow', methods=['GET'])
@login_required
def unfollow(author_id):
    data = {
        'user_id': current_user.get_id(),
        'followee_id': author_id
    }
    r = requests.delete(followers_url + "/follow", json=data)
    if r.status_code == 200:
        message = "Unfollowed!"
    elif r.status_code == 409:
        message = "You were not following that particular user!"
    elif r.status_code == 404:
        abort(404)
    elif r.status_code == 401:
        message = "Cannot unfollow yourself"
    else:
        abort(500)

    return render_template('message.html', message=message)

"""
This route lets a logged user see his own followers.
"""
@users.route('/my_wall/followers', methods=['GET'])
@login_required
def my_followers():
    r = requests.get(followers_url + "/followers-list/" + str(current_user.get_id()))
    if r.status_code == 200:
        followers = r.json()['followers']
    elif r.status_code == 404:
        followers = []
    else:
        abort(500)
    return render_template('myfollowers.html', followers=followers)
