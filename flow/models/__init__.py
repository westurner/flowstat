from flow.models.sql import Base
from flow.models.sql import DBSession
from flow.models.sql import initialize_sql
from flow.security.models import User

from pyramid.security import Everyone
from pyramid.security import Authenticated
from pyramid.security import Allow

class RootFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'post')
    ]
    def __init__(self, request):
        pass



