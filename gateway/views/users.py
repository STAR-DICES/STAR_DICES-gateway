import requests

from flask import Blueprint, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_user, logout_user, login_required

from gateway.auth import admin_required, current_user


users = Blueprint('users', __name__)
stories_url = "http://127.0.0.1:7000"
stats_url = "http://127.0.0.1:9000"

"""
This route returns to a logged user the list of the writers in the social network and
their last published story (if any).
"""
@users.route('/users')
@login_required
def _users():
    r = requests.get(stories_url + "/writers-last-story")
    data = r.json()
    return render_template("users.html", data=data)

"""
This route returns to a logged user his own wall with his score, pending drafts and published 
stories.
"""
@users.route('/my_wall')
@login_required
def my_wall():
    r = requests.get(stories_url + "/stories?writer_id=" + str(current_user.get_id()) + "&drafts=true")
    if r.status_code == 200:
        my_stories = r.json()['stories']
        print(my_stories)
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
    r = requests.get(stories_url + "/stories-by-writer-id?writer_id=" + author_id + "&user_id=" + current_usr)
    if r.status_code == 404:
        message = "Ooops.. Writer not found!"
        return render_template("message.html", message=message)
    elif r.status_code != 200:
        abort(500)

    stories = r.json()
    if not stories:
        # Only users with published stories are considered writers.
        message = "Ooops.. Writer not found!"
        return render_template("message.html", message=message)

    author = {
        'id': author_id,
        'name': stories[0].author_name
    }
    return render_template("wall.html", stories=stories, author=author, current_user=current_user)

"""
This route lets a logged user follow another user.
"""
@users.route('/wall/<int:author_id>/follow', methods=['GET'])
@login_required
def follow(author_id):
    if author_id == current_user.id:
        message = "Cannot follow yourself"
        return render_template('message.html', message=message)

    data = {
        'user_id': current_user,
        'followee_id': author_ir
    }
    r = requests.put(follows_url + "/follow", json=data)
    if r.status_code == 200:
        message = "Following!"
    elif r.status_code == 409:
        message = "Already following!"
    elif r.status_code == 404:
        abort(404)
    else:
        abort(500)

    return render_template('message.html', message=message)

"""
This route lets a logged user unfollow a followed user.
"""
@users.route('/wall/<int:author_id>/unfollow', methods=['GET'])
@login_required
def unfollow(author_id):
    if author_id == current_user.id:
        message = "Cannot unfollow yourself"
        return render_template('message.html', message=message)

    data = {
        'user_id': current_user,
        'followee_id': author_ir
    }
    r = requests.delete(follows_url + "/follow", json=data)
    if r.status_code == 200:
        message = "Following!"
    elif r.status_code == 409:
        message = "You were not following that particular user!"
    elif r.status_code == 404:
        abort(404)
    else:
        abort(500)

    return render_template('message.html', message=message)

"""
This route lets a logged user see his own followers.
"""
@users.route('/my_wall/followers', methods=['GET'])
@login_required
def my_followers():
    r = requests.get(followers_url + "/followers-list/" + current_user)
    if r.status_code == 200:
        followers = r.json()
    elif r.status_code == 404:
        followers = []
    else:
        abort(500)
    return render_template('myfollowers.html', followers=followers)
