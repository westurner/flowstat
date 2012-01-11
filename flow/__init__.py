from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.renderers import JSONP

from sqlalchemy import engine_from_config
from flow.models import initialize_sql
from flow.models.rdfmodels import initialize_rdflib

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'db_main.')
    initialize_sql(engine)

    #data_engine = engine_from_config(settings, 'db_data.')
    #initialize_sql(data_engine)

    initialize_rdflib(virtuoso_connstr=settings['rdflib.virtuoso_connstr'])

    session_factory = UnencryptedCookieSessionFactoryConfig('secret')

    authn_policy = AuthTktAuthenticationPolicy('s0secret')
    authz_policy = ACLAuthorizationPolicy()

    settings.setdefault('jinja2.i18n.domain', 'flow')

    config = configure_app(settings,
            authn_policy, authz_policy, session_factory)

    config.scan()
    return config.make_wsgi_app()

def configure_app(settings, authn_policy, authz_policy, session_factory):
    config = Configurator(
        settings=settings,
        root_factory='flow.models.RootFactory',
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        session_factory=session_factory
    )
    config.add_translation_dirs('locale/')
    config.include('pyramid_jinja2')
    config.add_renderer('jsonp', JSONP(param_name='callback'))

    config.add_subscriber('flow.subscribers.add_base_template',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('flow.subscribers.csrf_validation',
                          'pyramid.events.NewRequest')

    config.add_static_view('static', 'flow:static')


    config.add_route('sparql_query', '/sparql')
    config.add_route('deniz', '/browse')

    config.add_route('factors', '/factors')
    config.add_route('factors_of', '/factors/{n}')


    config.add_route('reference_graph_docs', '/graphs/docs')
    config.add_route('reference_graph', '/graphs/{graphname}')
    config.add_route('reference_graphs', '/graphs')

    config.add_route('idea', '/ideas/{idea_id}')
    config.add_route('user', '/users/{username}')
    config.add_route('tag', '/tags/{tag_name}')
    config.add_route('idea_add', '/idea_add')
    config.add_route('idea_vote', '/idea_vote')

    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('about', '/about')
    config.add_route('main', '/')

    return config


