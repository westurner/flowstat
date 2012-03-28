import unittest

from pyramid import testing

from flow.models.sql import _initialize_sql_test

from flow import _register_routes, _register_common_templates

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _initialize_sql_test()
        self.config = testing.setUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()

    def _addUser(self, username=u'username'):
        from flow.models import User
        user = User(username=username, passphrase=u'passphrase', name=u'name',
                    email=u'email@example.com')
        self.session.add(user)
        self.session.flush()
        return user

    def _addIdea(self, target=None, user=None):
        from flow.shootout.models import Idea
        if not user:
            user = self._addUser()
        idea = Idea(target=target, author=user, title=u'title',
                    text=u'text')
        self.session.add(idea)
        self.session.flush()
        return idea

    def test_ideas_main(self):
        from flow.shootout.views import ideas_main
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        result = ideas_main(request)
        self.assertEqual(result['username'], u'username')
        self.assertEqual(len(result['toplists']), 4)

    def test_idea_add_nosubmit_idea(self):
        from flow.shootout.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        result = idea_add(request)
        self.assertEqual(result['target'], None)
        self.assertEqual(result['kind'], 'idea')

    def test_idea_add_nosubmit_comment(self):
        from flow.shootout.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
        idea = self._addIdea()
        request = testing.DummyRequest(params={'target': idea.idea_id})
        result = idea_add(request)
        self.assertEqual(result['target'], idea)
        self.assertEqual(result['kind'], 'comment')

    def test_idea_add_not_existing_target(self):
        from flow.shootout.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest(params={'target': 100})
        result = idea_add(request)
        self.assertEqual(result.code, 404)


    def test_idea_add_submit_schema_fail_empty_params(self):
        from flow.shootout.views import idea_add
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
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
        from flow.shootout.views import idea_add
        from flow.shootout.models import Idea
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
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
        from flow.shootout.views import idea_vote
        from flow.models import User
        _register_routes(self.config)
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
        from flow.shootout.views import idea_vote
        from flow.models import User
        _register_routes(self.config)
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

    def test_idea_view(self):
        from flow.shootout.views import idea_view
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
        self._addIdea()
        request = testing.DummyRequest()
        request.matchdict = {'idea_id': 1}
        result = idea_view(request)
        self.assertEqual(result['idea'].title, u'title')
        self.assertEqual(result['idea'].idea_id, 1)
        self.assertEqual(result['viewer_username'], u'username')

    def test_tag_view(self):
        from flow.shootout.views import tag_view
        from flow.shootout.models import Tag
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
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

