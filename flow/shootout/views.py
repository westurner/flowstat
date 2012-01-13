import math
from operator import itemgetter

import formencode
from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer
from pyramid.view import view_config
from pyramid.url import route_url
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.security import authenticated_userid

from ..security.views import login_form_view
from ..models import DBSession
from ..models import User
from ..views.blocks import toolbar_view

from .models import Idea, Tag

# i178n
#from pyramid.i18n import TranslationStringFactory
#_ = TranslationStringFactory('flow')

def latest_view(request):
    latest = Idea.ideas_bunch(Idea.idea_id.desc())
    return render('shootout/templates/_latest.jinja2',
                    {'latest': latest},
                    request)

def cloud_view(request):
    totalcounts = []
    for tag in Tag.tag_counts():
        weight = int((math.log(tag[1] or 1) * 4) + 10)
        totalcounts.append((tag[0], tag[1], weight))
    cloud = sorted(totalcounts, key=itemgetter(0))

    return render('shootout/templates/_cloud.jinja2',
                    {'cloud': cloud},
                    request)


@view_config(permission='view', route_name='ideas_main',
             renderer='shootout/templates/main.jinja2')
def ideas_main(request):
    hitpct = Idea.ideas_bunch(Idea.hit_percentage.desc())
    top = Idea.ideas_bunch(Idea.hits.desc())
    bottom = Idea.ideas_bunch(Idea.misses.desc())
    last10 = Idea.ideas_bunch(Idea.idea_id.desc())

    toplists = [
        {'title': 'Latest shots', 'items': last10},
        {'title': 'Most hits', 'items': top},
        {'title': 'Most misses', 'items': bottom},
        {'title': 'Best performance', 'items': hitpct},
    ]

    login_form = login_form_view(request)

    return {
        'title': 'ideas',
        'username': authenticated_userid(request),
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'toplists': toplists,
    }


@view_config(permission='post', route_name='idea_vote')
def idea_vote(request):
    post_data = request.POST
    target = post_data.get('target')
    session = DBSession()

    idea = Idea.get_by_id(target)
    voter_username = authenticated_userid(request)
    voter = User.get_by_username(voter_username)

    if post_data.get('form.vote_hit'):
        idea.hits += 1
        idea.author.hits += 1
        voter.delivered_hits += 1

    elif post_data.get('form.vote_miss'):
        idea.misses += 1
        idea.author.misses += 1
        voter.delivered_misses += 1

    idea.voted_users.append(voter)

    session.flush()

    redirect_url = route_url('idea', request, idea_id=idea.idea_id)
    response = HTTPMovedPermanently(location=redirect_url)

    return response


class AddIdeaSchema(formencode.Schema):
    allow_extra_fields = True
    title = formencode.validators.String(not_empty=True)
    text = formencode.validators.String(not_empty=True)
    tags = formencode.validators.String(not_empty=True)


@view_config(permission='post', route_name='idea_add',
             renderer='shootout/templates/idea_add.jinja2')
def idea_add(request):
    target = request.GET.get('target')
    session = DBSession()
    if target:
        target = Idea.get_by_id(target)
        if not target:
            return HTTPNotFound()
        kind = 'comment'
    else:
        kind = 'idea'

    form = Form(request, schema=AddIdeaSchema)

    if 'form.submitted' in request.POST and form.validate():
        author_username = authenticated_userid(request)
        author = User.get_by_username(author_username)

        idea = Idea(
            target=target,
            author=author,
            title=form.data['title'],
            text=form.data['text']
        )

        tags = Tag.create_tags(form.data['tags'])
        if tags:
            idea.tags = tags

        session.add(idea)
        redirect_url = route_url('idea', request, idea_id=idea.idea_id)

        return HTTPFound(location=redirect_url)

    login_form = login_form_view(request)

    return {
        'title': 'add an idea',
        'form': FormRenderer(form),
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'target': target,
        'kind': kind,
    }


@view_config(permission='view', route_name='idea',
             renderer='shootout/templates/idea.jinja2')
def idea_view(request):
    idea_id = request.matchdict['idea_id']
    idea = Idea.get_by_id(idea_id)

    viewer_username = authenticated_userid(request)
    voted = idea.user_voted(viewer_username)
    login_form = login_form_view(request)

    return {
        'title': 'idea: %s' % idea.title,
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'voted': voted,
        'viewer_username': viewer_username,
        'idea': idea,
    }


@view_config(permission='view', route_name='tag',
             renderer='shootout/templates/tag.jinja2')
def tag_view(request):
    tagname = request.matchdict['tag_name']
    ideas = Idea.get_by_tagname(tagname)
    login_form = login_form_view(request)
    return {
        'title': u'tag: %s' % tagname,
        'tag': tagname,
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'ideas': ideas,
    }
