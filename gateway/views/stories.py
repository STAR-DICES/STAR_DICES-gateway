import datetime
import requests
import json
import re

from flask import Blueprint, redirect, render_template, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.sql.expression import func

from gateway.auth import admin_required, current_user


stories = Blueprint('stories', __name__)
stories_url = "http://127.0.0.1:7000"
rank_url = "http://127.0.0.1:9000"
reactions_url = "http://127.0.0.1:4000"

"""
This route returns, if the user is logged in, the list of stories of the followed writers
and a list of suggested stories that the user could be interested in.
If not logged, the anonymous user is redirected to the login page.
"""
@stories.route('/', methods=['GET'])
def _myhome(message=''):
    print('home page')
    if current_user.is_anonymous:
        return redirect("/login", code=302)

    r = requests.get(stories_url + "/following-stories/" + str(current_user.get_id()))
    if r.status_code != 200:
        abort(500)
    followed_stories = r.json()['stories']

#    r = requests.get(rank_url + "/rank/" + current_user)
#    if r.status_code != 200:
#        abort(500)
#    suggested_stories = r.json()
    suggested_stories = []

    return render_template("home.html", followed_stories=followed_stories, suggested_stories=suggested_stories)

"""
This route returns, if the user is logged in, the list of all stories from all users
in the social network. The POST is used to filters those stories by user picked date.
If not logged, the anonymous user is redirected to the login page.
"""
@stories.route('/explore', methods=['GET', 'POST'])
@login_required
def _stories(message=''):
    if request.method == 'POST':
        beginDate = request.form["beginDate"]
        if beginDate == "":
            beginDate = str(datetime.date.min)

        endDate = request.form["endDate"]
        if endDate == "":
            endDate = str(datetime.date.max)

        r = requests.get(stories_url + "/stories?start=" + beginDate + "&end=" + endDate)
        if r.status_code != 200:
            abort(500)

        filtered_stories = r.json()['stories']
        return render_template("explore.html", message="Filtered stories", stories=filtered_stories)
    else:
        r = requests.get(stories_url + "/stories")
        if r.status_code != 200:
            abort(500)

        stories = r.json()['stories']
        return render_template("explore.html", message=message, stories=stories)

"""
This route requires the user to be logged in and returns an entire published story
with relative dice rolled and author wall link. In the view, the user will find 
options for like/dislike/delete (if authorized) options.
"""
@stories.route('/story/<int:story_id>')
@login_required
def _story(story_id, message=''):
    r = requests.get(stories_url + "/story/" + str(story_id) + "/" + str(current_user.get_id()))
    if r.status_code == 404:
        message = 'Ooops.. Story not found!'
        return render_template("message.html", message=message)
    elif r.status_code != 200:
        abort(500)

    story = r.json()
    rolls_outcome = json.loads(story['rolls_outcome'])
    return render_template("story.html", message=message, story=story,
                           current_user=current_user, rolls_outcome=rolls_outcome)

"""
In this route the user must be be logged in, and deletes a published story
if the author id is the same of the user calling it.
"""
@stories.route('/story/<story_id>/delete')
@login_required
def _delete_story(story_id):
    r = requests.delete(stories_url + "/story/" + str(story_id) + "/" + str(current_user.get_id()))
    if r.status_code == 404:
        abort(404)
    elif r.status_code == 401:
        abort(401)
    elif r.status_code != 200:
        abort(500)

    message = 'Story sucessfully deleted'
    return render_template("message.html", message=message)

"""
This route requires the user to be logged in, and returns a random story
written from someone else user.
"""
@stories.route('/random_story')
@login_required
def _random_story(message=''):
    r = requests.get(stories_url + "/random-story/" + str(current_user.get_id()))
    if r.status_code == 200:
        story = r.json()
        rolls_outcome = json.loads(story['rolls_outcome'])
    elif r.status_code == 404:
        message = 'Ooops.. No random story for you!'
        rolls_outcome = []
        story = []
    else:
        abort(500)

    return render_template("story.html", message=message, story=story, current_user=current_user,
                           rolls_outcome=rolls_outcome)

"""
The route can be used by a logged in user to like a published story.
"""
@stories.route('/story/<int:story_id>/like')
@login_required
def _like(story_id):
    data = {
        'user_id': current_user.get_id(),
        'story_id': story_id
    }
    r = requests.post(reactions_url + "/like", json=data)
    if r.status_code == 200:
        message = 'Like added!'
    elif r.status_code == 409:
        message = "You've already liked this story!"
    elif r.status_code == 404:
        abort(404)
    else:
        abort(500)

    return _story(story_id, message)

