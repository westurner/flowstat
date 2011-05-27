import unittest

from pyramid import testing


def _initTestingDB():
    from flow.models import DBSession
    from flow.models import Base
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    session = DBSession()
    session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return session

def _registerRoutes(config):
    config.add_route('idea', '/ideas/{idea_id}')
    config.add_route('user', '/users/{username}')
    config.add_route('tag', '/tags/{tag_name}')
    config.add_route('idea_add', '/idea_add')
    config.add_route('idea_vote', '/idea_vote')

    config.add_route('sparql_query', '/sparql')

    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('about', '/about')
    config.add_route('main', '/')

def _registerCommonTemplates(config):
    config.testing_add_renderer('templates/login.pt')
    config.testing_add_renderer('templates/toolbar.pt')
    config.testing_add_renderer('templates/cloud.pt')
    config.testing_add_renderer('templates/latest.pt')
    config.testing_add_renderer('templates/sparql_query.jinja2')

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()
        self.config = testing.setUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()

    def _addUser(self, username=u'username'):
        from flow.models import User
        user = User(username=username, pwrd=u'pwrd', name=u'name',
                    email=u'email')
        self.session.add(user)
        self.session.flush()
        return user

    def _addIdea(self, target=None, user=None):
        from flow.models import Idea
        if not user:
            user = self._addUser()
        idea = Idea(target=target, author=user, title=u'title',
                    text=u'text')
        self.session.add(idea)
        self.session.flush()
        return idea
        
    def test_main_view(self):
        from flow.views import main_view
        self.config.testing_securitypolicy(u'username')
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = main_view(request)
        self.assertEqual(result['username'], u'username')
        self.assertEqual(len(result['toplists']), 4)

    def test_idea_add_nosubmit_idea(self):
        from flow.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = idea_add(request)
        self.assertEqual(result['target'], None)
        self.assertEqual(result['kind'], 'idea')
        
    def test_idea_add_nosubmit_comment(self):
        from flow.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _registerCommonTemplates(self.config)
        idea = self._addIdea()
        request = testing.DummyRequest(params={'target': idea.idea_id})
        result = idea_add(request)
        self.assertEqual(result['target'], idea)
        self.assertEqual(result['kind'], 'comment')

    def test_idea_add_not_existing_target(self):
        from flow.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest(params={'target': 100})
        result = idea_add(request)
        self.assertEqual(result.code, 404)


    def test_idea_add_submit_schema_fail_empty_params(self):
        from flow.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _registerCommonTemplates(self.config)
        _registerRoutes(self.config)
        request = testing.DummyRequest(post={'form.submitted': 'Shoot'})
        result = idea_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'text': u'Missing value',
                'tags': u'Missing value',
                'title': u'Missing value'
            }
        )

    def test_idea_add_submit_schema_succeed(self):
        from flow.views import idea_add
        from flow.models import Idea
        self.config.testing_securitypolicy(u'username')
        _registerRoutes(self.config)
        request = testing.DummyRequest(
            post={
                'form.submitted': u'Shoot',
                'tags': u'abc def, bar',
                'text': u'My idea is cool',
                'title': u'My idea',
            }
        )
        user = self._addUser(u'username')
        result = idea_add(request)
        self.assertEqual(result.location, 'http://example.com/ideas/1')
        ideas = self.session.query(Idea).all()
        self.assertEqual(len(ideas), 1)
        idea = ideas[0]
        self.assertEqual(idea.idea_id, 1)
        self.assertEqual(idea.text, u'My idea is cool')
        self.assertEqual(idea.title, u'My idea')
        self.assertEqual(idea.author, user)
        self.assertEqual(len(idea.tags), 3)
        self.assertEqual(idea.tags[0].name, u'abc')
        self.assertEqual(idea.tags[1].name, u'bar')
        self.assertEqual(idea.tags[2].name, u'def')

    def test_positive_idea_voting(self):
        from flow.views import idea_vote
        from flow.models import User
        _registerRoutes(self.config)        
        idea = self._addIdea()
        user = self.session.query(User).one()
        self.assertEqual(idea.user_voted(u'username'), False)
        self.config.testing_securitypolicy(u'username')
        post_data = {
            'form.vote_hit': u'Hit',
            'target': 1,
        }
        request = testing.DummyRequest(post=post_data)
        idea_vote(request)
        self.assertEqual(idea.hits, 1)
        self.assertEqual(idea.misses, 0)
        self.assertEqual(idea.hit_percentage, 100)
        self.assertEqual(idea.total_votes, 1)
        self.assertEqual(idea.vote_differential, 1)
        self.assertEqual(idea.author.hits, 1)
        self.assertEqual(len(idea.voted_users.all()), 1)
        self.assertEqual(idea.voted_users.one(), user)
        self.assertTrue(idea.user_voted(u'username'))

    def test_negative_idea_voting(self):
        from flow.views import idea_vote
        from flow.models import User
        _registerRoutes(self.config)        
        idea = self._addIdea()
        user = self.session.query(User).one()
        self.assertEqual(idea.user_voted(u'username'), False)
        self.config.testing_securitypolicy(u'username')
        post_data = {
            'form.vote_miss': u'Miss',
            'target': 1,
        }
        request = testing.DummyRequest(post=post_data)
        idea_vote(request)
        self.assertEqual(idea.hits, 0)
        self.assertEqual(idea.misses, 1)
        self.assertEqual(idea.hit_percentage, 0)
        self.assertEqual(idea.total_votes, 1)
        self.assertEqual(idea.vote_differential, -1)
        self.assertEqual(idea.author.hits, 0)
        self.assertEqual(len(idea.voted_users.all()), 1)
        self.assertEqual(idea.voted_users.one(), user)
        self.assertTrue(idea.user_voted(u'username'))

    def test_registration_nosubmit(self):
        from flow.views import user_add
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = user_add(request)
        self.assertTrue('form' in result)

    def test_registration_submit_empty(self):
        from flow.views import user_add
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = user_add(request)
        self.assertTrue('form' in result)
        request = testing.DummyRequest(post={'form.submitted': 'Shoot'})
        result = user_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'username': u'Missing value',
                'confirm_pwrd': u'Missing value',
                'pwrd': u'Missing value',
                'email': u'Missing value',
                'name': u'Missing value'
            }
        )

    def test_registration_submit_schema_succeed(self):
        from flow.views import user_add
        from flow.models import User
        _registerRoutes(self.config)        
        request = testing.DummyRequest(
            post={
                'form.submitted': u'Register',
                'username': u'username',
                'pwrd': u'secret',
                'confirm_pwrd': u'secret',
                'email': u'username@example.com',
                'name': u'John Doe',
            }
        )
        user_add(request)
        users = self.session.query(User).all()
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user.username, u'username')
        self.assertEqual(user.name, u'John Doe')
        self.assertEqual(user.email, u'username@example.com')
        self.assertEqual(user.hits, 0)
        self.assertEqual(user.misses, 0)
        self.assertEqual(user.delivered_hits, 0)
        self.assertEqual(user.delivered_misses, 0)
        self.assertEqual(user.ideas, [])
        self.assertEqual(user.voted_ideas, [])

    def test_user_view(self):
        from flow.views import user_view
        self.config.testing_securitypolicy(u'username')
        _registerRoutes(self.config)
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        request.matchdict = {'username': u'username'}
        self._addUser()
        result = user_view(request)
        self.assertEqual(result['user'].username, u'username')
        self.assertEqual(result['user'].user_id, 1)

    def test_idea_view(self):
        from flow.views import idea_view
        self.config.testing_securitypolicy(u'username')
        _registerRoutes(self.config)
        _registerCommonTemplates(self.config)
        self._addIdea()
        request = testing.DummyRequest()
        request.matchdict = {'idea_id': 1}
        result = idea_view(request)
        self.assertEqual(result['idea'].title, u'title')
        self.assertEqual(result['idea'].idea_id, 1)
        self.assertEqual(result['viewer_username'], u'username')

    def test_tag_view(self):
        from flow.views import tag_view
        from flow.models import Tag
        self.config.testing_securitypolicy(u'username')
        _registerRoutes(self.config)
        _registerCommonTemplates(self.config)
        user = self._addUser()
        tag1 = Tag(u'bar')
        tag2 = Tag(u'foo')
        self.session.add_all([tag1, tag2])
        idea1 = self._addIdea(user=user)
        idea1.tags.append(tag1)
        idea2 = self._addIdea(user=user)
        idea2.tags.append(tag1)
        idea3 = self._addIdea(user=user)
        idea3.tags.append(tag2)
        self.session.flush()
        
        request = testing.DummyRequest()
        request.matchdict = {'tag_name': u'bar'}
        result = tag_view(request)
        ideas = result['ideas'].all()
        self.assertEqual(ideas[0].idea_id, idea1.idea_id)
        self.assertEqual(ideas[1].idea_id, idea2.idea_id)
        self.assertEqual(result['tag'], u'bar')

        request = testing.DummyRequest()
        request.matchdict = {'tag_name': u'foo'}
        result = tag_view(request)
        self.assertEqual(result['ideas'].one().idea_id, idea3.idea_id)
        self.assertEqual(result['tag'], u'foo')

    def test_about_view(self):
        from flow.views import about_view
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        about_view(request)

    def test_login_view_submit_fail(self):
        from flow.views import login_view
        _registerRoutes(self.config)
        self._addUser()
        request = testing.DummyRequest(
            post={
                'submit': u'Login',
                'login': u'username',
                'pwrd': u'wrongpwrd',
            }
        )
        login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Failed to login.'])


    def test_login_view_submit_success(self):
        from flow.views import login_view
        _registerRoutes(self.config)
        self._addUser()
        request = testing.DummyRequest(
            post={
                'submit': u'Login',
                'login': u'username',
                'pwrd': u'pwrd',
            }
        )
        login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged in successfully.'])

    def test_logout_view(self):
        from flow.views import logout_view
        _registerRoutes(self.config)
        request = testing.DummyRequest()
        logout_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged out successfully.'])
