import datetime
import requests
import json
import re

from flask import Blueprint, redirect, render_template, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.sql.expression import func

from gateway.auth import admin_required, current_user


stories = Blueprint('stories', __name__)

"""
This route returns, if the user is logged in, the list of stories of the followed writers
and a list of suggested stories that the user could be interested in.
If not logged, the anonymous user is redirected to the login page.
"""
@stories.route('/', methods=['GET'])
def _myhome(message=''):
    if current_user.is_anonymous:
        return redirect("/login", code=302)

    r = requests.get(stories_url + "/following-stories/" + current_user)
    if r.status_code != 200:
        abort(500)
    followed_stories = json.loads(r.json())

    r = requests.get(rank_url + "/rank/" + current_user)
    if r.status_code != 200:
        abort(500)
    suggested_stories = json.loads(r.json())

    return render_template("home.html",followed_stories=followed_stories, suggested_stories=suggested_stories)

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
        if beginDate == "" or not is_date(beginDate):
            beginDate = str(datetime.date.min)

        endDate = request.form["endDate"]
        if endDate == "" or not is_date(endDate):
            endDate = str(datetime.date.max)

        r = requests.get(stories_url + "/stories_by_url/start=" + beginDate + "&end=" + endDate)
        if r.status_code != 200:
            abort(500)

        filtered_stories = json.loads(r.json())
        return render_template("explore.html", message="Filtered stories", stories=stories)
    else:
        r = requests.get(stories_url + "/stories")
        if r.status_code != 200:
            abort(500)

        stories = json.loads(r.json())
        return render_template("explore.html", message=message, stories=stories)

"""
This route requires the user to be logged in and returns an entire published story
with relative dice rolled and author wall link. In the view, the user will find 
options for like/dislike/delete (if authorized) options.
"""
@stories.route('/story/<int:story_id>')
@login_required
def _story(story_id, message=''):
    r = requests.get(stories_url + "/story/" + story_id + "/" + current_user)
    if r.status_code == 404:
        message = 'Ooops.. Story not found!'
        return render_template("message.html", message=message)
    elif r.status_code != 200:
        abort(500)

    story = json.loads(r.json())
    rolls_outcome = story['rolls_outcome']
    return render_template("story.html", message=message, story=story,
                           current_user=current_user, rolls_outcome=rolls_outcome)

"""
In this route the user must be be logged in, and deletes a published story
if the author id is the same of the user calling it.
"""
@stories.route('/story/<story_id>/delete')
@login_required
def _delete_story(story_id):
    data = {'user_id': current_user}
    r = requests.delete(stories_url + "/story/" + story_id, data=json.dumps(data))
    if r.status_code != 200:
        abort(r.status_code)

    message = 'Story sucessfully deleted'
    return render_template("message.html", message=message)

"""
This route requires the user to be logged in, and returns a random story
written from someone else user.
"""
@stories.route('/random_story')
@login_required
def _random_story(message=''):
    r = requests.get(stories_url + "/random-story")
    if r.status_code == 200:
        rolls_outcome = json.loads(story.rolls_outcome)
    elif r.status_code == 404:
        message = 'Ooops.. No random story for you!'
        rolls_outcome = []
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
        'user_id': current_user,
        'story_id': story_id
    }
    r.requests.post(reactions_url + "/like", data=json.dumps(data))
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
        'user_id': current_user,
        'story_id': story_id
    }
    r.requests.post(reactions_url + "/like", data=json.dumps(data))
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
        'user_id': current_user,
        'story_id': story_id
    }
    r.requests.delete(reactions_url + "/like", data=json.dumps(data))
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
        'user_id': current_user,
        'story_id': story_id
    }
    r.requests.post(reactions_url + "/like", data=json.dumps(data))
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

        dice_themes = json.loads(r.json())
        return render_template("new_story.html", themes=dice_themes)
    else:
        data = {
            'theme': request.form["theme"],
            'dice_number': request.form["dice_number"]
        }
        r = requests.post(stories_url + "/new_draft", data=json.dumps(data))
        if r.status_code != 200:
            abort(500)
        
        new_story_id = json.loads(r.json())['story_id']
        return redirect('/write_story/' + str(new_story_id), code=302)

"""
This route requires the user to be logged in and lets the user write a story or modify 
a draft while diplaying the related dice roll outcome.
In both cases the used will be able to save it as draft or publish it.
"""
@stories.route('/write_story/<story_id>', methods=['POST', 'GET'])
@login_required
def write_story(story_id):
    r = requests.get(stories_url + "/story/" + story_id + "/" + current_user)
    if r.status_code == 404:
        abort(404)
    elif r.status_code == 401:
        abort(401)
    elif r.status_code != 200:
        abort(500)

    story = json.loads(r.json())
    rolls_outcome = story.rolls_outcome

    if request.method == 'POST':
        story.text = request.form["text"],
        story.published = request.form["store_story"] == "1",
        if not story.published and (story.title == "None" or len(story.title.replace(" ", "")) == 0):
            story.title = "Draft(" + story.theme + ")" 
        else:
            story.title = request.form["title"]

        # TODO: move these checks to stories microservice.
        if story.published and not is_story_valid(story.text, rolls_outcome):
            message = "You must use all the words of the outcome!"
            return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome,
                                   title=story.title, text=story.text, message=message)

        if story.published and (story.title == "" or story.title == "None"):
            message = "You must complete the title in order to publish the story"
            return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome,
                                   title=story.title, text=story.text, message=message)

        r = requests.put(stories_url + "/write_story", data=json.dumps(story))
        if r.status_code != 200:
            abort(500)

        if story.published:
            return redirect("../story/" + str(story.id), code=302)
        else:
            return redirect("../", code=302)

    # GET method
    r = requests.get(stories_url + "/story/" + story_id + "/" + current_user)
    if r.status_code == 404:
        abort(404)
    elif r.status_code == 401:
        abort(401)
    elif r.status_code != 200:
        abort(500)

    faces = _throw_to_faces(rolls_outcome)
    return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome, title=story.title,
                           text=story.text, message="")

"""
Function to be called during story publishing that checks if the story
contains the rolled dice faces.
If it return False, stop publishing and return an error message.
"""
def is_story_valid(story_text, dice_roll):
    split_story_text = re.findall(r"[\w']+|[.,!?;]", story_text.lower())
    for word in dice_roll:
        if word.lower() not in split_story_text:
            return False
    return True