"""
The route can be used by a logged in user to dislike a published story.
"""
@stories.route('/story/<int:story_id>/dislike')
@login_required
def _dislike(story_id):
    data = {
        'user_id': current_user.get_id(),
        'story_id': story_id
    }
    r = requests.post(reactions_url + "/dislike", json=data)
    if r.status_code == 200:
        message = 'Dislike added!'
    elif r.status_code == 409:
        message = "You've already disliked this story!"
    elif r.status_code == 404:
        abort(404)
    else:
        abort(500)

    return _story(story_id, message)

"""
The route can be used by a logged in user to remove a like
from a published story.
"""
@stories.route('/story/<int:story_id>/remove_like')
@login_required
def _remove_like(story_id):
    data = {
        'user_id': current_user.get_id(),
        'story_id': story_id
    }
    r = requests.delete(reactions_url + "/like", json=data)
    if r.status_code == 200:
        message = 'You removed your like'
    elif r.status_code == 409:
        message = 'You have to like it first!'
    elif r.status_code == 404:
        abort(404)
    else:
        abort(500)

    return _story(story_id, message)
    
"""
The route can be used by a logged in user and to remove a dislike
from a published story.
"""
@stories.route('/story/<int:story_id>/remove_dislike')
@login_required
def _remove_dislike(story_id):
    data = {
        'user_id': current_user.get_id(),
        'story_id': story_id
    }
    r = requests.delete(reactions_url + "/dislike", json=data)
    if r.status_code == 200:
        message = 'You removed your dislike'
    elif r.status_code == 409:
        message = 'You have to dislike it first!'
    elif r.status_code == 404:
        abort(404)
    else:
        abort(500)

    return _story(story_id, message)

"""
This route requires the user to be logged in and lets the user select the dice set theme
and the number of dice to be rolled.
If no pending drafts are present with the same selected dice set theme, it redirects 
to /write_story displaying the dice roll outcome. 
Otherwise it redirects to /write_story of the pending draft.
"""
@stories.route('/stories/new_story', methods=['GET', 'POST'])
@login_required
def new_stories():
    if request.method == 'GET':
        r = requests.get(stories_url + "/retrieve-set-themes")
        if r.status_code != 200:
            abort(500)

        dice_themes = r.json()['themes']
        dice_number = [i+1 for i in range(r.json()['dice_number'])]
        return render_template("new_story.html", themes=dice_themes, dice_number=dice_number)
    else:
        data = {
            'user_id': current_user.get_id(),
            'theme': request.form["theme"],
            'dice_number': int(request.form["dice_number"]),
            'author_name': current_user.firstname
        }
        r = requests.post(stories_url + "/new-draft", json=data)
        if r.status_code != 200:
            abort(500)
        
        new_story_id = r.json()['story_id']
        return redirect('/write_story/' + str(new_story_id), code=302)

"""
This route requires the user to be logged in and lets the user write a story or modify 
a draft while diplaying the related dice roll outcome.
In both cases the used will be able to save it as draft or publish it.
"""
@stories.route('/write_story/<story_id>', methods=['POST', 'GET'])
@login_required
def write_story(story_id):
    r = requests.get(stories_url + "/story/" + str(story_id) + "/" + str(current_user.get_id()))
    if r.status_code == 404:
        abort(404)
    elif r.status_code == 401:
        abort(401)
    elif r.status_code != 200:
        abort(500)

    story = r.json()
    rolls_outcome = json.loads(story['rolls_outcome'])
    theme = story['theme']

    if request.method == 'POST':
        story = {}
        story['text'] = request.form["text"]
        story['published'] = request.form["store_story"] == "1"
        story['title'] = request.form["title"]
        story['story_id'] = int(story_id)
        r = requests.put(stories_url + "/write-story", json=story)
        if r.status_code != 200:
            message = r.json()['description']
            return render_template("/write_story.html", theme=theme, outcome=rolls_outcome,
                                   title=story['title'], text=story['text'], message=message)

        if story['published']:
            return redirect("../story/" + str(story['story_id']), code=302)
        else:
            return redirect("../", code=302)

    return render_template("/write_story.html", theme=story['theme'], outcome=rolls_outcome,
                           title=story['title'], text=story['text'], message="")

