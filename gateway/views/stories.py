import datetime
import json
import re

from monolith.database import db, Story, Like, Dislike, retrieve_themes, retrieve_dice_set, is_date, Follow, get_suggested_stories
from monolith.background import async_like, async_dislike, async_remove_like, async_remove_dislike
from monolith.auth import admin_required, current_user
from monolith.classes.DiceSet import _throw_to_faces

from flask import Blueprint, redirect, render_template, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.sql.expression import func

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
    followed_authors = []  # TODO: retrieve IDs of authors current user follows from follows microservice
    followed_stories = []  # TODO: retrieve published stories from authors followed from stories microservice (sending followed_authors or doing a filtering here)
    suggestedStories = []  # TODO: retrieve ranked stories from rank microservice
    return render_template("home.html", message=message, followingstories=followingStories, suggestedstories=suggestedStories)

"""
This route returns, if the user is logged in, the list of all stories from all users
in the social network. The POST is used to filters those stories by user picked date.
If not logged, the anonymous user is redirected to the login page.
"""
@stories.route('/explore', methods=['GET', 'POST'])
def _stories(message=''):
    if current_user.is_anonymous:
        return redirect("/login", code=302)

    allstories = []  # TODO: retrieve all published stories from stories microservice
    if request.method == 'POST':
        beginDate = request.form["beginDate"]
        if beginDate == "" or not is_date(beginDate):
            beginDate = str(datetime.date.min)

        endDate = request.form["endDate"]
        if endDate == "" or not is_date(endDate):
            endDate = str(datetime.date.max)

        filteredStories = []  # TODO: filter allstories using beginDate and endDate
        return render_template("explore.html", message="Filtered stories", stories=filteredStories, url="/story/")
    else:
        return render_template("explore.html", message=message, stories=allstories)

"""
This route requires the user to be logged in and returns an entire published story
with relative dice rolled and author wall link. In the view, the user will find 
options for like/dislike/delete (if authorized) options.
"""
@stories.route('/story/<int:story_id>')
@login_required
def _story(story_id, message=''):
    story = None  # TODO: retrieve story by story_id from stories microservice
    if story is None:
        message = 'Ooops.. Story not found!'
        return render_template("message.html", message=message)

    rolls_outcome = json.loads(story.rolls_outcome)
    return render_template("story.html", message=message, story=story,
                           url="/story/", current_user=current_user, rolls_outcome=rolls_outcome)

"""
In this route the user must be be logged in, and deletes a published story
if the author id is the same of the user calling it.
"""
@stories.route('/story/<story_id>/delete')
@login_required
def _delete_story(story_id):
    response = False  # TODO: send delete request for story with story_id to stories microservice
    if not response:
        # TODO: retrieve why we failed from response and tell the user
        abort(404)  # Story not found
        abort(401)  # Story belongs to somebody else

    message = 'Story sucessfully deleted'
    return render_template("message.html", message=message)

"""
This route requires the user to be logged in, and returns a random story
written from someone else user.
"""
@stories.route('/random_story')
@login_required
def _random_story(message=''):
    story = None  # TODO: retrieve random story from story microservice
    if story is None:
        message = 'Ooops.. No random story for you!'
        rolls_outcome = []
    else:
        rolls_outcome = json.loads(story.rolls_outcome)
    return render_template("story.html", message=message, story=story,
                           url="/story/", current_user=current_user, rolls_outcome=rolls_outcome)

"""
The route can be used by a logged in user to like a published story.
"""
@stories.route('/story/<int:story_id>/like')
@login_required
def _like(story_id):
    response = False  # TODO: send add like request to reactions microservice and check response
    if not response:
        abort(404)
    
    if response:  # TODO: discriminate based on response if like was already present or not
        message = 'Like added!'
    else:
        message = 'You\'ve already liked this story!'
    return _story(story_id, message)

"""
The route can be used by a logged in user to dislike a published story.
"""
@stories.route('/story/<int:story_id>/dislike')
@login_required
def _dislike(story_id):
    response = False  # TODO: send add dislike request to reactions microservice and check response
    if not response:
        abort(404)
    
    if response:  # TODO: discriminate based on response if dislike was already present or not
        message = 'Dislike added!'
    else:
        message = 'You\'ve already disliked this story!'
    return _story(story_id, message)

"""
The route can be used by a logged in user to remove a like
from a published story.
"""
@stories.route('/story/<int:story_id>/remove_like')
@login_required
def _remove_like(story_id):
    response = False  # TODO: send remove like request to reactions microservice and check response
    if not response:
        abort(404)
    
    if response:  # TODO: discriminate based on response if like was present or not
        message = 'You have to like it first!'
    else:
        message = 'You removed your like'
    return _story(story_id, message)
    
"""
The route can be used by a logged in user and to remove a dislike
from a published story.
"""
@stories.route('/story/<int:story_id>/remove_dislike')
@login_required
def _remove_dislike(story_id):
    response = False  # TODO: send remove dislike request to reactions microservice and check response
    if not response:
        abort(404)
    
    if response:  # TODO: discriminate based on response if dislike was present or not
        message = 'You have to dislike it first!'
    else:
        message = 'You removed your dislike'
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
        dice_themes = retrieve_themes()  # TODO: now it must retrieve them from the dice microservice
        return render_template("new_story.html", themes=dice_themes)
    else:
        stry = None  # TODO: retrieve unpublished story with selected theme written by the current user
        if stry != None:
            return redirect("/write_story/"+str(stry.id), code=302)

        dice_set = retrieve_dice_set(request.form["theme"])  # TODO: now it must retrieve it from the dice microservice
        face_set = dice_set.throw()[:int(request.form["dice_number"])]
        new_story = Story()
        new_story.author_id = current_user.id
        new_story.theme = request.form["theme"]
        new_story.rolls_outcome = json.dumps(face_set)
        response = False  # TODO: send store unpublished story request to stories microservice
        if not response:
            pass  # TODO: can this fail?
        return redirect('/write_story/'+str(new_story.id), code=302)

"""
This route requires the user to be logged in and lets the user write a story or modify 
a draft while diplaying the related dice roll outcome.
In both cases the used will be able to save it as draft or publish it.
"""
@stories.route('/write_story/<story_id>', methods=['POST', 'GET'])
@login_required
def write_story(story_id):
    story = None  # TODO: retrieve unpublished story with story_id from stories microservice
    if story is None:
        abort(404)

    if current_user.id != story.author_id:
        abort(401)

    rolls_outcome = json.loads(story.rolls_outcome)
    faces = _throw_to_faces(rolls_outcome)

    if request.method == 'POST':
        story.text = request.form["text"]
        story.title = request.form["title"]
        story.published = 1 if request.form["store_story"] == "1" else 0

        if story.published == 1 and (story.title == "" or story.title == "None"):
            message = "You must complete the title in order to publish the story"
            return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome,
                                   title=story.title, text=story.text, message=message)

        if story.published and not is_story_valid(story.text, faces):
            message = "You must use all the words of the outcome!"
            return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome, title=story.title, text=story.text, message=message)
        
        if story.published == 0 and (story.title == "None" or len(story.title.replace(" ", ""))==0):
            story.title="Draft("+str(story.theme)+")" 

        response = False  # TODO: send story update request to stories microservice
        if not response:
            pass  # TODO: can this fail?

        if story.published == 1:
            return redirect("../story/"+str(story.id), code=302)
        elif story.published == 0:
            return redirect("../", code=302)

    return render_template("/write_story.html", theme=story.theme, outcome=rolls_outcome, title=story.title, text=story.text, message="")

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
