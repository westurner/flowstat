from pyramid_restler.interfaces import IContext

from collections import Iterable

from pyramid.decorator import reify

from sqlalchemy.schema import Column

from zope.interface import implements

from ..models import json

class PlainContext(object):
    """Adapts a numbers class to the
    :class:`pyramid_restler.interfaces.IContext` interface."""

    implements(IContext)

    json_encoder = json.DefaultJSONEncoder

    def __init__(self, request, fn):
        self.request = request
        self.fn = fn

    #@reify
    #def session(self):
    #    return self.session_factory()

    #def session_factory(self):
    #    return self.request.db_session

    def get_collection(self, ):
        """ """
        return []

    def get_member(self, id):
        return self.fn(id) #get_number(int(n, 0))

    def create_member(self, data):
        # redirect
        raise NotImplementedError()
        #member = self.entity(**data)
        #self.session.add(member)
        #self.session.commit()
        #return member

    #def update_member(self, id, data):
    #    q = self.session.query(self.entity)
    #    member = q.get(id)
    #    if member is None:
    #        return None
    #    for name in data:
    #        setattr(member, name, data[name])
    #    self.session.commit()
    #    return member

    #def delete_member(self, id):
    #    q = self.session.query(self.entity)
    #    member = q.get(id)
    #    if member is None:
    #        return None
    #    self.session.delete(member)
    #    self.session.commit()
    #    return member



    def get_member_id_as_string(self, member):
        id = str(member.get('n'))
        if isinstance(id, basestring):
            return id
        else:
            return json.dumps(id, cls=self.json_encoder)

    def to_json(self, value, fields=None, wrap=True):
        """Convert instance or sequence of instances to JSON.

        ``value`` is a single ORM instance or an iterable that yields
        instances.

        ``fields`` is a list of fields to include for each instance.

        ``wrap`` indicates whether or not the result should be wrapped or
        returned as-is.

        """
        #obj = self.get_json_obj(value, fields, wrap)
        return json.dumps(value, cls=self.json_encoder)

    def get_json_obj(self, value, fields, wrap):
        if fields is None:
            fields = self.default_fields
        if not isinstance(value, Iterable):
            value = [value]
        obj = [self.member_to_dict(m, fields) for m in value]
        if wrap:
            obj = self.wrap_json_obj(obj)
        return obj

    def wrap_json_obj(self, obj):
        return dict(
            results=obj,
            result_count=len(obj),
        )

    def member_to_dict(self, member, fields=None):
        if fields is None:
            fields = self.default_fields
        return member
        #dict((name, getattr(member, name)) for name in fields)

    @reify
    def default_fields(self):
        fields = set('n')
        return fields
        class_attrs = dir(self.entity)
        for name in class_attrs:
            if name.startswith('_'):
                continue
            attr = getattr(self.entity, name)
            if isinstance(attr, property):
                fields.append(name)
            else:
                try:
                    clause_el = attr.__clause_element__()
                except AttributeError:
                    pass
                else:
                    if issubclass(clause_el.__class__, Column):
                        fields.append(name)
        fields = set(fields)
        return fields

